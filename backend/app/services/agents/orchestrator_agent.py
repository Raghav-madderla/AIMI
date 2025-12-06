"""
Orchestrator Agent

Purpose: Coordinates the interview flow by:
1. Getting interview plan from LLM (domains to cover)
2. Selecting domains in round-robin fashion
3. Using even difficulty distribution
4. All decisions are LLM-driven, no hardcoded sentences
"""

from typing import Dict, List
from app.utils.langgraph_state import InterviewState
from app.services.local_llm_service import local_llm_service


# Configuration
DEFAULT_TOTAL_QUESTIONS = 10  # Total questions to ask (excluding intro)
DIFFICULTY_DISTRIBUTION = {
    10: ["easy", "easy", "easy", "medium", "medium", "medium", "hard", "hard", "hard", "hard"],
    7: ["easy", "easy", "medium", "medium", "medium", "hard", "hard"],
    5: ["easy", "medium", "medium", "hard", "hard"],
}


async def orchestrator_agent(state: InterviewState) -> Dict:
    """
    Orchestrator Agent - Coordinates the interview flow
    
    Flow:
    1. Greeting phase → Intro question
    2. Intro phase → Generate interview plan from LLM
    3. Technical questions → Round-robin domains with even difficulty
    4. Closing → End interview
    """
    
    conversation_phase = state.get("conversation_phase", "greeting")
    question_count = state.get("question_count", 0)
    current_round = state.get("current_round", "welcome")
    job_role = state.get("job_role", "")
    resume_summary = state.get("resume_summary")
    planned_domains = state.get("planned_domains")
    difficulty_sequence = state.get("difficulty_sequence")
    total_questions = state.get("total_questions", DEFAULT_TOTAL_QUESTIONS)
    
    # DEBUG: Log current state
    print(f"ORCHESTRATOR DEBUG:")
    print(f"  conversation_phase: {conversation_phase}")
    print(f"  question_count: {question_count}")
    print(f"  current_round: {current_round}")
    print(f"  planned_domains: {planned_domains}")
    print(f"  resume_summary exists: {resume_summary is not None}")
    
    # Check if we just generated a question and it's waiting to be sent
    question_agent_response = state.get("question_agent_response")
    if question_agent_response:
        if question_agent_response.get("question") and not question_agent_response.get("error"):
            pending_question = state.get("pending_question")
            if pending_question:
                return {
                    "next_action": "wait",
                    "status": "active"
                }
            else:
                return {
                    "pending_question": question_agent_response.get("question"),
                    "next_action": "wait",
                    "status": "active"
                }
        elif question_agent_response.get("error"):
            return {
                "next_action": "complete",
                "status": "error"
            }
    
    # =========================================
    # GREETING PHASE
    # =========================================
    if conversation_phase == "greeting":
        return {
            "conversation_phase": "intro_question",
            "current_round": "intro",
            "next_action": "generate_question"
        }
    
    # =========================================
    # INTRO PHASE - Ask "Tell me about yourself"
    # =========================================
    if conversation_phase == "intro_question":
        if question_count > 0:
            # User answered intro question, now plan the interview
            print(f"Intro answered. Planning interview based on resume summary...")
            
            # Generate interview plan if not already done
            if not planned_domains:
                plan_result = await _generate_interview_plan(resume_summary, job_role, total_questions)
                planned_domains = plan_result.get("domains", [])
                difficulty_sequence = plan_result.get("difficulty_sequence", [])
                
                print(f"Interview plan generated:")
                print(f"  Domains: {planned_domains}")
                print(f"  Difficulty sequence: {difficulty_sequence}")
            
            # Set up the first technical question
            # technical_question_index = 0 (first technical question after intro)
            first_domain = planned_domains[0] if planned_domains else "Python"
            first_difficulty = difficulty_sequence[0] if difficulty_sequence else "easy"
            
            print(f"Technical Q#1: Domain={first_domain}, Difficulty={first_difficulty}")
        
            # Generate orchestrator intent for first question
            orchestrator_intent = await _generate_orchestrator_intent(first_domain, job_role, first_difficulty)
            
            # Transition to technical questions WITH question_context set
            return {
                "conversation_phase": "technical_question",
                "current_round": "technical_deep_dive",
                "planned_domains": planned_domains,
                "difficulty_sequence": difficulty_sequence,
                "selected_domain": first_domain,
                "difficulty": first_difficulty,
                "orchestrator_intent": orchestrator_intent,
                "question_context": {
                    "domain": first_domain,
                    "difficulty": first_difficulty,
                    "round": "technical_deep_dive"
                },
                "next_action": "generate_question",
                "status": "active"
            }
        else:
            # Generate intro question using LLM
            print(f"Generating intro question for {job_role}")
            intro_question = await _generate_intro_question(job_role)
            
            return {
                "question_agent_response": {
                    "question": intro_question,
                    "domain": "Introduction",
                    "difficulty": "easy",
                    "error": None
                },
                "next_action": "wait",
                "status": "active"
            }
    
    # =========================================
    # TECHNICAL QUESTIONS PHASE
    # =========================================
    if conversation_phase == "technical_question":
        # Check if we've asked enough questions
        # question_count includes intro question, so technical questions = question_count - 1
        technical_question_index = question_count - 1  # Subtract intro question
        
        if technical_question_index >= total_questions:
            print(f"All {total_questions} technical questions asked. Ending interview.")
            return {
                "conversation_phase": "closing",
                "status": "completed",
                "next_action": "complete"
            }
        
        # Ensure we have planned domains
        if not planned_domains:
            print(f"No planned domains, generating plan...")
            plan_result = await _generate_interview_plan(resume_summary, job_role, total_questions)
            planned_domains = plan_result.get("domains", [])
            difficulty_sequence = plan_result.get("difficulty_sequence", [])
        
        # Select domain using round-robin
        domain_index = technical_question_index % len(planned_domains)
        selected_domain = planned_domains[domain_index]
        
        # Get difficulty from pre-planned sequence
        if difficulty_sequence and technical_question_index < len(difficulty_sequence):
            difficulty = difficulty_sequence[technical_question_index]
        else:
            # Fallback to even distribution
            difficulty = _get_difficulty_for_index(technical_question_index, total_questions)
        
        print(f"Technical Q#{technical_question_index + 1}: Domain={selected_domain}, Difficulty={difficulty}")
        
        # Generate orchestrator intent using LLM (no hardcoded sentences)
        orchestrator_intent = await _generate_orchestrator_intent(selected_domain, job_role, difficulty)
        
        return {
            "selected_domain": selected_domain,
            "difficulty": difficulty,
            "orchestrator_intent": orchestrator_intent,
            "question_context": {
        "domain": selected_domain,
        "difficulty": difficulty,
                "round": "technical_deep_dive"
            },
            "planned_domains": planned_domains,
            "difficulty_sequence": difficulty_sequence,
            "next_action": "generate_question",
            "status": "active"
        }
    
    # =========================================
    # CLOSING PHASE
    # =========================================
    if conversation_phase == "closing":
        return {
            "status": "completed",
            "next_action": "complete"
        }
    
    # Default fallback
    print(f"FALLBACK: No phase matched! Phase={conversation_phase}")
    return {
        "next_action": "wait",
        "status": "active"
    }


async def _generate_interview_plan(resume_summary: dict, job_role: str, total_questions: int) -> Dict:
    """
    Generate interview plan using LLM based on resume summary
    
    Returns:
        {
            "domains": ["Domain1", "Domain2", ...],  # Ordered by priority
            "difficulty_sequence": ["easy", "medium", "hard", ...]
        }
    """
    
    # Get recommended domains from resume summary
    if resume_summary:
        recommended_domains = resume_summary.get("recommended_domains", [])
        candidate_overview = resume_summary.get("candidate_overview", "")
        technical_skills = resume_summary.get("technical_skills", [])
    else:
        recommended_domains = []
        candidate_overview = ""
        technical_skills = []
    
    available_domains = [
        "Python", "SQL", "Data Engineering", "Data Analysis",
        "Machine Learning", "Deep Learning", "Artificial Intelligence",
        "System Design", "Statistics"
    ]
    
    prompt = f"""You are an expert technical interviewer planning an interview for a {job_role} position.

CANDIDATE INFORMATION:
- Overview: {candidate_overview}
- Technical Skills: {', '.join(technical_skills) if technical_skills else 'Not specified'}
- Recommended Domains from Resume: {', '.join(recommended_domains) if recommended_domains else 'Not specified'}

AVAILABLE DOMAINS TO CHOOSE FROM:
{', '.join(available_domains)}

TASK:
Plan the technical portion of the interview with {total_questions} questions.
Select the most relevant domains based on the candidate's background and the {job_role} role requirements.

OUTPUT FORMAT (valid JSON only):
{{
    "domains": ["Domain1", "Domain2", "Domain3", "Domain4", "Domain5"],
    "reasoning": "Brief explanation of domain selection"
}}

INSTRUCTIONS:
1. Select 4-6 domains that best match the candidate's experience AND the {job_role} requirements
2. Order domains by priority - start with the candidate's strongest areas
3. Include at least one domain that tests breadth (not just their comfort zone)
4. Return ONLY valid JSON

JSON Output:"""

    try:
        messages = [
            {"role": "system", "content": "You are an expert technical interviewer. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = await local_llm_service.generate_json_async(messages, max_new_tokens=500, temperature=0.3)
        
        if result and result.get("domains"):
            domains = result["domains"]
            # Validate domains
            validated_domains = [d for d in domains if d in available_domains]
            if not validated_domains:
                validated_domains = recommended_domains if recommended_domains else ["Python", "SQL", "Machine Learning"]
        else:
            # Use recommended domains from resume summary
            validated_domains = recommended_domains if recommended_domains else ["Python", "SQL", "Machine Learning"]
        
        # Generate difficulty sequence with even distribution
        difficulty_sequence = _generate_difficulty_sequence(total_questions)
        
        print(f"Interview plan created: {validated_domains}")
        
        return {
            "domains": validated_domains[:6],  # Max 6 domains
            "difficulty_sequence": difficulty_sequence
        }
        
    except Exception as e:
        print(f"Interview plan generation failed: {str(e)}")
        # Fallback to recommended domains or defaults
        fallback_domains = recommended_domains if recommended_domains else ["Python", "SQL", "Machine Learning", "Data Analysis"]
        return {
            "domains": fallback_domains[:6],
            "difficulty_sequence": _generate_difficulty_sequence(total_questions)
        }


def _generate_difficulty_sequence(total_questions: int) -> List[str]:
    """
    Generate even difficulty distribution
    
    For 10 questions: 3 easy, 3 medium, 4 hard
    For 7 questions: 2 easy, 2 medium, 3 hard
    For 5 questions: 1 easy, 2 medium, 2 hard
    """
    if total_questions in DIFFICULTY_DISTRIBUTION:
        return DIFFICULTY_DISTRIBUTION[total_questions].copy()
    
    # Calculate distribution for custom question count
    easy_count = total_questions // 3
    medium_count = total_questions // 3
    hard_count = total_questions - easy_count - medium_count
    
    sequence = (["easy"] * easy_count) + (["medium"] * medium_count) + (["hard"] * hard_count)
    return sequence


def _get_difficulty_for_index(index: int, total_questions: int) -> str:
    """Get difficulty based on question index"""
    sequence = _generate_difficulty_sequence(total_questions)
    if index < len(sequence):
        return sequence[index]
    return "medium"


async def _generate_intro_question(job_role: str) -> str:
    """Generate intro question using LLM"""
    prompt = f"""Generate a warm, professional interview opening question for a {job_role} position.

The question should:
- Ask the candidate to introduce themselves
- Be conversational and welcoming
- Encourage them to share their background and interests

Output ONLY the question text, nothing else."""

    try:
        messages = [
            {"role": "system", "content": "You are a friendly professional interviewer. Output only the question."},
            {"role": "user", "content": prompt}
        ]
        
        intro_question = await local_llm_service.generate_async(messages, max_new_tokens=100, temperature=0.7)
        
        if intro_question:
            intro_question = intro_question.strip().strip('"\'')
            intro_question = intro_question.split('\n')[0].strip()
            
            if len(intro_question) > 10:
                return intro_question
        
        # Fallback
        return f"Welcome! I'm excited to learn more about you. Could you start by telling me about your background and what draws you to this {job_role} role?"
        
    except Exception as e:
        print(f"Intro question generation failed: {str(e)}")
        return f"Welcome! I'm excited to learn more about you. Could you start by telling me about your background and what draws you to this {job_role} role?"


async def _generate_orchestrator_intent(domain: str, job_role: str, difficulty: str) -> str:
    """Generate orchestrator intent using LLM (no hardcoded sentences)"""
    prompt = f"""You are an interviewer for a {job_role} position.
You want to assess the candidate's {domain} skills at {difficulty} difficulty level.

Generate a brief, natural intent statement (1 sentence) that describes what you want to explore.
This is internal context, not shown to the candidate.

Examples:
- "Explore their practical experience with Python data structures and when to use each"
- "Assess their understanding of ML model evaluation techniques"
- "Test their ability to design scalable data pipelines"

Output ONLY the intent statement:"""

    try:
        messages = [
            {"role": "system", "content": "Output only a brief intent statement."},
            {"role": "user", "content": prompt}
        ]
        
        intent = await local_llm_service.generate_async(messages, max_new_tokens=50, temperature=0.5)
        
        if intent:
            intent = intent.strip().strip('"\'')
            if len(intent) > 10:
                return intent
        
        return f"Assess {domain} skills at {difficulty} level"
        
    except Exception as e:
        print(f"Intent generation failed: {str(e)}")
        return f"Assess {domain} skills at {difficulty} level"


def should_continue(state: InterviewState) -> str:
    """Routing function for LangGraph workflow"""
    next_action = state.get("next_action", "wait")
    status = state.get("status", "active")
    
    if status == "completed" or status == "error" or next_action == "complete":
        return "complete"
    
    if next_action == "wait":
        return "complete"
    
    if next_action == "generate_question":
        return "generate_question"
    
    if next_action == "evaluate":
        return "evaluate"
    
    return "complete"
