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
            prompt = f"""Generate ONE interview question for a {job_role} position asking the candidate to introduce themselves.

Requirements:
- Be warm and conversational
- Ask about their journey and what excites them about the role
- Return ONLY the question text
- No explanations, no additional text

Question:"""

            try:
                messages = [
                        {"role": "system", "content": "You are a professional interview question generator. Return only the question, nothing else."},
                        {"role": "user", "content": prompt}
                ]
                
                intro_question = await local_llm_service.generate_async(messages, max_new_tokens=100, temperature=0.7)
                
                # Clean up any extra text (take only the first sentence or up to first newline)
                intro_question = intro_question.split('\n')[0].strip()
                # Remove quotes if present
                intro_question = intro_question.strip('"\'')
                
                # Fallback if empty
                if not intro_question or len(intro_question) < 10:
                    intro_question = "To get started, could you tell me a bit about yourself and what excites you about this role?"
                
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
        
        # Check if we have resume summary and summary points
        summary_points = resume_summary.get("summary_points", []) if resume_summary else []
        
        if not resume_summary or not summary_points or len(summary_points) == 0:
            print(f"No resume summary or no summary points ({len(summary_points)}), skipping to technical")
            # Skip to technical if no resume summary
            return {
                "conversation_phase": "technical_question",
                "current_round": "technical_deep_dive",
                "next_action": "generate_question"
            }
        
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
        # Simplified approach - skip LLM parsing, create directly
        try:
            # Create a simple comment and intent
            comment = f"I see you have experience with {point_text[:100]}."
            intent = f"Tell me more about your work with {domains[0] if domains else 'this area'}."
            domain = domains[0] if domains else "General"
            
            # Determine difficulty based on significance
            difficulty_map = {"high": "hard", "medium": "medium", "low": "easy"}
            difficulty = difficulty_map.get(significance, "medium")
            
            # Ensure domain is valid (not a placeholder)
            if not domain or domain in ["[insert here]", "General"]:
                domain = domains[0] if domains else "Data Analysis"
            
            print(f"Orchestrator Decision:")
            print(f"   Comment: {comment}")
            print(f"   Intent: {intent}")
            print(f"   Domain: {domain}")
            print(f"   Difficulty: {difficulty}")
            print(f"   Moving to next resume point: {current_resume_point_index} -> {current_resume_point_index + 1}")
            
            # Store orchestrator's intent and comment for later use
            # Note: question_context only has domain + difficulty (for question agent)
            # resume_context is stored separately for cleaning agent
            return {
                "orchestrator_intent": f"{comment} {intent}",
                "selected_domain": domain,
                "difficulty": difficulty,
                "question_context": {
                    "domain": domain,
                    "difficulty": difficulty,
                    "round": "resume_discussion",
                    "resume_context": point_text  # Stored here for cleaning agent only
                },
                "current_resume_point_index": current_resume_point_index + 1,  # Move to next point AFTER this question
                "next_action": "generate_question",
                "status": "active"
            }
            
        except Exception as e:
            print(f"Orchestrator planning failed: {str(e)}")
            # Fallback: Generate a simple question
            domain_fallback = domains[0] if domains else "Data Analysis"
            return {
                "orchestrator_intent": f"Tell me more about: {point_text[:100]}",
                "selected_domain": domain_fallback,
                "difficulty": "medium",
                "question_context": {
                    "domain": domain_fallback,
                    "difficulty": "medium",
                    "round": "resume_discussion",
                    "resume_context": point_text  # For cleaning agent only
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
        
        # Select technical domains from resume summary if available
        technical_domains = []
        if resume_summary:
            # Extract domains from summary points
            summary_points = resume_summary.get("summary_points", [])
            for point in summary_points:
                point_domains = point.get("domains", [])
                technical_domains.extend(point_domains)
            
            # Also add key strengths if they look like domains
            key_strengths = resume_summary.get("key_strengths", [])
            technical_domains.extend(key_strengths)
            
            # Deduplicate
            technical_domains = list(set(technical_domains))
        
        # Fallback to common domains if none found
        if not technical_domains:
            technical_domains = ["Python", "System Design", "Machine Learning", "SQL", "Data Analysis"]
        
        print(f"Technical domains from resume: {technical_domains}")
        
        # Cycle through domains
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
        
        print(f"Selected domain for Q{question_count}: {selected_domain}, difficulty: {difficulty}")
        
        return {
            "selected_domain": selected_domain,
            "difficulty": difficulty,
            "orchestrator_intent": f"Assess {selected_domain} skills",
            "question_context": {
        "domain": selected_domain,
        "difficulty": difficulty,
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
