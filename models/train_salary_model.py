"""
JobLens — Salary Prediction Model
====================================
Trains ML models to predict salary based on job attributes.

APPROACH:
We train three models and pick the best one:
1. Linear Regression — baseline, interpretable
2. Random Forest — handles non-linear relationships
3. XGBoost — gradient boosting, often best for tabular data

FEATURES:
- job_title (encoded) — different roles pay differently
- experience_min — experience is the #1 salary driver
- location (encoded) — Bangalore pays more than tier-2 cities
- skills_count — more skills required = higher salary
- company_tier (encoded) — Google pays more than TCS

TARGET: salary_avg (average salary in LPA)
"""

import os
import sys
import sqlite3
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Try importing XGBoost — it's optional
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠ XGBoost not available. Will train without it.")

warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def load_training_data():
    """
    Load processed job data for model training.
    
    Only includes rows where salary information is available,
    since we can't train a salary predictor without target values.
    
    Returns:
        pd.DataFrame: Filtered DataFrame with salary data
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'jobs.db')
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM job_postings WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL", conn)
        conn.close()
        
        # Calculate average salary if not present
        if 'salary_avg' not in df.columns:
            df['salary_avg'] = (df['salary_min'] + df['salary_max']) / 2
        
        # Calculate skills_count if not present
        if 'skills_count' not in df.columns:
            df['skills_count'] = df['required_skills'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) else 0
            )
        
        print(f"✓ Loaded {len(df)} jobs with salary data for training")
        return df
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return pd.DataFrame()


def prepare_features(df):
    """
    Prepare features and target for model training.
    
    Feature engineering steps:
    1. Encode categorical variables (job_title, location, company_tier)
    2. Select numeric features (experience, skills_count)
    3. Handle any remaining NaN values
    
    WHY LABEL ENCODING:
    We use LabelEncoder for tree-based models (Random Forest, XGBoost)
    because they handle ordinal encoding well. For Linear Regression,
    this is suboptimal but acceptable given our comparison approach.
    
    Args:
        df (pd.DataFrame): Training data
        
    Returns:
        tuple: (X, y, encoders_dict, feature_names)
    """
    # Initialize encoders
    encoders = {}
    
    # Encode job_title
    le_title = LabelEncoder()
    df['job_title_encoded'] = le_title.fit_transform(df['job_title'].astype(str))
    encoders['job_title'] = le_title
    
    # Encode location
    le_location = LabelEncoder()
    df['location_encoded'] = le_location.fit_transform(df['location'].astype(str))
    encoders['location'] = le_location
    
    # Encode company_tier
    le_tier = LabelEncoder()
    df['company_tier_encoded'] = le_tier.fit_transform(df['company_tier'].fillna('small').astype(str))
    encoders['company_tier'] = le_tier
    
    # Select features
    feature_cols = ['job_title_encoded', 'experience_min', 'location_encoded',
                    'skills_count', 'company_tier_encoded']
    
    # Ensure all feature columns exist and are numeric
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    X = df[feature_cols].values
    y = df['salary_avg'].values
    
    # Remove any remaining NaN in target
    valid_mask = ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"✓ Prepared {X.shape[0]} samples with {X.shape[1]} features")
    return X, y, encoders, feature_cols


def train_and_evaluate():
    """
    Train multiple models, compare performance, and save the best one.
    
    EVALUATION METRICS:
    - MAE (Mean Absolute Error): Average prediction error in LPA
    - RMSE (Root Mean Squared Error): Penalizes large errors more
    - R² Score: How much variance the model explains (1.0 = perfect)
    
    The best model is selected based on R² score on the test set.
    
    Returns:
        tuple: (best_model, encoders, feature_names, metrics_dict)
    """
    print("=" * 60)
    print("JobLens — Salary Prediction Model Training")
    print("=" * 60)
    
    # Load and prepare data
    df = load_training_data()
    if df.empty or len(df) < 10:
        print("✗ Insufficient data for training!")
        return None, None, None, None
    
    X, y, encoders, feature_names = prepare_features(df)
    
    # Split data: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain set: {X_train.shape[0]} samples")
    print(f"Test set:  {X_test.shape[0]} samples")
    
    # ─── Train Models ────────────────────────────────────────────────────
    models = {}
    results = {}
    
    # Model 1: Linear Regression
    print("\n--- Model 1: Linear Regression ---")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)
    
    lr_metrics = {
        'MAE': mean_absolute_error(y_test, lr_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, lr_pred)),
        'R2': r2_score(y_test, lr_pred)
    }
    models['Linear Regression'] = lr_model
    results['Linear Regression'] = lr_metrics
    print(f"  MAE:  {lr_metrics['MAE']:.2f} LPA")
    print(f"  RMSE: {lr_metrics['RMSE']:.2f} LPA")
    print(f"  R²:   {lr_metrics['R2']:.4f}")
    
    # Model 2: Random Forest Regressor
    print("\n--- Model 2: Random Forest Regressor ---")
    rf_model = RandomForestRegressor(
        n_estimators=100,    # Number of trees
        max_depth=10,        # Prevent overfitting
        min_samples_split=5, # Minimum samples to split a node
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    
    rf_metrics = {
        'MAE': mean_absolute_error(y_test, rf_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, rf_pred)),
        'R2': r2_score(y_test, rf_pred)
    }
    models['Random Forest'] = rf_model
    results['Random Forest'] = rf_metrics
    print(f"  MAE:  {rf_metrics['MAE']:.2f} LPA")
    print(f"  RMSE: {rf_metrics['RMSE']:.2f} LPA")
    print(f"  R²:   {rf_metrics['R2']:.4f}")
    
    # Feature importance for Random Forest
    print("\n  Feature Importance:")
    importances = rf_model.feature_importances_
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
        print(f"    {name:30s} {imp:.4f}")
    
    # Model 3: XGBoost Regressor
    if XGBOOST_AVAILABLE:
        print("\n--- Model 3: XGBoost Regressor ---")
        xgb_model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0
        )
        xgb_model.fit(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)
        
        xgb_metrics = {
            'MAE': mean_absolute_error(y_test, xgb_pred),
            'RMSE': np.sqrt(mean_squared_error(y_test, xgb_pred)),
            'R2': r2_score(y_test, xgb_pred)
        }
        models['XGBoost'] = xgb_model
        results['XGBoost'] = xgb_metrics
        print(f"  MAE:  {xgb_metrics['MAE']:.2f} LPA")
        print(f"  RMSE: {xgb_metrics['RMSE']:.2f} LPA")
        print(f"  R²:   {xgb_metrics['R2']:.4f}")
    
    # ─── Select Best Model ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Model Comparison Summary")
    print("=" * 60)
    print(f"{'Model':<25} {'MAE':>8} {'RMSE':>8} {'R²':>8}")
    print("-" * 55)
    
    best_model_name = None
    best_r2 = -float('inf')
    
    for name, metrics in results.items():
        print(f"{name:<25} {metrics['MAE']:>8.2f} {metrics['RMSE']:>8.2f} {metrics['R2']:>8.4f}")
        if metrics['R2'] > best_r2:
            best_r2 = metrics['R2']
            best_model_name = name
    
    print(f"\n🏆 Best Model: {best_model_name} (R² = {best_r2:.4f})")
    
    best_model = models[best_model_name]
    
    # ─── Save Models ────────────────────────────────────────────────────
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    os.makedirs(save_dir, exist_ok=True)
    
    # Save best model
    model_path = os.path.join(save_dir, 'salary_model.pkl')
    joblib.dump(best_model, model_path)
    print(f"\n✓ Saved best model to {model_path}")
    
    # Save encoders
    encoders_path = os.path.join(save_dir, 'encoders.pkl')
    joblib.dump(encoders, encoders_path)
    print(f"✓ Saved encoders to {encoders_path}")
    
    # Save feature names for prediction
    meta_path = os.path.join(save_dir, 'salary_model_meta.pkl')
    joblib.dump({
        'feature_names': feature_names,
        'best_model_name': best_model_name,
        'metrics': results[best_model_name]
    }, meta_path)
    print(f"✓ Saved model metadata to {meta_path}")
    
    return best_model, encoders, feature_names, results


def predict_salary(job_title, experience, location, skills_count, company_tier):
    """
    Predict salary for given job attributes using the trained model.
    
    Args:
        job_title (str): Job role title
        experience (int): Years of experience
        location (str): City name
        skills_count (int): Number of skills
        company_tier (str): 'top', 'mid', or 'small'
        
    Returns:
        dict: Predicted salary with confidence interval
    """
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_models')
    
    try:
        model = joblib.load(os.path.join(save_dir, 'salary_model.pkl'))
        encoders = joblib.load(os.path.join(save_dir, 'encoders.pkl'))
    except FileNotFoundError:
        return {"error": "Model not trained yet. Run training first."}
    
    try:
        # Encode inputs — handle unseen labels gracefully
        title_encoded = _safe_encode(encoders['job_title'], job_title)
        location_encoded = _safe_encode(encoders['location'], location)
        tier_encoded = _safe_encode(encoders['company_tier'], company_tier)
        
        # Create feature vector
        features = np.array([[title_encoded, experience, location_encoded,
                            skills_count, tier_encoded]])
        
        # Predict
        predicted_salary = model.predict(features)[0]
        
        # Calculate confidence interval (±15% as a heuristic)
        lower_bound = max(2.0, predicted_salary * 0.85)
        upper_bound = predicted_salary * 1.15
        
        return {
            "predicted_salary": round(predicted_salary, 1),
            "salary_min": round(lower_bound, 1),
            "salary_max": round(upper_bound, 1),
            "unit": "LPA",
            "confidence": "Based on market data analysis"
        }
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


def _safe_encode(encoder, value):
    """
    Safely encode a value, handling unseen labels.
    
    If the value wasn't seen during training, we use the most
    common class (index 0) as a fallback.
    
    Args:
        encoder: Fitted LabelEncoder
        value: Value to encode
        
    Returns:
        int: Encoded value
    """
    try:
        return encoder.transform([str(value)])[0]
    except ValueError:
        # Unseen label — use default (first class)
        return 0


if __name__ == "__main__":
    train_and_evaluate()
