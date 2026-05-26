"""
JobLens — Job Role Classifier
================================
Classifies job postings into role categories based on skill text.

APPROACH:
Given a set of skills (as text), predict which job role the posting
belongs to. This is useful for:
- Auto-categorizing scraped job postings
- Telling users which role their skills match
- Standardizing role classifications

MODELS TRAINED:
1. Multinomial Naive Bayes — Fast, works well with TF-IDF text features
2. Random Forest Classifier — More robust, handles feature interactions

FEATURES: TF-IDF vectors from the required_skills text
TARGET: job_title category (Data Scientist, Data Analyst, etc.)
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                           confusion_matrix)
import joblib

warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def load_training_data():
    """
    Load job postings for classifier training.
    
    We need jobs that have both skills and a clear job title.
    
    Returns:
        pd.DataFrame: Training data with skills and job titles
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'jobs.db')
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT job_title, required_skills, job_description FROM job_postings "
            "WHERE required_skills IS NOT NULL AND required_skills != ''",
            conn
        )
        conn.close()
        
        print(f"✓ Loaded {len(df)} jobs for classifier training")
        return df
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return pd.DataFrame()


def train_and_evaluate():
    """
    Train role classification models and save the best one.
    
    PIPELINE:
    1. Load data
    2. Create TF-IDF features from skills text
    3. Train Naive Bayes and Random Forest
    4. Compare accuracy
    5. Save best model and vectorizer
    
    Returns:
        tuple: (best_model, vectorizer, metrics_dict)
    """
    print("=" * 60)
    print("JobLens — Job Role Classifier Training")
    print("=" * 60)
    
    # Load data
    df = load_training_data()
    if df.empty or len(df) < 10:
        print("✗ Insufficient data for training!")
        return None, None, None
    
    # Combine skills and description for richer features
    df['text_features'] = df['required_skills'].fillna('') + ' ' + df['job_description'].fillna('')
    
    # Filter out classes with too few samples
    class_counts = df['job_title'].value_counts()
    valid_classes = class_counts[class_counts >= 5].index
    df = df[df['job_title'].isin(valid_classes)]
    
    print(f"\nClasses (roles) for classification:")
    for role, count in df['job_title'].value_counts().items():
        print(f"  {role}: {count} samples")
    
    # ─── TF-IDF Vectorization ───────────────────────────────────────────
    print("\nCreating TF-IDF features...")
    
    tfidf = TfidfVectorizer(
        max_features=500,      # Top 500 terms
        ngram_range=(1, 2),    # Unigrams and bigrams
        stop_words='english',  # Remove common English words
        min_df=2,              # Ignore very rare terms
        max_df=0.95            # Ignore terms in >95% of docs
    )
    
    X = tfidf.fit_transform(df['text_features'])
    y = df['job_title'].values
    
    print(f"TF-IDF matrix shape: {X.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train set: {X_train.shape[0]} | Test set: {X_test.shape[0]}")
    
    # ─── Model 1: Multinomial Naive Bayes ────────────────────────────────
    print("\n--- Model 1: Multinomial Naive Bayes ---")
    nb_model = MultinomialNB(alpha=0.1)  # Smoothing parameter
    nb_model.fit(X_train, y_train)
    nb_pred = nb_model.predict(X_test)
    
    nb_accuracy = accuracy_score(y_test, nb_pred)
    print(f"  Accuracy: {nb_accuracy:.4f} ({nb_accuracy*100:.1f}%)")
    print("\n  Classification Report:")
    print(classification_report(y_test, nb_pred, zero_division=0))
    
    # ─── Model 2: Random Forest Classifier ──────────────────────────────
    print("\n--- Model 2: Random Forest Classifier ---")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=3,
        random_state=42,
        n_jobs=-1  # Use all CPU cores
    )
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    
    rf_accuracy = accuracy_score(y_test, rf_pred)
    print(f"  Accuracy: {rf_accuracy:.4f} ({rf_accuracy*100:.1f}%)")
    print("\n  Classification Report:")
    print(classification_report(y_test, rf_pred, zero_division=0))
    
    # ─── Confusion Matrix ───────────────────────────────────────────────
    print("\n  Confusion Matrix (Random Forest):")
    cm = confusion_matrix(y_test, rf_pred)
    labels = sorted(df['job_title'].unique())
    
    # Print formatted confusion matrix
    print(f"{'':>20}", end='')
    for label in labels:
        print(f"{label[:8]:>10}", end='')
    print()
    
    for i, row_label in enumerate(labels):
        print(f"{row_label:>20}", end='')
        for j in range(len(labels)):
            if i < cm.shape[0] and j < cm.shape[1]:
                print(f"{cm[i][j]:>10}", end='')
            else:
                print(f"{'0':>10}", end='')
        print()
    
    # ─── Select & Save Best Model ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Model Comparison")
    print("=" * 60)
    print(f"  Naive Bayes:    {nb_accuracy*100:.1f}%")
    print(f"  Random Forest:  {rf_accuracy*100:.1f}%")
    
    if rf_accuracy >= nb_accuracy:
        best_model = rf_model
        best_name = "Random Forest"
        best_accuracy = rf_accuracy
    else:
        best_model = nb_model
        best_name = "Naive Bayes"
        best_accuracy = nb_accuracy
    
    print(f"\n🏆 Best Model: {best_name} ({best_accuracy*100:.1f}%)")
    
    # Save model and vectorizer
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    os.makedirs(save_dir, exist_ok=True)
    
    model_path = os.path.join(save_dir, 'role_classifier.pkl')
    joblib.dump(best_model, model_path)
    print(f"\n✓ Saved classifier to {model_path}")
    
    vectorizer_path = os.path.join(save_dir, 'classifier_tfidf.pkl')
    joblib.dump(tfidf, vectorizer_path)
    print(f"✓ Saved TF-IDF vectorizer to {vectorizer_path}")
    
    # Save class labels
    labels_path = os.path.join(save_dir, 'classifier_labels.pkl')
    joblib.dump(labels, labels_path)
    print(f"✓ Saved class labels to {labels_path}")
    
    return best_model, tfidf, {'accuracy': best_accuracy, 'model_name': best_name}


def predict_role(skills_text):
    """
    Predict the most likely job role given a set of skills.
    
    Args:
        skills_text (str): Comma-separated skills or description text
        
    Returns:
        dict: Predicted role with probabilities for each class
    """
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    
    try:
        model = joblib.load(os.path.join(save_dir, 'role_classifier.pkl'))
        tfidf = joblib.load(os.path.join(save_dir, 'classifier_tfidf.pkl'))
    except FileNotFoundError:
        return {"error": "Classifier not trained yet. Run training first."}
    
    try:
        X = tfidf.transform([skills_text])
        
        # Get prediction and probabilities
        predicted_role = model.predict(X)[0]
        
        # Get probability scores if available
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(X)[0]
            classes = model.classes_
            role_probs = {cls: round(float(prob) * 100, 1)
                        for cls, prob in zip(classes, probabilities)}
            # Sort by probability
            role_probs = dict(sorted(role_probs.items(), key=lambda x: -x[1]))
        else:
            role_probs = {predicted_role: 100.0}
        
        return {
            "predicted_role": predicted_role,
            "role_probabilities": role_probs
        }
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


if __name__ == "__main__":
    train_and_evaluate()
