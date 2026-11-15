# AI Education Assessment & Personalized Learning Evaluator (TP10)

An AI-powered educational assessment platform that helps teachers evaluate descriptive student answers using teacher-defined marking rubrics and semantic AI evaluation.

---

## 1. Project Overview

Grading descriptive student answers is often subjective and time-consuming. **AI Education Assessment & Personalized Learning Evaluator (TP10)** is an assisted grading platform designed with strict pedagogical standards:

- **Semantic Understanding**: Evaluates descriptive answers based on conceptual grasp rather than rigid keyword matching.
- **Rubric-Driven Evaluation**: Teachers define discrete criteria (expected concepts, maximum marks, evaluation guidelines).
- **Assisted Grading Workflow**: AI acts as a grading assistant. The teacher reviews, modifies, and approves all marks before reports are visible to students.
- **Deterministic Scoring Engine**: Programmatic enforcement ensures marks are non-negative, never exceed criterion maximums, and sum up accurately without LLM hallucination.
- **Diagnostic Learning Gaps**: Diagnoses exact missing or misunderstood concepts and pairs them with study recommendations.
- **Adaptive Practice Generator**: Creates targeted remediation questions across Beginner, Intermediate, and Advanced tiers.
- **Retrieval-Augmented Generation (RAG)**: Integrates course documents (PDF, DOCX, TXT) via Qdrant vector storage with metadata filtering for teacher isolation.
- **SQLite Database**: Optimized for zero-setup local execution and serverless Vercel deployment.

---

## 2. Technology Stack

- **Backend**: Python 3.12+, Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Pydantic 2, Flask Blueprints
- **Database**: SQLite (configured for `/tmp/evaluator.db` on serverless Vercel and local `evaluator.db` locally)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Jinja2 templates, Chart.js, Bootstrap Icons (no React or frontend build step needed)
- **AI & LLM**: Google Gemini API (`google-genai`), Ollama support, FastEmbed / Sentence Transformers
- **Vector DB / RAG**: Qdrant Client (in-memory or remote cluster)
- **Document Processing**: PyMuPDF (`pymupdf`), `python-docx`
- **Deployment Target**: Vercel Serverless (`@vercel/python`)

---

## 3. End-to-End Workflow

```
[ Teacher ] ──> Creates Assessment & Question
     │
     └──> Configures / AI-Generates Marking Rubric (Criteria sum == Max Marks)
     │
     └──> (Optional) Uploads Reference Documents (PDF/DOCX/TXT) into RAG
     │
[ Student ] ──> Submits Descriptive Answer
     │
[ AI Engine ] ──> Semantic Rubric Analysis + RAG Context Retrieval
     │
[ Scoring Engine ] ──> Validates & Clamps Marks Programmatically (Deterministic)
     │
[ Diagnostics ] ──> Diagnoses Learning Gaps & Generates 3-Tier Practice Questions
     │
[ Teacher Review ] ──> Reviews Criteria, Modifies Marks, Adds Notes & Approves
     │
[ Final Report ] ──> Student views official report, learning gaps & practice lab
```

---

## 4. Local Setup & Running Instructions

### Prerequisites
- Python 3.12+ (or Conda / Miniconda)
- Gemini API Key ([Get an API key from Google AI Studio](https://aistudio.google.com/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/ai-education-assessment-personalized-learning-Evaluator.git
cd ai-education-assessment-personalized-learning-Evaluator
```

### Step 2: Set Up Environment & Install Dependencies
If using Conda:
```bash
conda activate your_env
pip install -r requirements.txt
```

If using standard Python `venv`:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Edit `.env` and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
FLASK_SECRET_KEY=a_secure_random_key
GEMINI_MODEL=gemini-1.5-flash
DEFAULT_LLM_PROVIDER=gemini
```

### Step 4: Run the Application
```bash
python run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Pre-loaded Starter Accounts & Assessments
The application is pre-seeded with ready-to-use demo accounts and foundational assessments in `init.sql`:
- **Teacher Account**:
  - Username: `teacher_demo` (or email: `teacher@evaluator.edu`)
  - Password: `Teacher123!`
  - Role: Teacher
- **Student Account**:
  - Username: `student_demo` (or email: `student@evaluator.edu`)
  - Password: `Student123!`
  - Role: Student
- **Pre-loaded Assessments**:
  1. *Midterm Assessment: Retrieval-Augmented Generation (RAG)* (10 Marks, 4 Rubric Criteria)
  2. *Foundations of Supervised vs Unsupervised Machine Learning* (10 Marks, 4 Rubric Criteria)

---

## 5. Database Schema & Migration (`init.sql`)

The application automatically creates all necessary SQLite tables upon first startup.

If you wish to inspect or run the SQL schema manually (for SQLite or PostgreSQL), execute `init.sql`:

```bash
# SQLite
sqlite3 evaluator.db < init.sql

# PostgreSQL (if applicable)
psql -U your_user -d your_db -f init.sql
```

### Normalized Schema Overview
1. `users`: Teacher and Student accounts with secure password hashing.
2. `assessments`: Title, subject, topic, due date, status.
3. `questions`: Questions linked to assessments with maximum marks.
4. `rubrics`: Rubrics tied to questions.
5. `rubric_criteria`: Criterion name, maximum marks, expected concepts, keywords, guidelines.
6. `assessment_assignments`: Student-to-assessment assignments.
7. `student_answers`: Preserved original descriptive student submissions.
8. `documents`: Uploaded course files (PDF, DOCX, TXT) and chunk counts.
9. `evaluations`: AI-suggested marks, teacher-approved marks, and feedback.
10. `criterion_scores`: Criterion-level marks, evidence quotes, and missing concepts.
11. `learning_gaps`: Conceptual diagnostic gaps and study recommendations.
12. `practice_questions`: Beginner, Intermediate, and Advanced practice questions.
13. `teacher_feedback`: Audit trail of teacher reviews and approvals.

---

## 6. How to Deploy to Vercel

The application is pre-configured for Vercel using `@vercel/python` serverless functions.

### How Vercel Support Works:
- **`vercel.json`**: Directs all incoming traffic to `api/index.py`.
- **`api/index.py`**: Exports the Flask WSGI `app` callable.
- **Writable Storage**: Vercel serverless environments have a read-only root filesystem. The app automatically detects Vercel (`os.environ.get("VERCEL")`) and points SQLite and uploads to `/tmp/evaluator.db` and `/tmp/uploads`.

### Deployment Steps:

#### Option A: Deploy via GitHub (Recommended)
1. Push your project to a GitHub repository:
   ```bash
   git add .
   git commit -m "Deploy AI Education Evaluator"
   git push origin main
   ```
2. Log in to [Vercel](https://vercel.com/) and click **"Add New Project"**.
3. Import your GitHub repository.
4. In the **Environment Variables** section, add:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `FLASK_SECRET_KEY`: A random secret string (e.g., `edu-tp10-production-key-99`).
   - `GEMINI_MODEL`: `gemini-1.5-flash` (or `gemini-2.5-flash`).
5. Click **Deploy**. Vercel will build and host your web application.

#### Option B: Deploy via Vercel CLI
```bash
npm install -g vercel
vercel login
vercel
```
When prompted for environment variables, provide `GEMINI_API_KEY` and `FLASK_SECRET_KEY`.

---

## 7. Running Automated Tests

Run the test suite using `pytest`:
```bash
pytest -v
```

Tests include:
- `tests/test_scoring.py`: Clamping non-negative marks, bounding by criterion maximums, programmatic total and percentage calculation.
- `tests/test_auth.py`: User registration, password hashing verification, role separation (Teacher vs. Student), and login sessions.
- `tests/test_assessment_rubric.py`: Assessment creation, rubric criteria sum validation (sum must equal question max marks), and student answer submission flow.

---

## 8. Project Structure

```
ai-education-assessment-personalized-learning-Evaluator/
├── api/
│   └── index.py               # Vercel Serverless WSGI entry point
├── app/
│   ├── __init__.py            # Flask application factory
│   ├── config.py              # Configuration & Vercel /tmp detection
│   ├── database/              # SQLAlchemy & Migrate initialization
│   ├── models/                # 13 Normalized DB models
│   │   ├── user.py
│   │   ├── assessment.py
│   │   ├── rubric.py
│   │   ├── submission.py
│   │   └── evaluation.py
│   ├── routes/                # Modular Blueprints
│   │   ├── auth.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── assessment.py
│   │   ├── rubric.py
│   │   ├── documents.py
│   │   ├── evaluation.py
│   │   └── learning.py
│   ├── services/              # Business logic outside routes
│   │   ├── assessment_service.py
│   │   ├── rubric_service.py
│   │   ├── document_service.py
│   │   ├── evaluation_service.py
│   │   ├── scoring_service.py
│   │   ├── learning_gap_service.py
│   │   └── practice_service.py
│   ├── ai/                    # LLM & RAG modules
│   │   ├── llm_provider.py    # Base provider & Pydantic schemas
│   │   ├── gemini_provider.py # Gemini 2.x SDK integration
│   │   ├── ollama_provider.py # Local Ollama provider
│   │   ├── embedding_service.py
│   │   ├── rag_service.py     # Qdrant vector retrieval
│   │   └── prompts/           # Prompts for evaluation, rubric, gaps, practice
│   ├── templates/             # Jinja2 templates (Bootstrap 5)
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── teacher/
│   │   ├── student/
│   │   └── common/
│   └── static/                # CSS and JavaScript
│       ├── css/style.css
│       └── js/main.js
├── tests/                     # Pytest suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_scoring.py
│   └── test_assessment_rubric.py
├── init.sql                   # Database schema migration script
├── requirements.txt           # Python dependencies
├── vercel.json                # Vercel configuration
├── run.py                     # Local entrypoint
├── app.py                     # Alternative entrypoint
├── .env.example               # Environment variables template
└── README.md                  # Documentation
```

---

## 9. License & Credits

Built for **AI Education Assessment & Personalized Learning Evaluator (TP10)**.
Developed with Flask, Jinja2, Bootstrap 5, and Google Gemini API.
