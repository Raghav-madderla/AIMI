from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.services.interview_workflow import interview_workflow
from app.utils.langgraph_state import InterviewState
from app.services.agents.question_agent import question_agent
from app.services.agents.evaluation_agent import evaluation_agent
from app.models import Resume
import uuid


class InterviewService:
    """Service to manage interview workflow execution"""
    
    def __init__(self):
        self.workflow = interview_workflow
    
    async def initialize_interview(
        self,
        session_id: str,
        resume_id: str,
        job_role: str,
        resume_context: str = "",
        db: Session = None
    ) -> InterviewState:
        """Initialize a new interview session with conversational flow"""
        
        # Load resume summary from database
        resume_summary = None
        if db and resume_id:
            resume_obj = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if resume_obj and resume_obj.chunks_metadata:
                resume_summary = resume_obj.chunks_metadata.get("resume_summary")
        
        initial_state: InterviewState = {
            "session_id": session_id,
            "resume_id": resume_id,
            "job_role": job_role,
            "current_round": "welcome",
            "difficulty": "easy",
            "question_count": 0,
            "resume_context": resume_context,
            "previous_questions": [],
            "user_answers": [],
            "evaluation_history": [],
            "selected_domain": None,
            "next_action": "generate_question",
            "messages": [],
            "status": "active",
            "question_context": None,
            "evaluation_context": None,
            "question_agent_response": None,
            "evaluation_agent_response": None,
            "domain_coverage": None,  # Will be initialized by orchestrator
            "domain_plan": None,  # Will be created by orchestrator
            # NEW: Conversational flow fields
            "conversation_phase": "greeting",
            "current_resume_point_index": 0,
            "resume_summary": resume_summary,
            "orchestrator_intent": None,
            "pending_question": None
        }
        
        return initial_state
    
    async def generate_welcome_message(self, state: InterviewState) -> str:
        """Generate warm, friendly welcome message from AIMI"""
        job_role = state.get("job_role", "the position")
        
        # Warm, human-like greeting
        welcome_message = f"""Hello! I'm AIMI - your AI interview companion.

It's great to meet you! I've had a chance to look through your resume, and I'm really excited to chat with you about your journey and experiences for this {job_role} role.

Think of this as a friendly conversation where we'll explore your background, skills, and what makes you a great fit. I'm here to help you showcase your strengths!

Would you like to get started? Just say "yes" when you're ready, or "no" if you need a moment."""
        
        return welcome_message
    
    async def handle_welcome_response(
        self,
        state: InterviewState,
        user_response: str,
        db: Session = None,
        session_id: str = None
    ) -> Dict:
        """Handle user's response to welcome message and start conversational flow"""
        response_lower = user_response.lower().strip()
        
        # Check if user wants to start
        if any(word in response_lower for word in ["yes", "yeah", "yep", "sure", "okay", "ok", "start", "begin", "ready"]):
            # User confirmed, transition to intro phase
            updated_state = {
                **state,
                "current_round": "intro",
                "conversation_phase": "intro_question",
                "next_action": "generate_question"
            }
            
            # Generate first question (intro question from orchestrator)
            result = await self.generate_next_question(updated_state)
            return {
                "state": result.get("state", updated_state),
                "question": result.get("question"),
                "confirmed": True
            }
        elif any(word in response_lower for word in ["no", "nope", "not", "wait", "later", "cancel"]):
            # User declined or wants to wait
            return {
                "state": state,
                "question": None,
                "confirmed": False,
                "message": "No problem at all! Take your time. Just let me know when you're ready - I'll be here whenever you want to start."
            }
        else:
            # Ambiguous response, ask for clarification in friendly way
            return {
                "state": state,
                "question": None,
                "confirmed": None,
                "message": "Hmm, I wasn't quite sure what you meant. Could you let me know if you'd like to start now? A simple 'yes' or 'no' would be perfect!"
            }
    
    async def generate_next_question(self, state: InterviewState) -> Dict:
        """
        Generate the next question by running the workflow
        Returns the updated state with the question
        """
        # Run workflow to generate question
        # The orchestrator will determine action and route to question agent
        config = {"recursion_limit": 50}
        
        # Execute workflow until we get a question
        current_state = state
        async for step in self.workflow.astream(current_state, config):
            # The workflow will execute: orchestrator -> question_agent -> orchestrator
            for node, node_state in step.items():
                current_state = node_state
        
        # Extract question from state
        question_response = current_state.get("question_agent_response")
        if question_response and question_response.get("question"):
            question_data = {
                "question_text": question_response["question"],
                "domain": question_response.get("domain", ""),
                "difficulty": question_response.get("difficulty", "medium"),
                "round": current_state.get("current_round", "technical")
            }
            
            # Update domain coverage (increment count for the domain)
            domain_coverage = current_state.get("domain_coverage", {})
            domain = question_data.get("domain", "")
            if domain:
                domain_coverage = domain_coverage.copy() if domain_coverage else {}
                domain_coverage[domain] = domain_coverage.get(domain, 0) + 1
            
            # Increment question count
            old_count = current_state.get("question_count", 0)
            new_question_count = old_count + 1
            
            print(f"INCREMENTING question_count: {old_count} -> {new_question_count}")
            
            # Add question to previous_questions and messages
            updated_state = {
                **current_state,
                "question_count": new_question_count,
                "previous_questions": current_state.get("previous_questions", []) + [question_data],
                "messages": current_state.get("messages", []) + [{
                    "role": "assistant",
                    "content": question_response["question"],
                    "metadata": question_data
                }],
                "domain_coverage": domain_coverage,
                "next_action": "evaluate"  # Next action is to wait for user answer
            }
            
            return {
                "state": updated_state,
                "question": question_data
            }
        else:
            error = question_response.get("error", "Unknown error") if question_response else "No response"
            return {
                "state": current_state,
                "question": None,
                "error": error
            }
    
    async def evaluate_answer(
        self,
        state: InterviewState,
        answer: str,
        question: str,
        domain: str,
        difficulty: str
    ) -> Dict:
        """Evaluate a user's answer"""
        
        print(f"CLEARING old question_agent_response before evaluation")
        
        # Set evaluation context and CLEAR old question response
        evaluation_state = {
            **state,
            "question_agent_response": None,  # Clear old response!
            "evaluation_context": {
                "question": question,
                "answer": answer,
                "domain": domain,
                "round": state.get("current_round", "technical"),
                "difficulty": difficulty
            },
            "next_action": "evaluate"
        }
        
        # Call evaluation agent directly
        updated_state = await evaluation_agent(evaluation_state)
        
        # Merge evaluation results
        eval_response = updated_state.get("evaluation_agent_response")
        if eval_response and not eval_response.get("error"):
            score = eval_response.get("score", 0.5)
            feedback = eval_response.get("feedback", {})
            
            evaluation_data = {
                "score": score,
                "feedback": feedback,
                "domain": domain,
                "question": question
            }
            
            # Update state with evaluation
            final_state = {
                **evaluation_state,
                **updated_state,
                "evaluation_history": evaluation_state.get("evaluation_history", []) + [evaluation_data],
                "user_answers": evaluation_state.get("user_answers", []) + [{"answer": answer}],
                "messages": evaluation_state.get("messages", []) + [
                    {
                        "role": "user",
                        "content": answer,
                        "metadata": {"feedback": feedback, "score": score}
                    }
                ],
                "next_action": "generate_question"  # Ready for next question
            }
            
            return {
                "state": final_state,
                "evaluation": evaluation_data
            }
        else:
            error = eval_response.get("error", "Unknown error") if eval_response else "No response"
            return {
                "state": evaluation_state,
                "evaluation": None,
                "error": error
            }


interview_service = InterviewService()

