import pytest
import os
import csv
import asyncio
from unittest.mock import patch, AsyncMock
from dotenv import load_dotenv

# DeepEval Imports
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, GEval, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCaseParams

# App Imports
from app.core.config import settings
from app.services.local_llm_service import local_llm_service
from app.services.evaluation_service import evaluation_service

# Agent Imports
from app.services.agents.question_cleaning_agent import question_cleaning_agent
from app.services.agents.evaluation_agent import evaluation_agent
from tests.eval_data import (
    STRONG_CANDIDATE_RESUME, 
    QUESTION_GEN_TEST_CASES, 
    EVALUATION_TEST_CASES
)

TEST_RESULTS = []

# ==========================================
#  ENVIRONMENT SETUP FIXTURE
# ==========================================
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    load_dotenv() 
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        pytest.skip("OPENAI_API_KEY not found in .env. Cannot run DeepEval.")
    
    os.environ["OPENAI_API_KEY"] = openai_key
    settings.HUGGINGFACE_LLM_API_URL = os.getenv("HUGGINGFACE_LLM_API_URL")
    settings.HUGGINGFACE_LLM_API_KEY = os.getenv("HUGGINGFACE_LLM_API_KEY")
    settings.HUGGINGFACE_EVALUATION_API_URL = os.getenv("HUGGINGFACE_EVALUATION_API_URL")
    settings.HUGGINGFACE_EVALUATION_API_KEY = os.getenv("HUGGINGFACE_EVALUATION_API_KEY")

    print("\nRe-initializing AI Services with .env credentials...")
    local_llm_service._initialized = False
    local_llm_service.__init__()
    
    evaluation_service._initialized = False
    evaluation_service.__init__()

# ==========================================
#  CSV REPORT GENERATOR
# ==========================================
@pytest.fixture(scope="session", autouse=True)
def csv_report_generator():
    yield
    print("\nGenerating CSV Report...")
    csv_file = "agent_evaluation_results.csv"
    fieldnames = ["Test_Type", "Job_Role", "Domain", "Input_Context", "Agent_Output", "Score_Value", "Feedback", "Status"]
    
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in TEST_RESULTS:
                writer.writerow(row)
        print(f"Report saved successfully to {csv_file}")
    except Exception as e:
        print(f"Failed to save CSV report: {e}")

# ==========================================
#  MOCKS
# ==========================================
@pytest.fixture
def mock_vector_store():
    with patch('app.services.agents.question_cleaning_agent._retrieve_resume_context_by_domain', new_callable=AsyncMock) as mock:
        yield mock

# ==========================================
#  TEST 1: Question Generation
# ==========================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_data", QUESTION_GEN_TEST_CASES)
async def test_question_agent_faithfulness(mock_vector_store, test_data):
    mock_vector_store.return_value = test_data["resume_text"]
    
    raw_question = f"Tell me about your experience with {test_data['domain']}."
    print(f"\n[Gen Test] Role: {test_data['job_role']} | Domain: {test_data['domain']}")

    try:
        agent_result = await question_cleaning_agent(
            generated_question=raw_question,
            domain=test_data["domain"],
            resume_id="dummy_id",
            orchestrator_intent=test_data["intent"]
        )
        
        final_question = agent_result["cleaned_question"]
        print(f"[Agent Output]: {final_question}")
        
        test_case = LLMTestCase(
            input=raw_question,
            actual_output=final_question,
            retrieval_context=[test_data["resume_text"]]
        )

        faithfulness = FaithfulnessMetric(threshold=0.7, model="gpt-4o")
        relevance = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o")
        
        assert_test(test_case, [faithfulness, relevance])
        
        TEST_RESULTS.append({
            "Test_Type": "Question Generation",
            "Job_Role": test_data["job_role"],
            "Domain": test_data["domain"],
            "Input_Context": test_data["intent"],
            "Agent_Output": final_question,
            "Score_Value": "N/A",
            "Feedback": "Faithfulness/Relevance Passed",
            "Status": "PASSED"
        })

    except Exception as e:
        TEST_RESULTS.append({
            "Test_Type": "Question Generation",
            "Job_Role": test_data["job_role"],
            "Domain": test_data["domain"],
            "Input_Context": test_data["intent"],
            "Agent_Output": "Error",
            "Score_Value": "N/A",
            "Feedback": str(e),
            "Status": "FAILED"
        })
        raise e

# ==========================================
#  TEST 2: Answer Evaluation
# ==========================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_data", EVALUATION_TEST_CASES)
async def test_evaluation_agent_grading_logic(test_data):
    state = {
        "job_role": test_data["job_role"],
        "evaluation_context": {
            "question": test_data["question"],
            "answer": test_data["answer"],
            "domain": test_data["domain"],
            "difficulty": "medium"
        }
    }

    print(f"\n[Eval Test] Answer Quality: {test_data['expected_quality']}")

    try:
        result = await evaluation_agent(state)
        
        agent_score = result["evaluation_agent_response"]["score"]
        agent_feedback = result["evaluation_agent_response"]["feedback"]["feedback_text"]
        
        print(f"[Score]: {agent_score}")

        # 1. Check Score Range
        min_s, max_s = test_data["expected_score_range"]
        is_score_valid = min_s <= agent_score <= max_s
        
        status = "PASSED"
        error_msg = "Metrics Passed"
        
        if not is_score_valid:
            status = "FAILED"
            error_msg = f"Score {agent_score} outside range {min_s}-{max_s}"

        TEST_RESULTS.append({
            "Test_Type": "Answer Evaluation",
            "Job_Role": test_data["job_role"],
            "Domain": test_data["domain"],
            "Input_Context": f"Q: {test_data['question']} | A: {test_data['answer'][:50]}...",
            "Agent_Output": f"Score: {agent_score}",
            "Score_Value": agent_score,
            "Feedback": agent_feedback[:200],
            "Status": status
        })

        assert is_score_valid, error_msg

        # 2. Check Feedback Alignment (SMARTER PROMPT)
        alignment_metric = GEval(
            name="Feedback-Score Alignment",
            criteria="""
            Analyze if the feedback text is logically consistent with the numeric score.
            
            1. FOR LOW SCORES (<0.5):
               - The feedback SHOULD explain the correct concept or what was missing.
               - Do NOT mark it as 'misaligned' just because the text is high quality or educational.
               - Educational correction IS appropriate for low scores.
               
            2. FOR HIGH SCORES (>0.7):
               - The feedback SHOULD acknowledge the answer is correct.
               - It MAY include minor suggestions for improvement ("tough love").
               - Do NOT mark it as 'misaligned' just because it offers constructive criticism.
            
            Pass the test if the feedback explains the score, corrects mistakes, or helps the candidate improve.
            """,
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=0.6, 
            model="gpt-4o"
        )
        
        test_case = LLMTestCase(
            input=f"Question: {test_data['question']}\nAnswer: {test_data['answer']}",
            actual_output=f"Score: {agent_score}\nFeedback: {agent_feedback}"
        )
        
        assert_test(test_case, [alignment_metric])
        
    except Exception as e:
        if TEST_RESULTS and TEST_RESULTS[-1]["Input_Context"].startswith(f"Q: {test_data['question']}"):
             TEST_RESULTS[-1]["Status"] = "FAILED"
             TEST_RESULTS[-1]["Feedback"] = str(e)
        raise e