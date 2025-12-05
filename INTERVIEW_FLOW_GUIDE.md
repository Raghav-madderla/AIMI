# Complete Interview System Flow

## Overview

This document explains how the AI interview system works, showing the exact flow of data between agents.

---

## 1. Resume Upload & Processing

### Flow:
```
User uploads PDF/DOCX
    ↓
Resume Service processes file
    ↓
Resume Summary Agent
    Input: WHOLE RESUME TEXT
    Output: {
        "summary_points": [...],  // Key achievements with domains
        "key_strengths": [...],    // Technical skills/domains found
        "overall_impression": "..."
    }
    ↓
Store in database
```

### Resume Summary Agent Details:
- **Gets**: Complete resume text (first 2000 chars)
- **Extracts**: 
  - Experience points
  - Technical domains/skills (Python, ML, SQL, etc.)
  - Significance levels
- **Creates**: Structured summary for orchestrator to use

---

## 2. Interview Start

### Flow:
```
Start Interview
    ↓
Load Resume Summary from DB
    ↓
Initialize Orchestrator with summary
    ↓
Orchestrator creates INTERVIEW PLAN
    - Extracts domains from resume summary
    - Plans question progression
    - Sets difficulty levels
```

### Orchestrator Planning:
- **Gets**: Resume summary with domains
- **Plans**: 
  - Which domains to ask about (from resume)
  - Question difficulty progression
  - Interview phases (intro → resume → technical)

---

## 3. Question Generation Flow

### Complete Flow:
```
Orchestrator (decides what to ask)
    ↓
    Selects: Domain + Difficulty
    ↓
Question Agent (generates raw question)
    Input: ONLY Domain + Difficulty
    Output: Technical question
    ↓
Question Cleaning Agent (blends with resume)
    Input: 
        - Generated question
        - Resume context
        - Domain
        - Orchestrator intent
    Output: Clean, blended question
    ↓
User sees final question
```

### Detailed Agent Responsibilities:

#### **Orchestrator Agent**
**Input**: 
- Resume summary (with domains and key points)
- Interview state (phase, question count, etc.)

**Decides**:
1. Which domain to ask about (from resume summary)
2. Difficulty level (easy/medium/hard)
3. What aspect to focus on

**Output**:
```json
{
    "domain": "Machine Learning",
    "difficulty": "medium",
    "orchestrator_intent": "Assess ML pipeline skills"
}
```

#### **Question Agent** 
**Input**: 
```json
{
    "domain": "Machine Learning",
    "difficulty": "medium"
}
```

**Purpose**: Generate a pure technical question

**Output**: Raw technical question (may be generic)

**Example**: "Explain how you would build a machine learning pipeline for production."

#### **Question Cleaning Agent**
**Input**:
```json
{
    "generated_question": "Explain how you would build...",
    "resume_context": "Built ML pipelines at Company X",
    "domain": "Machine Learning",
    "orchestrator_intent": "Ask about ML pipeline experience"
}
```

**Purpose**: Blend technical question with resume context

**Output**: Clean, personalized question

**Example**: "I see you built ML pipelines at Company X. How did you handle model deployment and monitoring in production?"

#### **Key Feature: Aggressive Cleaning**
The cleaning agent ensures:
- Takes only first sentence/up to first '?'
- Removes quotes and meta-commentary
- No model "thinking" shown
- Only the final question appears

---

## 4. Complete Question-Answer Cycle

```
1. User submits answer
    ↓
2. Evaluation Agent evaluates answer
    Input: Question + Answer + Domain
    Output: Score + Feedback
    ↓
3. Orchestrator decides next action
    Uses: Resume summary domains
    Decides: Next domain + difficulty
    ↓
4. Question Agent generates question
    Input: Domain + Difficulty ONLY
    Output: Raw technical question
    ↓
5. Cleaning Agent refines question
    Input: Question + Resume context
    Output: Clean, blended question
    ↓
6. Return to user
```

---

## 5. Domain Planning (Orchestrator)

### Resume Discussion Phase:
```python
# Orchestrator iterates through resume summary points
for point in resume_summary["summary_points"]:
    domain = point["domains"][0]  # Extract domain from resume
    difficulty = based_on_significance(point["significance"])
    
    # Generate question for this domain
    question = generate_question(domain, difficulty)
```

### Technical Deep Dive Phase:
```python
# Extract all domains from resume summary
technical_domains = []
for point in resume_summary["summary_points"]:
    technical_domains.extend(point["domains"])

# Add key strengths (more domains)
technical_domains.extend(resume_summary["key_strengths"])

# Cycle through these domains for questions
selected_domain = technical_domains[question_count % len(domains)]
```

**Result**: Questions are based on candidate's actual resume skills!

---

## 6. Data Flow Summary

### What Each Agent Gets:

| Agent | Input | Purpose |
|-------|-------|---------|
| **Resume Summary** | Whole resume | Extract domains & key points |
| **Orchestrator** | Resume summary | Plan domains & difficulty |
| **Question Agent** | Domain + Difficulty | Generate technical question |
| **Cleaning Agent** | Question + Resume context | Blend resume with question |
| **Evaluation Agent** | Question + Answer + Domain | Score & provide feedback |

### Key Principle:
- **Question Agent**: Gets minimal input (domain + difficulty) → generates pure technical questions
- **Cleaning Agent**: Gets context → personalizes to candidate's background
- **Orchestrator**: Uses resume summary → intelligently selects relevant domains

---

## 7. Example End-to-End Flow

### Scenario: Candidate with ML experience

#### Step 1: Resume Processing
```
Resume contains: "Built ML models using Python and TensorFlow"
    ↓
Resume Summary Agent extracts:
{
    "summary_points": [{
        "point": "Built ML models using Python and TensorFlow",
        "domains": ["Machine Learning", "Python"],
        "significance": "high"
    }],
    "key_strengths": ["Machine Learning", "Python", "Tensorflow"]
}
```

#### Step 2: Interview Planning
```
Orchestrator sees domains: ["Machine Learning", "Python", "Tensorflow"]
Plans to ask questions about these domains
```

#### Step 3: First Question
```
Orchestrator: "Ask about Machine Learning, medium difficulty"
    ↓
Question Agent: "Explain how to evaluate a classification model."
    ↓
Cleaning Agent: 
    Input: Question + "Built ML models using Python and TensorFlow"
    Output: "I see you built ML models using Python and TensorFlow. How did you evaluate your classification models and which metrics did you prioritize?"
```

#### Step 4: User Answers
```
User provides answer
    ↓
Evaluation Agent: Scores answer, provides feedback
    ↓
Orchestrator: Selects next domain from resume (e.g., "Python")
    ↓
Repeat cycle
```

---

## 8. Benefits of This Architecture

### ✅ **Separation of Concerns**
- Question Agent focuses on technical accuracy
- Cleaning Agent handles personalization
- Orchestrator manages overall flow

### ✅ **Resume-Driven**
- All domains come from candidate's actual resume
- Questions are relevant to their experience
- Feels personalized and contextual

### ✅ **Clean Output**
- Aggressive cleaning removes model artifacts
- Only shows the final polished question
- No "[insert here]" or template text

### ✅ **Modular**
- Easy to swap Question Agent model
- Easy to improve Cleaning Agent
- Each agent has clear responsibility

---

## 9. Configuration

All endpoints configured in `backend/app/core/config.py`:

```python
# Question Generation (your fine-tuned model)
HUGGINGFACE_API_URL = "https://uzqqfj5jlvnp9uij..."

# General LLM (evaluation, cleaning, orchestrator)
HUGGINGFACE_LLM_API_URL = "https://jw77yivg4zxkljyt..."

# Embeddings
HUGGINGFACE_EMBEDDING_API_URL = "https://rxulpwe4zl8cu282..."
```

---

## 10. Summary

### The System Works As Expected:

✅ **Resume Summary Agent** → Gets whole resume, extracts domains  
✅ **Orchestrator** → Uses resume summary to plan domains  
✅ **Question Agent** → Gets ONLY domain + difficulty  
✅ **Cleaning Agent** → Blends question + resume context  
✅ **Clean Output** → Only shows final question, no model thinking  

### Flow:
```
Resume → Summary (domains) → Orchestrator (plans) → Question (pure technical) 
→ Cleaning (personalize) → User (clean output)
```

Everything is working according to your specifications!

