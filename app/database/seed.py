import uuid
from datetime import datetime, timedelta
from app.database import db
from app.models.user import User
from app.models.assessment import Assessment, Question
from app.models.rubric import Rubric, RubricCriterion

def seed_database_if_empty():
    """Seeds demo teacher, student, and initial descriptive assessment questions if database is empty."""
    if Assessment.query.first():
        return

    # 1. Seed Demo Teacher
    teacher = User.query.filter_by(username="teacher_demo").first()
    if not teacher:
        teacher = User(
            id="teacher-uuid-0001",
            username="teacher_demo",
            email="teacher@evaluator.edu",
            full_name="Dr. Alan Turing",
            role="teacher"
        )
        teacher.set_password("Teacher123!")
        db.session.add(teacher)
        db.session.flush()

    # 2. Seed Demo Student
    student = User.query.filter_by(username="student_demo").first()
    if not student:
        student = User(
            id="student-uuid-0001",
            username="student_demo",
            email="student@evaluator.edu",
            full_name="Alex Student",
            role="student"
        )
        student.set_password("Student123!")
        db.session.add(student)
        db.session.flush()

    # 3. Assessment 1: RAG Architecture & Vector Search
    a1 = Assessment(
        id="assess-uuid-0001",
        teacher_id=teacher.id,
        title="Midterm Assessment: Retrieval-Augmented Generation (RAG)",
        subject="Artificial Intelligence",
        topic="Information Retrieval & LLMs",
        due_date=datetime.utcnow() + timedelta(days=14),
        status="active"
    )
    db.session.add(a1)
    db.session.flush()

    q1 = Question(
        id="quest-uuid-0001",
        assessment_id=a1.id,
        question_text=(
            "Explain the architecture and working mechanism of Retrieval-Augmented Generation (RAG). "
            "Discuss how combining external vector search with a large language model addresses hallucinations "
            "and domain-specific knowledge gaps, and give a real-world example."
        ),
        maximum_marks=10.0
    )
    db.session.add(q1)
    db.session.flush()

    r1 = Rubric(
        id="rubric-uuid-0001",
        teacher_id=teacher.id,
        assessment_id=a1.id,
        question_id=q1.id,
        title="Marking Rubric for RAG Architecture",
        total_marks=10.0
    )
    db.session.add(r1)
    db.session.flush()

    criteria_1 = [
        RubricCriterion(
            id="crit-uuid-0001",
            rubric_id=r1.id,
            criterion_name="RAG Definition & Core Architecture",
            criterion_description="Clear definition explaining how external document retrieval couples with generation",
            maximum_marks=2.5,
            expected_concepts="Combines information retrieval with generative LLMs, avoids training from scratch",
            important_keywords="RAG, retrieval, generation, LLM, prompt augmentation",
            evaluation_guidelines="Award 2.5 marks for complete semantic clarity; 1.5 marks if partially explained"
        ),
        RubricCriterion(
            id="crit-uuid-0002",
            rubric_id=r1.id,
            criterion_name="Vector Search & Retrieval Mechanics",
            criterion_description="Explanation of chunking, vector embeddings, and similarity retrieval",
            maximum_marks=2.5,
            expected_concepts="Document chunking, vector embeddings, vector databases, cosine similarity distance",
            important_keywords="chunks, embeddings, vector database, similarity search, top-k",
            evaluation_guidelines="Award 2.5 marks for detailing the embedding and search flow; 1.0 for high-level mention"
        ),
        RubricCriterion(
            id="crit-uuid-0003",
            rubric_id=r1.id,
            criterion_name="Mitigating Hallucinations & Knowledge Gaps",
            criterion_description="How retrieved context grounds model generation to prevent falsehoods",
            maximum_marks=3.0,
            expected_concepts="Grounding generation with factual retrieved context, dynamic external knowledge, domain adaptation",
            important_keywords="hallucination reduction, grounding, factual accuracy, parametric memory",
            evaluation_guidelines="Award 3.0 marks for articulate reasoning on parametric vs non-parametric memory"
        ),
        RubricCriterion(
            id="crit-uuid-0004",
            rubric_id=r1.id,
            criterion_name="Real-World Application Example",
            criterion_description="Practical industrial or educational use case illustrating RAG in production",
            maximum_marks=2.0,
            expected_concepts="Customer support bot, enterprise document search, medical clinical decision support",
            important_keywords="enterprise search, customer support, documentation QA",
            evaluation_guidelines="Award 2.0 marks for a realistic domain-specific example with clear benefit"
        )
    ]
    for c in criteria_1:
        db.session.add(c)

    # 4. Assessment 2: Supervised vs Unsupervised Learning
    a2 = Assessment(
        id="assess-uuid-0002",
        teacher_id=teacher.id,
        title="Foundations of Supervised vs Unsupervised Machine Learning",
        subject="Machine Learning",
        topic="Learning Paradigms",
        due_date=datetime.utcnow() + timedelta(days=21),
        status="active"
    )
    db.session.add(a2)
    db.session.flush()

    q2 = Question(
        id="quest-uuid-0002",
        assessment_id=a2.id,
        question_text=(
            "Describe the primary distinctions between Supervised Learning and Unsupervised Learning. "
            "Explain how input data labeling affects model training, optimization objectives, and evaluation metrics, "
            "and provide an industry use case for each paradigm."
        ),
        maximum_marks=10.0
    )
    db.session.add(q2)
    db.session.flush()

    r2 = Rubric(
        id="rubric-uuid-0002",
        teacher_id=teacher.id,
        assessment_id=a2.id,
        question_id=q2.id,
        title="Marking Rubric for Machine Learning Paradigms",
        total_marks=10.0
    )
    db.session.add(r2)
    db.session.flush()

    criteria_2 = [
        RubricCriterion(
            id="crit-uuid-0005",
            rubric_id=r2.id,
            criterion_name="Supervised Learning Principles",
            criterion_description="Labeled datasets, mapping features to targets, regression and classification",
            maximum_marks=3.0,
            expected_concepts="Ground-truth labels, feature-target mapping, classification, regression",
            important_keywords="labeled data, target variable, ground truth",
            evaluation_guidelines="Award 3.0 marks for clear articulation of label supervision"
        ),
        RubricCriterion(
            id="crit-uuid-0006",
            rubric_id=r2.id,
            criterion_name="Unsupervised Learning Principles",
            criterion_description="Unlabeled data, identifying inherent structures, clusters, and dimensionality reduction",
            maximum_marks=3.0,
            expected_concepts="Unlabeled data, pattern discovery, clustering, dimensionality reduction",
            important_keywords="clustering, k-means, PCA, anomaly detection, unlabeled",
            evaluation_guidelines="Award 3.0 marks for explanation of latent pattern extraction"
        ),
        RubricCriterion(
            id="crit-uuid-0007",
            rubric_id=r2.id,
            criterion_name="Loss Functions & Evaluation Metrics",
            criterion_description="Comparison of optimization and validation methods (e.g. MSE/Accuracy vs Silhouette/Inertia)",
            maximum_marks=2.0,
            expected_concepts="Supervised error metrics vs unsupervised similarity metrics",
            important_keywords="accuracy, F1, MSE, silhouette score, inertia",
            evaluation_guidelines="Award 2.0 marks for identifying distinct evaluation mechanisms"
        ),
        RubricCriterion(
            id="crit-uuid-0008",
            rubric_id=r2.id,
            criterion_name="Real-World Industry Use Cases",
            criterion_description="Clear real-world examples for each paradigm",
            maximum_marks=2.0,
            expected_concepts="Fraud detection/spam filtering (supervised) and customer segmentation/market basket (unsupervised)",
            important_keywords="spam filter, medical diagnosis, customer segmentation",
            evaluation_guidelines="Award 1.0 mark per valid paradigm example"
        )
    ]
    for c in criteria_2:
        db.session.add(c)

    db.session.commit()
