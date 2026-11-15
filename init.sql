-- AI Education Assessment & Personalized Learning Evaluator (TP10)
-- Database Initialization & Schema Migration Script
-- Compatible with PostgreSQL and SQLite

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    full_name VARCHAR(120) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Assessments Table
CREATE TABLE IF NOT EXISTS assessments (
    id VARCHAR(36) PRIMARY KEY,
    teacher_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(150) NOT NULL,
    due_date TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_assessments_teacher_id ON assessments(teacher_id);

-- 3. Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL,
    question_text TEXT NOT NULL,
    maximum_marks REAL NOT NULL DEFAULT 10.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_questions_assessment_id ON questions(assessment_id);

-- 4. Rubrics Table
CREATE TABLE IF NOT EXISTS rubrics (
    id VARCHAR(36) PRIMARY KEY,
    teacher_id VARCHAR(36) NOT NULL,
    assessment_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(36) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    total_marks REAL NOT NULL DEFAULT 10.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rubrics_question_id ON rubrics(question_id);

-- 5. Rubric Criteria Table
CREATE TABLE IF NOT EXISTS rubric_criteria (
    id VARCHAR(36) PRIMARY KEY,
    rubric_id VARCHAR(36) NOT NULL,
    criterion_name VARCHAR(150) NOT NULL,
    criterion_description TEXT,
    maximum_marks REAL NOT NULL DEFAULT 1.0,
    expected_concepts TEXT,
    important_keywords TEXT,
    evaluation_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rubric_id) REFERENCES rubrics(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rubric_criteria_rubric_id ON rubric_criteria(rubric_id);

-- 6. Assessment Assignments Table
CREATE TABLE IF NOT EXISTS assessment_assignments (
    id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL,
    student_id VARCHAR(36) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_assessment_student UNIQUE (assessment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_assignments_assessment_student ON assessment_assignments(assessment_id, student_id);

-- 7. Student Answers Table
CREATE TABLE IF NOT EXISTS student_answers (
    id VARCHAR(36) PRIMARY KEY,
    assessment_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(36) NOT NULL,
    student_id VARCHAR(36) NOT NULL,
    answer_text TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'submitted',
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_student_answers_student_id ON student_answers(student_id);
CREATE INDEX IF NOT EXISTS idx_student_answers_assessment_id ON student_answers(assessment_id);

-- 8. Documents (RAG) Table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    teacher_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    collection_name VARCHAR(100) NOT NULL DEFAULT 'educational_documents',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_documents_teacher_id ON documents(teacher_id);

-- 9. Evaluations Table
CREATE TABLE IF NOT EXISTS evaluations (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) UNIQUE NOT NULL,
    total_suggested_marks REAL NOT NULL DEFAULT 0.0,
    total_approved_marks REAL,
    max_marks REAL NOT NULL DEFAULT 10.0,
    percentage REAL NOT NULL DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'pending_review',
    overall_feedback TEXT,
    teacher_notes TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES student_answers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_evaluations_submission_id ON evaluations(submission_id);

-- 10. Criterion Scores Table
CREATE TABLE IF NOT EXISTS criterion_scores (
    id VARCHAR(36) PRIMARY KEY,
    evaluation_id VARCHAR(36) NOT NULL,
    criterion_id VARCHAR(36),
    criterion_name VARCHAR(150) NOT NULL,
    max_marks REAL NOT NULL DEFAULT 1.0,
    suggested_marks REAL NOT NULL DEFAULT 0.0,
    approved_marks REAL,
    status VARCHAR(30) NOT NULL DEFAULT 'correct',
    explanation TEXT,
    supporting_evidence_json TEXT,
    missing_concepts_json TEXT,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
    FOREIGN KEY (criterion_id) REFERENCES rubric_criteria(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_criterion_scores_evaluation_id ON criterion_scores(evaluation_id);

-- 11. Learning Gaps Table
CREATE TABLE IF NOT EXISTS learning_gaps (
    id VARCHAR(36) PRIMARY KEY,
    evaluation_id VARCHAR(36) NOT NULL,
    student_id VARCHAR(36) NOT NULL,
    concept_name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT,
    recommended_material TEXT,
    difficulty_level VARCHAR(30) NOT NULL DEFAULT 'Intermediate',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_learning_gaps_student_id ON learning_gaps(student_id);

-- 12. Practice Questions Table
CREATE TABLE IF NOT EXISTS practice_questions (
    id VARCHAR(36) PRIMARY KEY,
    learning_gap_id VARCHAR(36) NOT NULL,
    student_id VARCHAR(36) NOT NULL,
    question_text TEXT NOT NULL,
    sample_answer TEXT,
    difficulty_level VARCHAR(30) NOT NULL DEFAULT 'Intermediate',
    student_practice_answer TEXT,
    is_completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (learning_gap_id) REFERENCES learning_gaps(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_practice_questions_gap_id ON practice_questions(learning_gap_id);
CREATE INDEX IF NOT EXISTS idx_practice_questions_student_id ON practice_questions(student_id);

-- 13. Teacher Feedback Table
CREATE TABLE IF NOT EXISTS teacher_feedback (
    id VARCHAR(36) PRIMARY KEY,
    evaluation_id VARCHAR(36) NOT NULL,
    teacher_id VARCHAR(36) NOT NULL,
    comments TEXT,
    action VARCHAR(20) NOT NULL DEFAULT 'approve',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_teacher_feedback_eval_id ON teacher_feedback(evaluation_id);


-- =========================================================================
-- SEED DATA: Starter Teacher, Student, Assessments, Questions & Rubrics
-- =========================================================================

-- 1. Demo Teacher (password: Teacher123!)
INSERT INTO users (id, username, email, password_hash, role, full_name, created_at, updated_at)
VALUES (
    'teacher-uuid-0001',
    'teacher_demo',
    'teacher@evaluator.edu',
    'scrypt:32768:8:1$Qjg6FMq11BwJ7LQD$4eab745cb1644bfa4542ae1bc968d17635266999baebe29101ee70484c2f79f726ba29bf45edd5d7d075245484476e0e763a9f44b37541667199058774f3102e',
    'teacher',
    'Dr. Alan Turing',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 2. Demo Student (password: Student123!)
INSERT INTO users (id, username, email, password_hash, role, full_name, created_at, updated_at)
VALUES (
    'student-uuid-0001',
    'student_demo',
    'student@evaluator.edu',
    'scrypt:32768:8:1$cekqp4VZHqAMfDcz$88ab6dd3b227074da0f200e5afa86e13bb6c1d5abdfc67e3fbffc0d1932f590d9013a8a9394b9586e3750ec3f5f57351828d0891b8882e2ed4bf32f86217da61',
    'student',
    'Alex Student',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 3. Assessment 1: RAG Architecture
INSERT INTO assessments (id, teacher_id, title, subject, topic, due_date, status, created_at, updated_at)
VALUES (
    'assess-uuid-0001',
    'teacher-uuid-0001',
    'Midterm Assessment: Retrieval-Augmented Generation (RAG)',
    'Artificial Intelligence',
    'Information Retrieval & LLMs',
    CURRENT_TIMESTAMP,
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO questions (id, assessment_id, question_text, maximum_marks, created_at)
VALUES (
    'quest-uuid-0001',
    'assess-uuid-0001',
    'Explain the architecture and working mechanism of Retrieval-Augmented Generation (RAG). Discuss how combining external vector search with a large language model addresses hallucinations and domain-specific knowledge gaps, and give a real-world example.',
    10.0,
    CURRENT_TIMESTAMP
);

INSERT INTO rubrics (id, teacher_id, assessment_id, question_id, title, total_marks, created_at, updated_at)
VALUES (
    'rubric-uuid-0001',
    'teacher-uuid-0001',
    'assess-uuid-0001',
    'quest-uuid-0001',
    'Marking Rubric for RAG Architecture',
    10.0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO rubric_criteria (id, rubric_id, criterion_name, criterion_description, maximum_marks, expected_concepts, important_keywords, evaluation_guidelines, created_at)
VALUES
(
    'crit-uuid-0001',
    'rubric-uuid-0001',
    'RAG Definition & Core Architecture',
    'Clear definition explaining how external document retrieval couples with generation',
    2.5,
    'Combines information retrieval with generative LLMs, avoids training from scratch',
    'RAG, retrieval, generation, LLM, prompt augmentation',
    'Award 2.5 marks for complete semantic clarity; 1.5 marks if partially explained',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0002',
    'rubric-uuid-0001',
    'Vector Search & Retrieval Mechanics',
    'Explanation of chunking, vector embeddings, and similarity retrieval',
    2.5,
    'Document chunking, vector embeddings, vector databases, cosine similarity distance',
    'chunks, embeddings, vector database, similarity search, top-k',
    'Award 2.5 marks for detailing the embedding and search flow; 1.0 for high-level mention',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0003',
    'rubric-uuid-0001',
    'Mitigating Hallucinations & Knowledge Gaps',
    'How retrieved context grounds model generation to prevent falsehoods',
    3.0,
    'Grounding generation with factual retrieved context, dynamic external knowledge, domain adaptation',
    'hallucination reduction, grounding, factual accuracy, parametric memory',
    'Award 3.0 marks for articulate reasoning on parametric vs non-parametric memory',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0004',
    'rubric-uuid-0001',
    'Real-World Application Example',
    'Practical industrial or educational use case illustrating RAG in production',
    2.0,
    'Customer support bot, enterprise document search, medical clinical decision support',
    'enterprise search, customer support, documentation QA',
    'Award 2.0 marks for a realistic domain-specific example with clear benefit',
    CURRENT_TIMESTAMP
);

-- 4. Assessment 2: Supervised vs Unsupervised Learning
INSERT INTO assessments (id, teacher_id, title, subject, topic, due_date, status, created_at, updated_at)
VALUES (
    'assess-uuid-0002',
    'teacher-uuid-0001',
    'Foundations of Supervised vs Unsupervised Machine Learning',
    'Machine Learning',
    'Learning Paradigms',
    CURRENT_TIMESTAMP,
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO questions (id, assessment_id, question_text, maximum_marks, created_at)
VALUES (
    'quest-uuid-0002',
    'assess-uuid-0002',
    'Describe the primary distinctions between Supervised Learning and Unsupervised Learning. Explain how input data labeling affects model training, optimization objectives, and evaluation metrics, and provide an industry use case for each paradigm.',
    10.0,
    CURRENT_TIMESTAMP
);

INSERT INTO rubrics (id, teacher_id, assessment_id, question_id, title, total_marks, created_at, updated_at)
VALUES (
    'rubric-uuid-0002',
    'teacher-uuid-0001',
    'assess-uuid-0002',
    'quest-uuid-0002',
    'Marking Rubric for Machine Learning Paradigms',
    10.0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO rubric_criteria (id, rubric_id, criterion_name, criterion_description, maximum_marks, expected_concepts, important_keywords, evaluation_guidelines, created_at)
VALUES
(
    'crit-uuid-0005',
    'rubric-uuid-0002',
    'Supervised Learning Principles',
    'Labeled datasets, mapping features to targets, regression and classification',
    3.0,
    'Ground-truth labels, feature-target mapping, classification, regression',
    'labeled data, target variable, ground truth',
    'Award 3.0 marks for clear articulation of label supervision',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0006',
    'rubric-uuid-0002',
    'Unsupervised Learning Principles',
    'Unlabeled data, identifying inherent structures, clusters, and dimensionality reduction',
    3.0,
    'Unlabeled data, pattern discovery, clustering, dimensionality reduction',
    'clustering, k-means, PCA, anomaly detection, unlabeled',
    'Award 3.0 marks for explanation of latent pattern extraction',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0007',
    'rubric-uuid-0002',
    'Loss Functions & Evaluation Metrics',
    'Comparison of optimization and validation methods',
    2.0,
    'Supervised error metrics vs unsupervised similarity metrics',
    'accuracy, F1, MSE, silhouette score, inertia',
    'Award 2.0 marks for identifying distinct evaluation mechanisms',
    CURRENT_TIMESTAMP
),
(
    'crit-uuid-0008',
    'rubric-uuid-0002',
    'Real-World Industry Use Cases',
    'Clear real-world examples for each paradigm',
    2.0,
    'Fraud detection/spam filtering (supervised) and customer segmentation/market basket (unsupervised)',
    'spam filter, medical diagnosis, customer segmentation',
    'Award 1.0 mark per valid paradigm example',
    CURRENT_TIMESTAMP
);
