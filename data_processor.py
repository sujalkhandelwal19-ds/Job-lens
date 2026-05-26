"""
JobLens — Data Processing & NLP Pipeline
==========================================
Cleans, processes, and enriches raw job posting data.

PIPELINE STAGES:
1. Load raw data from SQLite or CSV
2. Clean and standardize fields (titles, salaries, experience)
3. Extract skills from descriptions using NLP
4. Compute skill frequency statistics
5. Save processed data back to the database

WHY NLP FOR SKILL EXTRACTION:
Job descriptions are unstructured text. We use a combination of
dictionary-based matching (master skills list) and text preprocessing
to reliably extract which skills each job requires, even when they're
mentioned in different formats (e.g., "ML" vs "Machine Learning").
"""

import os
import sys
import re
import sqlite3
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.master_skills import extract_skills_from_text, ALL_SKILLS, SKILLS_LOOKUP

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_data(db_path="data/jobs.db"):
    """
    Load job postings from SQLite database into a Pandas DataFrame.
    
    Falls back to CSV if database is not available.
    
    Args:
        db_path (str): Path to the SQLite database
        
    Returns:
        pd.DataFrame: Job postings data
    """
    try:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT * FROM job_postings", conn)
            conn.close()
            print(f"✓ Loaded {len(df)} jobs from database")
            return df
    except Exception as e:
        print(f"⚠ Database load failed: {e}")
    
    # Fallback to CSV
    csv_path = "data/jobs_data.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} jobs from CSV backup")
        return df
    
    print("✗ No data source found. Run data_generator.py first.")
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: DATA CLEANING
# ─────────────────────────────────────────────────────────────────────────────

def standardize_job_titles(df):
    """
    Standardize job titles to consistent categories.
    
    WHY: Job titles in scraped data come in many variants:
    - "Sr. Data Scientist" → "Data Scientist"
    - "Junior Data Analyst" → "Data Analyst"
    - "ML/AI Engineer" → "ML Engineer"
    
    Standardization enables meaningful grouping and analysis.
    
    Args:
        df (pd.DataFrame): DataFrame with 'job_title' column
        
    Returns:
        pd.DataFrame: DataFrame with standardized job titles
    """
    # Mapping of common variants to standard titles
    title_mapping = {
        # Data Scientist variants
        r'(?i).*data\s*scien.*': 'Data Scientist',
        r'(?i).*senior\s*data\s*scien.*': 'Data Scientist',
        r'(?i).*lead\s*data\s*scien.*': 'Data Scientist',
        r'(?i).*junior\s*data\s*scien.*': 'Data Scientist',
        
        # Data Analyst variants
        r'(?i).*data\s*analy.*': 'Data Analyst',
        r'(?i).*analytics\s*analy.*': 'Data Analyst',
        r'(?i).*research\s*analy.*': 'Data Analyst',
        
        # ML Engineer variants
        r'(?i).*ml\s*eng.*': 'ML Engineer',
        r'(?i).*machine\s*learn.*eng.*': 'ML Engineer',
        r'(?i).*ai\s*eng.*': 'ML Engineer',
        r'(?i).*deep\s*learn.*eng.*': 'ML Engineer',
        
        # Business Analyst variants
        r'(?i).*business\s*analy.*': 'Business Analyst',
        r'(?i).*ba\b.*analy.*': 'Business Analyst',
        
        # Python Developer variants
        r'(?i).*python\s*dev.*': 'Python Developer',
        r'(?i).*backend\s*dev.*python.*': 'Python Developer',
        
        # SQL Developer variants
        r'(?i).*sql\s*dev.*': 'SQL Developer',
        r'(?i).*database\s*dev.*': 'SQL Developer',
        r'(?i).*db\s*dev.*': 'SQL Developer',
        
        # Power BI Developer variants
        r'(?i).*power\s*bi.*': 'Power BI Developer',
        r'(?i).*bi\s*dev.*': 'Power BI Developer',
        r'(?i).*tableau\s*dev.*': 'Power BI Developer',
    }
    
    def map_title(title):
        """Map a single title to its standard form."""
        if pd.isna(title):
            return "Unknown"
        for pattern, standard in title_mapping.items():
            if re.match(pattern, str(title)):
                return standard
        return str(title).strip()
    
    df['job_title_original'] = df['job_title']  # Keep original for reference
    df['job_title'] = df['job_title'].apply(map_title)
    
    return df


def clean_salary(df):
    """
    Clean and parse salary data into numeric columns.
    
    Handles various formats found in Indian job postings:
    - "₹5 - 10 LPA" → min=5.0, max=10.0, avg=7.5
    - "5-10 Lakhs" → min=5.0, max=10.0, avg=7.5
    - "Not Disclosed" → NaN
    - "₹50,000 - 80,000 per month" → converted to LPA
    
    Args:
        df (pd.DataFrame): DataFrame with salary columns
        
    Returns:
        pd.DataFrame: DataFrame with cleaned salary_min, salary_max, salary_avg
    """
    def parse_salary_range(row):
        """Parse salary string and existing min/max values."""
        sal_min = row.get('salary_min')
        sal_max = row.get('salary_max')
        sal_range = str(row.get('salary_range', ''))
        
        # If numeric values already exist, use them
        if pd.notna(sal_min) and pd.notna(sal_max):
            return sal_min, sal_max
        
        # Skip non-disclosed salaries
        if 'not disclosed' in sal_range.lower() or sal_range.strip() == '':
            return np.nan, np.nan
        
        # Try to extract numbers from the salary string
        numbers = re.findall(r'[\d.]+', sal_range.replace(',', ''))
        
        if len(numbers) >= 2:
            try:
                val1 = float(numbers[0])
                val2 = float(numbers[1])
                
                # Check if values are in monthly format (> 100 suggests monthly/annual ₹)
                if val1 > 100:
                    # Assume monthly, convert to LPA
                    val1 = round(val1 * 12 / 100000, 1)
                    val2 = round(val2 * 12 / 100000, 1)
                
                return min(val1, val2), max(val1, val2)
            except (ValueError, IndexError):
                pass
        elif len(numbers) == 1:
            try:
                val = float(numbers[0])
                if val > 100:
                    val = round(val * 12 / 100000, 1)
                return val * 0.8, val * 1.2  # ±20% range for single values
            except ValueError:
                pass
        
        return np.nan, np.nan
    
    # Apply salary parsing
    salary_parsed = df.apply(parse_salary_range, axis=1, result_type='expand')
    df['salary_min'] = salary_parsed[0]
    df['salary_max'] = salary_parsed[1]
    df['salary_avg'] = (df['salary_min'] + df['salary_max']) / 2
    
    # Cap unrealistic values (nobody earns >200 LPA in most DS roles)
    df.loc[df['salary_avg'] > 200, ['salary_min', 'salary_max', 'salary_avg']] = np.nan
    
    print(f"✓ Salary data cleaned — {df['salary_avg'].notna().sum()} jobs have salary info")
    return df


def clean_experience(df):
    """
    Extract numeric experience values from text.
    
    Handles formats like:
    - "3-5 years" → min=3, max=5
    - "5+ years" → min=5, max=8
    - "Fresher" → min=0, max=1
    
    Args:
        df (pd.DataFrame): DataFrame with experience columns
        
    Returns:
        pd.DataFrame: DataFrame with cleaned experience_min, experience_max
    """
    def parse_experience(row):
        """Parse experience string into min/max years."""
        exp_min = row.get('experience_min')
        exp_max = row.get('experience_max')
        exp_str = str(row.get('experience_required', ''))
        
        # If numeric values exist, use them
        if pd.notna(exp_min) and pd.notna(exp_max):
            return int(exp_min), int(exp_max)
        
        # Handle fresher/entry level
        if 'fresher' in exp_str.lower() or 'entry' in exp_str.lower():
            return 0, 1
        
        # Extract numbers
        numbers = re.findall(r'\d+', exp_str)
        
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            val = int(numbers[0])
            return val, val + 2
        
        return 0, 0
    
    exp_parsed = df.apply(parse_experience, axis=1, result_type='expand')
    df['experience_min'] = exp_parsed[0]
    df['experience_max'] = exp_parsed[1]
    
    print(f"✓ Experience data cleaned")
    return df


def handle_missing_values(df):
    """
    Handle missing values across all columns.
    
    Strategy:
    - Text fields: Fill with sensible defaults
    - Numeric fields: Leave as NaN (handled by ML models)
    - Required fields: Drop rows where critical data is missing
    
    Args:
        df (pd.DataFrame): Raw DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with missing values handled
    """
    initial_count = len(df)
    
    # Drop rows missing critical fields
    df = df.dropna(subset=['job_title', 'company_name'])
    
    # Fill text field defaults
    df['location'] = df['location'].fillna('India')
    df['salary_range'] = df['salary_range'].fillna('Not Disclosed')
    df['required_skills'] = df['required_skills'].fillna('')
    df['experience_required'] = df['experience_required'].fillna('Not Specified')
    df['job_description'] = df['job_description'].fillna('')
    df['portal_name'] = df['portal_name'].fillna('Unknown')
    df['company_tier'] = df['company_tier'].fillna('small')
    df['date_posted'] = df['date_posted'].fillna(datetime.now().strftime('%Y-%m-%d'))
    
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"  ⚠ Dropped {dropped} rows with missing critical fields")
    
    print(f"✓ Missing values handled — {len(df)} valid records")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: NLP SKILL EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_and_update_skills(df):
    """
    Extract skills from job descriptions using NLP.
    
    For each job posting, scans the description text and identifies
    which skills from our master list are mentioned. This enriches
    the data even for postings where skills weren't explicitly listed.
    
    Args:
        df (pd.DataFrame): DataFrame with job descriptions
        
    Returns:
        pd.DataFrame: DataFrame with updated required_skills column
    """
    print("Extracting skills from job descriptions...")
    
    skills_extracted = 0
    
    for idx, row in df.iterrows():
        # Combine description and existing skills for comprehensive extraction
        text = f"{row.get('job_description', '')} {row.get('required_skills', '')} {row.get('job_title', '')}"
        
        skills = extract_skills_from_text(text)
        
        if skills:
            df.at[idx, 'required_skills'] = ", ".join(skills)
            skills_extracted += 1
    
    # Count skills per job
    df['skills_count'] = df['required_skills'].apply(
        lambda x: len(x.split(", ")) if x else 0
    )
    
    print(f"✓ Skills extracted for {skills_extracted}/{len(df)} jobs")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4: SKILL FREQUENCY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_skill_frequency(df):
    """
    Analyze how frequently each skill appears across all job postings.
    
    This tells us which skills are most in-demand in the market,
    which is crucial for the skill gap analysis feature.
    
    Args:
        df (pd.DataFrame): DataFrame with required_skills column
        
    Returns:
        dict: Contains skill_counts, role_skill_counts, city_skill_counts
    """
    print("Analyzing skill frequency...")
    
    # Overall skill frequency
    all_skills_list = []
    for skills_str in df['required_skills'].dropna():
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        all_skills_list.extend(skills)
    
    skill_counts = Counter(all_skills_list)
    
    # Skill frequency by role
    role_skill_counts = {}
    for role in df['job_title'].unique():
        role_df = df[df['job_title'] == role]
        role_skills = []
        for skills_str in role_df['required_skills'].dropna():
            skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            role_skills.extend(skills)
        role_skill_counts[role] = Counter(role_skills)
    
    # Skill frequency by city
    city_skill_counts = {}
    for city in df['location'].unique():
        city_df = df[df['location'] == city]
        city_skills = []
        for skills_str in city_df['required_skills'].dropna():
            skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            city_skills.extend(skills)
        city_skill_counts[city] = Counter(city_skills)
    
    # Print top skills
    print("\nTop 15 Most In-Demand Skills:")
    print("-" * 40)
    for skill, count in skill_counts.most_common(15):
        pct = (count / len(df)) * 100
        print(f"  {skill:25s} {count:4d} ({pct:.1f}%)")
    
    return {
        "overall": skill_counts,
        "by_role": role_skill_counts,
        "by_city": city_skill_counts
    }


def compute_skill_cooccurrence(df, top_n=20):
    """
    Compute which skills frequently appear together in job postings.
    
    This reveals skill clusters — e.g., if a job requires Python,
    it often also requires SQL and Machine Learning.
    
    Args:
        df (pd.DataFrame): DataFrame with required_skills column
        top_n (int): Number of top skills to analyze co-occurrence for
        
    Returns:
        pd.DataFrame: Co-occurrence matrix for top skills
    """
    # Get top N skills
    all_skills_list = []
    for skills_str in df['required_skills'].dropna():
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        all_skills_list.extend(skills)
    
    top_skills = [s for s, _ in Counter(all_skills_list).most_common(top_n)]
    
    # Build co-occurrence matrix
    cooccurrence = pd.DataFrame(0, index=top_skills, columns=top_skills)
    
    for skills_str in df['required_skills'].dropna():
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        relevant = [s for s in skills if s in top_skills]
        
        for i, s1 in enumerate(relevant):
            for s2 in relevant[i+1:]:
                cooccurrence.at[s1, s2] += 1
                cooccurrence.at[s2, s1] += 1
    
    return cooccurrence


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5: SAVE PROCESSED DATA
# ─────────────────────────────────────────────────────────────────────────────

def save_processed_data(df, db_path="data/jobs.db", csv_path="data/jobs_data.csv"):
    """
    Save the cleaned and processed data back to storage.
    
    Overwrites the original data with the cleaned version,
    so subsequent analyses use clean data.
    
    Args:
        df (pd.DataFrame): Processed DataFrame
        db_path (str): Path to SQLite database
        csv_path (str): Path to CSV backup
    """
    # Save to SQLite
    try:
        conn = sqlite3.connect(db_path)
        df.to_sql('job_postings', conn, if_exists='replace', index=False)
        conn.close()
        print(f"✓ Saved processed data to {db_path}")
    except Exception as e:
        print(f"✗ Database save failed: {e}")
    
    # Save to CSV
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✓ Saved processed data to {csv_path}")
    except Exception as e:
        print(f"✗ CSV save failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline():
    """
    Run the complete data processing pipeline.
    
    This is the main entry point that orchestrates all processing stages
    in the correct order:
    1. Load → 2. Clean → 3. Extract Skills → 4. Analyze → 5. Save
    
    Returns:
        pd.DataFrame: Fully processed job postings data
    """
    print("=" * 60)
    print("JobLens — Data Processing Pipeline")
    print("=" * 60)
    
    # Stage 1: Load data
    print("\n📥 Stage 1: Loading data...")
    df = load_data()
    
    if df.empty:
        print("✗ No data to process!")
        return df
    
    # Stage 2: Clean data
    print("\n🧹 Stage 2: Cleaning data...")
    df = handle_missing_values(df)
    df = standardize_job_titles(df)
    df = clean_salary(df)
    df = clean_experience(df)
    
    # Stage 3: NLP skill extraction
    print("\n🔍 Stage 3: Extracting skills with NLP...")
    df = extract_and_update_skills(df)
    
    # Stage 4: Skill analysis
    print("\n📊 Stage 4: Analyzing skill frequency...")
    skill_stats = analyze_skill_frequency(df)
    
    # Stage 5: Save processed data
    print("\n💾 Stage 5: Saving processed data...")
    save_processed_data(df)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    print(f"  Total jobs processed: {len(df)}")
    print(f"  Unique roles: {df['job_title'].nunique()}")
    print(f"  Unique companies: {df['company_name'].nunique()}")
    print(f"  Unique cities: {df['location'].nunique()}")
    print(f"  Jobs with salary info: {df['salary_avg'].notna().sum()}")
    print(f"  Avg skills per job: {df['skills_count'].mean():.1f}")
    print(f"  Unique skills tracked: {len(skill_stats['overall'])}")
    print("=" * 60)
    
    return df


if __name__ == "__main__":
    df = run_pipeline()
