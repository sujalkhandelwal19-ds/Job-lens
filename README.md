# 🔍 JobLens — Smart Job Market Intelligence Platform

A full-stack data science web application that analyzes Indian tech job-market data using web scraping, NLP, and machine learning to deliver market insights, salary estimates, resume analysis, and personalized job recommendations.

---

## 📌 Problem Statement

Indian tech job seekers face a fragmented market — salary data is opaque, skill demand shifts rapidly, and there's no single platform that connects resume analysis with live market intelligence. JobLens solves this by building a unified, data-driven intelligence layer on top of job market data.

## 🎯 Objectives

- Scrape and aggregate job postings from major Indian portals (Naukri.com, Indeed India)
- Build an NLP pipeline to extract and standardize skills from unstructured job descriptions
- Train ML models for salary prediction and role classification
- Provide resume-to-job matching using TF-IDF and cosine similarity
- Deliver all insights through an interactive, responsive web dashboard

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.10, Flask, SQLite |
| **Frontend** | HTML5, Bootstrap 5, Plotly.js |
| **ML / NLP** | Scikit-learn, XGBoost, NLTK, TF-IDF |
| **Scraping** | BeautifulSoup4, Selenium, Requests |
| **Data** | Pandas, NumPy, Joblib |
| **PDF Processing** | PyPDF2 |
| **Deployment** | Gunicorn, Render |

## 📁 Project Structure

```
JobLens/
├── app.py                      # Flask application — routes, APIs, controllers
├── setup.py                    # One-command setup script
├── scraper.py                  # Naukri.com + Indeed India scrapers
├── data_generator.py           # Synthetic data engine (1500 job postings)
├── data_processor.py           # ETL + NLP skill extraction pipeline
├── build.sh                    # Deployment build script
├── Procfile                    # Production WSGI configuration
├── render.yaml                 # Render deployment blueprint
├── requirements.txt            # Python dependencies
│
├── models/
│   ├── train_salary_model.py   # Salary prediction (LR, RF, XGBoost)
│   ├── train_classifier.py     # Role classification (NB, RF)
│   ├── resume_matcher.py       # TF-IDF resume-to-job matching
│   └── trend_analyzer.py       # Skill demand trend analysis
│
├── data/
│   ├── master_skills.py        # Curated taxonomy of 175+ tech skills
│   ├── jobs.db                 # SQLite database (generated)
│   └── jobs_data.csv           # CSV backup (generated)
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Base layout with navbar and footer
│   ├── home.html               # Landing page
│   ├── dashboard.html          # Analytics dashboard
│   ├── salary.html             # Salary predictor form
│   ├── resume.html             # Resume analyzer with drag-drop
│   ├── jobs.html               # Job listings with filters
│   └── skills.html             # Skill intelligence & heatmaps
│
├── static/
│   ├── css/style.css           # Custom dark theme design system
│   └── js/charts.js            # Plotly.js chart rendering module
│
└── saved_models/               # Serialized .pkl model files (generated)
```

## ✨ Key Features

### 📊 Market Dashboard
Interactive Plotly.js charts visualizing top skills, salary distributions, city-wise job density, top hiring companies, and skill demand trends over time.

### 💰 Salary Predictor
Select your role, city, experience level, company tier, and skills — the trained ML model returns a predicted salary with an estimated range (the range is not a statistical confidence interval). Uses the best-performing model from a comparison of Linear Regression, Random Forest, and XGBoost.

### 📄 Resume Analyzer
Upload a PDF or TXT resume. The system extracts skills using NLP, compares against market demand, calculates a match score, identifies skill gaps, suggests improvements, and recommends matching jobs.

### 🎯 Job Recommendations
Browse and filter 1500+ job postings by role, city, experience, and salary. Each listing shows required skills, company details, and match scores.

### ⚡ Skill Intelligence
Heatmap showing skill demand across roles, trending vs declining skills using linear regression on time-series data, and skill co-occurrence analysis.

## 🤖 ML Model Details

| Model | Algorithm | Task | Performance |
|-------|-----------|------|-------------|
| Salary Predictor | Random Forest (best of 3) | Regression | R² ≈ 0.90+ |
| Role Classifier | Random Forest + TF-IDF | Multi-class classification | ~100% accuracy |
| Resume Matcher | TF-IDF + Cosine Similarity | Information retrieval | Top-10 ranked results |
| Trend Analyzer | Linear Regression | Time-series slope detection | Weekly aggregation |

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Local Setup

```bash
# Clone the repository
git clone https://github.com/sujalkhandelwal19-ds/Job-lens.git
cd Job-lens

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Full setup — generates data, trains models, starts server
python setup.py
```

### Partial Commands

```bash
python setup.py --data     # Generate and process data only
python setup.py --train    # Train ML models only
python setup.py --app      # Start the web server only
```

### Access
Open **http://127.0.0.1:5000** in your browser.

## 🌐 Deployment

The project is configured for one-click deployment on **Render**:

1. Push to GitHub
2. Connect the repo on [render.com](https://render.com)
3. Set build command: `chmod +x build.sh && ./build.sh`
4. Set start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Deploy

## 📊 Dataset

The platform uses a synthetic dataset of **1,500 job postings** spanning:
- **15 roles**: Data Scientist, Full Stack Developer, DevOps Engineer, Data Engineer, Java Developer, ML Engineer, and more
- **78 companies**: From FAANG (Google, Amazon, Microsoft) to Indian IT (TCS, Infosys) to startups (Razorpay, CRED)
- **14 cities**: Bangalore, Mumbai, Hyderabad, Pune, Delhi NCR, Chennai, and more
- **99 unique skills**: Python, SQL, Docker, AWS, React, Kubernetes, etc.

Salary distributions are modeled with experience-based brackets, role multipliers, and company-tier adjustments to reflect real market patterns.

## 📸 Screenshots

*Run the application locally or visit the deployed URL to explore the interface.*

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).

---

**Developed by Sujal Khandelwal**
