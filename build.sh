#!/usr/bin/env bash
# Build script for Render deployment
# Runs during the build phase to generate data and train models

set -e

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Generating job data ==="
python -c "
from data_generator import generate_jobs, save_to_sqlite, save_to_csv
jobs = generate_jobs(1500)
save_to_sqlite(jobs, db_path='data/jobs.db')
save_to_csv(jobs, csv_path='data/jobs_data.csv')
print('Data generation complete!')
"

echo "=== Processing data ==="
python -c "
from data_processor import run_pipeline
run_pipeline()
print('Data processing complete!')
"

echo "=== Training ML models ==="
python -c "
try:
    from models.train_salary_model import train_and_evaluate
    train_and_evaluate()
    print('Salary model trained!')
except Exception as e:
    print(f'Salary model warning: {e}')

try:
    from models.train_classifier import train_and_evaluate as train_clf
    train_clf()
    print('Classifier trained!')
except Exception as e:
    print(f'Classifier warning: {e}')

try:
    from models.resume_matcher import train_vectorizer
    train_vectorizer()
    print('Resume matcher trained!')
except Exception as e:
    print(f'Resume matcher warning: {e}')

print('All models trained!')
"

echo "=== Build complete! ==="
