"""
JobLens — Skill Demand Trend Analyzer
========================================
Analyzes how skill demand changes over time.

HOW IT WORKS:
1. Group job postings by date_posted and skill
2. Calculate weekly skill frequency
3. Fit simple linear regression to each skill's trend
4. Identify trending (slope > 0) and declining (slope < 0) skills

WHY THIS MATTERS:
Job seekers need to know not just what's popular NOW, but what's
GROWING vs DECLINING. Learning a declining skill is a waste of time,
while catching a rising trend early gives a competitive advantage.
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def load_data():
    """
    Load job postings with date information for trend analysis.
    
    Returns:
        pd.DataFrame: Job postings with parsed dates
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'jobs.db')
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM job_postings", conn)
        conn.close()
        
        # Parse dates
        df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
        df = df.dropna(subset=['date_posted'])
        
        print(f"✓ Loaded {len(df)} jobs for trend analysis")
        return df
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return pd.DataFrame()


def compute_weekly_skill_frequency(df, top_n=15):
    """
    Calculate how often each skill appears per week.
    
    This creates a time series for each skill showing its
    "popularity" over time, measured as the number of job postings
    per week that mention that skill.
    
    Args:
        df (pd.DataFrame): Job postings with dates and skills
        top_n (int): Number of top skills to track
        
    Returns:
        dict: {skill_name: [(week_date, count), ...]}
    """
    # Find top N skills overall
    all_skills = []
    for skills_str in df['required_skills'].dropna():
        skills = [s.strip() for s in str(skills_str).split(',') if s.strip()]
        all_skills.extend(skills)
    
    top_skills = [s for s, _ in Counter(all_skills).most_common(top_n)]
    
    # Create week column
    df['week'] = df['date_posted'].dt.isocalendar().week
    df['year_week'] = df['date_posted'].dt.strftime('%Y-W%U')
    
    # Count skill appearances per week
    skill_weekly = defaultdict(list)
    
    weeks = sorted(df['year_week'].unique())
    
    for week in weeks:
        week_df = df[df['year_week'] == week]
        week_skills = []
        
        for skills_str in week_df['required_skills'].dropna():
            skills = [s.strip() for s in str(skills_str).split(',') if s.strip()]
            week_skills.extend(skills)
        
        week_counts = Counter(week_skills)
        
        for skill in top_skills:
            skill_weekly[skill].append({
                'week': week,
                'count': week_counts.get(skill, 0)
            })
    
    return skill_weekly, weeks


def analyze_trends(skill_weekly, weeks):
    """
    Fit linear regression to each skill's weekly counts
    to determine if it's trending up or down.
    
    A positive slope means the skill is becoming more demanded.
    A negative slope means it's declining in demand.
    
    Args:
        skill_weekly (dict): Weekly counts per skill
        weeks (list): List of week labels
        
    Returns:
        dict: {skill: {'slope': float, 'trend': 'up'/'down'/'stable'}}
    """
    trends = {}
    
    for skill, weekly_data in skill_weekly.items():
        if not weekly_data:
            continue
        
        counts = [d['count'] for d in weekly_data]
        
        if len(counts) < 3:
            trends[skill] = {'slope': 0, 'trend': 'stable', 'avg_count': np.mean(counts)}
            continue
        
        # Fit linear regression: X = week index, y = count
        X = np.arange(len(counts)).reshape(-1, 1)
        y = np.array(counts)
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        
        # Classify trend based on slope magnitude
        if slope > 0.5:
            trend = 'up'
        elif slope < -0.5:
            trend = 'down'
        else:
            trend = 'stable'
        
        trends[skill] = {
            'slope': round(float(slope), 3),
            'trend': trend,
            'avg_count': round(float(np.mean(counts)), 1),
            'recent_count': int(counts[-1]) if counts else 0,
            'weekly_counts': counts
        }
    
    return trends


def get_trending_skills(n=10):
    """
    Get the top trending and declining skills.
    
    This is the main function called by the web application
    to show skill trends on the dashboard.
    
    Args:
        n (int): Number of skills to return in each category
        
    Returns:
        dict: {'trending': [...], 'declining': [...], 'stable': [...]}
    """
    df = load_data()
    if df.empty:
        return {'trending': [], 'declining': [], 'stable': []}
    
    skill_weekly, weeks = compute_weekly_skill_frequency(df)
    trends = analyze_trends(skill_weekly, weeks)
    
    # Sort by slope
    sorted_skills = sorted(trends.items(), key=lambda x: x[1]['slope'], reverse=True)
    
    trending = [
        {'skill': s, 'slope': d['slope'], 'avg_count': d['avg_count']}
        for s, d in sorted_skills if d['trend'] == 'up'
    ][:n]
    
    declining = [
        {'skill': s, 'slope': d['slope'], 'avg_count': d['avg_count']}
        for s, d in sorted_skills if d['trend'] == 'down'
    ][:n]
    
    stable = [
        {'skill': s, 'slope': d['slope'], 'avg_count': d['avg_count']}
        for s, d in sorted_skills if d['trend'] == 'stable'
    ][:n]
    
    return {
        'trending': trending,
        'declining': declining,
        'stable': stable,
        'all_trends': {s: d for s, d in trends.items()},
        'weeks': weeks
    }


def get_skill_trend_data():
    """
    Get complete trend data for plotting skill demand over time.
    
    Returns data formatted for Plotly line charts.
    
    Returns:
        dict: Skill trend data with weekly breakdowns
    """
    df = load_data()
    if df.empty:
        return {}
    
    skill_weekly, weeks = compute_weekly_skill_frequency(df, top_n=10)
    trends = analyze_trends(skill_weekly, weeks)
    
    # Format for charting
    chart_data = {
        'weeks': list(weeks),
        'skills': {}
    }
    
    for skill, weekly_data in skill_weekly.items():
        chart_data['skills'][skill] = {
            'counts': [d['count'] for d in weekly_data],
            'trend': trends.get(skill, {}).get('trend', 'stable'),
            'slope': trends.get(skill, {}).get('slope', 0)
        }
    
    return chart_data


if __name__ == "__main__":
    print("=" * 60)
    print("JobLens — Skill Demand Trend Analysis")
    print("=" * 60)
    
    result = get_trending_skills()
    
    print("\n📈 Trending Skills (Demand Increasing):")
    print("-" * 40)
    for item in result.get('trending', []):
        print(f"  ↑ {item['skill']:25s} slope={item['slope']:+.3f}  avg={item['avg_count']}")
    
    print("\n📉 Declining Skills (Demand Decreasing):")
    print("-" * 40)
    for item in result.get('declining', []):
        print(f"  ↓ {item['skill']:25s} slope={item['slope']:+.3f}  avg={item['avg_count']}")
    
    print("\n📊 Stable Skills:")
    print("-" * 40)
    for item in result.get('stable', []):
        print(f"  → {item['skill']:25s} slope={item['slope']:+.3f}  avg={item['avg_count']}")
    
    print("\n✓ Trend analysis complete!")
