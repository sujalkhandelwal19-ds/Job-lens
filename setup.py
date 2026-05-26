"""
JobLens — Setup & Initialization Script
==========================================
Runs everything in the correct order:
1. Generate dummy data (1000 job postings)
2. Process and clean data (NLP pipeline)
3. Train all ML models
4. Start the Flask web application

Usage:
    python setup.py          # Full setup + start app
    python setup.py --data   # Only generate and process data
    python setup.py --train  # Only train models
    python setup.py --app    # Only start app (assumes data exists)
"""

import os
import sys
import time
import argparse

# Ensure we're running from the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)


def banner():
    """Display the startup banner."""
    print("\n" + "═" * 60)
    print("  🔍 JobLens — Smart Job Market Intelligence Platform")
    print("  Setup & Initialization")
    print("═" * 60 + "\n")


def step_generate_data():
    """Step 1: Generate realistic dummy job data."""
    print("\n" + "─" * 60)
    print("  📊 STEP 1: Generating Job Data")
    print("─" * 60)

    try:
        from data_generator import generate_jobs, save_to_sqlite, save_to_csv

        jobs = generate_jobs(1500)
        save_to_sqlite(jobs, db_path="data/jobs.db")
        save_to_csv(jobs, csv_path="data/jobs_data.csv")
        print("✅ Data generation complete!\n")
        return True
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step_process_data():
    """Step 2: Clean and process data through NLP pipeline."""
    print("\n" + "─" * 60)
    print("  🧹 STEP 2: Processing Data (NLP Pipeline)")
    print("─" * 60)

    try:
        from data_processor import run_pipeline
        run_pipeline()
        print("✅ Data processing complete!\n")
        return True
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step_train_models():
    """Step 3: Train all ML models."""
    print("\n" + "─" * 60)
    print("  🤖 STEP 3: Training ML Models")
    print("─" * 60)

    success = True

    # Train salary prediction model
    print("\n▶ Training Salary Predictor...")
    try:
        from models.train_salary_model import train_and_evaluate
        train_and_evaluate()
        print("✅ Salary model trained!\n")
    except Exception as e:
        print(f"⚠ Salary model training failed: {e}")
        success = False

    # Train role classifier
    print("\n▶ Training Role Classifier...")
    try:
        from models.train_classifier import train_and_evaluate as train_classifier
        train_classifier()
        print("✅ Role classifier trained!\n")
    except Exception as e:
        print(f"⚠ Role classifier training failed: {e}")
        success = False

    # Train resume matcher (TF-IDF vectorizer)
    print("\n▶ Training Resume Matcher...")
    try:
        from models.resume_matcher import train_vectorizer
        train_vectorizer()
        print("✅ Resume matcher trained!\n")
    except Exception as e:
        print(f"⚠ Resume matcher training failed: {e}")
        success = False

    # Run trend analysis
    print("\n▶ Running Trend Analysis...")
    try:
        from models.trend_analyzer import get_trending_skills
        trends = get_trending_skills()
        print(f"   Found {len(trends.get('trending', []))} trending skills")
        print("✅ Trend analysis complete!\n")
    except Exception as e:
        print(f"⚠ Trend analysis failed: {e}")
        success = False

    return success


def step_start_app():
    """Step 4: Start the Flask application."""
    print("\n" + "─" * 60)
    print("  🚀 STEP 4: Starting Flask Application")
    print("─" * 60)

    try:
        # Verify data exists
        db_path = os.path.join(BASE_DIR, 'data', 'jobs.db')
        if not os.path.exists(db_path):
            print("⚠ No data found! Running data generation first...")
            step_generate_data()
            step_process_data()
            step_train_models()

        print("\n" + "═" * 60)
        print("  🔍 JobLens is ready!")
        print("  Open http://127.0.0.1:5000 in your browser")
        print("  Press Ctrl+C to stop the server")
        print("═" * 60 + "\n")

        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

    except KeyboardInterrupt:
        print("\n\n👋 JobLens server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='JobLens — Setup & Initialization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py          Full setup: generate data → process → train → start
  python setup.py --data   Only generate and process data
  python setup.py --train  Only train ML models
  python setup.py --app    Only start the web application
        """
    )
    parser.add_argument('--data', action='store_true',
                        help='Only generate and process data')
    parser.add_argument('--train', action='store_true',
                        help='Only train ML models')
    parser.add_argument('--app', action='store_true',
                        help='Only start the Flask app')

    args = parser.parse_args()
    banner()

    start_time = time.time()

    if args.data:
        step_generate_data()
        step_process_data()
    elif args.train:
        step_train_models()
    elif args.app:
        step_start_app()
    else:
        # Full setup pipeline
        if step_generate_data():
            if step_process_data():
                step_train_models()

        elapsed = time.time() - start_time
        print(f"\n⏱ Setup completed in {elapsed:.1f} seconds")

        step_start_app()


if __name__ == '__main__':
    main()
