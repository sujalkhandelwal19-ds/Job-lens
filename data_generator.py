"""
JobLens — Dummy Data Generator
================================
Generates 1500 realistic Indian job postings across 15 diverse tech roles.

WHY THIS EXISTS:
Live scraping of job portals (Naukri, Indeed) is often blocked by anti-bot
measures. This generator creates a realistic dataset that mirrors actual
Indian job market patterns, ensuring the platform always has data to work with.

The generated data includes realistic:
- Indian company names (TCS, Infosys, startups, etc.)
- Indian cities with proper distribution (Bangalore gets more tech jobs)
- Salary ranges in LPA that correlate with experience and company tier
- Skills that are realistic for each role type
- Job descriptions that read like actual postings
"""

import random
import sqlite3
import csv
import os
import sys
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# Add project root to path so we can import from data/
# ─────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.master_skills import ALL_SKILLS

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — All the building blocks for realistic data
# 15 DIVERSE JOB ROLES covering the full Indian tech market
# ─────────────────────────────────────────────────────────────────────────────

JOB_ROLES = {
    "Data Scientist": {
        "base_skills": ["Python", "Machine Learning", "Statistics", "SQL"],
        "optional_skills": ["Deep Learning", "TensorFlow", "PyTorch", "NLP",
                          "Computer Vision", "Scikit-Learn", "Pandas", "NumPy",
                          "Feature Engineering", "A/B Testing", "R",
                          "Hypothesis Testing", "PySpark", "AWS", "Docker",
                          "Generative AI", "LLM", "Hugging Face"],
        "exp_range": (1, 12),
        "salary_multiplier": 1.3
    },
    "Data Analyst": {
        "base_skills": ["SQL", "Excel", "Data Analysis", "Data Visualization"],
        "optional_skills": ["Python", "Tableau", "Power BI", "Statistics",
                          "Google Sheets", "Advanced Excel", "R", "Pandas",
                          "Matplotlib", "Seaborn", "Google Data Studio",
                          "Business Analysis", "Reporting", "DAX"],
        "exp_range": (0, 8),
        "salary_multiplier": 0.9
    },
    "ML Engineer": {
        "base_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow"],
        "optional_skills": ["PyTorch", "Docker", "Kubernetes", "AWS",
                          "MLOps", "Model Deployment", "Scikit-Learn",
                          "Computer Vision", "NLP", "Spark", "Kafka",
                          "CI/CD", "Git", "REST API", "Flask", "FastAPI",
                          "Generative AI", "LLM", "Fine Tuning", "RAG"],
        "exp_range": (2, 10),
        "salary_multiplier": 1.4
    },
    "Business Analyst": {
        "base_skills": ["Excel", "SQL", "Business Analysis", "Communication"],
        "optional_skills": ["Tableau", "Power BI", "Data Analysis",
                          "Stakeholder Management", "Agile", "JIRA",
                          "Python", "Statistics", "Reporting",
                          "Product Analytics", "Customer Analytics",
                          "Google Sheets", "Confluence", "Scrum"],
        "exp_range": (0, 10),
        "salary_multiplier": 0.85
    },
    "Python Developer": {
        "base_skills": ["Python", "Git", "SQL", "REST API"],
        "optional_skills": ["Django", "Flask", "FastAPI", "Docker",
                          "PostgreSQL", "MongoDB", "Redis", "AWS",
                          "CI/CD", "Linux", "Microservices",
                          "Kubernetes", "JavaScript",
                          "API Development", "Selenium"],
        "exp_range": (0, 8),
        "salary_multiplier": 1.0
    },
    "SQL Developer": {
        "base_skills": ["SQL", "Database Design", "Query Optimization"],
        "optional_skills": ["MySQL", "PostgreSQL", "SQL Server", "Oracle",
                          "Python", "ETL", "Data Warehousing", "Data Modeling",
                          "Power BI", "Tableau", "Excel", "Reporting",
                          "MongoDB", "NoSQL", "Hive", "Snowflake"],
        "exp_range": (1, 8),
        "salary_multiplier": 0.85
    },
    "Power BI Developer": {
        "base_skills": ["Power BI", "SQL", "DAX", "Data Visualization"],
        "optional_skills": ["Excel", "Power Query", "Azure", "Python",
                          "Tableau", "ETL", "Data Modeling", "Reporting",
                          "Dashboard Development", "Business Intelligence",
                          "Advanced Excel", "VBA", "SQL Server", "Snowflake"],
        "exp_range": (1, 7),
        "salary_multiplier": 0.9
    },
    "Full Stack Developer": {
        "base_skills": ["JavaScript", "Python", "Git", "REST API"],
        "optional_skills": ["React", "Node.js", "TypeScript", "Django",
                          "Flask", "MongoDB", "PostgreSQL", "Docker",
                          "AWS", "CI/CD", "Redis", "Linux",
                          "HTML", "CSS", "GraphQL", "Kubernetes",
                          "Microservices", "API Development"],
        "exp_range": (1, 10),
        "salary_multiplier": 1.15
    },
    "DevOps Engineer": {
        "base_skills": ["Docker", "Kubernetes", "CI/CD", "Linux"],
        "optional_skills": ["AWS", "Azure", "GCP", "Terraform",
                          "Jenkins", "Git", "Python", "Bash",
                          "Ansible", "Prometheus", "Grafana",
                          "Shell Scripting", "Microservices",
                          "Cloud Computing", "Kafka"],
        "exp_range": (2, 10),
        "salary_multiplier": 1.25
    },
    "Data Engineer": {
        "base_skills": ["Python", "SQL", "ETL", "Spark"],
        "optional_skills": ["Hadoop", "Kafka", "Airflow", "AWS",
                          "Azure", "Snowflake", "Databricks",
                          "Data Pipeline", "Data Warehousing", "Hive",
                          "Docker", "PySpark", "Scala",
                          "Data Lake", "dbt", "PostgreSQL"],
        "exp_range": (2, 10),
        "salary_multiplier": 1.2
    },
    "Java Developer": {
        "base_skills": ["Java", "SQL", "Git", "REST API"],
        "optional_skills": ["Spring Boot", "Microservices", "Docker",
                          "Kubernetes", "AWS", "MongoDB", "PostgreSQL",
                          "Redis", "Kafka", "CI/CD", "Maven",
                          "Hibernate", "JUnit", "Linux",
                          "Oracle", "Jenkins"],
        "exp_range": (0, 10),
        "salary_multiplier": 1.05
    },
    "Frontend Developer": {
        "base_skills": ["JavaScript", "HTML", "CSS", "Git"],
        "optional_skills": ["React", "Angular", "Vue.js", "TypeScript",
                          "Node.js", "Sass", "Webpack", "Redux",
                          "REST API", "GraphQL", "Figma",
                          "Jest", "Tailwind CSS", "Next.js",
                          "Responsive Design", "UI/UX"],
        "exp_range": (0, 8),
        "salary_multiplier": 0.95
    },
    "Cloud Engineer": {
        "base_skills": ["AWS", "Cloud Computing", "Linux", "Docker"],
        "optional_skills": ["Azure", "GCP", "Kubernetes", "Terraform",
                          "CI/CD", "Python", "Shell Scripting",
                          "Networking", "Security", "Ansible",
                          "CloudFormation", "Serverless",
                          "Microservices", "Jenkins", "Git"],
        "exp_range": (2, 10),
        "salary_multiplier": 1.3
    },
    "Cybersecurity Analyst": {
        "base_skills": ["Linux", "Python", "Networking", "Security"],
        "optional_skills": ["AWS", "Azure", "Ethical Hacking",
                          "Penetration Testing", "SIEM", "Firewall",
                          "Incident Response", "SOC", "OWASP",
                          "Bash", "Shell Scripting", "Docker",
                          "Vulnerability Assessment", "Risk Analytics",
                          "Compliance", "Encryption"],
        "exp_range": (1, 10),
        "salary_multiplier": 1.2
    },
    "QA Engineer": {
        "base_skills": ["Selenium", "SQL", "Git", "Python"],
        "optional_skills": ["Java", "Jenkins", "JIRA", "Agile",
                          "REST API", "Postman", "Cucumber",
                          "TestNG", "JUnit", "CI/CD", "Docker",
                          "Performance Testing", "API Development",
                          "Linux", "Automation Testing"],
        "exp_range": (0, 8),
        "salary_multiplier": 0.85
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# COMPANIES — Categorized by tier for salary calculation
# ─────────────────────────────────────────────────────────────────────────────
COMPANIES = {
    "top": [
        "Google India", "Microsoft India", "Amazon India", "Meta India",
        "Apple India", "Goldman Sachs", "Morgan Stanley", "JP Morgan",
        "Uber India", "Flipkart", "PhonePe", "Razorpay", "CRED",
        "Zerodha", "Atlassian India", "Adobe India", "Oracle India",
        "Salesforce India", "Netflix India", "LinkedIn India"
    ],
    "mid": [
        "TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra",
        "Cognizant", "Accenture India", "Capgemini India", "Deloitte India",
        "EY India", "KPMG India", "PwC India", "IBM India",
        "Paytm", "Zomato", "Swiggy", "MakeMyTrip", "PolicyBazaar",
        "Byju's", "Ola", "Dream11", "Meesho", "Groww", "upGrad",
        "Nykaa", "CarDekho", "1mg", "Freshworks"
    ],
    "small": [
        "HDFC Bank", "ICICI Bank", "Axis Bank", "SBI", "Kotak Mahindra",
        "Reliance Jio", "Airtel", "Vodafone Idea", "Tata Motors",
        "Mahindra & Mahindra", "L&T Infotech", "Mphasis", "Mindtree",
        "Persistent Systems", "NIIT Technologies", "Hexaware",
        "Zensar Technologies", "Cyient", "Birlasoft", "Sonata Software",
        "DataWeave", "Sigmoid", "Tiger Analytics", "Fractal Analytics",
        "LatentView Analytics", "MuSigma", "AbsolutData", "Gramener",
        "Celebal Technologies", "Quantiphi"
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# INDIAN CITIES — With probability weights reflecting actual job distribution
# ─────────────────────────────────────────────────────────────────────────────
CITIES = {
    "Bangalore": 0.25,
    "Mumbai": 0.15,
    "Hyderabad": 0.14,
    "Pune": 0.12,
    "Delhi NCR": 0.10,
    "Chennai": 0.08,
    "Kolkata": 0.04,
    "Ahmedabad": 0.03,
    "Jaipur": 0.02,
    "Kochi": 0.02,
    "Indore": 0.02,
    "Chandigarh": 0.01,
    "Coimbatore": 0.01,
    "Remote": 0.01,
}

# ─────────────────────────────────────────────────────────────────────────────
# BASE SALARIES — In LPA (Lakhs Per Annum), indexed by experience level
# ─────────────────────────────────────────────────────────────────────────────
BASE_SALARY_BY_EXPERIENCE = {
    (0, 1): (3, 6),
    (1, 3): (5, 12),
    (3, 5): (8, 18),
    (5, 8): (12, 28),
    (8, 12): (20, 45),
    (12, 20): (30, 60),
}

COMPANY_SALARY_MULTIPLIER = {
    "top": 1.5,
    "mid": 1.0,
    "small": 0.85
}

# ─────────────────────────────────────────────────────────────────────────────
# JOB DESCRIPTION TEMPLATES — Generic template that works for ALL roles
# Uses a role-aware format so we only need one universal template set
# ─────────────────────────────────────────────────────────────────────────────
JD_TEMPLATES = [
    "We are looking for a passionate {role} to join our {team} team at {company}. "
    "You will work on {project} using cutting-edge technologies. "
    "The ideal candidate will have {exp} years of experience and "
    "strong proficiency in {skills}. Experience with {extra_skills} is a plus. "
    "This role offers competitive compensation and the opportunity to work on "
    "real-world problems in {domain}.",

    "{company} is hiring a {role} for our {team} department. "
    "You should have {exp} years of experience with {skills}. "
    "You will be responsible for building solutions, collaborating with teams, "
    "and driving impact. Knowledge of {extra_skills} is preferred. "
    "Join us and help shape the future of {domain}.",

    "Join {company} as a {role} and make an impact. "
    "We need someone with {exp} years of experience who excels at {skills}. "
    "You'll work closely with cross-functional teams on {project}. "
    "Familiarity with {extra_skills} is highly desirable. "
    "Our {team} team works on exciting challenges in {domain}.",

    "As a {role} at {company}, you will develop and maintain critical systems. "
    "We need {exp} years of experience in {skills}. You'll design, build, "
    "and optimize solutions for our {project}. "
    "Knowledge of {extra_skills} is expected. Our {team} team works on "
    "exciting initiatives in the {domain} space.",
]

TEAMS = ["Analytics", "Data", "Engineering", "Product", "Technology", "AI/ML",
         "Business Intelligence", "Research", "Platform", "Growth",
         "Infrastructure", "Security", "DevOps", "Cloud", "Frontend", "Backend"]

PROJECTS = ["customer analytics platform", "recommendation engine",
            "fraud detection system", "demand forecasting model",
            "real-time analytics dashboard", "data warehouse modernization",
            "AI-powered chatbot", "predictive maintenance system",
            "supply chain optimization", "marketing analytics suite",
            "risk assessment model", "personalization engine",
            "automated reporting system", "data quality framework",
            "NLP-based search engine", "computer vision pipeline",
            "cloud migration initiative", "microservices architecture",
            "CI/CD pipeline modernization", "security monitoring platform",
            "mobile app backend", "e-commerce platform",
            "payment gateway integration", "content delivery system"]

DOMAINS = ["fintech", "e-commerce", "healthcare", "logistics", "edtech",
           "SaaS", "banking", "insurance", "retail", "telecom",
           "automotive", "media", "travel", "food delivery", "real estate",
           "cybersecurity", "cloud services", "enterprise software"]

PORTALS = ["Naukri.com", "Indeed India", "LinkedIn", "Glassdoor"]


def get_company_tier(company_name):
    """Determine the tier of a company based on its name."""
    for tier, companies in COMPANIES.items():
        if company_name in companies:
            return tier
    return "small"


def calculate_salary(exp_min, exp_max, role_multiplier, company_tier):
    """
    Calculate a realistic salary range based on experience, role, and company.

    Formula: base_salary x role_multiplier x company_tier_multiplier x noise
    """
    avg_exp = (exp_min + exp_max) / 2

    base_min, base_max = 3, 6
    for (bracket_min, bracket_max), (sal_min, sal_max) in BASE_SALARY_BY_EXPERIENCE.items():
        if bracket_min <= avg_exp < bracket_max:
            base_min, base_max = sal_min, sal_max
            break
    else:
        if avg_exp >= 12:
            base_min, base_max = 30, 60

    tier_mult = COMPANY_SALARY_MULTIPLIER.get(company_tier, 1.0)
    noise = random.uniform(0.85, 1.15)
    salary_min = round(base_min * role_multiplier * tier_mult * noise, 1)
    salary_max = round(base_max * role_multiplier * tier_mult * noise, 1)

    salary_min = max(2.0, salary_min)
    salary_max = max(salary_min + 1.0, salary_max)

    return salary_min, salary_max


def generate_job_description(role, company, exp_str, skills, extra_skills):
    """Generate a realistic job description from templates."""
    template = random.choice(JD_TEMPLATES)

    return template.format(
        role=role,
        company=company,
        exp=exp_str,
        skills=", ".join(skills[:5]),
        extra_skills=", ".join(extra_skills[:3]) if extra_skills else "related technologies",
        team=random.choice(TEAMS),
        project=random.choice(PROJECTS),
        domain=random.choice(DOMAINS)
    )


def generate_jobs(num_jobs=1500):
    """
    Generate realistic Indian job posting data across 15 diverse roles.

    Ensures broader distribution across all tech roles, not just
    data science positions.

    Args:
        num_jobs (int): Number of job postings to generate (default: 1500)

    Returns:
        list: List of dictionaries, each representing a job posting
    """
    jobs = []

    city_names = list(CITIES.keys())
    city_weights = list(CITIES.values())

    all_companies = []
    for tier, company_list in COMPANIES.items():
        all_companies.extend([(c, tier) for c in company_list])

    # Broader, more even distribution across all 15 roles
    role_weights = {
        "Data Scientist": 0.09,
        "Data Analyst": 0.09,
        "ML Engineer": 0.07,
        "Business Analyst": 0.08,
        "Python Developer": 0.08,
        "SQL Developer": 0.06,
        "Power BI Developer": 0.05,
        "Full Stack Developer": 0.10,
        "DevOps Engineer": 0.07,
        "Data Engineer": 0.07,
        "Java Developer": 0.08,
        "Frontend Developer": 0.06,
        "Cloud Engineer": 0.04,
        "Cybersecurity Analyst": 0.03,
        "QA Engineer": 0.03,
    }
    role_names = list(role_weights.keys())
    role_probs = list(role_weights.values())

    end_date = datetime.now()

    print(f"Generating {num_jobs} realistic job postings across {len(role_names)} roles...")

    for i in range(num_jobs):
        role = random.choices(role_names, weights=role_probs, k=1)[0]
        role_config = JOB_ROLES[role]

        company, company_tier = random.choice(all_companies)
        city = random.choices(city_names, weights=city_weights, k=1)[0]

        # Generate experience range
        exp_min_possible, exp_max_possible = role_config["exp_range"]
        exp_min = random.randint(exp_min_possible, max(exp_min_possible, exp_max_possible - 3))
        exp_max = min(exp_min + random.randint(1, 4), exp_max_possible)

        # Generate skills
        num_optional = random.randint(2, 6)
        optional = random.sample(
            role_config["optional_skills"],
            min(num_optional, len(role_config["optional_skills"]))
        )
        all_job_skills = list(set(role_config["base_skills"] + optional))

        # Calculate salary
        salary_min, salary_max = calculate_salary(
            exp_min, exp_max,
            role_config["salary_multiplier"],
            company_tier
        )

        salary_str = f"{salary_min} - {salary_max} LPA"

        # 20% chance salary is not disclosed
        if random.random() < 0.2:
            salary_str = "Not Disclosed"
            salary_min_val = None
            salary_max_val = None
        else:
            salary_min_val = salary_min
            salary_max_val = salary_max

        days_ago = random.randint(0, 90)
        date_posted = (end_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        exp_str = f"{exp_min}-{exp_max}"
        extra_skills = [s for s in role_config["optional_skills"] if s not in all_job_skills][:3]
        description = generate_job_description(role, company, exp_str, all_job_skills, extra_skills)

        job = {
            "job_title": role,
            "company_name": company,
            "location": city,
            "salary_range": salary_str,
            "salary_min": salary_min_val,
            "salary_max": salary_max_val,
            "required_skills": ", ".join(all_job_skills),
            "experience_required": f"{exp_min}-{exp_max} years",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "job_description": description,
            "date_posted": date_posted,
            "portal_name": random.choice(PORTALS),
            "company_tier": company_tier
        }

        jobs.append(job)

    print(f"Generated {len(jobs)} job postings successfully!")
    return jobs


def save_to_sqlite(jobs, db_path="data/jobs.db"):
    """Save generated jobs to SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            location TEXT,
            salary_range TEXT,
            salary_min REAL,
            salary_max REAL,
            required_skills TEXT,
            experience_required TEXT,
            experience_min INTEGER,
            experience_max INTEGER,
            job_description TEXT,
            date_posted TEXT,
            portal_name TEXT,
            company_tier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("DELETE FROM job_postings")

    for job in jobs:
        cursor.execute("""
            INSERT INTO job_postings
            (job_title, company_name, location, salary_range, salary_min, salary_max,
             required_skills, experience_required, experience_min, experience_max,
             job_description, date_posted, portal_name, company_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["job_title"], job["company_name"], job["location"],
            job["salary_range"], job["salary_min"], job["salary_max"],
            job["required_skills"], job["experience_required"],
            job["experience_min"], job["experience_max"],
            job["job_description"], job["date_posted"],
            job["portal_name"], job["company_tier"]
        ))

    conn.commit()
    conn.close()
    print(f"Saved {len(jobs)} jobs to {db_path}")


def save_to_csv(jobs, csv_path="data/jobs_data.csv"):
    """Save generated jobs to CSV as backup."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    if not jobs:
        print("No jobs to save!")
        return

    fieldnames = jobs[0].keys()

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Saved {len(jobs)} jobs to {csv_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("JobLens - Dummy Data Generator")
    print("=" * 60)

    jobs = generate_jobs(1500)

    save_to_sqlite(jobs)
    save_to_csv(jobs)

    print("\n--- Dataset Summary ---")
    roles = {}
    cities = {}
    for job in jobs:
        roles[job["job_title"]] = roles.get(job["job_title"], 0) + 1
        cities[job["location"]] = cities.get(job["location"], 0) + 1

    print("\nJobs by Role:")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"  {role}: {count}")

    print("\nTop Cities:")
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:8]:
        print(f"  {city}: {count}")

    print("\nData generation complete!")
