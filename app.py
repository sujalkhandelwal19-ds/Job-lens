"""
JobLens — Main Flask Application
===================================
Central web application that ties all modules together:
- Routes for all pages (dashboard, salary, resume, jobs, skills)
- API endpoints for chart data
- File upload handling for resume analysis
- Integration with ML models for predictions

ARCHITECTURE:
All heavy computation (model training, data processing) happens
during setup. The Flask app loads pre-trained models and serves
predictions in real-time.
"""

import os
import sys
import sqlite3
import json
import traceback
from collections import Counter

import pandas as pd
import numpy as np
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify)

# ─── Add project root to path ────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from data.master_skills import (extract_skills_from_text, ALL_SKILLS,
                                get_skills_by_category)

# ─── PDF text extraction ─────────────────────────────────────────
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# ─── ML model imports ────────────────────────────────────────────
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

# ─── Flask App Setup ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'saved_models'), exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_db():
    """Get a database connection with row factory."""
    db_path = os.path.join(BASE_DIR, 'data', 'jobs.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_jobs_df():
    """Load all jobs as a DataFrame."""
    db_path = os.path.join(BASE_DIR, 'data', 'jobs.db')
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM job_postings", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def get_top_skills(df, n=10):
    """Get the top N most demanded skills."""
    all_skills = []
    for s in df['required_skills'].dropna():
        all_skills.extend([x.strip() for x in str(s).split(',') if x.strip()])
    return Counter(all_skills).most_common(n)


def extract_resume_text(file):
    """Extract text from uploaded resume file (PDF or TXT)."""
    filename = file.filename.lower()

    if filename.endswith('.txt'):
        return file.read().decode('utf-8', errors='ignore')

    if filename.endswith('.pdf') and PYPDF2_AVAILABLE:
        try:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return text
        except Exception as e:
            return f"ERROR: Could not read PDF — {str(e)}"

    return "ERROR: Unsupported file format. Please upload PDF or TXT."


# ═══════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    """Landing page with platform overview and stats."""
    try:
        df = get_jobs_df()
        stats = {
            'total_jobs': f"{len(df):,}" if len(df) > 0 else "1,000+",
            'total_companies': str(df['company_name'].nunique()) if len(df) > 0 else "75+",
            'total_skills': str(len(ALL_SKILLS)),
            'total_cities': str(df['location'].nunique()) if len(df) > 0 else "14"
        }
    except Exception:
        stats = {}
    return render_template('home.html', stats=stats)


@app.route('/dashboard')
def dashboard():
    """Market insights dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/market-stats')
def api_market_stats():
    """
    JSON API endpoint providing all dashboard chart data.
    Called by charts.js via fetch() on dashboard page load.
    """
    try:
        df = get_jobs_df()
        if df.empty:
            return jsonify({'error': 'No data available. Run setup first.'})

        # Top 10 skills
        top_skills_data = get_top_skills(df, 10)
        top_skills = [{'skill': s, 'count': int(c)} for s, c in top_skills_data]

        # Avg salary by role
        salary_df = df.dropna(subset=['salary_min', 'salary_max']).copy()
        salary_df['salary_avg'] = (salary_df['salary_min'] + salary_df['salary_max']) / 2
        salary_by_role = salary_df.groupby('job_title')['salary_avg'].mean().sort_values(ascending=False)
        salary_data = [{'role': r, 'avg_salary': round(float(s), 1)}
                       for r, s in salary_by_role.items()]

        # Jobs by city
        city_counts = df['location'].value_counts().head(12)
        city_data = [{'city': c, 'count': int(n)} for c, n in city_counts.items()]

        # Top hiring companies
        company_counts = df['company_name'].value_counts().head(10)
        company_data = [{'company': c, 'count': int(n)} for c, n in company_counts.items()]

        # Skill trends
        try:
            from models.trend_analyzer import get_skill_trend_data
            trend_data = get_skill_trend_data()
        except Exception:
            trend_data = {'weeks': [], 'skills': {}}

        # Summary metrics
        overall_top_skills = get_top_skills(df, 1)
        summary = {
            'total_jobs': len(df),
            'avg_salary': round(float(salary_df['salary_avg'].mean()), 1) if len(salary_df) > 0 else 0,
            'top_skill': overall_top_skills[0][0] if overall_top_skills else 'N/A',
            'top_city': df['location'].value_counts().index[0] if len(df) > 0 else 'N/A'
        }

        # Recent jobs (last 20)
        recent = df.sort_values('date_posted', ascending=False).head(20)
        recent_jobs = recent[['job_title', 'company_name', 'location',
                              'salary_range', 'experience_required', 'date_posted']].to_dict('records')

        return jsonify({
            'top_skills': top_skills,
            'salary_by_role': salary_data,
            'jobs_by_city': city_data,
            'top_companies': company_data,
            'skill_trends': trend_data,
            'summary': summary,
            'recent_jobs': recent_jobs
        })

    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/salary-predictor')
def salary_predictor():
    """Salary prediction form page."""
    df = get_jobs_df()
    roles = sorted(df['job_title'].unique().tolist()) if len(df) > 0 else []
    cities = sorted(df['location'].unique().tolist()) if len(df) > 0 else []

    # Popular skills for the checkbox grid
    popular = [s for s, _ in get_top_skills(df, 24)] if len(df) > 0 else ALL_SKILLS[:24]

    return render_template('salary.html', roles=roles, cities=cities,
                           popular_skills=popular, result=None)


@app.route('/predict-salary', methods=['POST'])
def predict_salary():
    """Process salary prediction form submission."""
    df = get_jobs_df()
    roles = sorted(df['job_title'].unique().tolist()) if len(df) > 0 else []
    cities = sorted(df['location'].unique().tolist()) if len(df) > 0 else []
    popular = [s for s, _ in get_top_skills(df, 24)] if len(df) > 0 else ALL_SKILLS[:24]

    try:
        job_title = request.form.get('job_title', '')
        location = request.form.get('location', '')
        experience = int(request.form.get('experience', 3))
        company_tier = request.form.get('company_tier', 'mid')
        selected_skills = request.form.getlist('skills')
        skills_count = max(len(selected_skills), 1)

        # Try ML model prediction
        model_path = os.path.join(BASE_DIR, 'saved_models', 'salary_model.pkl')
        encoders_path = os.path.join(BASE_DIR, 'saved_models', 'encoders.pkl')

        if os.path.exists(model_path) and os.path.exists(encoders_path) and JOBLIB_AVAILABLE:
            from models.train_salary_model import predict_salary as ml_predict
            result = ml_predict(job_title, experience, location, skills_count, company_tier)
        else:
            # Fallback: statistical estimate from data
            filtered = df[df['job_title'] == job_title].dropna(subset=['salary_min', 'salary_max'])
            if len(filtered) > 0:
                filtered = filtered.copy()
                filtered['salary_avg'] = (filtered['salary_min'] + filtered['salary_max']) / 2
                avg_sal = filtered['salary_avg'].mean()
                exp_factor = 1 + (experience * 0.08)
                tier_factor = {'top': 1.5, 'mid': 1.0, 'small': 0.85}.get(company_tier, 1.0)
                predicted = avg_sal * exp_factor * tier_factor * (1 + skills_count * 0.01)
                predicted = max(0, predicted)
                result = {
                    'predicted_salary': round(predicted, 1),
                    'salary_min': round(predicted * 0.85, 1),
                    'salary_max': round(predicted * 1.15, 1),
                    'unit': 'LPA',
                    'confidence': 'Estimated from market data (fallback statistical estimate)'
                }
            else:
                result = {'error': 'Not enough data for this role. Try another role.'}

    except Exception as e:
        result = {'error': f'Prediction error: {str(e)}'}

    return render_template('salary.html', roles=roles, cities=cities,
                           popular_skills=popular, result=result)


@app.route('/resume-analyzer')
def resume_analyzer():
    """Resume upload page."""
    return render_template('resume.html', result=None)


@app.route('/analyze-resume', methods=['POST'])
def analyze_resume():
    """Process uploaded resume and return comprehensive analysis."""
    try:
        file = request.files.get('resume')
        if not file or file.filename == '':
            return render_template('resume.html',
                                   result={'error': 'Please select a file to upload.'})

        # Extract text from resume
        resume_text = extract_resume_text(file)
        if resume_text.startswith('ERROR:'):
            return render_template('resume.html', result={'error': resume_text})

        if len(resume_text.strip()) < 50:
            return render_template('resume.html',
                                   result={'error': 'Could not extract enough text from resume. Try a different file.'})

        # Extract skills from resume
        resume_skills = set(extract_skills_from_text(resume_text))

        # Get market demand data
        df = get_jobs_df()
        top_market_skills = get_top_skills(df, 30)
        top_market_set = set(s for s, _ in top_market_skills)

        # Calculate matches and gaps
        matched = sorted(resume_skills & top_market_set)
        gaps = sorted(top_market_set - resume_skills)
        low_priority = sorted(resume_skills - top_market_set)

        # Match score: percentage of top market skills found in resume
        score = round((len(matched) / max(len(top_market_set), 1)) * 100)
        score = min(score, 100)

        # Recommend roles based on skills
        recommended_roles = _get_role_recommendations(resume_skills, df)

        # Get top matching jobs via TF-IDF
        top_jobs = _get_matching_jobs(resume_text)

        # Generate improvement suggestions
        suggestions = _generate_suggestions(matched, gaps, score)

        result = {
            'match_score': score,
            'matched_skills': list(matched),
            'skill_gaps': list(gaps),
            'low_priority_skills': list(low_priority),
            'recommended_roles': recommended_roles,
            'top_jobs': top_jobs,
            'suggestions': suggestions,
            'total_resume_skills': len(resume_skills)
        }

        return render_template('resume.html', result=result)

    except Exception as e:
        traceback.print_exc()
        return render_template('resume.html',
                               result={'error': f'Analysis failed: {str(e)}'})


def _get_role_recommendations(resume_skills, df):
    """Determine which roles best match the candidate's skills."""
    role_scores = []
    for role in df['job_title'].unique():
        role_df = df[df['job_title'] == role]
        role_skills_list = []
        for s in role_df['required_skills'].dropna():
            role_skills_list.extend([x.strip() for x in str(s).split(',') if x.strip()])
        role_skill_set = set(role_skills_list)
        if role_skill_set:
            overlap = len(resume_skills & role_skill_set)
            score = round((overlap / len(role_skill_set)) * 100)
            role_scores.append({'role': role, 'score': score})

    role_scores.sort(key=lambda x: -x['score'])
    return role_scores[:5]


def _get_matching_jobs(resume_text):
    """Use the trained TF-IDF matcher to find top matching jobs."""
    try:
        from models.resume_matcher import match_resume
        matches = match_resume(resume_text, top_n=10)
        if isinstance(matches, list):
            return matches
    except Exception:
        pass
    return []


def _generate_suggestions(matched, gaps, score):
    """Generate personalized improvement suggestions."""
    suggestions = []
    if score >= 80:
        suggestions.append("🎉 Excellent! Your skills strongly align with market demand.")
    elif score >= 50:
        suggestions.append("👍 Good foundation! Focus on filling the skill gaps below to stand out.")
    else:
        suggestions.append("📚 Consider upskilling in high-demand areas to improve your marketability.")

    if gaps:
        top_gaps = gaps[:3]
        suggestions.append(f"🎯 Priority skills to learn: {', '.join(top_gaps)}")

    high_value = {'Python', 'SQL', 'Machine Learning', 'AWS', 'Docker'}
    missing_hv = high_value - set(matched)
    if missing_hv:
        suggestions.append(f"💡 High-value skills you're missing: {', '.join(sorted(missing_hv)[:3])}")

    if 'Python' in matched and 'Machine Learning' in matched:
        suggestions.append("🚀 With Python + ML, consider learning Deep Learning or MLOps for senior roles.")

    suggestions.append("📝 Tailor your resume keywords to match job descriptions for better ATS scores.")
    return suggestions


@app.route('/job-recommendations')
def job_recommendations():
    """Job listings page with filters."""
    df = get_jobs_df()
    roles = sorted(df['job_title'].unique().tolist()) if len(df) > 0 else []
    cities = sorted(df['location'].unique().tolist()) if len(df) > 0 else []

    # Apply filters
    selected_role = request.args.get('role', '')
    selected_city = request.args.get('city', '')
    selected_exp_min = request.args.get('exp_min', '')
    selected_salary_max = request.args.get('salary_max', '')

    filtered = df.copy()
    if selected_role:
        filtered = filtered[filtered['job_title'] == selected_role]
    if selected_city:
        filtered = filtered[filtered['location'] == selected_city]
    if selected_exp_min:
        try:
            filtered = filtered[filtered['experience_min'] >= int(selected_exp_min)]
        except (ValueError, KeyError):
            pass
    if selected_salary_max:
        try:
            filtered = filtered[filtered['salary_max'] <= float(selected_salary_max)]
        except (ValueError, KeyError):
            pass

    # Limit to 50 for performance
    jobs = filtered.head(50).to_dict('records')

    return render_template('jobs.html', jobs=jobs, roles=roles, cities=cities,
                           selected_role=selected_role, selected_city=selected_city,
                           selected_exp_min=selected_exp_min,
                           selected_salary_max=selected_salary_max)


@app.route('/skill-gap')
def skill_gap():
    """Skill intelligence and gap analysis page."""
    df = get_jobs_df()

    # Build heatmap data: skills × roles
    roles = sorted(df['job_title'].unique().tolist())
    top_skills_list = [s for s, _ in get_top_skills(df, 15)]

    heatmap_values = []
    for role in roles:
        role_df = df[df['job_title'] == role]
        row = []
        for skill in top_skills_list:
            count = role_df['required_skills'].apply(
                lambda x: skill.lower() in str(x).lower() if pd.notna(x) else False
            ).sum()
            row.append(int(count))
        heatmap_values.append(row)

    heatmap_data = {'roles': roles, 'skills': top_skills_list, 'values': heatmap_values}

    # Co-occurrence matrix
    try:
        from data_processor import compute_skill_cooccurrence
        cooc = compute_skill_cooccurrence(df, top_n=12)
        cooccurrence_data = {
            'labels': cooc.columns.tolist(),
            'values': cooc.values.tolist()
        }
    except Exception:
        cooccurrence_data = {'labels': [], 'values': []}

    # Trending skills
    try:
        from models.trend_analyzer import get_trending_skills
        trends = get_trending_skills()
        trending = trends.get('trending', [])
        declining = trends.get('declining', [])
        stable = trends.get('stable', [])
    except Exception:
        trending, declining, stable = [], [], []

    return render_template('skills.html', heatmap_data=heatmap_data,
                           cooccurrence_data=cooccurrence_data,
                           trending=trending, declining=declining, stable=stable)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("🔍 JobLens — Smart Job Market Intelligence Platform")
    print("=" * 60)
    print(f"Server starting at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=5000)
