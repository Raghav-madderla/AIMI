from typing import TypedDict, List, Optional, Literal
from typing_extensions import Annotated
import operator


class InterviewState(TypedDict):
    """Shared state for the LangGraph interview workflow"""
    session_id: str
    resume_id: str
    job_role: str
    current_round: Literal["welcome", "intro", "resume_discussion", "technical_deep_dive", "completed"]
    difficulty: Literal["easy", "medium", "hard"]
    question_count: int
    resume_context: str  # RAG-retrieved chunks
    previous_questions: Annotated[List[dict], operator.add]
    user_answers: Annotated[List[dict], operator.add]
    evaluation_history: Annotated[List[dict], operator.add]
    selected_domain: Optional[str]
    next_action: Literal["generate_question", "evaluate", "complete", "wait"]
    messages: Annotated[List[dict], operator.add]
    status: Literal["active", "completed"]
    
    # Current question context (set by orchestrator, used by question agent)
    question_context: Optional[dict]  # {domain, difficulty, resume_context}
    
    # Current evaluation context (set by orchestrator, used by evaluation agent)
    evaluation_context: Optional[dict]  # {question, answer, domain, round}
    
    # Agent responses
    question_agent_response: Optional[dict]
    evaluation_agent_response: Optional[dict]
    
    # Interview planning
    domain_coverage: Optional[dict]  # {domain: count} - tracks questions asked per domain
    domain_plan: Optional[dict]  # {domain: target_count} - planned questions per domain
    
    # NEW: Conversational flow tracking
    conversation_phase: Literal["greeting", "intro_question", "resume_point", "technical_question", "closing"]
    current_resume_point_index: int  # Track which resume point we're discussing
    resume_summary: Optional[dict]  # Structured summary from resume_summary_agent
    orchestrator_intent: Optional[str]  # What the orchestrator wants to ask about
    pending_question: Optional[str]  # Question waiting to be cleaned
    current_question_key_points: Optional[List[str]]  # The required concepts for the current question

