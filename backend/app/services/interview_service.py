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
        """
        Process user answer through the graph.
        1. Update state with new answer.
        2. Run workflow (Orchestrator -> Evaluate -> Orchestrator -> Question).
        3. Return new question and evaluation.
        """
        
        # 1. Update State with new answer
        current_messages = state.get("messages", [])
        new_messages = current_messages + [{
            "role": "user",
            "content": answer
        }]
        
        current_answers = state.get("user_answers", [])
        new_answers = current_answers + [{
            "answer": answer,
            "question": question
        }]
        
        # Prepare input state
        input_state = {
            **state,
            "messages": new_messages,
            "user_answers": new_answers,
            "question_agent_response": None,  # Clear old response so Orchestrator generates a new one
            # Note: We don't manually set 'evaluation_context' here anymore.
            # The Orchestrator will detect the new answer and set it.
        }
        
        # 2. Invoke Workflow
        # The graph will cycle: Orchestrator (sees new answer) -> EvaluationAgent -> Orchestrator -> QuestionAgent -> CleaningAgent -> Orchestrator (wait)
        config = {"recursion_limit": 50}
        final_state = await self.workflow.ainvoke(input_state, config)
        
        # 3. Extract Results
        # Evaluation should be in evaluation_history[-1]
        evaluation_history = final_state.get("evaluation_history", [])
        latest_evaluation = evaluation_history[-1] if evaluation_history else None
        
        # New Question should be in question_agent_response
        question_response = final_state.get("question_agent_response")
        new_question_data = None
        
        if question_response and question_response.get("question"):
            new_question_data = {
                "question_text": question_response["question"],
                "domain": question_response.get("domain", ""),
                "difficulty": question_response.get("difficulty", "medium"),
                "round": final_state.get("current_round", "technical")
            }
            
            # Update messages with the assistant's new question
            final_state["messages"] = final_state.get("messages", []) + [{
                "role": "assistant",
                "content": new_question_data["question_text"],
                "metadata": new_question_data
            }]
            
            # Update previous_questions
            final_state["previous_questions"] = final_state.get("previous_questions", []) + [new_question_data]
            final_state["question_count"] = final_state.get("question_count", 0) + 1
            
            # Update domain coverage
            domain_coverage = final_state.get("domain_coverage", {}) or {}
            q_domain = new_question_data.get("domain", "")
            if q_domain:
                domain_coverage[q_domain] = domain_coverage.get(q_domain, 0) + 1
            final_state["domain_coverage"] = domain_coverage
            
            # Ensure next action is set to wait for user
            final_state["next_action"] = "evaluate"
            
            return {
                "state": final_state,
                "evaluation": latest_evaluation,
                "question": new_question_data
            }
        else:
            # Handle error or missing question
            error = question_response.get("error", "Unknown error") if question_response else "No question generated"
            return {
                "state": final_state,
                "evaluation": latest_evaluation,
                "question": None,
                "error": error
            }


interview_service = InterviewService()

