# AI Interviewer - Complete Implementation Documentation

## Executive Summary

AIMI (AI Interview Platform) is a sophisticated, end-to-end interview automation system that leverages multiple AI agents orchestrated through LangGraph to conduct personalized technical interviews. The system uses fine-tuned language models, retrieval-augmented generation (RAG), vector search, and a multi-agent architecture to deliver context-aware, adaptive interview experiences with comprehensive performance analytics.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Data Flow & Integration](#data-flow--integration)
6. [Key Algorithms & Techniques](#key-algorithms--techniques)
7. [Deployment Considerations](#deployment-considerations)

---

## System Architecture Overview

### High-Level Architecture

The application follows a **microservices-inspired monolithic architecture** with clear separation of concerns:

- **Frontend (React SPA)**: User interface for authentication, resume upload, interview interaction, and report visualization
- **Backend (FastAPI)**: RESTful API server with async capabilities
- **AI Layer**: Multi-agent LangGraph workflow orchestrating specialized AI models
- **Data Layer**: SQLite database for relational data + Pinecone vector database for embeddings
- **External AI Services**: Hugging Face hosted inference endpoints for LLMs and embeddings

### Core Design Principles

1. **Conversational AI**: Natural, human-like dialogue flow rather than rigid Q&A
2. **Resume-Aware Intelligence**: Questions personalized based on candidate's experience
3. **Multi-Agent Orchestration**: Specialized agents for different aspects (questions, evaluation, orchestration)
4. **Asynchronous Processing**: Non-blocking operations for responsiveness
5. **Stateful Workflow**: Persistent interview state across sessions

---

## Technology Stack

### Backend Stack

**Core Framework**
- **FastAPI 0.104.1**: Modern async web framework with automatic OpenAPI documentation
- **Uvicorn**: ASGI server with auto-reload for development
- **Python 3.8+**: Runtime environment

**AI & Machine Learning**
- **LangGraph 0.0.20**: Agent orchestration framework for building stateful multi-agent workflows
- **LangChain 0.1.0**: LLM abstraction layer and chaining framework
- **Hugging Face Hub**: API client for hosted inference endpoints
- **Qwen Models**: 
  - Qwen3-Embedding-0.6B (1024 dimensions) for text embeddings
  - Qwen3-0.6B as fallback local LLM
  - OpenAI GPT-OSS-20B for main LLM operations

**Vector Database & Search**
- **Pinecone 3.0.0**: Managed vector database for semantic search
- **Dimension**: 1024-dimensional embeddings from Qwen3
- **Indexing**: Serverless deployment with cosine similarity

**Document Processing**
- **Docling 2.0.0+**: Advanced PDF parsing with layout understanding
- **python-docx 1.1.2**: DOCX file parsing

**Database & ORM**
- **SQLAlchemy 2.0.23**: Async ORM with declarative base
- **Alembic 1.12.1**: Database migration management
- **SQLite**: Development database (supports PostgreSQL via connection strings)
- **aiosqlite 0.19.0**: Async SQLite driver

**Authentication & Security**
- **python-jose 3.3.0**: JWT token generation and validation
- **bcrypt 4.1.2**: Password hashing with salt
- **email-validator 2.0.0**: Email format validation

**HTTP & Utilities**
- **httpx 0.25.2**: Async HTTP client for API calls
- **pydantic 2.5.0**: Data validation and settings management
- **python-multipart 0.0.6**: File upload handling

### Frontend Stack

**Core Framework**
- **React 18.2.0**: Component-based UI library
- **react-scripts 5.0.1**: Create React App build configuration

**Data Visualization**
- **Chart.js 4.5.1**: Canvas-based charting library
- **react-chartjs-2 5.3.1**: React wrapper for Chart.js
- **Three.js 0.160.1**: 3D graphics library for animated visualizations

**State Management**
- **React Hooks**: useState, useEffect, useRef for local state
- **Local Storage**: Persistence for authentication tokens and user data

**Styling**
- **CSS-in-JS**: Inline styles with dynamic theming
- **Inter Font**: Modern UI font family

---

## Backend Implementation

### 1. Application Entry Point & Configuration

#### Main Application Setup (`main.py`)

The FastAPI application is initialized with:
- **CORS middleware**: Configured from settings to allow frontend origins
- **Auto table creation**: SQLAlchemy creates all tables on startup
- **Router inclusion**: Modular API routing for auth and interview endpoints
- **Health check endpoints**: Root `/` and `/health` for monitoring

#### Configuration Management (`config.py`)

**Hard-coded configuration approach**: All settings defined directly in code for simplicity. Key configurations include:

1. **Database Configuration**
   - SQLite URL: `sqlite:///./interview.db`
   - Supports async operations via `sqlite+aiosqlite://`

2. **Pinecone Vector DB**
   - API key, environment, index name
   - Dimension: 1024 (auto-detected from embedding model)

3. **Hugging Face Endpoints**
   - Question Generation: Fine-tuned model endpoint
   - LLM Operations: GPT-OSS-20B endpoint
   - Embeddings: Qwen3-Embedding-0.6B endpoint
   - Evaluation: Dedicated evaluation model endpoint

4. **JWT Authentication**
   - HS256 algorithm
   - 24-hour token expiration
   - Configurable secret key

#### Database Setup (`database.py`)

**Dual-mode database access**:

1. **Async Engine**: Primary for FastAPI async endpoints
   - `AsyncSession` with `async_sessionmaker`
   - SQLite-specific handling with `StaticPool` and `check_same_thread=False`

2. **Sync Engine**: For table creation and legacy operations
   - Enables foreign keys for SQLite via event listener
   - Used by initial migrations

**Dependency Injection**: `get_db()` async generator provides session per request

### 2. Data Models

#### User Model (`user.py`)

**Schema**:
- `user_id`: Primary key (UUID string)
- `email`: Unique, indexed
- `name`: Full name
- `password_hash`: bcrypt hashed password
- `is_active`: Boolean flag
- `created_at`, `updated_at`: Timestamps

**Methods**:
- `set_password()`: Generates salt and hashes password with bcrypt
- `check_password()`: Verifies password against stored hash

#### Resume Model (`resume.py`)

**Schema**:
- `resume_id`: Primary key (UUID)
- `user_id`: Foreign key to users
- `job_role`: Target position
- `file_path`: Physical file location
- `file_hash`: SHA256 for deduplication
- `parsed_content`: JSON with full text and extracted data
- `skills`: JSON array of identified skills
- `chunks_metadata`: JSON containing:
  - `num_chunks`: Total chunks created
  - `matched_domains`: Domains found in resume
  - `resume_summary`: LLM-generated structured summary
- `vector_store_ids`: JSON array of Pinecone vector IDs

**Key Feature - Deduplication**: 
- Computes SHA256 hash of file content
- Checks for existing resume with same hash before processing
- Returns existing resume data if duplicate found

#### Interview Session Model (`session.py`)

**Schema**:
- `session_id`: Primary key (UUID)
- `user_id`: Foreign key to users
- `resume_id`: Foreign key to resumes
- `job_role`: Position being interviewed for
- `current_round`: Phase of interview (welcome, intro, technical_deep_dive, completed)
- `status`: active or completed
- `technical_questions_count`, `behavioral_questions_count`: Question counters
- `workflow_state`: **JSON blob storing complete LangGraph state**
- `created_at`, `updated_at`: Timestamps

**Relationship**:
- One-to-many with messages (cascade delete)

**Critical Design**: `workflow_state` preserves entire conversational flow including:
- Agent responses
- Question context
- Evaluation history
- Domain coverage tracking
- Difficulty sequencing

#### Message Model (`message.py`)

**Schema**:
- `message_id`: Primary key (UUID)
- `session_id`: Foreign key to interview_sessions
- `role`: "user" or "assistant"
- `content`: Message text
- `message_metadata`: JSON containing:
  - Question data (domain, difficulty, round)
  - Feedback and scores
  - Report data (for completion messages)
- `created_at`: Timestamp

**Relationship**: Belongs to interview session

### 3. Authentication System

#### JWT Implementation (`utils/auth.py`)

**Token Creation**:
- Uses `python-jose` for JWT encoding
- Payload contains:
  - `sub`: User ID
  - `exp`: Expiration timestamp (24 hours default)
- Signed with HS256 algorithm and secret key

**Token Verification**:
- Decodes and validates JWT
- Returns payload dict on success, None on failure
- Catches `JWTError` for invalid/expired tokens

#### Auth Endpoints (`api/v1/auth.py`)

**Registration Flow**:
1. Validate email uniqueness
2. Generate UUID user ID
3. Hash password with bcrypt salt
4. Create user record
5. Generate and return JWT token

**Login Flow**:
1. Query user by email
2. Verify password with bcrypt
3. Generate and return JWT token

**Current User Dependency**:
- `get_current_user()` FastAPI dependency
- Extracts token from `Authorization: Bearer <token>` header
- Validates token and fetches user from database
- Raises 401 if invalid

### 4. Resume Processing Pipeline

#### Resume Service (`resume_service.py`)

**Initialization**:
- Creates upload directory if not exists
- Initializes Docling converter with PDF support

**File Hash & Deduplication**:
- `compute_file_hash()`: SHA256 of file bytes
- `check_duplicate_resume()`: Database query for existing hash
- Returns cached data if duplicate, avoiding reprocessing

**Text Extraction**:

1. **PDF Extraction** (`_extract_text_from_pdf()`):
   - Saves temporary file for Docling
   - Calls `DocumentConverter.convert()`
   - Exports to markdown format for better structure preservation
   - Cleans up temp file

2. **DOCX Extraction** (`_extract_text_from_docx()`):
   - Uses python-docx library
   - Extracts all paragraph text
   - Joins with newlines

**Resume Parsing** (`_parse_resume_text()`):

Simple keyword-based extraction:
- **Skills**: Matches predefined keywords (Python, SQL, ML, etc.)
- **Experience**: Identifies sections with experience-related keywords
- **Education**: Finds education-related sections

Returns structured dict with full text, skills array, experience, education.

**Hierarchical Chunking** (`_chunk_resume_hierarchically()`):

**Section Identification**:
- Pattern matches common section headings
- Maps to categories: summary, experience, education, projects, skills, etc.
- Builds section dictionary

**Entry Parsing**:
- **Experience**: Splits by date patterns, identifies individual jobs
- **Education**: Separates degree entries
- **Projects**: Identifies individual projects
- **Other sections**: Splits by paragraphs or bullet points

**Chunk Structure**:
Each chunk contains:
- `text`: Content
- `parent_section`: Section name
- `chunk_type`: "entry"
- `entry_index`: Position within section

**Domain Matching** (`_match_chunk_to_domains()`):

Uses **LLM-based classification**:
1. Constructs prompt with:
   - Chunk text (truncated to 1000 chars)
   - Available domains (9 technical domains)
2. Sends to LLM via `local_llm_service.generate_json_async()`
3. Expects JSON response: `{"domains": ["Domain1", "Domain2"]}`
4. Validates domains against allowed list
5. Fallback to keyword matching if LLM fails

**Resume Processing Flow** (`process_resume()`):

1. **Read & Hash**:
   - Read file bytes
   - Compute SHA256 hash
   - Check for duplicate

2. **Save File**:
   - Generate UUID resume_id
   - Save to uploads directory with UUID filename

3. **Extract & Parse**:
   - Call appropriate extractor (PDF/DOCX)
   - Parse into structured format
   - Create hierarchical chunks

4. **Domain Matching**:
   - For each chunk, call LLM to match domains
   - Build domain coverage map
   - Track all matched domains

5. **Generate Embeddings**:
   - Batch embed all chunks using `embedding_service`
   - Uses Qwen3-Embedding-0.6B (1024 dimensions)

6. **Store in Vector DB**:
   - Upsert to Pinecone with metadata:
     - `resume_id`, `chunk_index`, `job_role`
     - `parent_section`, `chunk_type`, `entry_index`
     - `domains`: Array of matched domains
     - `primary_domain`: First domain in list

7. **Generate Resume Summary**:
   - Call `resume_summary_agent` (LLM-based)
   - Creates structured summary with:
     - Candidate overview
     - Key experiences
     - Technical skills
     - Recommended domains for interview
     - Experience level (junior/mid/senior)

8. **Save to Database**:
   - Create Resume record with:
     - Parsed content
     - Skills array
     - Chunks metadata (including summary)
     - Vector store IDs

**Output**: Returns resume_id, skills, domains, summary

### 5. Multi-Agent Interview Workflow

#### LangGraph Workflow Architecture (`interview_workflow.py`)

**State Definition** (`langgraph_state.py`):

The `InterviewState` TypedDict contains:
- **Session Info**: session_id, resume_id, job_role
- **Round Management**: current_round, conversation_phase, status
- **Questions**: question_count, previous_questions, difficulty, selected_domain
- **Answers & Evaluation**: user_answers, evaluation_history
- **Resume Context**: resume_context, resume_summary
- **Interview Planning**: 
  - `interview_plan`: LLM-generated plan
  - `planned_domains`: Ordered domain list
  - `difficulty_sequence`: Pre-planned difficulty progression
  - `domain_coverage`: Tracks questions per domain
  - `total_questions`: Target question count (default 10)
- **Agent Communication**:
  - `question_context`: Input for question agent
  - `evaluation_context`: Input for evaluation agent
  - `orchestrator_intent`: What orchestrator wants to assess
  - `pending_question`: Question awaiting cleaning
  - `current_question_key_points`: Required concepts
- **Agent Responses**:
  - `question_agent_response`: Generated question
  - `evaluation_agent_response`: Evaluation results
- **Flow Control**: next_action (generate_question, evaluate, wait, complete)
- **Conversation**: messages array with role/content/metadata

**Annotated Fields**:
- Lists use `operator.add` for appending (LangGraph feature)

**Workflow Graph**:

```
orchestrator (entry) 
    ↓
  [conditional edge based on next_action]
    ↓
  ├─→ question_agent → cleaning_agent → orchestrator
  ├─→ evaluation_agent → orchestrator
  └─→ END (complete)
```

**Node Functions**:

1. **orchestrator_node**: Wrapper for async `orchestrator_agent`
2. **cleaning_agent_node**: 
   - Retrieves resume context from VDB by domain
   - Blends generated question with candidate's experience
   - Returns cleaned question
3. **question_agent**: Generates raw technical question
4. **evaluation_agent**: Evaluates user answer

**Conditional Routing** (`should_continue`):
- Checks `next_action` and `status` in state
- Routes to: generate_question, evaluate, or complete

### 6. AI Agents Implementation

#### Orchestrator Agent (`orchestrator_agent.py`)

**Purpose**: Central coordinator that decides what to ask next and manages interview flow.

**Configuration**:
- `DEFAULT_TOTAL_QUESTIONS`: 10
- `DIFFICULTY_DISTRIBUTION`: Pre-defined sequences for 10, 7, 5 questions
  - Example for 10: ["easy", "easy", "easy", "medium", "medium", "medium", "hard", "hard", "hard", "hard"]

**Conversation Phases**:

1. **Greeting Phase**:
   - Transitions to intro_question phase
   - Sets current_round to "intro"

2. **Intro Question Phase**:
   - First call (question_count=0):
     - Generates intro question using LLM: "Tell me about yourself"
     - Returns as `question_agent_response`
   - After user answers (question_count > 0):
     - Generates interview plan if not exists
     - Selects first domain and difficulty
     - Generates orchestrator intent (LLM-based)
     - Transitions to technical_question phase

3. **Technical Question Phase**:
   - Calculates `technical_question_index` = question_count - 1 (excluding intro)
   - Checks if reached total_questions limit
   - If not complete:
     - **Domain Selection**: Round-robin through planned_domains
     - **Difficulty Selection**: From pre-planned sequence
     - **Intent Generation**: LLM creates assessment goal
     - Sets `question_context` for question agent
   - If complete: Transitions to closing

4. **Closing Phase**:
   - Returns complete status

**Interview Plan Generation** (`_generate_interview_plan()`):

Uses **LLM to create personalized interview strategy**:

Input:
- Resume summary (candidate overview, skills, recommended domains)
- Available domains (9 technical domains)
- Total questions to ask

Prompt asks LLM to:
- Select 4-6 most relevant domains based on candidate's background
- Order by priority (start with strengths)
- Include at least one breadth-testing domain

Output:
```json
{
  "domains": ["Python", "Machine Learning", "SQL", ...],
  "reasoning": "Brief explanation"
}
```

Also generates difficulty sequence using even distribution logic.

**Intent Generation** (`_generate_orchestrator_intent()`):

LLM creates brief statement describing what to assess:
- Input: domain, job_role, difficulty
- Output: "Assess their understanding of ML model evaluation techniques"

This intent guides the question cleaning agent.

#### Question Agent (`question_agent.py`)

**Purpose**: Generates raw technical questions using fine-tuned model.

**Process**:

1. **Extract Context**:
   - Receives `question_context` from orchestrator
   - Contains: domain, difficulty, job_role

2. **Format Prompt**:
   - Uses **Alpaca instruction format**:
     ```
     Below is an instruction that describes a task, paired with an input that provides further context.
     
     ### Instruction:
     Generate a technical interview question for a {job_role} position about {domain} at {difficulty} difficulty level.
     
     ### Input:
     Domain: {domain}
     Difficulty: {difficulty}
     Job Role: {job_role}
     
     Output only the interview question. Do not include explanations, answers, or formatting.
     
     ### Response:
     ```

3. **Call Fine-Tuned Model**:
   - Uses `question_gen_service.generate_question()`
   - Hits Hugging Face inference endpoint
   - Model: Fine-tuned for interview question generation
   - Parameters: max_new_tokens=150, temperature=0.7

4. **Clean Response**:
   - Strips quotes and whitespace
   - Validates minimum length (10 chars)
   - Returns error if invalid

5. **Return Format**:
   ```json
   {
     "question": "What is the difference between...",
     "domain": "Machine Learning",
     "difficulty": "medium",
     "error": null
   }
   ```

#### Question Cleaning Agent (`question_cleaning_agent.py`)

**Purpose**: Personalizes questions by blending with candidate's experience using RAG.

**Process**:

1. **Retrieve Resume Context** (`_retrieve_resume_context_by_domain()`):
   - Generates embedding for the raw question
   - Queries Pinecone with domain filter:
     - Filters by `resume_id` and `domain`
     - Uses semantic search (cosine similarity)
     - Returns top 3 chunks
   - Fallback: If no domain matches, gets any chunks for resume
   - Formats as: "[Experience 1]: chunk1\n[Experience 2]: chunk2..."

2. **Blend with LLM** (`_blend_question_with_context()`):

   **Prompt Structure**:
   - Raw technical question
   - Candidate's relevant experience from resume
   - Domain and assessment goal
   
   **Instructions**:
   - Create natural, personalized question referencing specific experience
   - Avoid robotic phrases like "I see you..." or "Could you walk me through..."
   - Use varied strategies:
     - Deep Dive: "In your [project], how did you handle [concept]?"
     - Direct Challenge: "What happens under the hood when...?"
     - Scenario-Based: "Imagine your team encounters..."
     - Comparative: "You used [A]. When would [B] be better?"
     - Practical Application: "When building [system], why did you choose...?"
   - Must be complete sentence with question mark
   - 20-80 words

   **Output**: Single cleaned question

3. **Fallback Strategies**:
   - If no resume context: Generate standalone question
   - If LLM fails: Return original question
   - If response too short: Use fallback

4. **Response Cleaning**:
   - Removes common prefixes ("Here is the question:", etc.)
   - Strips quotes
   - Ensures ends with question mark
   - Validates length

**Key Feature**: This agent transforms generic questions into personalized ones that reference the candidate's actual projects and experience.

#### Evaluation Agent (`evaluation_agent.py`)

**Purpose**: Assesses candidate answers using dedicated evaluation model.

**Process**:

1. **Extract Context**:
   - Receives `evaluation_context` from orchestrator
   - Contains: question, answer, domain, difficulty

2. **Call Evaluation Service**:
   - Delegates to `evaluation_service.evaluate_answer()`
   - Two-step evaluation process (see Evaluation Service section)

3. **Structure Response**:
   ```json
   {
     "score": 0.75,
     "feedback": {
       "feedback_text": "Good explanation...",
       "analysis": "Technical comparison...",
       "technical_accuracy": 0.8,
       "completeness": 0.7,
       "clarity": 0.75,
       "strengths": [],
       "improvements": ["Consider mentioning..."]
     },
     "reference_answer": "The correct approach...",
     "error": null
   }
   ```

4. **Metrics**:
   - **technical_accuracy**: Factual correctness (0.0-1.0)
   - **completeness**: Coverage of key points (0.0-1.0)
   - **clarity**: Communication quality (0.0-1.0)
   - **overall_score**: Weighted average

#### Report Agent (`report_agent.py`)

**Purpose**: Generates comprehensive interview report with analytics.

**Report Sections**:

1. **Executive Summary**:
   - Overall score and percentage
   - Performance level (Outstanding, Excellent, Strong, Good, Developing, Needs Improvement)
   - Total questions answered
   - Timestamp

2. **Metric Breakdown** (3 Core Pillars):
   - Aggregates technical_accuracy, completeness, clarity across all answers
   - Calculates averages
   - Provides descriptions for each metric

3. **Domain Performance**:
   - Score per domain (excludes intro question)
   - Identifies strongest and weakest domains
   - Question count per domain

4. **Difficulty Performance**:
   - Separates scores by easy, medium, hard
   - Shows count and average score for each

5. **Question-by-Question Breakdown**:
   - Lists all questions with:
     - Index, question text, user answer (truncated to 500 chars)
     - Domain, difficulty
     - Score and all three metric scores
     - Detailed feedback

6. **LLM-Generated Insights** (`_generate_llm_insights()`):
   
   **Prompt includes**:
   - Performance data summary
   - Domain scores
   - Difficulty performance
   - Metric breakdown
   
   **Expected JSON output**:
   ```json
   {
     "overall_summary": "2-3 sentence summary",
     "strengths": ["strength1", "strength2", "strength3"],
     "areas_for_improvement": ["area1", "area2", "area3"],
     "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
     "hiring_recommendation": {
       "decision": "Strongly Recommend / Recommend / Consider / Not Recommended",
       "confidence": 0.75,
       "reasoning": "Based on performance..."
     }
   }
   ```
   
   **Fallback**: If LLM fails, generates insights based on data analysis:
   - Finds strongest/weakest domains
   - Checks metric thresholds
   - Provides templated recommendations

7. **Score Progression**:
   - Plots score per question
   - Calculates trend:
     - Improving: Second half avg > First half avg + 0.1
     - Declining: Second half avg < First half avg - 0.1
     - Consistent: Otherwise
   - Identifies highest and lowest scores

**Output**: Comprehensive JSON report with all 7 sections, ready for frontend visualization.

#### Resume Summary Agent (`resume_summary_agent.py`)

**Purpose**: Creates structured, LLM-powered resume analysis for interview planning.

**Process**:

1. **Input Processing**:
   - Receives full resume text and job_role
   - Truncates to 4000 chars if needed

2. **LLM Prompt**:
   - Provides resume excerpt
   - Lists available domains
   - Asks for structured JSON output:
   
   ```json
   {
     "candidate_overview": "2-3 sentence professional summary",
     "key_experiences": [
       {
         "experience": "Description of key project/role",
         "technologies": ["tech1", "tech2"],
         "impact": "What was achieved"
       }
     ],
     "technical_skills": ["skill1", "skill2", ...],
     "recommended_domains": ["Domain1", "Domain2", ...],
     "experience_level": "junior OR mid OR senior"
   }
   ```

3. **Validation**:
   - Validates domains against allowed list
   - Ensures proper JSON structure
   - Provides defaults if fields missing

4. **Fallback**:
   - If LLM fails: Uses keyword-based domain extraction
   - Default recommended domains: ["Python", "SQL", "Data Analysis"]

**Usage**: This summary is stored in resume `chunks_metadata` and used by orchestrator to plan interviews.

### 7. Supporting Services

#### Local LLM Service (`local_llm_service.py`)

**Purpose**: Unified interface for text generation across all agents (except question generation).

**Singleton Pattern**: Single instance shared across application.

**Configuration**:
- Primary: Hugging Face API with GPT-OSS-20B model
- Fallback: Local model loading (optional, for offline use)

**Methods**:

1. **generate_async()**: Main text generation
   - Input: messages (chat format), max_tokens, temperature
   - Calls `AsyncInferenceClient.chat.completions.create()`
   - Returns generated text
   - Cleans special tokens

2. **generate_json_async()**: JSON-structured generation
   - Calls `generate_async()`
   - Parses JSON from response with multiple strategies:
     - Direct JSON.parse
     - Regex extraction of JSON object
     - Regex extraction of JSON array
   - Returns dict or empty dict on failure

3. **_clean_special_tokens()**: Removes model-specific tokens
   - Strips tokens like `<|end_of_text|>`, `</s>`, `<|im_end|>`, etc.

**Error Handling**:
- Logs failures
- Returns None or empty dict
- Allows callers to implement fallbacks

#### Question Generation Service (`question_gen_service.py`)

**Purpose**: Dedicated service for fine-tuned question generation model.

**Endpoint**: Separate Hugging Face inference endpoint from main LLM.

**Method**:

**generate_question()**:
- Input: messages, max_tokens, temperature
- Formats prompt by converting messages to string
- Calls `AsyncInferenceClient.text_generation()` (not chat completions)
- Parameters:
  - `return_full_text=False`: Only new tokens
  - `do_sample=True`: Enable sampling
- Cleans special tokens
- Removes formatting artifacts:
  - "Here is your interview question:"
  - Question prefixes
  - Markdown headers
  - Leading numbers
- Validates against generic responses
- Returns cleaned question string

**Format Handling**: Fine-tuned model may output questions with prefixes; service strips these to return only the question.

#### Evaluation Service (`evaluation_service.py`)

**Purpose**: Two-step answer evaluation using dedicated model.

**Singleton Pattern**: Single instance.

**Configuration**:
- Dedicated Hugging Face endpoint for evaluation model
- Separate from main LLM and question generation

**Two-Step Process**:

**Step 1: Generate Reference Answer** (`_generate_reference_answer()`):

Prompt:
```
You are an expert in {domain}.
Write a concise, technically perfect answer to the following interview question.
Focus on the definition and the 'why'. Do NOT use code examples unless absolutely necessary.

Question: {question}

Answer:
```

- Uses `text_generation()` endpoint
- Parameters: max_tokens=256, temperature=0.2 (low for factual accuracy)
- Returns reference (expert) answer

**Step 2: Judge Candidate's Answer** (`_judge_answer()`):

Prompt:
```
You are a strict technical interviewer.

### Question:
{question}

### Reference Answer (Truth):
{reference_answer}

### Candidate's Answer:
{user_answer}

### Evaluation Protocol:
1. Analyze: Compare candidate's answer to reference. Note matches and misses.
2. Score Technical Accuracy (0.0-1.0): Is the information factually correct?
3. Score Completeness (0.0-1.0): Did they cover the main points?
4. Score Clarity (0.0-1.0): Is the answer easy to understand?
5. Overall Score (0.0-1.0): Weighted average

### Instructions:
- Be objective.
- CRITICAL: Respond using ONLY valid JSON. Do not write anything else.

### Output Format (JSON):
{
  "analysis": "<Short comparison>",
  "technical_accuracy": <float>,
  "completeness": <float>,
  "clarity": <float>,
  "overall_score": <float>,
  "feedback": "<Constructive feedback>"
}
```

- Uses `text_generation()` endpoint
- Parameters: max_tokens=512, temperature=0.1 (very low for consistency)
- Parses JSON response with fallbacks

**Fallback Evaluation**:
If LLM fails, uses heuristic scoring based on answer length:
- < 20 chars: 0.3
- < 50 chars: 0.5
- < 150 chars: 0.65
- ≥ 150 chars: 0.75

**Output**:
```json
{
  "technical_accuracy": 0.8,
  "completeness": 0.7,
  "clarity": 0.75,
  "overall_score": 0.75,
  "feedback": "Good explanation, but consider...",
  "analysis": "Candidate covered main points...",
  "reference_answer": "The correct approach is..."
}
```

#### Embedding Service (`embedding_service.py`)

**Purpose**: Generate text embeddings for semantic search.

**Singleton Pattern**: Single instance.

**Configuration**:
- Primary: Hugging Face Embedding API (Qwen3-Embedding-0.6B)
- Dimension: 1024
- Fallback: Local SentenceTransformer model

**Methods**:

1. **embed_text()**: Single text embedding
   - Input: text string
   - Returns: 1024-dimensional float array

2. **embed_texts()**: Batch embedding (more efficient)
   - Input: list of texts
   - Returns: list of embedding arrays

3. **embed_text_sync() / embed_texts_sync()**: Synchronous wrappers
   - Creates event loop if needed
   - Calls async version

**API Call**:
- POST to Hugging Face endpoint
- Body: `{"inputs": texts}`
- Response: List of embeddings
- Handles multiple response formats

**Performance**: Batch processing reduces API calls and latency.

#### Vector Store Service (`vector_store.py`)

**Purpose**: Interface to Pinecone vector database for resume chunks.

**Lazy Initialization**: Connects only when first accessed.

**Setup**:
- Creates index if doesn't exist
- Serverless spec: AWS, us-east-1
- Metric: Cosine similarity
- Dimension: 1024

**Methods**:

1. **add_documents()**:
   - Input: documents, ids, metadatas, embeddings
   - Cleans metadata (Pinecone only accepts strings, numbers, booleans, lists)
   - Stores text in metadata for retrieval
   - Upserts in batches of 100

2. **query()**:
   - Input: query_embeddings, n_results, where (filter)
   - Queries Pinecone with cosine similarity
   - Returns: ids, documents, metadatas, distances

3. **get_by_resume_id()**:
   - Filters by resume_id metadata
   - Returns all chunks for a resume (up to n_results)

4. **query_by_domain()**:
   - **Key Method for RAG**
   - Filters by: resume_id AND domain
   - Process:
     - Queries with 3x requested results
     - Filters in Python for domain membership (checks `domains` list and `primary_domain`)
     - Returns top n_results after filtering
   - Handles both primary_domain and domains array

5. **clear_all()**:
   - Deletes and recreates index
   - For testing/cleanup

**Metadata Schema** (per chunk):
```json
{
  "resume_id": "uuid",
  "chunk_index": 0,
  "job_role": "Data Scientist",
  "parent_section": "experience",
  "chunk_type": "entry",
  "entry_index": 0,
  "domains": ["Python", "Machine Learning"],
  "primary_domain": "Python",
  "text": "Actual chunk content..."
}
```

#### RAG Service (`rag_service.py`)

**Purpose**: High-level interface for retrieval-augmented generation.

**Methods**:

1. **retrieve_relevant_context()**:
   - Input: query, resume_id, top_k, optional domain
   - Generates query embedding
   - If domain specified: Uses `vector_store.query_by_domain()`
   - Else: Regular query with resume_id filter
   - Combines retrieved chunks with newlines
   - Returns: concatenated context string

2. **get_resume_summary()**:
   - Gets top_k chunks for resume (any domain)
   - Used for initial context

3. **get_domains_for_resume()**:
   - Fetches all chunks for resume
   - Extracts unique domains from metadata
   - Returns: list of domain names

4. **get_chunks_by_domain()**:
   - Filters chunks by specific domain
   - Optional: semantic search with query
   - Returns: list of chunk texts

5. **get_domain_relevance()**:
   - Counts chunks per domain
   - Returns: dict mapping domain → count
   - Useful for understanding resume's technical profile

### 8. API Endpoints

#### Interview Endpoints (`api/v1/interviews.py`)

**POST /api/v1/resumes/upload**:

Request:
- `multipart/form-data`
- `file`: PDF or DOCX
- `job_role`: String (default: "Data Scientist")

Process:
1. Calls `resume_service.process_resume()`
2. Saves file, parses, chunks, embeds, stores in VDB
3. Generates resume summary

Response:
```json
{
  "resume_id": "uuid",
  "message": "Resume processed successfully",
  "skills": ["Python", "SQL", ...]
}
```

**POST /api/v1/interviews/start**:

Request:
```json
{
  "resume_id": "uuid",
  "job_role": "Data Scientist"
}
```

Process:
1. Validates resume belongs to user
2. Creates InterviewSession in database
3. Initializes workflow state
4. Generates welcome message
5. Saves workflow state and welcome message

Response:
```json
{
  "session_id": "uuid",
  "message": "Welcome message...",
  "type": "welcome",
  "message_text": "Interview session created"
}
```

**POST /api/v1/sessions/{session_id}/answer**:

Request:
```json
{
  "answer": "User's answer text",
  "question": "Previous question",
  "domain": "Machine Learning",
  "difficulty": "medium"
}
```

Process:

**Welcome Phase**:
1. Checks if current_round == "welcome"
2. Calls `interview_service.handle_welcome_response()`
3. If user confirms: Generates first intro question
4. If user declines: Returns wait message
5. If ambiguous: Asks for clarification

**Regular Phase** (after welcome):
1. Saves user answer as Message
2. Calls `interview_service.evaluate_answer()`
   - Runs evaluation agent
   - Returns evaluation with scores
3. Calls `interview_service.generate_next_question()`
   - Runs workflow: orchestrator → question_agent → cleaning_agent
   - Returns next question or completion signal
4. Saves next question as Message
5. Updates session counters and workflow state

**Completion**:
- If no next question: 
  - Sets status to "completed"
  - Calls `generate_final_report()`
  - Saves report in message metadata
  - Returns report with completion message

Response (regular):
```json
{
  "evaluation": {
    "score": 0.75,
    "feedback": {...}
  },
  "next_question": {
    "question_text": "Next question...",
    "domain": "SQL",
    "difficulty": "hard",
    "round": "technical_deep_dive"
  }
}
```

Response (completion):
```json
{
  "evaluation": {...},
  "next_question": null,
  "message": "Interview session completed",
  "report": {
    // Full 7-section report
  }
}
```

**GET /api/v1/sessions/{session_id}/messages**:

Response:
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "message_id": "uuid",
      "role": "assistant",
      "content": "Question text",
      "message_metadata": {
        "domain": "Python",
        "difficulty": "medium",
        "round": "technical_deep_dive"
      },
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

**GET /api/v1/sessions**:

Lists all sessions for authenticated user, ordered by most recent.

Response:
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "Interview 2024-01-01",
      "createdAt": "2024-01-01T00:00:00",
      "job_role": "Data Scientist",
      "status": "completed"
    }
  ]
}
```

**GET /api/v1/sessions/{session_id}**:

Returns session details.

**DELETE /api/v1/sessions/{session_id}**:

Deletes session and all associated messages (cascade).

**GET /api/v1/sessions/{session_id}/report**:

Regenerates report for completed interview.

Requirements:
- Session must be completed
- Workflow state must exist

Returns: Full 7-section report JSON.

#### Auth Endpoints (`api/v1/auth.py`)

Covered in Authentication System section.

---

## Frontend Implementation

### 1. Application Structure

#### Main App Component (`App.js`)

**State Management**:

- **Authentication**: isAuthenticated, user, checkingAuth
- **App Navigation**: appState ("interview"), currentSessionId
- **Sessions**: chatSessions array, sidebarOpen
- **Interview**: currentQuestion, isLoading, error
- **UI**: isDarkMode, showSetupModal
- **Reports**: showReport, currentReport

**Lifecycle**:

1. **Mount**:
   - Check localStorage for authToken and user
   - If found: Parse user, set authenticated
   - Mark checkingAuth complete

2. **Authentication Change**:
   - On authenticated: Check backend health, load sessions

3. **Session Management**:
   - Loads all sessions from API
   - Formats for UI display
   - Stores in chatSessions state

**Key Functions**:

**handleStartInterview()**:
1. Calls `apiService.startInterview()`
2. Creates new session object with welcome message
3. Adds to chatSessions array (prepends for recency)
4. Sets as currentSessionId
5. Transitions to interview screen

**handleSendMessage()**:

Welcome Phase:
1. Adds user message to UI immediately (optimistic update)
2. Calls `apiService.submitAnswer()`
3. If user confirmed:
   - Adds clarification message
   - Adds first question
4. If user declined or ambiguous:
   - Adds clarification message

Regular Phase:
1. Adds user message to UI
2. Calls `apiService.submitAnswer()`
3. If next_question exists:
   - Adds next question to chat
   - Updates currentQuestion
4. If interview complete:
   - Sets currentQuestion to null
   - If report exists:
     - Sets currentReport
     - Shows report dashboard
     - Adds completion message with report
   - Else: Adds generic completion message

**handleSelectSession()**:
1. Sets currentSessionId
2. Calls `fetchSessionData()`:
   - Loads messages from API
   - Restores chat history
   - Finds last question (for currentQuestion)
   - Checks for saved report
3. Updates session.messages
4. If report found: Sets currentReport

**Screen Routing**:

1. **Not authenticated**: LoginScreen
2. **Authenticated**:
   - If showReport: ReportDashboard
   - Else: ChatInterviewScreen + Sidebar

**Features**:
- Dark mode toggle (persisted in state)
- Modal for setup screen
- Loading states during API calls
- Error display

### 2. API Service (`api.js`)

**Singleton Class**: Single instance exported.

**Base URL**: `process.env.REACT_APP_API_URL` or `http://localhost:8000`

**Authentication**:
- `getAuthToken()`: Reads from localStorage
- `getAuthHeaders()`: Returns headers with Bearer token

**Methods**:

All methods are async and use fetch API:

1. **uploadResume(file, jobRole)**:
   - Creates FormData with file and job_role
   - POST to `/api/v1/resumes/upload`
   - Returns resume_id

2. **startInterview(resumeId, jobRole)**:
   - POST to `/api/v1/interviews/start`
   - Returns session_id and welcome message

3. **submitAnswer(sessionId, answer, question, domain, difficulty)**:
   - POST to `/api/v1/sessions/{sessionId}/answer`
   - Returns evaluation and next_question (or report on completion)

4. **getSessionMessages(sessionId)**:
   - GET `/api/v1/sessions/{sessionId}/messages`
   - Returns array of messages

5. **getAllSessions()**:
   - GET `/api/v1/sessions`
   - Returns all user sessions

6. **deleteSession(sessionId)**:
   - DELETE `/api/v1/sessions/{sessionId}`

7. **getInterviewReport(sessionId)**:
   - GET `/api/v1/sessions/{sessionId}/report`
   - Returns full report for completed interview

8. **login(email, password)** / **register(email, password, name)**:
   - POST to auth endpoints
   - Returns token and user
   - Stores token in localStorage

9. **logout()**:
   - POST to logout endpoint
   - Clears localStorage

10. **healthCheck()**:
    - GET `/health`
    - Used to verify backend connectivity

**Error Handling**:
- Checks response.ok
- Throws Error with detail from response JSON
- Caller must handle in try-catch

### 3. Screen Components

#### LoginScreen (`LoginScreen.js`)

**Features**:
- Toggle between login and registration
- Form validation
- Password confirmation for registration
- Minimum password length check
- Error display
- Loading state

**State**:
- isLogin: true (login) / false (register)
- email, password, confirmPassword, name
- error, isLoading

**Styling**:
- Dark mode aware
- Inter font
- Rounded input fields with focus states
- Smooth transitions

**Flow**:
1. User enters credentials
2. Validates fields
3. Calls apiService.login() or apiService.register()
4. On success:
   - Stores token and user in localStorage
   - Calls onLogin(userData)
5. On error: Displays error message

#### SetupScreen (`SetupScreen.js`)

**Features**:
- File upload (PDF/DOCX)
- Job role selection (dropdown)
- Upload progress indicator
- Error handling
- Can be used standalone or as modal

**State**:
- jobRole: Selected role
- selectedFile: File object
- resumeId: UUID after upload
- isUploading, uploadError

**Job Roles**:
- Data Scientist (default)
- Software Engineer
- Data Engineer
- ML Engineer

**Flow**:
1. User selects file
2. Automatically triggers upload via `handleFileUpload()`
3. Calls `apiService.uploadResume()`
4. Stores resumeId on success
5. User clicks "Start Interview"
6. Calls `onStartInterview(resumeId, jobRole)`

**Modal Mode**:
- Overlay with backdrop blur
- Close button
- Click outside to close

#### ChatInterviewScreen (`ChatInterviewScreen.js`)

**Features**:
- Message display with roles (user/assistant)
- Auto-scroll to bottom on new messages
- Textarea with auto-resize
- Loading animation (3 dots)
- User avatar with initials
- AIMI branding
- View Report button (for completed interviews)

**Message Rendering**:

**User Messages**:
- Right-aligned
- Avatar on right
- Bubble style: white/dark background

**Assistant Messages**:
- Left-aligned
- AIMI logo avatar with gradient
- Plain text style (no bubble)
- Special handling for completion messages: Shows "View Performance Report" button

**Input Area**:
- Auto-expanding textarea (up to 200px height)
- Enter to submit (Shift+Enter for newline)
- Send button (disabled when empty or loading)
- Placeholder changes based on phase

**Loading State**:
- Animated dots with staggered animation
- Shows "AIMI is typing..." effect

**Styling**:
- Dark mode support
- Inter font
- ChatGPT-inspired design
- Smooth scrolling

#### ReportDashboard (`ReportDashboard.js`)

**Advanced Visualization Component**: Comprehensive analytics dashboard with 3D graphics and charts.

**State**:
- expandedQuestion: Index of expanded Q&A
- activeTab: "overview", "details", "insights"

**3D Visualization** (Three.js):

**Score Ring**:
- Animated torus geometry
- Color based on score (green/yellow/red)
- Rotates continuously
- Background ring for context
- Particle system for visual interest

**Implementation**:
- Creates WebGL renderer
- Scene with camera, ring meshes, particles
- Animation loop with requestAnimationFrame
- Cleanup on unmount

**Charts** (Chart.js + react-chartjs-2):

1. **Radar Chart** (Domain Performance):
   - Shows scores across all technical domains
   - Highlights strongest and weakest areas
   - Responsive sizing

2. **Bar Chart** (Difficulty Breakdown):
   - Easy/Medium/Hard performance
   - Color-coded bars
   - Horizontal axis: difficulty levels

3. **Line Chart** (Score Progression):
   - Shows performance over time
   - Filled area under line
   - Point markers for each question
   - Trend indicator badge

4. **Doughnut Chart** (Core Metrics):
   - Technical Accuracy, Completeness, Clarity
   - Color-coded segments
   - Cutout center for modern look

**Tabs**:

**Overview Tab**:
- Executive Summary card with 3D score visualization
- Metric Breakdown with doughnut chart and progress bars
- Domain Radar chart
- Difficulty bar chart
- Score Progression line chart

**Details Tab**:
- Question-by-Question breakdown
- Expandable cards for each question
- Shows:
  - Question index, domain, difficulty
  - Score with color coding
  - Full question text
  - User's answer
  - Individual metric scores
  - Feedback

**Insights Tab**:
- Overall Assessment (LLM-generated summary)
- Key Strengths (bullet list)
- Areas for Development (bullet list)
- Recommendations (numbered list)
- Hiring Assessment:
  - Decision badge (color-coded)
  - Confidence percentage
  - Reasoning text

**Styling**:
- Professional dashboard design
- Card-based layout
- Gradient backgrounds
- Smooth animations
- Dark mode support
- Responsive grid

**Icons**: Inline SVG icons for sections (chart, target, trend, list, check, arrow).

**Performance Level Colors**:
- Outstanding: Green (#10b981)
- Excellent: Green (#22c55e)
- Strong: Lime (#84cc16)
- Good: Yellow (#eab308)
- Developing: Orange (#f97316)
- Needs Improvement: Red (#ef4444)

#### Sidebar (`Sidebar.js`)

**Features**:
- Session list with recent first
- New Interview button
- User info with avatar
- Logout button
- Session menu (delete)
- Hover effects
- Close button

**Session Display**:
- Title (truncated if long)
- Active session highlighted
- Three-dot menu on hover
- Delete option in dropdown menu

**Styling**:
- Fixed sidebar (260px width)
- Slide-in animation
- Dark mode support
- Scrollable session list
- Sticky header and footer

**User Avatar**:
- Initials from name (first + last)
- Fallback to email initial
- Rounded square background

**Interactions**:
- Click session to load
- Hover to show menu button
- Click menu to show options
- Click delete to remove session

---

## Data Flow & Integration

### Complete Interview Flow

**1. User Registration/Login**:
```
User → Frontend (LoginScreen) → POST /api/v1/auth/register or /login
→ Backend (auth.py) → Create/Verify User → Generate JWT
→ Store in localStorage → Redirect to App
```

**2. Resume Upload**:
```
User → Frontend (SetupScreen) → Select PDF/DOCX
→ POST /api/v1/resumes/upload (multipart)
→ Backend (resume_service.py):
  - Save file
  - Extract text (Docling/python-docx)
  - Parse & chunk hierarchically
  - Match chunks to domains (LLM)
  - Generate embeddings (Qwen3)
  - Store in Pinecone with metadata
  - Generate resume summary (resume_summary_agent)
  - Save to database
→ Return resume_id
```

**3. Start Interview**:
```
User → Frontend → POST /api/v1/interviews/start
→ Backend (interviews.py):
  - Create InterviewSession in database
  - Initialize workflow state (InterviewState)
  - Generate welcome message
  - Save state to session.workflow_state
  - Save welcome message as Message
→ Return session_id and welcome message
→ Frontend displays welcome message
```

**4. User Confirms Start**:
```
User → "Yes" → POST /api/v1/sessions/{session_id}/answer
→ Backend (interview_service.py):
  - Detect welcome phase
  - Call handle_welcome_response()
  - Update to intro round
  - Generate first intro question:
    - LangGraph workflow: orchestrator → question_agent
    - Orchestrator generates LLM-based intro question
    - Returns question
→ Save question as Message
→ Return question to frontend
```

**5. User Answers Intro Question**:
```
User → Types answer → POST /api/v1/sessions/{session_id}/answer
→ Backend:
  - Save user answer as Message
  - Call evaluate_answer():
    - Set evaluation_context in state
    - Run evaluation_agent:
      - Call evaluation_service.evaluate_answer()
      - Two-step: Generate reference, Judge answer
      - Return scores and feedback
    - Update state with evaluation
  - Call generate_next_question():
    - Orchestrator generates interview plan (LLM):
      - Uses resume_summary to select relevant domains
      - Creates domain sequence
      - Creates difficulty sequence
    - Selects first technical domain and difficulty
    - Generates orchestrator_intent (LLM)
    - Sets question_context
    - Runs workflow: orchestrator → question_agent → cleaning_agent
      - Question agent: Calls fine-tuned model to generate raw question
      - Cleaning agent:
        - Queries Pinecone for relevant resume chunks by domain
        - Blends question with candidate's experience (LLM)
        - Returns personalized question
    - Returns cleaned question
  - Save next question as Message
  - Update workflow_state
→ Return evaluation (not shown) and next question
```

**6. Technical Questions Loop** (Repeats for 10 questions):
```
User → Answers → POST /api/v1/sessions/{session_id}/answer
→ Backend:
  - Evaluate answer (same as step 5)
  - Generate next question:
    - Orchestrator checks question_count
    - If < total_questions:
      - Round-robin selects next domain
      - Selects difficulty from sequence
      - Generates intent
      - Question agent generates
      - Cleaning agent personalizes
    - If >= total_questions:
      - Returns complete signal
  - Update state and save
→ Return evaluation and next question (or completion)
```

**7. Interview Completion**:
```
Backend (when total_questions reached):
  - No next question generated
  - Call generate_final_report():
    - Aggregate all evaluations
    - Calculate domain scores
    - Calculate difficulty scores
    - Create metric breakdown
    - Generate LLM insights (strengths, improvements, recommendations)
    - Calculate score progression
    - Create 7-section report
  - Save report in Message metadata
  - Update session status to "completed"
→ Return report with completion message
→ Frontend:
  - Displays completion message
  - Shows "View Performance Report" button
  - Stores report in session
```

**8. View Report**:
```
User → Clicks "View Performance Report"
→ Frontend (ReportDashboard):
  - Renders 3D score visualization
  - Displays charts (radar, bar, line, doughnut)
  - Shows tabbed interface (overview, details, insights)
  - Allows question-by-question expansion
```

**9. Session Management**:
```
User → Clicks session in sidebar
→ GET /api/v1/sessions/{session_id}/messages
→ Backend: Returns all messages for session
→ Frontend:
  - Loads chat history
  - Restores currentQuestion (if not complete)
  - Checks for saved report in messages
  - Sets currentReport if found
```

### State Synchronization

**Workflow State Persistence**:

The `workflow_state` JSON field in `InterviewSession` is critical for maintaining conversational continuity:

1. **Initial Creation**: Empty or minimal state
2. **After Each Interaction**: Full state saved including:
   - All agent responses
   - Question context and history
   - Evaluation results
   - Domain coverage
   - Conversation phase
   - Interview plan
3. **Session Restoration**: State loaded from database, allowing:
   - Resume interrupted interviews
   - View historical context
   - Regenerate reports

**Message Synchronization**:

Messages in database serve dual purpose:
1. **Chat History**: Display in UI
2. **State Recovery**: Reconstruct workflow state if needed (fallback)

### Error Handling

**Frontend**:
- Try-catch around all API calls
- Display error messages in UI
- Optimistic updates with rollback on failure

**Backend**:
- HTTPException with status codes
- Detailed error messages in JSON response
- Logging for debugging

**Fallbacks**:
- LLM failures → Heuristic/template responses
- Vector DB failures → Default contexts
- Embedding failures → Retry or skip

---

## Key Algorithms & Techniques

### 1. Semantic Search with Pinecone

**Query Process**:
1. Embed query text (1024-dim vector)
2. Send to Pinecone index
3. Pinecone computes cosine similarity with all vectors
4. Returns top-k most similar chunks
5. Apply metadata filters (resume_id, domain)

**Optimization**:
- Batch embeddings during resume upload
- Domain filtering reduces search space
- Store text in metadata for immediate retrieval

### 2. Hierarchical Resume Chunking

**Strategy**: Preserve document structure

**Benefits**:
- Maintains context within sections
- Allows section-level retrieval
- Supports granular matching

**Implementation**:
- Regex patterns for section detection
- Heuristics for entry separation (dates, patterns)
- Metadata tracking (parent_section, entry_index)

### 3. LLM-Based Domain Classification

**Why LLM instead of Keywords**:
- Understands semantic relationships
- Handles synonyms and variations
- Can infer implicit domains

**Process**:
- Prompt LLM with chunk and available domains
- Request JSON response with matched domains
- Validate and deduplicate results
- Fallback to keyword matching

### 4. Two-Step Answer Evaluation

**Rationale**: More accurate than single-pass evaluation

**Step 1: Reference Generation**:
- Provides objective "correct" answer
- Uses low temperature for factual accuracy

**Step 2: Comparative Judgment**:
- Compares candidate against reference
- Scores multiple dimensions
- Provides constructive feedback

**Alternative Considered**: Direct evaluation without reference
- Less consistent
- More prone to bias
- Harder to calibrate scoring

### 5. Round-Robin Domain Selection

**Goal**: Comprehensive assessment across multiple domains

**Algorithm**:
```python
domain_index = (question_count - 1) % len(planned_domains)
selected_domain = planned_domains[domain_index]
```

**Benefits**:
- Even coverage of all domains
- Predictable sequence
- Avoids domain clustering

### 6. Even Difficulty Distribution

**Pre-planned Sequence**:
```
10 questions: [easy, easy, easy, medium, medium, medium, hard, hard, hard, hard]
7 questions: [easy, easy, medium, medium, medium, hard, hard]
5 questions: [easy, medium, medium, hard, hard]
```

**Rationale**:
- Gradual ramp-up
- More weight on harder questions
- Predictable progression

### 7. Question Personalization with RAG

**Process**:
1. Generate generic question (fine-tuned model)
2. Retrieve relevant experience (vector search by domain)
3. Blend with LLM:
   - Reference specific projects
   - Use actual technologies mentioned
   - Create natural phrasing

**Example Transformation**:
- Generic: "What is the difference between supervised and unsupervised learning?"
- Personalized: "In your sentiment analysis project using LSTM, how did you handle the unlabeled tweets? What made you choose supervised learning over unsupervised clustering?"

### 8. Async/Await Patterns

**FastAPI**:
- All endpoints async
- Non-blocking I/O for database, LLM calls
- Concurrent handling of multiple requests

**Database**:
- `AsyncSession` for non-blocking queries
- `async with` context managers

**LLM Calls**:
- `AsyncInferenceClient` for Hugging Face
- Parallel calls where possible (e.g., batch embeddings)

### 9. State Management in LangGraph

**Annotated Reducers**:
```python
previous_questions: Annotated[List[dict], operator.add]
```
- Automatically appends to list
- Preserves history across agent calls

**Conditional Edges**:
```python
workflow.add_conditional_edges(
    "orchestrator",
    should_continue,
    {"generate_question": "question_agent", "evaluate": "evaluation_agent"}
)
```
- Dynamic routing based on state
- Flexible workflow paths

### 10. Report Generation with Aggregation

**Data Collection**:
- Iterates through evaluation_history
- Groups by domain, difficulty
- Calculates averages, counts

**LLM Insights**:
- Summarizes quantitative data
- Provides qualitative analysis
- Generates actionable recommendations

**Fallback Logic**:
- If LLM fails, uses rule-based insights
- Ensures report always available

---

## Deployment Considerations

### Environment Variables

**Backend**:
- `DATABASE_URL`: SQLite or PostgreSQL connection string
- `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`
- `HUGGINGFACE_API_URL`, `HUGGINGFACE_API_KEY` (4 endpoints)
- `SECRET_KEY`: JWT signing key (must be secure in production)
- `CORS_ORIGINS`: Allowed frontend origins

**Frontend**:
- `REACT_APP_API_URL`: Backend URL

### Database Migrations

**SQLAlchemy + Alembic**:
1. Generate migration: `alembic revision --autogenerate -m "description"`
2. Apply migration: `alembic upgrade head`

**Initial Setup**:
- `Base.metadata.create_all(bind=sync_engine)` creates tables on startup
- Good for development, but use Alembic in production

### Scaling Considerations

**Database**:
- SQLite: Single-file, limited concurrency
- PostgreSQL: Production-ready, supports async
- Connection pooling configured in database.py

**Vector Database**:
- Pinecone serverless: Auto-scales
- No infrastructure management

**LLM Endpoints**:
- Hugging Face: Managed scaling
- Rate limits may apply
- Consider caching frequent queries

**Frontend**:
- Static build served by CDN
- API calls from browser (CORS configured)

### Security Best Practices

**Implemented**:
- JWT authentication
- bcrypt password hashing with salt
- CORS whitelist
- Foreign key constraints

**Recommended Additions**:
- HTTPS in production
- Rate limiting on API endpoints
- Input validation and sanitization
- File upload size limits (already implemented: 10MB)
- SQL injection protection (SQLAlchemy ORM provides)

### Monitoring & Logging

**Current**:
- Print statements for debugging
- FastAPI automatic OpenAPI docs at `/docs`

**Production Recommendations**:
- Structured logging (JSON format)
- Application performance monitoring (APM)
- Error tracking (Sentry)
- Usage analytics

### Performance Optimization

**Backend**:
- Async operations throughout
- Batch embedding generation
- Vector DB query optimization (domain filtering)
- State caching in session

**Frontend**:
- React.memo for expensive components
- Lazy loading for charts
- Debouncing for user input
- Local state management (avoid prop drilling)

### Cost Optimization

**LLM Calls**:
- Fine-tuned model for question generation (more efficient)
- Batch API calls where possible
- Cache common queries
- Use lower-cost models for non-critical tasks

**Vector Database**:
- Pinecone serverless: Pay per use
- Optimize query size (top_k)
- Clean up unused indexes

### Backup & Recovery

**Database**:
- Regular SQLite backups (if using SQLite)
- PostgreSQL automated backups
- Export resume files separately

**Vector Database**:
- Pinecone handles redundancy
- Re-embed from source if needed

**Resume Files**:
- Store in object storage (S3, GCS)
- Backup upload directory

---

## Conclusion

This AI Interviewer system represents a sophisticated integration of multiple AI technologies:

1. **Multi-Agent Orchestration**: LangGraph coordinates specialized agents for questions, evaluation, and workflow management.

2. **Retrieval-Augmented Generation**: Pinecone vector database enables semantic search to personalize questions based on candidate's resume.

3. **Fine-Tuned Models**: Dedicated model for question generation improves quality and reduces costs.

4. **Conversational AI**: Natural dialogue flow with state management across interactions.

5. **Comprehensive Analytics**: Multi-dimensional evaluation with visual reports.

The architecture is modular, scalable, and maintainable, with clear separation between AI logic, business logic, and presentation layer. The use of async patterns throughout ensures responsiveness, while the dual database approach (relational + vector) provides both structured data management and semantic search capabilities.

Key innovations include:
- Hierarchical resume chunking preserving document structure
- Two-step answer evaluation for accuracy
- LLM-driven interview planning based on candidate profile
- Question personalization by blending generic questions with specific experience
- Persistent workflow state enabling session resumption

This implementation demonstrates production-ready patterns for building AI-powered applications with complex multi-agent workflows.

