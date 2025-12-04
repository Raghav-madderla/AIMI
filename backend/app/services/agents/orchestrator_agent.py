"""
Conversational Orchestrator Agent

Acts like a real hiring manager - friendly, conversational, and strategic.
Guides the interview through different phases naturally.
"""

from typing import Dict
from app.utils.langgraph_state import InterviewState
from app.services.local_llm_service import local_llm_service


async def orchestrator_agent(state: InterviewState) -> Dict:
    """
    Orchestrator Agent - Acts like a human hiring manager
    
    Flow:
    1. Greeting phase - Warm welcome
    2. Intro phase - Ask "Tell me about yourself"
    3. Resume discussion - Go through resume points, appreciate and ask questions
    4. Technical deep dive - Ask domain-specific questions
    5. Closing - Thank the candidate
    
    The orchestrator decides what to ask and coordinates with other agents.
    """
    
    conversation_phase = state.get("conversation_phase", "greeting")
    current_resume_point_index = state.get("current_resume_point_index", 0)
    resume_summary = state.get("resume_summary")
    question_count = state.get("question_count", 0)
    current_round = state.get("current_round", "welcome")
    job_role = state.get("job_role", "")
    
    # DEBUG: Log current state
    print(f"ORCHESTRATOR DEBUG:")
    print(f"  conversation_phase: {conversation_phase}")
    print(f"  question_count: {question_count}")
    print(f"  current_round: {current_round}")
    print(f"  resume_summary exists: {resume_summary is not None}")
    
    # Check if we just generated a question and it's waiting to be sent
    question_agent_response = state.get("question_agent_response")
    if question_agent_response:
        if question_agent_response.get("question") and not question_agent_response.get("error"):
            # Question generated - now it needs to be cleaned
            # Check if we're waiting for cleaning
            pending_question = state.get("pending_question")
            if pending_question:
                # Question is already cleaned, ready to send
                return {
                    "next_action": "wait",
                    "status": "active"
                }
            else:
                # Mark question as pending for cleaning
                return {
                    "pending_question": question_agent_response.get("question"),
                    "next_action": "wait",
                    "status": "active"
                }
        elif question_agent_response.get("error"):
            # Question generation failed
            return {
                "next_action": "complete",
                "status": "error"
            }
    
    # GREETING PHASE
    if conversation_phase == "greeting":
        # This is handled in interview_service.generate_welcome_message
        # Move to intro phase after greeting
        return {
            "conversation_phase": "intro_question",
            "current_round": "intro",
            "next_action": "generate_question"
        }
    
    # INTRO PHASE - Ask "Tell me about yourself"
    if conversation_phase == "intro_question":
        # Check if we've already asked the intro question (question_count > 0 means we've asked something)
        print(f"INTRO PHASE CHECK: question_count = {question_count}")
        if question_count > 0:
            # User has answered, DON'T just transition - actually process resume discussion!
            print(f"Moving to resume_point phase - will process in this call")
            conversation_phase = "resume_point"
            current_round = "resume_discussion"
            # Continue execution to the resume_point block below (don't return yet!)
        else:
            # question_count == 0, generate intro question
            print(f"GENERATING intro question (question_count = 0)")
            
            # Generate a warm intro question using local LLM
            prompt = f"""You are AIMI, a friendly AI hiring manager conducting an interview for a {job_role} position.

Generate a warm, conversational follow-up after your initial greeting. Ask the candidate to introduce themselves.

Keep it natural and friendly, like: "To get started, I'd love to hear about your journey. Could you tell me a bit about yourself and what excites you about this role?"

Return ONLY the question, nothing else."""

            try:
                messages = [
                        {"role": "system", "content": "You are AIMI, a friendly AI interviewer."},
                        {"role": "user", "content": prompt}
                ]
                
                intro_question = local_llm_service.generate(messages, max_new_tokens=150, temperature=0.8)
                
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
            except Exception as e:
                print(f"Intro question generation failed: {str(e)}")
                # Fallback intro question
                return {
                    "question_agent_response": {
                        "question": "Thank you for joining! To get started, could you tell me a bit about yourself and what excites you about this role?",
                        "domain": "Introduction",
                        "difficulty": "easy",
                        "error": None
                    },
                    "next_action": "wait",
                    "status": "active"
                }
    
    # RESUME DISCUSSION PHASE
    if conversation_phase == "resume_point":
        print(f"RESUME DISCUSSION PHASE")
        
        # Check if we have resume summary
        if not resume_summary:
            print(f"No resume summary, skipping to technical")
            # Skip to technical if no resume summary
            return {
                "conversation_phase": "technical_question",
                "current_round": "technical_deep_dive",
                "next_action": "generate_question"
            }
        
        summary_points = resume_summary.get("summary_points", [])
        print(f"Resume has {len(summary_points)} summary points")
        print(f"Current index: {current_resume_point_index}")
        
        # Check if we've covered all resume points
        if current_resume_point_index >= len(summary_points):
            print(f"All resume points covered, moving to technical")
            # Move to technical deep dive
            return {
                "conversation_phase": "technical_question",
                "current_round": "technical_deep_dive",
                "current_resume_point_index": 0,  # Reset
                "next_action": "generate_question"
            }
        
        print(f"Processing resume point #{current_resume_point_index}")
        
        # Get current resume point
        try:
            current_point = summary_points[current_resume_point_index]
            point_text = current_point.get("point", "")
            domains = current_point.get("domains", ["General"])
            significance = current_point.get("significance", "medium")
            talking_angle = current_point.get("talking_angle", "")
            
            print(f"Point: {point_text[:100]}")
            print(f"Domains: {domains}")
        except Exception as e:
            print(f"ERROR getting resume point: {str(e)}")
            # Fallback to technical
            return {
                "conversation_phase": "technical_question",
                "current_round": "technical_deep_dive",
                "next_action": "generate_question"
            }
        
        # Orchestrator decides what to ask about this point
        prompt = f"""You are AIMI, a hiring manager reviewing a candidate's resume for a {job_role} position.

You're discussing this achievement from their resume:
"{point_text}"

Relevant technical areas: {', '.join(domains)}

What you want to explore: {talking_angle}

Your task:
1. Make a brief, warm comment appreciating this achievement (1 sentence)
2. Decide what specific aspect you want to ask about (be specific)
3. Identify the PRIMARY technical domain to focus on (choose ONE from: {', '.join(domains)})

Respond in this EXACT format:
COMMENT: [Your appreciative comment]
INTENT: [What you want to ask about - be specific]
DOMAIN: [Single domain name]
"""

        try:
            messages = [
                    {"role": "system", "content": "You are an expert hiring manager."},
                    {"role": "user", "content": prompt}
            ]
            
            orchestrator_response = local_llm_service.generate(messages, max_new_tokens=300, temperature=0.7)
            
            # Parse response
            comment = ""
            intent = ""
            domain = domains[0] if domains else "General"
            
            for line in orchestrator_response.split('\n'):
                if line.startswith("COMMENT:"):
                    comment = line.replace("COMMENT:", "").strip()
                elif line.startswith("INTENT:"):
                    intent = line.replace("INTENT:", "").strip()
                elif line.startswith("DOMAIN:"):
                    domain = line.replace("DOMAIN:", "").strip()
            
            # Determine difficulty based on significance
            difficulty_map = {"high": "hard", "medium": "medium", "low": "easy"}
            difficulty = difficulty_map.get(significance, "medium")
            
            print(f"Orchestrator Decision:")
            print(f"   Comment: {comment}")
            print(f"   Intent: {intent}")
            print(f"   Domain: {domain}")
            print(f"   Difficulty: {difficulty}")
            print(f"   Moving to next resume point: {current_resume_point_index} -> {current_resume_point_index + 1}")
            
            # Store orchestrator's intent and comment for later use
            return {
                "orchestrator_intent": f"{comment} {intent}",
                "selected_domain": domain,
                "difficulty": difficulty,
                "question_context": {
                    "domain": domain,
                    "difficulty": difficulty,
                    "resume_context": point_text,
                    "job_role": job_role,
                    "round": "resume_discussion",
                    "orchestrator_comment": comment,
                    "orchestrator_intent": intent
                },
                "current_resume_point_index": current_resume_point_index + 1,  # Move to next point AFTER this question
                "next_action": "generate_question",
                "status": "active"
            }
            
        except Exception as e:
            print(f"Orchestrator planning failed: {str(e)}")
            # Fallback: Generate a simple question
            return {
                "orchestrator_intent": f"Tell me more about: {point_text}",
                "selected_domain": domains[0] if domains else "General",
                "difficulty": "medium",
                "question_context": {
                    "domain": domains[0] if domains else "General",
                    "difficulty": "medium",
                    "resume_context": point_text,
                    "job_role": job_role,
                    "round": "resume_discussion"
                },
                "current_resume_point_index": current_resume_point_index + 1,
                "next_action": "generate_question",
                "status": "active"
            }
    
    # TECHNICAL DEEP DIVE PHASE
    if conversation_phase == "technical_question":
        # Ask a few more technical questions (5-7 questions total)
        MAX_TOTAL_QUESTIONS = 7
        
        if question_count >= MAX_TOTAL_QUESTIONS:
            # End interview
            return {
                "conversation_phase": "closing",
                "status": "completed",
                "next_action": "complete"
            }
        
        # Select a technical domain (could be from resume or general)
        # For now, cycle through common domains
        technical_domains = ["Python", "System Design", "Machine Learning", "SQL", "Data Structures"]
        selected_domain = technical_domains[question_count % len(technical_domains)]
        
        # Adjust difficulty based on performance
        evaluation_history = state.get("evaluation_history", [])
        difficulty = state.get("difficulty", "medium")
        
        if len(evaluation_history) >= 2:
            recent_scores = [eval.get("score", 0.5) for eval in evaluation_history[-3:]]
            avg_score = sum(recent_scores) / len(recent_scores)
            
            if avg_score > 0.8 and difficulty != "hard":
                difficulty = "hard"
            elif avg_score < 0.5 and difficulty != "easy":
                difficulty = "easy"
        
        return {
            "selected_domain": selected_domain,
            "difficulty": difficulty,
            "orchestrator_intent": f"Test knowledge in {selected_domain}",
            "question_context": {
        "domain": selected_domain,
        "difficulty": difficulty,
                "resume_context": "",
        "job_role": job_role,
                "round": "technical_deep_dive"
            },
            "next_action": "generate_question",
            "status": "active"
        }
    
    # CLOSING PHASE
    if conversation_phase == "closing":
        return {
            "status": "completed",
            "next_action": "complete"
        }
    
    # Default fallback
    print(f"FALLBACK: No phase matched! Phase={conversation_phase}, Round={current_round}")
    return {
        "next_action": "wait",
        "status": "active"
    }


def should_continue(state: InterviewState) -> str:
    """Routing function for LangGraph workflow"""
    next_action = state.get("next_action", "wait")
    status = state.get("status", "active")
    
    # Check if interview is complete
    if status == "completed" or status == "error" or next_action == "complete":
        return "complete"
    
    # Check if we need to wait for user response
    if next_action == "wait":
        return "complete"
    
    # Check if we need to generate a question
    if next_action == "generate_question":
        return "generate_question"
    
    # Check if we need to evaluate
    if next_action == "evaluate":
        return "evaluate"
    
    return "complete"
