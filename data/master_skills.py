"""
Master Skills List for JobLens
==============================
This module defines the comprehensive list of data science and tech skills
used across the entire platform for:
- Extracting skills from job descriptions
- Extracting skills from resumes
- Matching candidates to jobs
- Analyzing skill demand trends

The list is organized by category for maintainability, but flattened
into a single set for efficient lookup during NLP processing.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PROGRAMMING LANGUAGES
# ─────────────────────────────────────────────────────────────────────────────
PROGRAMMING_SKILLS = [
    "Python", "R", "Java", "Scala", "C++", "JavaScript", "SQL", "SAS",
    "MATLAB", "Julia", "Go", "Rust", "TypeScript", "Bash", "Shell Scripting"
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA SCIENCE & MACHINE LEARNING
# ─────────────────────────────────────────────────────────────────────────────
ML_SKILLS = [
    "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP",
    "Computer Vision", "Reinforcement Learning", "Neural Networks",
    "Supervised Learning", "Unsupervised Learning", "Feature Engineering",
    "Model Deployment", "MLOps", "AutoML", "Transfer Learning",
    "Ensemble Methods", "Gradient Boosting", "Random Forest",
    "Linear Regression", "Logistic Regression", "Decision Trees",
    "Support Vector Machines", "SVM", "Clustering", "K-Means",
    "Dimensionality Reduction", "PCA", "Time Series Analysis",
    "Recommendation Systems", "A/B Testing", "Hypothesis Testing",
    "Bayesian Statistics", "Generative AI", "LLM", "Prompt Engineering",
    "RAG", "Fine Tuning"
]

# ─────────────────────────────────────────────────────────────────────────────
# LIBRARIES & FRAMEWORKS
# ─────────────────────────────────────────────────────────────────────────────
LIBRARY_SKILLS = [
    "TensorFlow", "PyTorch", "Keras", "Scikit-Learn", "XGBoost", "LightGBM",
    "CatBoost", "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn",
    "Plotly", "NLTK", "spaCy", "Hugging Face", "Transformers", "OpenCV",
    "Flask", "Django", "FastAPI", "Streamlit", "PySpark", "Dask",
    "Beautiful Soup", "Selenium", "Scrapy", "Statsmodels", "LangChain"
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA ENGINEERING & BIG DATA
# ─────────────────────────────────────────────────────────────────────────────
DATA_ENGINEERING_SKILLS = [
    "Hadoop", "Spark", "Kafka", "Airflow", "ETL", "Data Pipeline",
    "Data Warehousing", "Data Lake", "Data Modeling", "Data Governance",
    "Hive", "Pig", "MapReduce", "Databricks", "Snowflake", "dbt",
    "Data Integration", "Stream Processing", "Batch Processing"
]

# ─────────────────────────────────────────────────────────────────────────────
# DATABASES
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_SKILLS = [
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "SQLite",
    "Oracle", "SQL Server", "DynamoDB", "Neo4j", "Elasticsearch",
    "NoSQL", "Database Design", "Query Optimization"
]

# ─────────────────────────────────────────────────────────────────────────────
# CLOUD & DEVOPS
# ─────────────────────────────────────────────────────────────────────────────
CLOUD_SKILLS = [
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes",
    "CI/CD", "Jenkins", "Git", "GitHub", "GitLab", "Terraform",
    "Linux", "AWS SageMaker", "Azure ML", "Google Vertex AI",
    "Cloud Computing", "Microservices", "REST API", "API Development"
]

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS INTELLIGENCE & VISUALIZATION
# ─────────────────────────────────────────────────────────────────────────────
BI_SKILLS = [
    "Tableau", "Power BI", "Excel", "Google Sheets", "Looker",
    "QlikView", "Qlik Sense", "Data Visualization", "Dashboard Development",
    "Business Intelligence", "Reporting", "Google Data Studio",
    "Advanced Excel", "VBA", "DAX", "Power Query"
]

# ─────────────────────────────────────────────────────────────────────────────
# STATISTICS & MATHEMATICS
# ─────────────────────────────────────────────────────────────────────────────
STATS_SKILLS = [
    "Statistics", "Probability", "Linear Algebra", "Calculus",
    "Optimization", "Regression Analysis", "Statistical Modeling",
    "Experimental Design", "Causal Inference", "Survival Analysis"
]

# ─────────────────────────────────────────────────────────────────────────────
# SOFT SKILLS & DOMAIN
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_SKILLS = [
    "Data Analysis", "Data Science", "Business Analysis",
    "Problem Solving", "Communication", "Stakeholder Management",
    "Agile", "Scrum", "JIRA", "Confluence", "Project Management",
    "Product Analytics", "Customer Analytics", "Risk Analytics",
    "Fraud Detection", "Supply Chain Analytics"
]

# ─────────────────────────────────────────────────────────────────────────────
# COMBINED MASTER LIST — Used for all skill extraction operations
# Using a set for O(1) lookup performance during text matching
# ─────────────────────────────────────────────────────────────────────────────
ALL_SKILLS = list(set(
    PROGRAMMING_SKILLS + ML_SKILLS + LIBRARY_SKILLS +
    DATA_ENGINEERING_SKILLS + DATABASE_SKILLS + CLOUD_SKILLS +
    BI_SKILLS + STATS_SKILLS + DOMAIN_SKILLS
))

# Sort alphabetically for consistent ordering
ALL_SKILLS.sort()

# Create a lowercase mapping for case-insensitive matching
# Maps lowercase skill name → proper case skill name
SKILLS_LOOKUP = {skill.lower(): skill for skill in ALL_SKILLS}


def get_all_skills():
    """Return the complete list of all tracked skills."""
    return ALL_SKILLS


def get_skills_by_category():
    """Return skills organized by category as a dictionary."""
    return {
        "Programming Languages": PROGRAMMING_SKILLS,
        "Machine Learning & AI": ML_SKILLS,
        "Libraries & Frameworks": LIBRARY_SKILLS,
        "Data Engineering": DATA_ENGINEERING_SKILLS,
        "Databases": DATABASE_SKILLS,
        "Cloud & DevOps": CLOUD_SKILLS,
        "BI & Visualization": BI_SKILLS,
        "Statistics & Mathematics": STATS_SKILLS,
        "Domain & Soft Skills": DOMAIN_SKILLS
    }


def extract_skills_from_text(text):
    """
    Extract skills from a given text (job description or resume).
    
    Uses case-insensitive matching against the master skills list.
    Also handles multi-word skills and common abbreviations.
    
    Args:
        text (str): The text to extract skills from
        
    Returns:
        list: Sorted list of unique skills found in the text
    """
    if not text:
        return []
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in ALL_SKILLS:
        skill_lower = skill.lower()
        # Check if the skill appears in the text
        # Use word boundary-aware matching for short skills to avoid false positives
        if len(skill_lower) <= 2:
            # For very short skills like "R", require word boundaries
            import re
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        else:
            if skill_lower in text_lower:
                found_skills.add(skill)
    
    return sorted(list(found_skills))


if __name__ == "__main__":
    print(f"Total unique skills tracked: {len(ALL_SKILLS)}")
    print("\nSkills by category:")
    for category, skills in get_skills_by_category().items():
        print(f"  {category}: {len(skills)} skills")
    
    # Test skill extraction
    sample_text = """
    Looking for a Data Scientist with expertise in Python, Machine Learning,
    and Deep Learning. Must know TensorFlow, PyTorch, and SQL. Experience
    with AWS and Docker is a plus. Strong Statistics background required.
    """
    extracted = extract_skills_from_text(sample_text)
    print(f"\nExtracted skills from sample: {extracted}")
