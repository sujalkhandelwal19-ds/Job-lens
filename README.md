# 🔍 JobLens — Smart Job Market Intelligence Platform

> An AI-powered platform for Indian tech job seekers to analyze live job market data, predict salaries, identify skill gaps, and get personalized job recommendations.

---

## 📋 Project Overview

**JobLens** solves a real problem for Indian job seekers by providing data-driven insights into the tech job market. Instead of manually browsing hundreds of job listings, candidates can:

- **See real-time market trends** — Which skills are hot, which are fading
- **Predict their salary** — ML models trained on 1000+ job postings
- **Analyze their resume** — Identify skill gaps vs market demand
- **Get job recommendations** — TF-IDF + cosine similarity matching
- **Track skill trends** — Know what to learn next

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Market Dashboard** | Interactive Plotly charts showing top skills, salaries, hiring trends |
| 💰 **Salary Predictor** | ML model predicting salary based on role, experience, location, skills |
| 📄 **Resume Analyzer** | Upload PDF/TXT resume, get skill gap analysis and match score |
| 🎯 **Job Recommendations** | Smart matching using TF-IDF and cosine similarity |
| ⚡ **Skill Intelligence** | Demand heatmaps, trending/declining skills, co-occurrence analysis |
| 🕷️ **Web Scraping** | BeautifulSoup + Selenium scrapers for Naukri.com and Indeed India |
| 🤖 **4 ML Models** | Salary predictor, role classifier, resume matcher, trend analyzer |

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, Flask
- **Frontend:** HTML5, Bootstrap 5, Plotly.js
- **ML/AI:** Scikit-learn, XGBoost, NLTK
- **Data:** Pandas, NumPy, SQLite
- **Scraping:** BeautifulSoup4, Selenium
- **PDF Processing:** PyPDF2
- **Visualization:** Plotly.js (frontend), Matplotlib (backend)

## 📁 Project Structure

```
JobLens/
├── app.py                  # Main Flask application
├── setup.py                # One-click setup script
├── scraper.py              # Web scraping (Naukri + Indeed)
├── data_generator.py       # Realistic dummy data generator
├── data_processor.py       # Data cleaning & NLP pipeline
├── models/
│   ├── train_salary_model.py   # Salary prediction (LR, RF, XGBoost)
│   ├── train_classifier.py     # Role classification (NB, RF)
│   ├── resume_matcher.py       # TF-IDF resume matching
│   └── trend_analyzer.py       # Skill demand trends
├── saved_models/           # Trained model files (.pkl)
├── data/
│   ├── jobs.db             # SQLite database
│   ├── jobs_data.csv       # CSV backup
│   └── master_skills.py    # 150+ skills taxonomy
├── templates/              # Jinja2 HTML templates
│   ├── base.html, home.html, dashboard.html
│   ├── salary.html, resume.html, jobs.html, skills.html
├── static/
│   ├── css/style.css       # Premium dark theme CSS
│   └── js/charts.js        # Plotly chart rendering
├── requirements.txt
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Quick Start

```bash
# 1. Clone or navigate to the project
cd JobLens

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run complete setup (generates data, trains models, starts app)
python setup.py
```

### Partial Setup Options

```bash
python setup.py --data    # Only generate and process data
python setup.py --train   # Only train ML models
python setup.py --app     # Only start web app (data must exist)
```

### Access the Application
Open **http://127.0.0.1:5000** in your browser after starting the server.

## 📊 ML Models

### Model 1: Salary Predictor
- **Algorithms:** Linear Regression, Random Forest, XGBoost
- **Features:** Job title, experience, location, skills count, company tier
- **Metrics:** MAE, RMSE, R² Score
- **Best model auto-selected** based on R² score

### Model 2: Role Classifier
- **Algorithms:** Multinomial Naive Bayes, Random Forest
- **Features:** TF-IDF vectors from skills text
- **Metrics:** Accuracy, Classification Report, Confusion Matrix

### Model 3: Resume Matcher
- **Method:** TF-IDF Vectorization + Cosine Similarity
- **Returns:** Top 10 matching jobs with similarity percentages

### Model 4: Trend Analyzer
- **Method:** Weekly frequency tracking + Linear Regression
- **Output:** Trending up / declining / stable skills

## 📸 Screenshots

*Screenshots will be added after running the application.*

## 🔮 Future Improvements

- [ ] Real-time scraping with rotating proxies and CAPTCHA solving
- [ ] User accounts and saved resume profiles
- [ ] Email alerts for new matching jobs
- [ ] Integration with LinkedIn API
- [ ] Advanced NLP with BERT/LLM for better skill extraction
- [ ] Salary negotiation advisor based on market data
- [ ] Interview question predictor based on job description
- [ ] Mobile-responsive PWA version

## 📜 License

This project is built for educational and portfolio purposes.

---

**Built with ❤️ using Python, Flask, and Machine Learning**
