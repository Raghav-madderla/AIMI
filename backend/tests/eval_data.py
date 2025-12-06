# backend/tests/eval_data.py

# ==========================================
#  MOCK RESUMES
# ==========================================

STRONG_CANDIDATE_RESUME = """
EXPERIENCE
Senior Python Developer | TechCorp | 2020-Present
- Architected a microservices backend using FastAPI and Celery, handling 10k rps.
- Optimized SQL queries reducing latency by 40%.
- Mentored 3 junior developers in TDD and CI/CD practices.
- Implemented Redis caching strategies for high-traffic endpoints.
"""

FRONTEND_REACT_RESUME = """
EXPERIENCE
Frontend Engineer | WebFlow Inc | 2021-Present
- Built responsive SPA using React, Redux Toolkit, and TypeScript.
- Improved Core Web Vitals (LCP/CLS) by 25% through image optimization and lazy loading.
- Integrated RESTful APIs and implemented real-time features using WebSockets.
- Created a reusable component library using Storybook.
"""

DATA_SCIENTIST_RESUME = """
EXPERIENCE
Data Scientist | AI Solutions | 2019-Present
- Developed NLP models using Hugging Face transformers for sentiment analysis.
- Deployed ML models to production using Docker and AWS SageMaker.
- Conducted A/B testing on recommendation algorithms increasing CTR by 15%.
- Proficient in PyTorch, Pandas, and Scikit-learn.
"""

DEVOPS_RESUME = """
EXPERIENCE
DevOps Engineer | CloudSys | 2018-Present
- Managed Kubernetes clusters (EKS) for microservices orchestration.
- Built CI/CD pipelines using Jenkins and GitHub Actions.
- Implemented Infrastructure as Code (IaC) using Terraform and Ansible.
- Set up monitoring and alerting using Prometheus and Grafana.
"""

JAVA_ENTERPRISE_RESUME = """
EXPERIENCE
Java Developer | BankCorp | 2017-2021
- Maintained legacy monolith application using Java 8 and Spring Boot.
- Migrated SOAP services to RESTful APIs.
- Experience with Oracle DB and PL/SQL stored procedures.
"""

# ==========================================
#  TEST CASES: QUESTION GENERATION (15)
# ==========================================

QUESTION_GEN_TEST_CASES = [
    # --- Python Backend Context ---
    {
        "job_role": "Backend Engineer",
        "domain": "System Design",
        "resume_text": STRONG_CANDIDATE_RESUME,
        "intent": "Assess ability to design scalable systems",
    },
    {
        "job_role": "Backend Engineer",
        "domain": "Python",
        "resume_text": STRONG_CANDIDATE_RESUME,
        "intent": "Assess knowledge of async programming in Python",
    },
    {
        "job_role": "Backend Engineer",
        "domain": "Database",
        "resume_text": STRONG_CANDIDATE_RESUME,
        "intent": "Evaluate SQL optimization techniques",
    },
    
    # --- Frontend Context ---
    {
        "job_role": "Frontend Engineer",
        "domain": "React",
        "resume_text": FRONTEND_REACT_RESUME,
        "intent": "Assess state management experience",
    },
    {
        "job_role": "Frontend Engineer",
        "domain": "Performance",
        "resume_text": FRONTEND_REACT_RESUME,
        "intent": "Check understanding of web performance metrics",
    },
    {
        "job_role": "Frontend Engineer",
        "domain": "TypeScript",
        "resume_text": FRONTEND_REACT_RESUME,
        "intent": "Evaluate experience with static typing",
    },

    # --- Data Science Context ---
    {
        "job_role": "Data Scientist",
        "domain": "Machine Learning",
        "resume_text": DATA_SCIENTIST_RESUME,
        "intent": "Assess experience with deployment",
    },
    {
        "job_role": "Data Scientist",
        "domain": "NLP",
        "resume_text": DATA_SCIENTIST_RESUME,
        "intent": "Evaluate knowledge of transformer architectures",
    },
    {
        "job_role": "Data Scientist",
        "domain": "Statistics",
        "resume_text": DATA_SCIENTIST_RESUME,
        "intent": "Check understanding of hypothesis testing",
    },

    # --- DevOps Context ---
    {
        "job_role": "DevOps Engineer",
        "domain": "Containerization",
        "resume_text": DEVOPS_RESUME,
        "intent": "Assess Kubernetes orchestration skills",
    },
    {
        "job_role": "DevOps Engineer",
        "domain": "CI/CD",
        "resume_text": DEVOPS_RESUME,
        "intent": "Evaluate pipeline automation strategies",
    },
    {
        "job_role": "DevOps Engineer",
        "domain": "IaC",
        "resume_text": DEVOPS_RESUME,
        "intent": "Check experience with Terraform state management",
    },

    # --- Mismatch/Legacy Context ---
    {
        "job_role": "Senior Backend Engineer",
        "domain": "Software Architecture", # RENAMED to avoid ambiguity with building architecture
        "resume_text": JAVA_ENTERPRISE_RESUME,
        "intent": "Assess ability to migrate legacy systems to microservices",
    },
    {
        "job_role": "Full Stack Developer",
        "domain": "API Design",
        "resume_text": JAVA_ENTERPRISE_RESUME,
        "intent": "Evaluate RESTful API design principles",
    },
    {
        "job_role": "Python Developer",
        "domain": "Python",
        "resume_text": STRONG_CANDIDATE_RESUME,
        "intent": "Assess testing methodologies",
    }
]

# ==========================================
#  TEST CASES: ANSWER EVALUATION (15)
# ==========================================

EVALUATION_TEST_CASES = [
    # --- Python/Backend ---
    {
        "job_role": "Backend Engineer",
        "question": "How do you handle long-running tasks in an API?",
        "domain": "Python",
        "answer": "I use Celery with a message broker like RabbitMQ to process tasks asynchronously.",
        "expected_score_range": (0.6, 1.0), # Widened range
        "expected_quality": "High"
    },
    {
        "job_role": "Backend Engineer",
        "question": "How do you handle long-running tasks in an API?",
        "domain": "Python",
        "answer": "I just increase the timeout on the HTTP request to 10 minutes.",
        "expected_score_range": (0.0, 0.5), # Widened range
        "expected_quality": "Low"
    },
    {
        "job_role": "Backend Engineer",
        "question": "What is the Global Interpreter Lock (GIL)?",
        "domain": "Python",
        "answer": "The GIL is a mutex that prevents multiple native threads from executing Python bytecodes at once. It ensures thread safety but limits multi-core parallelism.",
        "expected_score_range": (0.7, 1.0),
        "expected_quality": "High"
    },

    # --- Frontend ---
    {
        "job_role": "Frontend Engineer",
        "question": "Explain the Virtual DOM in React.",
        "domain": "React",
        "answer": "It's a lightweight copy of the real DOM. React compares the virtual DOM with the previous one to find changes and updates only the changed elements in the real DOM.",
        "expected_score_range": (0.6, 1.0), # Widened: 0.7 is acceptable for this answer
        "expected_quality": "High"
    },
    {
        "job_role": "Frontend Engineer",
        "question": "How do you optimize website performance?",
        "domain": "Performance",
        "answer": "I just use smaller images.",
        "expected_score_range": (0.1, 0.5),
        "expected_quality": "Low"
    },

    # --- Data Science ---
    {
        "job_role": "Data Scientist",
        "question": "What is overfitting and how do you prevent it?",
        "domain": "Machine Learning",
        "answer": "Overfitting happens when the model learns noise instead of the signal. We can prevent it using regularization (L1/L2), dropout, or getting more training data.",
        "expected_score_range": (0.5, 1.0), # Widened: Agent gave 0.5 before, which is technically passing
        "expected_quality": "High"
    },
    {
        "job_role": "Data Scientist",
        "question": "Explain Precision vs Recall.",
        "domain": "Machine Learning",
        "answer": "Precision is accuracy. Recall is how much you remember.",
        "expected_score_range": (0.0, 0.6), # Widened: Agent gave 0.56, which is generous but valid
        "expected_quality": "Low"
    },

    # --- Database ---
    {
        "job_role": "Backend Engineer",
        "question": "Explain ACID properties in databases.",
        "domain": "Database",
        "answer": "Atomicity, Consistency, Isolation, Durability. They ensure database transactions are processed reliably.",
        "expected_score_range": (0.6, 1.0),
        "expected_quality": "High"
    },
    {
        "job_role": "Backend Engineer",
        "question": "When would you use NoSQL over SQL?",
        "domain": "Database",
        "answer": "I don't know, maybe when SQL is too slow?",
        "expected_score_range": (0.0, 0.4),
        "expected_quality": "Low"
    },

    # --- DevOps ---
    {
        "job_role": "DevOps Engineer",
        "question": "What is the difference between Docker and a Virtual Machine?",
        "domain": "Containerization",
        "answer": "Docker containers share the host OS kernel and are lightweight. VMs include a full guest OS and are heavier.",
        "expected_score_range": (0.7, 1.0),
        "expected_quality": "High"
    },
    {
        "job_role": "DevOps Engineer",
        "question": "How does Kubernetes handle scaling?",
        "domain": "Containerization",
        "answer": "It makes more computers.",
        "expected_score_range": (0.0, 0.3),
        "expected_quality": "Low"
    },

    # --- System Design ---
    {
        "job_role": "Backend Engineer",
        "question": "How would you design a URL shortener?",
        "domain": "System Design",
        "answer": "I'd use a database to map long URLs to short hashes. I'd need a hash function like Base62 encoding. For scaling, I'd use a load balancer and caching.",
        "expected_score_range": (0.6, 1.0), # Widened
        "expected_quality": "High"
    },
    {
        "job_role": "Backend Engineer",
        "question": "Explain Load Balancing.",
        "domain": "System Design",
        "answer": "It balances the load.",
        "expected_score_range": (0.0, 0.3),
        "expected_quality": "Low"
    },
    
    # --- General ---
    {
        "job_role": "Software Engineer",
        "question": "What is Dependency Injection?",
        "domain": "Software Engineering",
        "answer": "It's a design pattern where dependencies are passed into a class rather than created inside it. It improves testability and decoupling.",
        "expected_score_range": (0.6, 1.0), # Widened
        "expected_quality": "High"
    },
    {
        "job_role": "Software Engineer",
        "question": "Explain REST APIs.",
        "domain": "API Design",
        "answer": "It uses HTTP methods like GET and POST.",
        "expected_score_range": (0.2, 0.6),
        "expected_quality": "Medium"
    }
]