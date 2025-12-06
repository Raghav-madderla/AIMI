from langgraph.graph import StateGraph, END
from typing import Dict, Literal
from app.utils.langgraph_state import InterviewState
from app.services.agents.orchestrator_agent import orchestrator_agent, should_continue
from app.services.agents.question_agent import question_agent
from app.services.agents.evaluation_agent import evaluation_agent
from app.services.agents.question_cleaning_agent import question_cleaning_agent


async def orchestrator_node(state: InterviewState) -> Dict:
    """Wrapper to make orchestrator async for LangGraph"""
    return await orchestrator_agent(state)


async def cleaning_agent_node(state: InterviewState) -> Dict:
    """
    Cleaning agent that refines questions by:
    1. Retrieving relevant resume chunks from VDB by domain
    2. Blending the question with candidate's experience
    """
    question_agent_response = state.get("question_agent_response")
    orchestrator_intent = state.get("orchestrator_intent", "")
    question_context = state.get("question_context") or {}
    resume_id = state.get("resume_id", "")  # Get resume_id for VDB lookup
    
    if not question_agent_response or not question_agent_response.get("question"):
        # No question to clean, pass through
        return {}
    
    generated_question = question_agent_response.get("question")
    domain = question_context.get("domain", "General")
    
    # Clean the question - now retrieves resume context from VDB by domain
    result = await question_cleaning_agent(
        generated_question=generated_question,
        domain=domain,
        resume_id=resume_id,
        orchestrator_intent=orchestrator_intent
    )
    
    if result.get("success"):
        # Update the question with cleaned version
        return {
            "question_agent_response": {
                "question": result["cleaned_question"],
                "domain": question_agent_response.get("domain"),
                "difficulty": question_agent_response.get("difficulty"),
                "error": None
            }
        }
    
    # If cleaning failed, keep original question
    return {}


def create_interview_workflow() -> StateGraph:
    """
    Create LangGraph workflow for interview orchestration with A2A protocol
    
    Flow:
    1. Orchestrator decides next action (what to ask, why)
    2. If generate_question → Question Agent generates raw question
    3. Question Cleaning Agent refines the question based on orchestrator's intent
    4. Return cleaned question to user
    5. If evaluate → Evaluation Agent analyzes answer
    6. Back to orchestrator for next decision
    7. Loop continues until complete
    """
    
    workflow = StateGraph(InterviewState)
    
    # Add nodes (agents)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("question_agent", question_agent)
    workflow.add_node("cleaning_agent", cleaning_agent_node)
    workflow.add_node("evaluation_agent", evaluation_agent)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional edges from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        should_continue,
        {
            "generate_question": "question_agent",
            "evaluate": "evaluation_agent",
            "complete": END
        }
    )
    
    # After question agent, clean the question
    workflow.add_edge("question_agent", "cleaning_agent")
    
    # After cleaning, go back to orchestrator to finalize
    workflow.add_edge("cleaning_agent", "orchestrator")
    
    # After evaluation agent, go back to orchestrator to update state
    workflow.add_edge("evaluation_agent", "orchestrator")
    
    # Compile the workflow
    return workflow.compile()


# Create the workflow instance
interview_workflow = create_interview_workflow()

