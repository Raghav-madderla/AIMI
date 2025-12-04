# AI Interviewer - System Design Architecture

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [Component Architecture](#component-architecture)
3. [Agent Workflow (A2A Protocol)](#agent-workflow-a2a-protocol)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [API Design](#api-design)
7. [Technology Stack](#technology-stack)
8. [Scalability & Performance](#scalability--performance)
9. [Security Architecture](#security-architecture)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            React Frontend (Port 3000)                   │    │
│  │  - Login/Auth Screen                                    │    │
│  │  - Resume Upload                                        │    │
│  │  - Interview Interface                                  │    │
│  │  - Feedback Display                                     │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API (HTTP/JSON)
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │       FastAPI Backend (Port 8000)                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Auth Router  │  │ Interview    │  │ Resume      │  │    │
│  │  │              │  │ Router       │  │ Router      │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     SERVICE LAYER                                │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Interview       │  │ Resume Service   │  │ RAG Service   │ │
│  │ Service         │  │ - Docling Parser │  │ - Embedding   │ │
│  │ - Workflow      │  │ - Chunking       │  │ - Vector      │ │
│  │ - State Mgmt    │  │ - Domain Match   │  │   Search      │ │
│  └─────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │               AGENT ORCHESTRATION LAYER                     ││
│  │     (LangGraph - Agent-to-Agent Protocol)                  ││
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐   ││
│  │  │Orchestrator│→ │  Question   │→ │    Cleaning      │   ││
│  │  │   Agent    │  │   Agent     │  │     Agent        │   ││
│  │  └─────┬──────┘  └─────────────┘  └──────────────────┘   ││
│  │        ↓                                                    ││
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐   ││
│  │  │ Evaluation │  │   Report    │  │  Resume Summary  │   ││
│  │  │   Agent    │  │   Agent     │  │     Agent        │   ││
│  │  └────────────┘  └─────────────┘  └──────────────────┘   ││
│  └────────────────────────────────────────────────────────────┘│
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐│
│  │   SQLite     │  │  Pinecone    │  │   File Storage        ││
│  │   Database   │  │  Vector DB   │  │   (uploads/)          ││
│  │  - Users     │  │  - Embeddings│  │   - PDF/DOCX          ││
│  │  - Sessions  │  │  - Metadata  │  │                       ││
│  │  - Messages  │  │              │  │                       ││
│  │  - Resumes   │  │              │  │                       ││
│  └──────────────┘  └──────────────┘  └───────────────────────┘│
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                   EXTERNAL SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐│
│  │   OpenAI     │  │ Hugging Face │  │      Pinecone         ││
│  │   API        │  │   Models     │  │      Cloud            ││
│  │  - GPT-4o    │  │  - Fine-tuned│  │   - Vector Index      ││
│  │  - Embedding │  │    QA Model  │  │   - Serverless        ││
│  └──────────────┘  └──────────────┘  └───────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Frontend Components

```
src/
├── App.js                      # Main application router
├── LoginScreen.js              # Authentication
├── SetupScreen.js              # Resume upload & job role
├── ChatInterviewScreen.js      # Main interview UI
├── FeedbackScreen.js           # Report display
├── Sidebar.js                  # Session navigation
└── api.js                      # API client utilities
```

### 2.2 Backend Structure

```
backend/
├── main.py                     # FastAPI application entry
├── app/
│   ├── api/v1/
│   │   ├── auth.py            # Authentication endpoints
│   │   └── interviews.py      # Interview & Resume endpoints
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── database.py        # Database connection
│   ├── models/
│   │   ├── user.py            # User model
│   │   ├── resume.py          # Resume model
│   │   ├── session.py         # InterviewSession model
│   │   └── message.py         # Message model
│   ├── services/
│   │   ├── agents/            # AI Agents (see section 3)
│   │   ├── interview_service.py   # Interview orchestration
│   │   ├── interview_workflow.py  # LangGraph workflow
│   │   ├── resume_service.py      # Resume processing
│   │   ├── rag_service.py         # RAG implementation
│   │   ├── embedding_service.py   # OpenAI embeddings
│   │   └── vector_store.py        # Pinecone interface
│   └── utils/
│       ├── auth.py            # JWT utilities
│       └── langgraph_state.py # Shared state definition
└── migrate_add_file_hash.py   # Database migrations
```

---

## 3. Agent Workflow (A2A Protocol)

### 3.1 Agent Communication Flow

```
┌────────────────────────────────────────────────────────────────┐
│                   USER SUBMITS ANSWER                           │
└─────────────────────────┬──────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                            │
│  Role: Interview Manager (Human-like hiring manager)            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  1. Analyze conversation phase                             │ │
│  │  2. Decide next action:                                    │ │
│  │     - greeting → intro_question                            │ │
│  │     - intro_question → resume_point                        │ │
│  │     - resume_point → technical_question                    │ │
│  │     - technical_question → closing                         │ │
│  │  3. Set context for other agents                           │ │
│  │  4. Track domain coverage and question count               │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────────┬────────────────────────┬───────────────────────────┘
            │                        │
      next_action                next_action
      = "generate_question"      = "evaluate"
            │                        │
            ↓                        ↓
┌──────────────────────┐   ┌────────────────────────┐
│   QUESTION AGENT     │   │   EVALUATION AGENT     │
│  ┌────────────────┐  │   │  ┌──────────────────┐  │
│  │ 1. Read context│  │   │  │ 1. Read context  │  │
│  │    from state  │  │   │  │    (Q, A, domain)│  │
│  │ 2. Call HF     │  │   │  │ 2. Call GPT-4o   │  │
│  │    model API   │  │   │  │ 3. Generate:     │  │
│  │ 3. Generate    │  │   │  │    - Score       │  │
│  │    raw question│  │   │  │    - Feedback    │  │
│  │ 4. Store in    │  │   │  │    - Strengths   │  │
│  │    state       │  │   │  │    - Improvements│  │
│  └────────────────┘  │   │  └──────────────────┘  │
└──────────┬───────────┘   └────────┬───────────────┘
           │                        │
           ↓                        │
┌──────────────────────┐            │
│   CLEANING AGENT     │            │
│  ┌────────────────┐  │            │
│  │ 1. Read raw Q  │  │            │
│  │ 2. Read intent │  │            │
│  │ 3. Refine to   │  │            │
│  │    be natural  │  │            │
│  │ 4. Update state│  │            │
│  └────────────────┘  │            │
└──────────┬───────────┘            │
           │                        │
           └───────┬────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│           ORCHESTRATOR AGENT (Return)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  1. Receive cleaned question or evaluation        │  │
│  │  2. Update conversation_phase                     │  │
│  │  3. Prepare response for user                     │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              RETURN TO USER                              │
│  - Question text                                         │
│  - Domain, Difficulty                                    │
│  - Evaluation (if applicable)                            │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Agent Responsibilities

#### **Orchestrator Agent**
```python
# File: app/services/agents/orchestrator_agent.py

Responsibilities:
- Manage conversation flow (greeting → intro → resume → technical → closing)
- Track interview state (phase, question_count, domain_coverage)
- Decide next action (generate_question, evaluate, complete)
- Set context for other agents
- Maintain conversational continuity

Inputs:
- InterviewState (shared state)

Outputs:
- next_action: Literal["generate_question", "evaluate", "complete"]
- question_context: dict (for Question Agent)
- evaluation_context: dict (for Evaluation Agent)
- orchestrator_intent: str (for Cleaning Agent)
```

#### **Question Agent**
```python
# File: app/services/agents/question_agent.py

Responsibilities:
- Generate interview questions using fine-tuned HF model
- Use domain-specific context
- Apply difficulty levels (easy, medium, hard)

Inputs:
- question_context: {domain, difficulty, resume_context, job_role}

Outputs:
- question_agent_response: {question, domain, difficulty, error}

API:
- Hugging Face Inference API (your fine-tuned model)
- Format: Alpaca prompt format
```

#### **Cleaning Agent**
```python
# File: app/services/agents/question_cleaning_agent.py

Responsibilities:
- Refine raw questions to be conversational
- Align question with orchestrator's intent
- Remove technical artifacts

Inputs:
- generated_question: str (from Question Agent)
- orchestrator_intent: str (what to ask about)
- resume_point: str (context)
- domain: str

Outputs:
- cleaned_question: str
- success: bool
```

#### **Evaluation Agent**
```python
# File: app/services/agents/evaluation_agent.py

Responsibilities:
- Evaluate candidate answers
- Provide detailed feedback
- Generate scores (0.0 - 1.0)

Inputs:
- evaluation_context: {question, answer, domain, round, difficulty}

Outputs:
- evaluation_agent_response: {
    score: float,
    feedback_text: str,
    strengths: List[str],
    improvements: List[str]
  }

API:
- OpenAI GPT-4o
```

#### **Resume Summary Agent**
```python
# File: app/services/agents/resume_summary_agent.py

Responsibilities:
- Extract structured summary from resume
- Identify key points for discussion
- Generate conversation topics

Inputs:
- resume_text: str
- job_role: str

Outputs:
- summary: {
    summary_points: List[str],
    key_skills: List[str],
    experience_highlights: List[str]
  }
```

#### **Report Agent**
```python
# File: app/services/agents/report_agent.py

Responsibilities:
- Generate comprehensive interview report
- Calculate overall performance
- Provide recommendations

Inputs:
- evaluation_history: List[dict]
- user_answers: List[dict]
- previous_questions: List[dict]
- job_role: str

Outputs:
- report: {
    overall_score: float,
    domain_scores: dict,
    strengths: List[str],
    weaknesses: List[str],
    recommendations: List[str],
    hiring_recommendation: str
  }
```

### 3.3 LangGraph Workflow

```python
# File: app/services/interview_workflow.py

# Node connections:
workflow = StateGraph(InterviewState)

# Nodes (Agents)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("question_agent", question_agent)
workflow.add_node("cleaning_agent", cleaning_agent_node)
workflow.add_node("evaluation_agent", evaluation_agent)

# Entry point
workflow.set_entry_point("orchestrator")

# Conditional routing
workflow.add_conditional_edges(
    "orchestrator",
    should_continue,
    {
        "generate_question": "question_agent",  # A2A: Orch → Question
        "evaluate": "evaluation_agent",          # A2A: Orch → Eval
        "complete": END                          # End interview
    }
)

# Sequential flows
workflow.add_edge("question_agent", "cleaning_agent")    # Question → Clean
workflow.add_edge("cleaning_agent", "orchestrator")      # Clean → Orch
workflow.add_edge("evaluation_agent", "orchestrator")    # Eval → Orch
```

### 3.4 Shared State (A2A Communication)

```python
# File: app/utils/langgraph_state.py

class InterviewState(TypedDict):
    # Session info
    session_id: str
    resume_id: str
    job_role: str
    
    # Interview progress
    current_round: Literal["welcome", "intro", "resume_discussion", 
                          "technical_deep_dive", "completed"]
    difficulty: Literal["easy", "medium", "hard"]
    question_count: int
    
    # Context data
    resume_context: str
    resume_summary: Optional[dict]
    
    # Question/Answer history
    previous_questions: List[dict]
    user_answers: List[dict]
    evaluation_history: List[dict]
    
    # Agent communication (A2A)
    next_action: Literal["generate_question", "evaluate", "complete", "wait"]
    question_context: Optional[dict]           # Set by Orchestrator
    evaluation_context: Optional[dict]         # Set by Orchestrator
    orchestrator_intent: Optional[str]         # Set by Orchestrator
    question_agent_response: Optional[dict]    # Set by Question Agent
    evaluation_agent_response: Optional[dict]  # Set by Evaluation Agent
    
    # Conversational flow
    conversation_phase: Literal["greeting", "intro_question", 
                               "resume_point", "technical_question", "closing"]
    current_resume_point_index: int
    
    # Domain tracking
    selected_domain: Optional[str]
    domain_coverage: Optional[dict]  # {domain: count}
    domain_plan: Optional[dict]      # {domain: target_count}
    
    # System
    messages: List[dict]
    status: Literal["active", "completed"]
```

---

## 4. Data Flow

### 4.1 Resume Upload Flow

```
User uploads PDF/DOCX
        ↓
FastAPI receives file
        ↓
Compute SHA256 hash
        ↓
Check database for duplicate
        ↓
    ┌───┴───┐
    │       │
   YES     NO
    │       │
    │       ↓
    │   Parse with Docling
    │       ↓
    │   Chunk hierarchically
    │       ↓
    │   Match domains (LLM)
    │       ↓
    │   Generate embeddings (OpenAI)
    │       ↓
    │   Store in Pinecone
    │       ↓
    │   Generate resume summary
    │       ↓
    │   Save to database
    │       ↓
    └───────┤
            ↓
    Return resume_id
```

### 4.2 Interview Flow

```
Start Interview
        ↓
Create session in DB
        ↓
Initialize LangGraph state
        ↓
Load resume summary
        ↓
Generate welcome message
        ↓
┌────────────────────────────────┐
│      INTERVIEW LOOP            │
│                                │
│  User submits answer           │
│         ↓                      │
│  Save message to DB            │
│         ↓                      │
│  Load workflow state           │
│         ↓                      │
│  ┌───────────────┐             │
│  │ If welcome:   │             │
│  │ - Parse Y/N   │             │
│  │ - Generate Q1 │             │
│  └───────────────┘             │
│         ↓                      │
│  ┌───────────────┐             │
│  │ If answering: │             │
│  │ 1. Evaluate   │             │
│  │ 2. Save eval  │             │
│  │ 3. Generate   │             │
│  │    next Q     │             │
│  └───────────────┘             │
│         ↓                      │
│  Update session state          │
│         ↓                      │
│  Save to database              │
│         ↓                      │
│  Return to user                │
│         ↓                      │
│  ┌──────────────┐              │
│  │ Check:       │              │
│  │ Complete?    │              │
│  └──┬───────┬───┘              │
│     │       │                  │
│    NO      YES                 │
│     │       │                  │
│     └───────┼──► Loop          │
│             │                  │
│             ↓                  │
│     Generate Report            │
│             ↓                  │
│     Save report to DB          │
│             ↓                  │
│     Mark session complete      │
│                                │
└────────────────────────────────┘
```

### 4.3 RAG Flow

```
User answer submitted
        ↓
Extract keywords from answer
        ↓
Generate embedding (OpenAI)
        ↓
Query Pinecone
  - Filter: resume_id + domain
  - Top-K: 3-5 chunks
        ↓
Retrieve relevant chunks
        ↓
Combine with question context
        ↓
Pass to Question Agent
        ↓
Generate personalized question
```

---

## 5. Database Schema

### 5.1 SQLite Schema

```sql
-- Users table
CREATE TABLE users (
    user_id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Resumes table
CREATE TABLE resumes (
    resume_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    job_role VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_hash VARCHAR UNIQUE,  -- SHA256 for deduplication
    parsed_content JSON,
    skills JSON,  -- List of extracted skills
    chunks_metadata JSON,  -- {num_chunks, matched_domains, resume_summary}
    vector_store_ids JSON,  -- List of Pinecone vector IDs
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX ix_resumes_user_id ON resumes(user_id);
CREATE UNIQUE INDEX ix_resumes_file_hash ON resumes(file_hash);

-- Interview Sessions table
CREATE TABLE interview_sessions (
    session_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    resume_id VARCHAR NOT NULL,
    job_role VARCHAR NOT NULL,
    current_round VARCHAR NOT NULL,  -- welcome, intro, resume_discussion, etc.
    status VARCHAR DEFAULT 'active',  -- active, completed
    technical_questions_count INT DEFAULT 0,
    behavioral_questions_count INT DEFAULT 0,
    workflow_state JSON,  -- Serialized InterviewState
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id)
);
CREATE INDEX ix_sessions_user_id ON interview_sessions(user_id);

-- Messages table
CREATE TABLE messages (
    message_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    message_metadata JSON,  -- {type, domain, difficulty, score, feedback, report}
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id)
);
CREATE INDEX ix_messages_session_id ON messages(session_id);
```

### 5.2 Pinecone Schema

```python
# Vector index structure
{
    "id": "resume_id_chunk_0",  # Unique vector ID
    "values": [0.1, 0.2, ...],  # 512-dim embedding (OpenAI text-embedding-3-small)
    "metadata": {
        "text": "chunk content here...",
        "resume_id": "abc-123",
        "chunk_index": 0,
        "job_role": "Data Scientist",
        "parent_section": "experience",
        "chunk_type": "entry",
        "entry_index": 0,
        "domains": ["Python", "Machine Learning"],  # List of matched domains
        "primary_domain": "Python"  # Main domain
    }
}
```

---

## 6. API Design

### 6.1 Authentication Endpoints

```
POST /api/v1/auth/register
Request:
{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
}
Response:
{
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "access_token": "jwt_token"
}

POST /api/v1/auth/login
Request:
{
    "email": "user@example.com",
    "password": "password123"
}
Response:
{
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user": {
        "user_id": "uuid",
        "email": "user@example.com",
        "name": "John Doe"
    }
}

GET /api/v1/auth/me
Headers: Authorization: Bearer <token>
Response:
{
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
}
```

### 6.2 Resume Endpoints

```
POST /api/v1/resumes/upload
Headers: Authorization: Bearer <token>
Content-Type: multipart/form-data
Request:
{
    "file": <PDF/DOCX>,
    "job_role": "Data Scientist"
}
Response:
{
    "resume_id": "uuid",
    "message": "Resume processed successfully",
    "skills": ["Python", "SQL", "ML"],
    "duplicate": false  // true if resume already exists
}
```

### 6.3 Interview Endpoints

```
POST /api/v1/interviews/start
Headers: Authorization: Bearer <token>
Request:
{
    "resume_id": "uuid",
    "job_role": "Data Scientist"
}
Response:
{
    "session_id": "uuid",
    "message": "Welcome message...",
    "type": "welcome"
}

POST /api/v1/sessions/{session_id}/answer
Headers: Authorization: Bearer <token>
Request:
{
    "answer": "Yes, I'm ready!",
    "question": "optional",
    "domain": "optional",
    "difficulty": "optional"
}
Response:
{
    "evaluation": {
        "score": 0.85,
        "feedback": {
            "feedback_text": "Great answer!",
            "strengths": ["clear explanation"],
            "improvements": ["add more examples"]
        }
    },
    "next_question": {
        "question_text": "Tell me about...",
        "domain": "Python",
        "difficulty": "medium",
        "round": "technical"
    }
}

GET /api/v1/sessions
Headers: Authorization: Bearer <token>
Response:
{
    "sessions": [
        {
            "id": "uuid",
            "title": "Interview 2025-11-04",
            "createdAt": "2025-11-04T10:00:00",
            "job_role": "Data Scientist",
            "status": "completed"
        }
    ]
}

GET /api/v1/sessions/{session_id}/messages
Headers: Authorization: Bearer <token>
Response:
{
    "session_id": "uuid",
    "messages": [
        {
            "message_id": "uuid",
            "role": "assistant",
            "content": "Welcome...",
            "message_metadata": {"type": "welcome"},
            "created_at": "2025-11-04T10:00:00"
        }
    ]
}

GET /api/v1/sessions/{session_id}/report
Headers: Authorization: Bearer <token>
Response:
{
    "overall_score": 0.78,
    "domain_scores": {
        "Python": 0.85,
        "SQL": 0.72
    },
    "strengths": ["Strong Python skills"],
    "weaknesses": ["SQL optimization needs work"],
    "recommendations": ["Practice SQL joins"],
    "hiring_recommendation": "Recommend for interview"
}

DELETE /api/v1/sessions/{session_id}
Headers: Authorization: Bearer <token>
Response:
{
    "message": "Session deleted successfully",
    "session_id": "uuid"
}
```

---

## 7. Technology Stack

### 7.1 Frontend
```
- Framework: React 18
- UI: Custom CSS
- State Management: React Hooks (useState, useEffect)
- HTTP Client: fetch API
- Build Tool: Create React App
```

### 7.2 Backend
```
- Framework: FastAPI 0.104+
- Language: Python 3.10+
- ASGI Server: Uvicorn
- API Documentation: OpenAPI (Swagger)
```

### 7.3 AI/ML
```
- Agent Framework: LangGraph (StateGraph)
- LLM (Evaluation): OpenAI GPT-4o
- LLM (Questions): Hugging Face (fine-tuned model)
- Embeddings: OpenAI text-embedding-3-small (512 dim)
- Document Parsing: Docling 2.0+
```

### 7.4 Database & Storage
```
- Primary DB: SQLite (production: PostgreSQL)
- Vector DB: Pinecone (serverless, AWS)
- File Storage: Local filesystem (uploads/)
- ORM: SQLAlchemy 2.0
```

### 7.5 External Services
```
- OpenAI API: GPT-4o, embeddings
- Hugging Face API: Inference endpoints
- Pinecone Cloud: Vector storage
```

---

## 8. Scalability & Performance

### 8.1 Current Architecture (Single Instance)
```
- Handles: ~50-100 concurrent interviews
- Bottleneck: OpenAI API rate limits
- Database: SQLite (single file)
```

### 8.2 Scalability Improvements

#### **Horizontal Scaling**
```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)            │
└───────────┬──────────────┬──────────────┘
            │              │
    ┌───────▼──────┐  ┌────▼──────────┐
    │ FastAPI      │  │ FastAPI       │
    │ Instance 1   │  │ Instance 2    │
    └──────┬───────┘  └──────┬────────┘
           │                 │
           └────────┬────────┘
                    │
           ┌────────▼────────┐
           │   PostgreSQL    │
           │   (Primary)     │
           └─────────────────┘
```

#### **Caching Layer**
```
- Redis: Cache resume embeddings, summaries
- TTL: 24 hours for resume data
- Reduces: OpenAI API calls by ~60%
```

#### **Async Processing**
```
- Celery: Background tasks for resume processing
- RabbitMQ/Redis: Message queue
- Workers: Parallel resume parsing
```

#### **Database Optimization**
```
- Move to PostgreSQL
- Read replicas for sessions/messages
- Connection pooling (pgbouncer)
- Indexes on frequently queried fields
```

### 8.3 Performance Metrics

```
Operation                  | Current    | Target
---------------------------|------------|-------------
Resume Upload & Process    | 30-60s     | 20-30s
Question Generation        | 2-5s       | 1-3s
Answer Evaluation          | 3-7s       | 2-4s
Report Generation          | 10-15s     | 5-10s
Database Query             | <100ms     | <50ms
Vector Search (Pinecone)   | 200-500ms  | 100-300ms
```

---

## 9. Security Architecture

### 9.1 Authentication & Authorization

```
┌──────────────────────────────────────────────────┐
│              User Login                           │
└────────────────┬─────────────────────────────────┘
                 ↓
        Email + Password
                 ↓
        ┌────────────────┐
        │ Bcrypt Hash    │
        │ Verification   │
        └────────┬───────┘
                 ↓
        ┌────────────────┐
        │  Generate JWT  │
        │  - user_id     │
        │  - email       │
        │  - exp: 7 days │
        └────────┬───────┘
                 ↓
         Return access_token
                 ↓
┌────────────────────────────────────────────────┐
│         Subsequent Requests                     │
│  Authorization: Bearer <token>                 │
└────────────────┬───────────────────────────────┘
                 ↓
        ┌────────────────┐
        │  Verify JWT    │
        │  - Signature   │
        │  - Expiration  │
        └────────┬───────┘
                 ↓
        ┌────────────────┐
        │  Extract user  │
        │  from token    │
        └────────┬───────┘
                 ↓
         Inject current_user
         into endpoint
```

### 9.2 Data Security

#### **File Upload Security**
```python
# 1. File validation
- Max size: 10MB
- Allowed types: PDF, DOCX
- Virus scanning (future)

# 2. Storage
- Unique filename (UUID)
- Isolated directory (uploads/)
- No direct access (served via API)

# 3. Deduplication
- SHA256 hash
- Prevent duplicate storage
- Privacy-preserving (one-way hash)
```

#### **API Security**
```python
# 1. CORS
- Allowed origins: frontend domain only
- Credentials: allowed
- Methods: GET, POST, PUT, DELETE

# 2. Rate Limiting (future)
- Per-user: 100 req/min
- Per-IP: 200 req/min

# 3. Input Validation
- Pydantic models
- SQL injection prevention (ORM)
- XSS protection
```

#### **Database Security**
```python
# 1. Password Storage
- Bcrypt hashing (cost=12)
- Salt per password
- Never store plaintext

# 2. Access Control
- Row-level security (user_id checks)
- Foreign key constraints
- Indexes for efficient lookups

# 3. Session Management
- JWT tokens (7-day expiry)
- Stateless authentication
- Revocation: not implemented (future)
```

### 9.3 External API Security

```python
# 1. API Keys
- Stored in .env (never in code)
- Loaded via environment variables
- Rotation policy (manual)

# 2. Rate Limiting
- OpenAI: Tier-based limits
- Hugging Face: Model-specific limits
- Pinecone: Quota monitoring

# 3. Error Handling
- Never expose API keys in logs
- Sanitize error messages
- Generic errors to client
```

---

## 10. Deployment Architecture

### 10.1 Development

```
┌──────────────────────────────────────────┐
│         Developer Machine                 │
│  ┌────────────┐    ┌──────────────┐     │
│  │  Backend   │    │   Frontend   │     │
│  │  :8000     │◄───┤   :3000      │     │
│  └────────────┘    └──────────────┘     │
│       │                                  │
│       ├─► SQLite (local)                │
│       ├─► Pinecone (cloud)              │
│       └─► OpenAI API                    │
└──────────────────────────────────────────┘
```

### 10.2 Production (Future)

```
┌─────────────────────────────────────────────────────┐
│                  Cloud Provider                      │
│  ┌───────────────────────────────────────────────┐ │
│  │            CDN (CloudFlare)                    │ │
│  │       - Static assets                          │ │
│  │       - Frontend (React build)                 │ │
│  └───────────────────┬───────────────────────────┘ │
│                      │                              │
│  ┌───────────────────▼───────────────────────────┐ │
│  │       Load Balancer (AWS ALB/Nginx)           │ │
│  └──────────────┬──────────────┬─────────────────┘ │
│                 │              │                    │
│  ┌──────────────▼────┐  ┌──────▼─────────────┐    │
│  │  FastAPI Server   │  │  FastAPI Server    │    │
│  │  (Container)      │  │  (Container)       │    │
│  └──────────┬────────┘  └───────┬────────────┘    │
│             │                    │                  │
│  ┌──────────▼────────────────────▼────────────┐   │
│  │         PostgreSQL (RDS/Managed)            │   │
│  │         - Primary + Read Replica            │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │         Redis (ElastiCache)                  │  │
│  │         - Caching layer                      │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │         S3 Bucket                            │  │
│  │         - Resume storage                     │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │              │
         │              └─────► Pinecone (Cloud)
         │
         └────────────────────► OpenAI API
```

---

## 11. Key Design Patterns

### 11.1 Agent Pattern (A2A Protocol)
```
- Agents communicate via shared state
- LangGraph orchestrates execution flow
- Each agent has single responsibility
- State transitions are explicit
```

### 11.2 Service Layer Pattern
```
- Controllers (routers) → Services → Repositories (models)
- Business logic in service layer
- Database access through ORM
- Clean separation of concerns
```

### 11.3 RAG Pattern
```
- Document chunking (hierarchical)
- Embedding generation (OpenAI)
- Vector storage (Pinecone)
- Semantic search for context
- Context injection in prompts
```

### 11.4 State Management Pattern
```
- Workflow state in LangGraph
- Session state in database (JSON)
- Stateless API (JWT)
- State hydration from DB
```

---

## 12. Future Enhancements

### 12.1 Features
```
- Multi-language support
- Voice interview mode
- Video recording & analysis
- Practice mode (no evaluation)
- Custom question banks
- Interview scheduling
- Candidate dashboard
```

### 12.2 Technical
```
- WebSocket support (real-time)
- GraphQL API
- Microservices architecture
- Event-driven architecture (Kafka)
- ML model fine-tuning pipeline
- A/B testing framework
- Analytics & monitoring
```

---

## Summary

This AI Interviewer platform is built on a modern, scalable architecture with:

1. **Multi-Agent System (A2A Protocol)**: Orchestrated by LangGraph
2. **RAG Implementation**: Pinecone + OpenAI embeddings
3. **Conversational AI**: Natural, human-like interview flow
4. **Secure & Scalable**: JWT auth, modular design, cloud-ready
5. **Full-Stack**: React frontend + FastAPI backend

The system demonstrates advanced AI capabilities including agent orchestration, semantic search, and conversational intelligence while maintaining production-ready code quality and security standards.

