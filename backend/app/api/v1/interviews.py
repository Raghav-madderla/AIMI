from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_sync_db
from app.models import Resume, InterviewSession, Message, User
from app.services.interview_service import interview_service
from app.services.resume_service import resume_service
from app.services.agents.report_agent import generate_final_report
from app.utils.langgraph_state import InterviewState
from app.api.v1.auth import get_current_user
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["interviews"])


# Pydantic models for request/response
class StartInterviewRequest(BaseModel):
    resume_id: str
    job_role: str


class AnswerRequest(BaseModel):
    answer: str
    question: str = ""  # Optional for welcome phase
    domain: str = ""  # Optional for welcome phase
    difficulty: str = ""  # Optional for welcome phase


class SessionResponse(BaseModel):
    session_id: str
    resume_id: str
    job_role: str
    current_round: str
    status: str
    technical_questions_count: int
    behavioral_questions_count: int
    created_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    metadata: dict
    created_at: str

    class Config:
        from_attributes = True


@router.post("/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    job_role: str = "Data Scientist",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a resume"""
    try:
        # Save file
        resume_data = await resume_service.process_resume(
            file=file,
            job_role=job_role,
            user_id=current_user.user_id,
            db=db
        )
        return {
            "resume_id": resume_data["resume_id"],
            "message": "Resume processed successfully",
            "skills": resume_data.get("skills", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/start")
async def start_interview(
    request: StartInterviewRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new interview session"""
    # Verify resume exists and belongs to user
    resume = db.query(Resume).filter(
        Resume.resume_id == request.resume_id,
        Resume.user_id == current_user.user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Create session in database
    session_id = str(uuid.uuid4())
    session = InterviewSession(
        session_id=session_id,
        user_id=current_user.user_id,
        resume_id=request.resume_id,
        job_role=request.job_role,
        current_round="welcome",  # Start with welcome phase
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Get resume context for initializing workflow
    resume_context = resume_service.get_resume_context(request.resume_id)
    
    # Initialize interview workflow state
    workflow_state = await interview_service.initialize_interview(
        session_id=session_id,
        resume_id=request.resume_id,
        job_role=request.job_role,
        resume_context=resume_context,
        db=db  # Pass db to load resume summary
    )
    
    # Generate welcome message
    welcome_message = await interview_service.generate_welcome_message(workflow_state)
    
    # Save workflow state to session
    session.workflow_state = workflow_state
    
    # Save welcome message to database
    welcome_msg = Message(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=welcome_message,
        message_metadata={"type": "welcome", "round": "welcome"}
    )
    db.add(welcome_msg)
    db.commit()
    
    return {
        "session_id": session_id,
        "message": welcome_message,
        "type": "welcome",
        "message_text": "Interview session created. Waiting for user confirmation."
    }


@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: str,
    request: AnswerRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer and get evaluation"""
    # Get session and verify it belongs to user
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user answer message
    answer_msg = Message(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=request.answer,
        message_metadata={}
    )
    db.add(answer_msg)
    
    # Get workflow state from session (preserves conversational flow)
    if session.workflow_state:
        # Restore saved workflow state
        workflow_state = session.workflow_state
    else:
        # Fallback: reconstruct from messages (for old sessions)
        workflow_state = await interview_service.initialize_interview(
            session_id=session_id,
            resume_id=session.resume_id,
            job_role=session.job_role,
            db=db  # Pass db to load resume summary
        )
        
        # Load messages from DB to reconstruct state
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        
        # Reconstruct previous questions and answers
        for msg in messages:
            if msg.role == "assistant":
                if msg.message_metadata and msg.message_metadata.get("type") != "welcome":
                    workflow_state["previous_questions"].append(msg.message_metadata or {})
            elif msg.role == "user":
                workflow_state["user_answers"].append({"answer": msg.content})
        
        workflow_state["question_count"] = len(workflow_state["previous_questions"])
        workflow_state["current_round"] = session.current_round  # Use session's current round
    
    # Check if we're in welcome phase
    if session.current_round == "welcome":
        # Handle welcome response
        result = await interview_service.handle_welcome_response(
            state=workflow_state,
            user_response=request.answer,
            db=db,
            session_id=session_id
        )
        
        # Save response message
        db.commit()
        
        if result.get("confirmed") is True:
            # User confirmed, update session to technical round
            session.current_round = "intro"
            # Save updated workflow state
            session.workflow_state = result.get("state", workflow_state)
            
            if result.get("question"):
                # Save first question
                question_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content=result["question"]["question_text"],
                    message_metadata=result["question"]
                )
                db.add(question_msg)
            
            db.commit()
            
            return {
                "message": "Great! Let's begin the interview.",
                "next_question": result.get("question"),
                "evaluation": None
            }
        elif result.get("confirmed") is False:
            # User declined
            clarification_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=result.get("message", "I'll wait for you."),
                message_metadata={"type": "clarification", "round": "welcome"}
            )
            db.add(clarification_msg)
            db.commit()
            
            return {
                "message": result.get("message", "I'll wait for you."),
                "next_question": None,
                "evaluation": None
            }
        else:
            # Ambiguous response, ask for clarification
            clarification_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=result.get("message", "Could you clarify?"),
                message_metadata={"type": "clarification", "round": "welcome"}
            )
            db.add(clarification_msg)
            db.commit()
            
            return {
                "message": result.get("message", "Could you clarify?"),
                "next_question": None,
                "evaluation": None
            }
    
    # Regular answer evaluation (not in welcome phase)
    # Evaluate answer
    result = await interview_service.evaluate_answer(
        state=workflow_state,
        answer=request.answer,
        question=request.question,
        domain=request.domain,
        difficulty=request.difficulty
    )
    
    if result.get("evaluation"):
        # Update answer message with feedback
        answer_msg.message_metadata = {
            "feedback": result["evaluation"]["feedback"],
            "score": result["evaluation"]["score"]
        }
        db.commit()
        
        # Update session counts
        if session.current_round == "technical":
            session.technical_questions_count += 1
        else:
            session.behavioral_questions_count += 1
        db.commit()
        
        # Generate next question
        try:
            next_result = await interview_service.generate_next_question(result["state"])
        except Exception as e:
            # If question generation fails, return evaluation with error
            # Save state before error
            session.workflow_state = result["state"]
            db.commit()
            error_msg = str(e)
            if "400 Bad Request" in error_msg:
                error_msg = "Your Hugging Face model endpoint returned an error. Please check your model configuration."
            return {
                "evaluation": result["evaluation"],
                "next_question": None,
                "error": error_msg
            }
        
        if next_result.get("question"):
            # Save updated workflow state (preserves conversational phase)
            session.workflow_state = next_result.get("state", result["state"])
            
            # Save next question message
            next_question_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=next_result["question"]["question_text"],
                message_metadata=next_result["question"]
            )
            db.add(next_question_msg)
            
            # Update session round if needed
            if result["state"].get("current_round") != session.current_round:
                session.current_round = result["state"]["current_round"]
            
            db.commit()
            
            return {
                "evaluation": result["evaluation"],
                "next_question": next_result["question"]
            }
        else:
            # Interview complete - generate final report
            session.workflow_state = result["state"]
            session.status = "completed"
            db.commit()
            
            # Generate comprehensive report
            print(f"Generating final interview report...")
            try:
                workflow_state = result["state"]
                report = await generate_final_report(
                    evaluation_history=workflow_state.get("evaluation_history", []),
                    user_answers=workflow_state.get("user_answers", []),
                    previous_questions=workflow_state.get("previous_questions", []),
                    job_role=session.job_role,
                    session_id=session_id
                )
                print(f"Report generated successfully")
                
                # Save report as a message in the database
                report_message = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content="Interview Report - See details below",
                    message_metadata={
                        "type": "report",
                        "report": report,
                        "round": "completion"
                    }
                )
                db.add(report_message)
                db.commit()
                print(f"Report saved to database")
                
                return {
                    "evaluation": result["evaluation"],
                    "next_question": None,
                    "message": "Interview session completed. Thank you for your time!",
                    "report": report  # Include full report in response
                }
            except Exception as e:
                print(f"Report generation failed: {str(e)}")
                
                # Save completion message without report
                completion_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content="Interview session completed. Thank you for your time!",
                    message_metadata={"type": "completion", "round": "completion"}
                )
                db.add(completion_msg)
                db.commit()
                
                return {
                    "evaluation": result["evaluation"],
                    "next_question": None,
                    "message": "Interview session completed. Thank you for your time!",
                    "report": None
                }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate answer: {result.get('error', 'Unknown error')}"
        )


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a session"""
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()
    
    # Debug logging
    print(f"Loading {len(messages)} messages for session {session_id}")
    for msg in messages:
        if msg.message_metadata and msg.message_metadata.get("type") == "report":
            print(f"   Found report message: {msg.message_id}")
    
    return {
        "session_id": session_id,
        "messages": [
            {
                "message_id": msg.message_id,
                "role": msg.role,
                "content": msg.content,
                "message_metadata": msg.message_metadata or {},  # Changed from "metadata" to "message_metadata"
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.get("/sessions")
async def list_sessions(
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """List all interview sessions for the current user"""
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.user_id
    ).order_by(
        InterviewSession.created_at.desc()
    ).all()
    
    return {
        "sessions": [
            {
                "id": s.session_id,
                "title": f"Interview {s.created_at.strftime('%Y-%m-%d')}",
                "createdAt": s.created_at.isoformat(),
                "job_role": s.job_role,
                "status": s.status
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Get session details"""
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "resume_id": session.resume_id,
        "job_role": session.job_role,
        "current_round": session.current_round,
        "status": session.status,
        "technical_questions_count": session.technical_questions_count,
        "behavioral_questions_count": session.behavioral_questions_count,
        "created_at": session.created_at.isoformat()
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a session and all its messages"""
    # Verify session exists and belongs to user
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages associated with this session
    db.query(Message).filter(Message.session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully", "session_id": session_id}


@router.get("/sessions/{session_id}/report")
async def get_interview_report(
    session_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and return comprehensive interview report with analytics
    Only available for completed interviews
    """
    # Verify session exists and belongs to user
    session = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id,
        InterviewSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if interview is completed
    if session.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Interview not completed yet. Report only available after completion."
        )
    
    # Get workflow state to extract evaluation history
    if not session.workflow_state:
        raise HTTPException(
            status_code=404,
            detail="No interview data found"
        )
    
    workflow_state = session.workflow_state
    evaluation_history = workflow_state.get("evaluation_history", [])
    user_answers = workflow_state.get("user_answers", [])
    previous_questions = workflow_state.get("previous_questions", [])
    
    if not evaluation_history:
        return {
            "message": "No evaluations available. Interview may have been too short.",
            "session_id": session_id
        }
    
    # Generate comprehensive report
    report = await generate_final_report(
        evaluation_history=evaluation_history,
        user_answers=user_answers,
        previous_questions=previous_questions,
        job_role=session.job_role,
        session_id=session_id
    )
    
    return report

