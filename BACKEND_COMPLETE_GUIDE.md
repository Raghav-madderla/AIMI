# Complete Backend Architecture & Implementation Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Database Models](#database-models)
6. [API Endpoints](#api-endpoints)
7. [Service Layer](#service-layer)
8. [Agent System (A2A Protocol)](#agent-system-a2a-protocol)
9. [Workflow Orchestration](#workflow-orchestration)
10. [Data Flow](#data-flow)
11. [Configuration](#configuration)
12. [Key Implementation Details](#key-implementation-details)

---

## System Overview

This is an **AI-powered interview platform** that conducts automated technical interviews using a multi-agent system. The backend is built with **FastAPI** and uses **LangGraph** for agent orchestration.

### Key Features:
- **Resume Processing**: Parses PDF/DOCX resumes, extracts skills, chunks content hierarchically
- **Vector Search**: Uses Pinecone for semantic search of resume content
- **Multi-Agent Interview**: 6 specialized AI agents working together via LangGraph
- **RAG (Retrieval-Augmented Generation)**: Retrieves relevant resume context for personalized questions
- **Evaluation System**: Scores answers and provides detailed feedback
- **Report Generation**: Comprehensive interview analysis

---

## Technology Stack

### Core Framework
- **FastAPI 0.104.1**: Modern async web framework
- **Python 3.10+**: Programming language
- **Uvicorn**: ASGI server
- **SQLAlchemy 2.0.23**: ORM for database operations
- **Pydantic 2.5+**: Data validation and settings

### AI/ML Stack
- **LangGraph 0.0.20**: Agent orchestration framework
- **LangChain 0.1.0**: LLM integration
- **Transformers 4.40+**: Local model loading (Qwen)
- **Sentence-Transformers 2.7+**: Embedding generation
- **Torch 2.0+**: Deep learning framework

### Database & Storage
- **SQLite**: Primary database (can be PostgreSQL)
- **Pinecone 3.0.0**: Vector database for embeddings
- **Local Filesystem**: Resume file storage (`uploads/`)

### External Services
- **Hugging Face API**: Fine-tuned question generation model
- **Pinecone Cloud**: Vector storage (AWS serverless)

### Utilities
- **Docling 2.0+**: PDF parsing
- **python-docx**: DOCX parsing
- **bcrypt**: Password hashing
- **python-jose**: JWT authentication
- **httpx**: Async HTTP client

---

## Project Structure

```
backend/
├── main.py                          # FastAPI app entry point
├── requirements.txt                 # Python dependencies
├── interview.db                     # SQLite database (created on first run)
├── uploads/                         # Resume file storage
│
├── app/
│   ├── __init__.py
│   │
│   ├── core/                        # Core configuration
│   │   ├── config.py                # Settings & environment variables
│   │   └── database.py              # DB connection & session management
│   │
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                  # User model
│   │   ├── resume.py                # Resume model
│   │   ├── session.py               # InterviewSession model
│   │   └── message.py               # Message model
│   │
│   ├── api/v1/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication endpoints
│   │   └── interviews.py            # Interview & resume endpoints
│   │
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   │
│   │   ├── agents/                  # AI Agents
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator_agent.py    # Main interview coordinator
│   │   │   ├── question_agent.py        # Question generation (HF API)
│   │   │   ├── question_cleaning_agent.py  # Question refinement
│   │   │   ├── evaluation_agent.py      # Answer evaluation
│   │   │   ├── resume_summary_agent.py   # Resume analysis
│   │   │   └── report_agent.py          # Final report generation
│   │   │
│   │   ├── interview_service.py     # Interview orchestration
│   │   ├── interview_workflow.py    # LangGraph workflow definition
│   │   ├── resume_service.py        # Resume processing
│   │   ├── rag_service.py           # RAG implementation
│   │   ├── embedding_service.py     # Embedding generation (Qwen)
│   │   ├── vector_store.py          # Pinecone interface
│   │   └── local_llm_service.py     # Local Qwen LLM
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── auth.py                  # JWT token management
│       └── langgraph_state.py       # Shared state definition
```

---

## Core Components

### 1. Configuration (`app/core/config.py`)

**Purpose**: Centralized configuration management with environment variable support.

**Key Settings**:
```python
# Database
DATABASE_URL = "sqlite:///./interview.db"  # Can be PostgreSQL

# Pinecone Vector DB
PINECONE_API_KEY = ""  # Required
PINECONE_ENVIRONMENT = "us-east-1"
PINECONE_INDEX_NAME = "resumes"
PINECONE_DIMENSION = 1024  # Qwen3-Embedding-0.6B dimension

# Embedding Model (Local)
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_DIMENSION = 1024

# Hugging Face API (Question Generation)
HUGGINGFACE_API_URL = ""  # Your fine-tuned model endpoint
HUGGINGFACE_API_KEY = ""  # HF API key

# Local LLM (Evaluation, Cleaning, etc.)
LOCAL_LLM_MODEL = "Qwen/Qwen3-0.6B"

# File Storage
UPLOAD_DIR = "./uploads"
MAX_FILE_SIZE = 10485760  # 10MB

# Security
SECRET_KEY = "change-this-secret-key-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# CORS
CORS_ORIGINS = "http://localhost:3000,http://localhost:3001"
```

**How to Configure**:
1. Edit `app/core/config.py` directly, OR
2. Create `.env` file in `backend/` directory
3. Environment variables override defaults

---

### 2. Database (`app/core/database.py`)

**Purpose**: Database connection management with async and sync support.

**Key Features**:
- **Async Engine**: For async operations (preferred)
- **Sync Engine**: For table creation and compatibility
- **SQLite Support**: Special handling for SQLite async (`sqlite+aiosqlite://`)
- **PostgreSQL Support**: Can switch to PostgreSQL
- **Foreign Keys**: Enabled for SQLite

**Session Management**:
```python
# Async session (preferred)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync session (for compatibility)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Database Models

### 1. User Model (`app/models/user.py`)

**Table**: `users`

**Fields**:
- `user_id` (String, PK): UUID
- `email` (String, Unique, Indexed): User email
- `name` (String): User's name
- `password_hash` (String): Bcrypt hashed password
- `is_active` (Boolean): Account status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Methods**:
- `set_password(password)`: Hash and store password
- `check_password(password)`: Verify password

---

### 2. Resume Model (`app/models/resume.py`)

**Table**: `resumes`

**Fields**:
- `resume_id` (String, PK): UUID
- `user_id` (String, FK): References `users.user_id`
- `job_role` (String): Target job role
- `file_path` (String): Path to uploaded file
- `file_hash` (String, Unique, Indexed): SHA256 hash for deduplication
- `parsed_content` (JSON): Extracted resume content
- `skills` (JSON): List of extracted skills
- `chunks_metadata` (JSON): 
  - `num_chunks`: Number of chunks created
  - `matched_domains`: List of domains found
  - `resume_summary`: Structured summary from agent
- `vector_store_ids` (JSON): List of Pinecone vector IDs
- `created_at` (DateTime): Upload timestamp

**Deduplication**: Uses SHA256 hash to prevent duplicate processing.

---

### 3. InterviewSession Model (`app/models/session.py`)

**Table**: `interview_sessions`

**Fields**:
- `session_id` (String, PK): UUID
- `user_id` (String, FK): References `users.user_id`
- `resume_id` (String, FK): References `resumes.resume_id`
- `job_role` (String): Interview job role
- `current_round` (String): `welcome`, `intro`, `resume_discussion`, `technical_deep_dive`, `completed`
- `status` (String): `active` or `completed`
- `technical_questions_count` (Integer): Count of technical questions
- `behavioral_questions_count` (Integer): Count of behavioral questions
- `workflow_state` (JSON): **Full LangGraph state** (preserves conversation flow)
- `created_at` (DateTime): Session start time
- `updated_at` (DateTime): Last update time

**Relationships**:
- `messages`: One-to-many with `Message` model

**State Persistence**: The `workflow_state` JSON field stores the complete LangGraph state, allowing the interview to resume exactly where it left off.

---

### 4. Message Model (`app/models/message.py`)

**Table**: `messages`

**Fields**:
- `message_id` (String, PK): UUID
- `session_id` (String, FK): References `interview_sessions.session_id`
- `role` (String): `user` or `assistant`
- `content` (String): Message text
- `message_metadata` (JSON): 
  - For questions: `{type, domain, difficulty, round}`
  - For answers: `{feedback, score}`
  - For reports: `{type: "report", report: {...}}`
- `created_at` (DateTime): Message timestamp

**Relationships**:
- `session`: Many-to-one with `InterviewSession`

---

## API Endpoints

### Authentication (`app/api/v1/auth.py`)

#### POST `/api/v1/auth/register`
Register a new user.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response**:
```json
{
  "token": "jwt_token_here",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### POST `/api/v1/auth/login`
Login and get JWT token.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**: Same as register.

#### GET `/api/v1/auth/me`
Get current user (requires JWT token in `Authorization: Bearer <token>` header).

---

### Interview Endpoints (`app/api/v1/interviews.py`)

#### POST `/api/v1/resumes/upload`
Upload and process a resume.

**Headers**: `Authorization: Bearer <token>`

**Request** (multipart/form-data):
- `file`: PDF or DOCX file
- `job_role`: String (e.g., "Data Scientist")

**Response**:
```json
{
  "resume_id": "uuid",
  "message": "Resume processed successfully",
  "skills": ["Python", "SQL", "ML"]
}
```

**Processing Flow**:
1. Compute SHA256 hash
2. Check for duplicate
3. Parse with Docling (PDF) or python-docx (DOCX)
4. Chunk hierarchically (sections → entries)
5. Match domains using LLM
6. Generate embeddings (Qwen)
7. Store in Pinecone
8. Generate resume summary
9. Save to database

---

#### POST `/api/v1/interviews/start`
Start a new interview session.

**Request**:
```json
{
  "resume_id": "uuid",
  "job_role": "Data Scientist"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "message": "Welcome message...",
  "type": "welcome"
}
```

**What Happens**:
1. Creates `InterviewSession` in database
2. Initializes LangGraph state
3. Loads resume summary
4. Generates welcome message
5. Saves state to `workflow_state` JSON field

---

#### POST `/api/v1/sessions/{session_id}/answer`
Submit an answer and get evaluation + next question.

**Request**:
```json
{
  "answer": "My answer here...",
  "question": "Previous question text",
  "domain": "Python",
  "difficulty": "medium"
}
```

**Response**:
```json
{
  "evaluation": {
    "score": 0.85,
    "feedback": {
      "feedback_text": "Great answer!",
      "strengths": ["Clear explanation"],
      "improvements": ["Add more examples"]
    }
  },
  "next_question": {
    "question_text": "Next question...",
    "domain": "SQL",
    "difficulty": "medium",
    "round": "technical"
  }
}
```

**Flow**:
1. Save user answer message
2. Load workflow state from `session.workflow_state`
3. If `welcome` phase: Handle welcome response
4. Otherwise: Evaluate answer → Generate next question
5. Update `workflow_state` in database
6. Save messages
7. If interview complete: Generate final report

---

#### GET `/api/v1/sessions/{session_id}/messages`
Get all messages for a session.

**Response**:
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "message_id": "uuid",
      "role": "assistant",
      "content": "Welcome...",
      "message_metadata": {"type": "welcome"},
      "created_at": "2025-01-01T10:00:00"
    }
  ]
}
```

---

#### GET `/api/v1/sessions`
List all sessions for current user.

**Response**:
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "Interview 2025-01-01",
      "createdAt": "2025-01-01T10:00:00",
      "job_role": "Data Scientist",
      "status": "completed"
    }
  ]
}
```

---

#### GET `/api/v1/sessions/{session_id}/report`
Get comprehensive interview report (only for completed interviews).

**Response**:
```json
{
  "session_id": "uuid",
  "job_role": "Data Scientist",
  "statistics": {
    "total_questions": 7,
    "overall_score": 0.78,
    "overall_percentage": 78.0,
    "domain_scores": {
      "Python": 0.85,
      "SQL": 0.72
    }
  },
  "analysis": {
    "overall_summary": "...",
    "strengths": ["..."],
    "areas_for_improvement": ["..."],
    "domain_analysis": {...},
    "recommendations": ["..."],
    "hiring_decision": {
      "recommendation": "Recommend",
      "reasoning": "..."
    }
  }
}
```

---

#### DELETE `/api/v1/sessions/{session_id}`
Delete a session and all its messages.

---

## Service Layer

### 1. Interview Service (`app/services/interview_service.py`)

**Purpose**: High-level interview orchestration.

**Key Methods**:

#### `initialize_interview()`
Creates initial LangGraph state:
- Sets conversation phase to `greeting`
- Initializes empty lists for questions/answers/evaluations
- Loads resume summary from database
- Sets initial difficulty to `easy`

#### `generate_welcome_message()`
Generates friendly welcome message from AIMI.

#### `handle_welcome_response()`
Processes user's response to welcome:
- Parses "yes"/"no" intent
- Transitions to `intro_question` phase if confirmed
- Returns clarification if ambiguous

#### `generate_next_question()`
Runs LangGraph workflow to generate next question:
- Executes: `orchestrator → question_agent → cleaning_agent → orchestrator`
- Extracts question from state
- Updates `question_count` and `domain_coverage`
- Returns question data

#### `evaluate_answer()`
Evaluates user's answer:
- Sets evaluation context
- Calls evaluation agent
- Updates state with evaluation results
- Sets `next_action` to `generate_question`

---

### 2. Resume Service (`app/services/resume_service.py`)

**Purpose**: Resume processing and domain matching.

**Key Methods**:

#### `process_resume()`
Complete resume processing pipeline:
1. **Deduplication**: Compute SHA256 hash, check database
2. **Text Extraction**: 
   - PDF: Docling parser
   - DOCX: python-docx
3. **Hierarchical Chunking**:
   - Identifies sections (experience, education, projects, etc.)
   - Parses entries within sections
   - Creates chunks with metadata
4. **Domain Matching**:
   - Uses local LLM to match chunks to 9 domains:
     - Python, SQL, Data Engineering, Data Analysis
     - Machine Learning, Deep Learning, AI
     - System Design, Statistics
5. **Embedding Generation**: Batch embeddings using Qwen
6. **Vector Storage**: Stores in Pinecone with metadata
7. **Resume Summary**: Calls resume_summary_agent
8. **Database Save**: Stores resume metadata

#### `_chunk_resume_hierarchically()`
Creates hierarchical chunks:
- Parent: Section headers (optional)
- Children: Individual entries within sections
- Metadata: `parent_section`, `chunk_type`, `entry_index`

#### `_match_chunk_to_domains()`
Uses local LLM to classify chunks:
- Prompt includes chunk text and available domains
- Returns list of matched domains (max 3 per chunk)
- Fallback to keyword matching if LLM fails

#### `get_resume_context()`
Retrieves resume summary for RAG (delegates to RAG service).

---

### 3. RAG Service (`app/services/rag_service.py`)

**Purpose**: Retrieval-Augmented Generation for context retrieval.

**Key Methods**:

#### `retrieve_relevant_context()`
Retrieves relevant resume chunks:
- Generates query embedding
- Queries Pinecone with optional domain filter
- Returns concatenated context

#### `get_resume_summary()`
Gets top-K chunks for initial context.

#### `get_domains_for_resume()`
Extracts all unique domains from resume chunks.

#### `get_chunks_by_domain()`
Gets chunks filtered by specific domain.

#### `get_domain_relevance()`
Returns domain relevance scores (chunk counts per domain).

---

### 4. Embedding Service (`app/services/embedding_service.py`)

**Purpose**: Generate embeddings using local Qwen model.

**Model**: `Qwen/Qwen3-Embedding-0.6B` (1024 dimensions)

**Key Methods**:
- `embed_text()`: Single text embedding (async)
- `embed_texts()`: Batch embeddings (async)
- `embed_text_sync()`: Synchronous version
- `embed_texts_sync()`: Synchronous batch

**Lazy Loading**: Model loads only when first used.

---

### 5. Vector Store (`app/services/vector_store.py`)

**Purpose**: Pinecone vector database interface.

**Key Methods**:

#### `add_documents()`
Upserts documents to Pinecone:
- Converts metadata to Pinecone-compatible types
- Stores text in metadata
- Batches upserts (100 vectors per batch)

#### `query()`
Queries Pinecone with embedding:
- Supports metadata filters
- Returns documents, metadatas, distances

#### `query_by_domain()`
Queries with domain filter:
- Filters by `primary_domain` or `domains` list
- Returns top-K matching chunks

#### `get_by_resume_id()`
Gets all chunks for a resume (uses filter).

**Lazy Initialization**: Connects to Pinecone only when first used.

---

### 6. Local LLM Service (`app/services/local_llm_service.py`)

**Purpose**: Text generation using local Qwen model.

**Model**: `Qwen/Qwen3-0.6B`

**Key Methods**:

#### `generate()`
Generates text from messages:
- Uses chat template
- Supports temperature and max tokens
- Returns generated text

#### `generate_json()`
Generates and parses JSON:
- Attempts direct JSON parsing
- Falls back to regex extraction
- Returns parsed dict or empty dict

**Lazy Loading**: Model loads only when first used.

---

## Agent System (A2A Protocol)

The system uses **6 specialized agents** that communicate via shared state (LangGraph).

### Agent Communication Flow

```
User Answer
    ↓
Orchestrator Agent (decides next action)
    ↓
    ├─→ Question Agent (generates question)
    │       ↓
    │   Cleaning Agent (refines question)
    │       ↓
    │   Back to Orchestrator
    │
    └─→ Evaluation Agent (evaluates answer)
            ↓
        Back to Orchestrator
```

---

### 1. Orchestrator Agent (`app/services/agents/orchestrator_agent.py`)

**Role**: Interview manager (human-like hiring manager)

**Responsibilities**:
- Manages conversation flow through phases:
  1. **Greeting**: Welcome message
  2. **Intro Question**: "Tell me about yourself"
  3. **Resume Discussion**: Goes through resume points
  4. **Technical Deep Dive**: Domain-specific questions
  5. **Closing**: Thank you message
- Tracks interview progress (`question_count`, `domain_coverage`)
- Decides next action (`generate_question`, `evaluate`, `complete`)
- Sets context for other agents
- Adjusts difficulty based on performance

**Key Logic**:
- **Resume Discussion**: Iterates through `resume_summary.summary_points`
- **Technical Phase**: Cycles through domains, asks 5-7 questions total
- **Difficulty Adjustment**: Based on recent evaluation scores

**Outputs**:
- `next_action`: What to do next
- `question_context`: Context for question agent
- `evaluation_context`: Context for evaluation agent
- `orchestrator_intent`: What to ask about (for cleaning agent)

---

### 2. Question Agent (`app/services/agents/question_agent.py`)

**Role**: Generate interview questions using fine-tuned Hugging Face model

**Inputs** (from `question_context`):
- `domain`: Technical domain (e.g., "Python")
- `difficulty`: `easy`, `medium`, `hard`
- `resume_context`: Relevant resume chunks
- `job_role`: Target job role

**Process**:
1. Builds Alpaca-format prompt
2. Calls Hugging Face Inference API
3. Cleans generated text (removes special tokens)
4. Returns question

**API Format**:
```json
{
  "inputs": "prompt...",
  "parameters": {
    "max_new_tokens": 150,
    "temperature": 0.7,
    "return_full_text": false
  }
}
```

**Outputs**:
- `question_agent_response.question`: Generated question text
- `question_agent_response.domain`: Domain
- `question_agent_response.difficulty`: Difficulty
- `question_agent_response.error`: Error if failed

**No Fallback**: Returns error if HF API fails (no local fallback).

---

### 3. Question Cleaning Agent (`app/services/agents/question_cleaning_agent.py`)

**Role**: Refine questions to be conversational and contextual

**Inputs**:
- `generated_question`: Raw question from question agent
- `resume_point`: Specific resume point being discussed
- `orchestrator_intent`: What orchestrator wants to ask
- `domain`: Technical domain

**Process**:
1. Uses local LLM to refine question
2. Makes it conversational (like a hiring manager)
3. References resume point when relevant
4. Aligns with orchestrator's intent

**Outputs**:
- `cleaned_question`: Refined question text
- `success`: Boolean

**Fallback**: Returns original question if cleaning fails.

---

### 4. Evaluation Agent (`app/services/agents/evaluation_agent.py`)

**Role**: Evaluate candidate answers and provide feedback

**Inputs** (from `evaluation_context`):
- `question`: The question asked
- `answer`: User's answer
- `domain`: Technical domain
- `round`: `technical` or `behavioral`
- `difficulty`: Question difficulty

**Process**:
1. Builds evaluation prompt
2. Calls local LLM (Qwen) to generate JSON evaluation
3. Parses JSON response
4. Returns structured feedback

**Output Format**:
```json
{
  "score": 0.85,
  "feedback_text": "Detailed feedback...",
  "strengths": ["Clear explanation", "Good examples"],
  "improvements": ["Add more depth", "Mention best practices"]
}
```

**Outputs**:
- `evaluation_agent_response.score`: Float 0.0-1.0
- `evaluation_agent_response.feedback`: Structured feedback dict
- `evaluation_agent_response.error`: Error if failed

---

### 5. Resume Summary Agent (`app/services/agents/resume_summary_agent.py`)

**Role**: Extract structured summary from resume

**Inputs**:
- `resume_text`: Full resume text
- `job_role`: Target job role

**Process**:
1. Uses local LLM to analyze resume
2. Extracts 5-7 key talking points
3. Identifies domains and significance for each point
4. Generates talking angles

**Output Format**:
```json
{
  "summary_points": [
    {
      "point": "Brief description",
      "domains": ["Python", "ML"],
      "significance": "high",
      "talking_angle": "What to discuss"
    }
  ],
  "overall_impression": "Brief summary",
  "key_strengths": ["strength1", "strength2"]
}
```

**Used By**: Orchestrator to guide resume discussion phase.

---

### 6. Report Agent (`app/services/agents/report_agent.py`)

**Role**: Generate comprehensive interview report

**Inputs**:
- `evaluation_history`: List of all evaluations
- `user_answers`: List of user answers
- `previous_questions`: List of questions asked
- `job_role`: Target job role
- `session_id`: Session ID

**Process**:
1. Calculates statistics (overall score, domain scores)
2. Formats conversation history
3. Uses local LLM to generate analysis
4. Combines statistics with LLM analysis

**Output Format**:
```json
{
  "session_id": "uuid",
  "job_role": "Data Scientist",
  "statistics": {
    "total_questions": 7,
    "overall_score": 0.78,
    "overall_percentage": 78.0,
    "domain_scores": {...},
    "score_distribution": {...}
  },
  "analysis": {
    "overall_summary": "...",
    "strengths": [...],
    "areas_for_improvement": [...],
    "domain_analysis": {...},
    "recommendations": [...],
    "hiring_decision": {
      "recommendation": "Recommend",
      "reasoning": "..."
    }
  },
  "detailed_feedback": [...]
}
```

**Fallback**: Returns basic statistics if LLM fails.

---

## Workflow Orchestration

### LangGraph Workflow (`app/services/interview_workflow.py`)

**Purpose**: Defines the agent execution flow using LangGraph StateGraph.

**Workflow Definition**:
```python
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
    should_continue,  # Routing function
    {
        "generate_question": "question_agent",
        "evaluate": "evaluation_agent",
        "complete": END
    }
)

# Sequential flows
workflow.add_edge("question_agent", "cleaning_agent")
workflow.add_edge("cleaning_agent", "orchestrator")
workflow.add_edge("evaluation_agent", "orchestrator")
```

**Routing Function** (`should_continue`):
- Reads `next_action` from state
- Returns: `"generate_question"`, `"evaluate"`, or `"complete"`

**State Management**:
- State is passed between agents via LangGraph
- Full state is saved to `session.workflow_state` JSON field
- State is restored from database on each API call

---

### Shared State (`app/utils/langgraph_state.py`)

**Type**: `InterviewState` (TypedDict)

**Key Fields**:

**Session Info**:
- `session_id`: Session UUID
- `resume_id`: Resume UUID
- `job_role`: Target job role

**Interview Progress**:
- `current_round`: `welcome`, `intro`, `resume_discussion`, `technical_deep_dive`, `completed`
- `difficulty`: `easy`, `medium`, `hard`
- `question_count`: Number of questions asked
- `conversation_phase`: `greeting`, `intro_question`, `resume_point`, `technical_question`, `closing`

**Context Data**:
- `resume_context`: RAG-retrieved chunks
- `resume_summary`: Structured summary from agent
- `current_resume_point_index`: Index in resume summary points

**History**:
- `previous_questions`: List of questions asked
- `user_answers`: List of user answers
- `evaluation_history`: List of evaluations

**Agent Communication**:
- `next_action`: `generate_question`, `evaluate`, `complete`, `wait`
- `question_context`: Context for question agent
- `evaluation_context`: Context for evaluation agent
- `orchestrator_intent`: What orchestrator wants to ask
- `question_agent_response`: Response from question agent
- `evaluation_agent_response`: Response from evaluation agent
- `pending_question`: Question waiting to be cleaned

**Domain Tracking**:
- `selected_domain`: Current domain
- `domain_coverage`: `{domain: count}` - questions per domain
- `domain_plan`: `{domain: target_count}` - planned questions

**System**:
- `messages`: List of conversation messages
- `status`: `active` or `completed`

**State Annotations**:
- Lists use `Annotated[List[dict], operator.add]` for automatic merging in LangGraph

---

## Data Flow

### 1. Resume Upload Flow

```
User uploads PDF/DOCX
    ↓
FastAPI receives file
    ↓
Compute SHA256 hash
    ↓
Check database for duplicate
    ├─→ YES: Return existing resume_id
    └─→ NO: Continue
        ↓
Parse with Docling (PDF) or python-docx (DOCX)
    ↓
Extract text and structure
    ↓
Chunk hierarchically (sections → entries)
    ↓
For each chunk:
    ├─→ Match domains using local LLM
    └─→ Generate embedding (Qwen)
    ↓
Store chunks in Pinecone (with metadata)
    ↓
Generate resume summary (resume_summary_agent)
    ↓
Save to database (Resume model)
    ↓
Return resume_id
```

---

### 2. Interview Flow

```
Start Interview
    ↓
Create InterviewSession in DB
    ↓
Initialize LangGraph state
    ↓
Load resume summary from DB
    ↓
Generate welcome message
    ↓
Save state to workflow_state JSON
    ↓
┌─────────────────────────────────┐
│      INTERVIEW LOOP              │
│                                  │
│  User submits answer             │
│       ↓                          │
│  Save message to DB              │
│       ↓                          │
│  Load workflow_state from DB     │
│       ↓                          │
│  If welcome phase:               │
│    └─→ Handle welcome response   │
│       ↓                          │
│  Otherwise:                      │
│    ├─→ Evaluate answer           │
│    │   └─→ Evaluation Agent      │
│    │       ↓                      │
│    │   Save evaluation            │
│    │       ↓                      │
│    └─→ Generate next question    │
│        └─→ Run LangGraph workflow│
│            ├─→ Orchestrator      │
│            ├─→ Question Agent     │
│            ├─→ Cleaning Agent     │
│            └─→ Back to Orchestrator│
│                ↓                  │
│        Save question              │
│            ↓                      │
│  Update workflow_state in DB     │
│            ↓                      │
│  Return to user                  │
│            ↓                      │
│  Check if complete               │
│    ├─→ NO: Loop back             │
│    └─→ YES: Generate report      │
│        └─→ Report Agent          │
│            ↓                      │
│        Save report to DB          │
│            ↓                      │
│        Mark session complete     │
│                                  │
└─────────────────────────────────┘
```

---

### 3. RAG Flow (Question Generation)

```
Orchestrator decides to ask about domain X
    ↓
Extract keywords from resume point
    ↓
Generate query embedding (Qwen)
    ↓
Query Pinecone:
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

## Configuration

### Required Configuration

1. **Pinecone API Key**:
   - Get from [Pinecone Console](https://app.pinecone.io)
   - Set in `app/core/config.py`: `PINECONE_API_KEY`

2. **Hugging Face API** (for question generation):
   - Deploy your fine-tuned model to HF Inference API
   - Set `HUGGINGFACE_API_URL` and `HUGGINGFACE_API_KEY`

3. **Secret Key** (for JWT):
   - Change `SECRET_KEY` in production
   - Use strong random string

### Optional Configuration

- **Database**: Switch to PostgreSQL by changing `DATABASE_URL`
- **CORS Origins**: Add frontend URLs to `CORS_ORIGINS`
- **File Size**: Adjust `MAX_FILE_SIZE` if needed

### Environment Variables

Create `.env` file in `backend/`:
```env
PINECONE_API_KEY=your_key_here
HUGGINGFACE_API_URL=https://api-inference.huggingface.co/models/your-model
HUGGINGFACE_API_KEY=your_hf_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./interview.db
```

---

## Key Implementation Details

### 1. State Persistence

**Problem**: LangGraph state needs to persist between API calls.

**Solution**: 
- Store full state in `session.workflow_state` JSON field
- Load state on each API call
- Save updated state after each operation

**Code Pattern**:
```python
# Load state
workflow_state = session.workflow_state or initial_state

# Run workflow
result = await interview_service.evaluate_answer(workflow_state, ...)

# Save state
session.workflow_state = result["state"]
db.commit()
```

---

### 2. Resume Deduplication

**Problem**: Prevent processing same resume multiple times.

**Solution**:
- Compute SHA256 hash of file content
- Check `file_hash` unique index before processing
- Return existing resume if duplicate found

**Benefits**:
- Saves processing time
- Reduces Pinecone storage
- Prevents duplicate embeddings

---

### 3. Hierarchical Chunking

**Problem**: Resume has structure (sections, entries) that should be preserved.

**Solution**:
- Identify sections (experience, education, projects, etc.)
- Parse entries within sections
- Store metadata: `parent_section`, `chunk_type`, `entry_index`

**Benefits**:
- Better context for RAG
- Preserves resume structure
- Enables section-specific queries

---

### 4. Domain Matching

**Problem**: Automatically classify resume chunks into 9 technical domains.

**Solution**:
- Use local LLM (Qwen) to analyze each chunk
- Prompt includes chunk text and available domains
- Returns list of matched domains (max 3 per chunk)
- Fallback to keyword matching if LLM fails

**Domains**:
- Python, SQL, Data Engineering, Data Analysis
- Machine Learning, Deep Learning, AI
- System Design, Statistics

---

### 5. Conversational Flow

**Problem**: Make interview feel natural, not robotic.

**Solution**:
- Orchestrator manages phases: greeting → intro → resume → technical → closing
- Goes through resume points one by one
- Appreciates achievements before asking questions
- Adjusts difficulty based on performance

**Phases**:
1. **Greeting**: Welcome message
2. **Intro Question**: "Tell me about yourself"
3. **Resume Discussion**: Iterate through resume summary points
4. **Technical Deep Dive**: 5-7 domain-specific questions
5. **Closing**: Thank you + report

---

### 6. Error Handling

**Question Generation**:
- If HF API fails, returns error (no fallback)
- Error message shown to user

**Evaluation**:
- If LLM fails, returns fallback score (0.7)
- Logs error for debugging

**Report Generation**:
- If LLM fails, returns basic statistics
- Includes error in response

---

### 7. Async vs Sync

**Async Operations** (Preferred):
- Database queries (using `AsyncSession`)
- LLM calls
- HTTP requests (HF API)
- Embedding generation

**Sync Operations** (Compatibility):
- Table creation
- Some database operations (using `SessionLocal`)
- File I/O

**Pattern**:
- Use async where possible
- Fallback to sync for compatibility

---

### 8. Lazy Loading

**Models Loaded on First Use**:
- Embedding model (Qwen3-Embedding-0.6B)
- Local LLM (Qwen3-0.6B)
- Pinecone connection

**Benefits**:
- Faster startup
- Only loads what's needed
- Reduces memory if service not used

---

## Running the Backend

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure

Edit `app/core/config.py` or create `.env` file.

### 3. Run Database Migration (if needed)

```bash
python migrate_add_file_hash.py
```

### 4. Start Server

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Testing Endpoints

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "name": "Test User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

Save the `token` from response.

### 3. Upload Resume

```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf" \
  -F "job_role=Data Scientist"
```

Save the `resume_id` from response.

### 4. Start Interview

```bash
curl -X POST http://localhost:8000/api/v1/interviews/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "YOUR_RESUME_ID",
    "job_role": "Data Scientist"
  }'
```

Save the `session_id` from response.

### 5. Submit Answer

```bash
curl -X POST http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/answer \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Yes, I am ready!",
    "question": "",
    "domain": "",
    "difficulty": ""
  }'
```

---

## Troubleshooting

### 1. Pinecone Connection Error

**Error**: `Pinecone API key not configured`

**Solution**: Set `PINECONE_API_KEY` in config.

### 2. Hugging Face API Error

**Error**: `400 Bad Request` from HF API

**Solution**: 
- Check `HUGGINGFACE_API_URL` is correct
- Verify model is deployed and accessible
- Check API key is valid

### 3. Model Loading Slow

**First Request Takes Long**: Models load lazily on first use. This is normal.

**Solution**: Pre-load models in startup event (optional).

### 4. Database Locked (SQLite)

**Error**: `database is locked`

**Solution**: 
- Only one process should access SQLite
- Consider PostgreSQL for production

### 5. Embedding Dimension Mismatch

**Error**: Pinecone dimension doesn't match model

**Solution**: 
- Run `python check_embedding_dimension.py`
- Update `PINECONE_DIMENSION` in config

---

## Production Considerations

### 1. Database

- **Switch to PostgreSQL**: Change `DATABASE_URL`
- **Connection Pooling**: Configure SQLAlchemy pool
- **Migrations**: Use Alembic for schema changes

### 2. Security

- **Change SECRET_KEY**: Use strong random string
- **HTTPS**: Use reverse proxy (Nginx)
- **Rate Limiting**: Add rate limiting middleware
- **Input Validation**: Already handled by Pydantic

### 3. Performance

- **Caching**: Add Redis for resume summaries
- **Async Processing**: Use Celery for resume processing
- **CDN**: Serve static files via CDN

### 4. Monitoring

- **Logging**: Configure structured logging
- **Metrics**: Add Prometheus metrics
- **Error Tracking**: Integrate Sentry

### 5. Scaling

- **Horizontal Scaling**: Multiple FastAPI instances
- **Load Balancer**: Nginx or AWS ALB
- **Database Replicas**: Read replicas for queries

---

## Summary

This backend is a **sophisticated AI interview platform** with:

1. **Multi-Agent System**: 6 specialized agents orchestrated by LangGraph
2. **RAG Implementation**: Semantic search using Pinecone + Qwen embeddings
3. **State Management**: Persistent workflow state in database
4. **Resume Processing**: Hierarchical chunking with domain matching
5. **Conversational Flow**: Natural interview progression
6. **Comprehensive Evaluation**: Detailed feedback and reports

**Key Technologies**:
- FastAPI for API
- LangGraph for agent orchestration
- Pinecone for vector search
- Qwen models for local LLM operations
- Hugging Face API for question generation

**Architecture Pattern**:
- **Layered**: API → Service → Agent → External Services
- **Agent-to-Agent (A2A)**: Agents communicate via shared state
- **Stateful**: Interview state persists between requests

This architecture provides **full control** over the interview process while maintaining flexibility for customization and scaling.

