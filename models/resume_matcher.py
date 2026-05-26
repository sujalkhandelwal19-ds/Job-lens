"""
JobLens — Resume Job Matcher
================================
Matches uploaded resumes to job postings using TF-IDF and Cosine Similarity.

HOW IT WORKS:
1. All job descriptions form a "corpus" (collection of documents)
2. User's resume is treated as a query document
3. TF-IDF converts both into numerical vectors
4. Cosine similarity measures how "close" the resume is to each job
5. Top 10 most similar jobs are returned as recommendations

WHY TF-IDF + COSINE:
- TF-IDF (Term Frequency-Inverse Document Frequency) weights words by
  how important they are in a document relative to the whole corpus
- Cosine similarity is scale-independent — it measures direction, not magnitude
- Together they provide robust text similarity even with varying document lengths
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def build_job_corpus():
    """
    Build the job description corpus from the database.
    
    Each job's "document" is a combination of its title, skills,
    and full description. This gives the TF-IDF vectorizer rich
    text to work with.
    
    Returns:
        tuple: (documents_list, jobs_dataframe)
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'jobs.db')
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT * FROM job_postings WHERE job_description IS NOT NULL",
            conn
        )
        conn.close()
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return [], pd.DataFrame()
    
    # Create combined text for each job
    documents = []
    for _, row in df.iterrows():
        doc = f"{row.get('job_title', '')} {row.get('required_skills', '')} {row.get('job_description', '')}"
        documents.append(doc)
    
    print(f"✓ Built corpus with {len(documents)} job documents")
    return documents, df


def train_vectorizer():
    """
    Train the TF-IDF vectorizer on the job corpus and save it.
    
    This needs to be done once after data generation/scraping.
    The trained vectorizer and document vectors are saved for
    fast matching during user requests.
    
    Returns:
        tuple: (vectorizer, tfidf_matrix, jobs_df)
    """
    print("=" * 60)
    print("JobLens — Resume Matcher Training")
    print("=" * 60)
    
    documents, df = build_job_corpus()
    
    if not documents:
        print("✗ No job documents found!")
        return None, None, None
    
    # Train TF-IDF vectorizer
    print("\nTraining TF-IDF vectorizer...")
    tfidf = TfidfVectorizer(
        max_features=1000,     # Top 1000 terms
        ngram_range=(1, 2),    # Unigrams and bigrams
        stop_words='english',  # Remove common words
        min_df=2,              # Term must appear in at least 2 docs
        max_df=0.95,           # Ignore terms in >95% of docs
        sublinear_tf=True      # Apply sublinear TF scaling (1 + log(tf))
    )
    
    tfidf_matrix = tfidf.fit_transform(documents)
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
    print(f"Vocabulary size: {len(tfidf.vocabulary_)}")
    
    # Save vectorizer and matrix
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    os.makedirs(save_dir, exist_ok=True)
    
    vectorizer_path = os.path.join(save_dir, 'tfidf_vectorizer.pkl')
    joblib.dump(tfidf, vectorizer_path)
    print(f"✓ Saved TF-IDF vectorizer to {vectorizer_path}")
    
    matrix_path = os.path.join(save_dir, 'job_tfidf_matrix.pkl')
    joblib.dump(tfidf_matrix, matrix_path)
    print(f"✓ Saved job TF-IDF matrix to {matrix_path}")
    
    # Show top terms
    feature_names = tfidf.get_feature_names_out()
    print(f"\nSample vocabulary terms: {list(feature_names[:20])}")
    
    return tfidf, tfidf_matrix, df


def match_resume(resume_text, top_n=10):
    """
    Match a resume against all job postings and return top matches.
    
    Args:
        resume_text (str): Full text of the candidate's resume
        top_n (int): Number of top matches to return
        
    Returns:
        list: Top N matching jobs with similarity scores
              Each item is a dict with job details and match_score
    """
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    
    try:
        tfidf = joblib.load(os.path.join(save_dir, 'tfidf_vectorizer.pkl'))
        job_matrix = joblib.load(os.path.join(save_dir, 'job_tfidf_matrix.pkl'))
    except FileNotFoundError:
        return {"error": "Resume matcher not trained. Run training first."}
    
    # Load job data for result details
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'jobs.db')
    try:
        conn = sqlite3.connect(db_path)
        jobs_df = pd.read_sql_query(
            "SELECT * FROM job_postings WHERE job_description IS NOT NULL", conn
        )
        conn.close()
    except Exception as e:
        return {"error": f"Could not load job data: {e}"}
    
    try:
        # Transform resume text using the same vectorizer
        resume_vector = tfidf.transform([resume_text])
        
        # Calculate cosine similarity between resume and all jobs
        similarities = cosine_similarity(resume_vector, job_matrix).flatten()
        
        # Get top N indices (highest similarity first)
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        # Build results
        matches = []
        for idx in top_indices:
            if idx < len(jobs_df):
                job = jobs_df.iloc[idx]
                match_score = round(float(similarities[idx]) * 100, 1)
                
                matches.append({
                    "job_title": str(job.get('job_title', 'N/A')),
                    "company_name": str(job.get('company_name', 'N/A')),
                    "location": str(job.get('location', 'N/A')),
                    "salary_range": str(job.get('salary_range', 'N/A')),
                    "required_skills": str(job.get('required_skills', 'N/A')),
                    "experience_required": str(job.get('experience_required', 'N/A')),
                    "match_score": match_score,
                    "portal_name": str(job.get('portal_name', 'N/A'))
                })
        
        return matches
    
    except Exception as e:
        return {"error": f"Matching failed: {str(e)}"}


if __name__ == "__main__":
    # Train the vectorizer
    train_vectorizer()
    
    # Test with a sample resume
    sample_resume = """
    Experienced Data Scientist with 5 years in machine learning and AI.
    Proficient in Python, TensorFlow, PyTorch, SQL, and AWS.
    Built recommendation systems and NLP pipelines.
    Strong background in statistics and deep learning.
    Experience with Docker, Kubernetes, and MLOps.
    """
    
    print("\n\n--- Testing Resume Matching ---")
    results = match_resume(sample_resume)
    
    if isinstance(results, list):
        print(f"\nTop {len(results)} Job Matches:")
        for i, match in enumerate(results, 1):
            print(f"\n{i}. {match['job_title']} at {match['company_name']}")
            print(f"   Location: {match['location']} | Match: {match['match_score']}%")
    else:
        print(f"Error: {results}")
