import sys
import os

# Add current directory to sys.path to allow imports from src
sys.path.append(os.getcwd())

def test_structure():
    print("Testing imports...")
    try:
        from src.models.assignment_models import Assignment, Submission, PeerReview
        print("✅ Models imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        sys.exit(1)

    try:
        from src.api.v1.assignments import router
        print("✅ API Router imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import API Router: {e}")
        sys.exit(1)

    try:
        from src.services.grading_service import auto_grade_code, check_plagiarism, ai_feedback
        print("✅ Services imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Services: {e}")
        sys.exit(1)

    try:
        from src.main import app
        print("✅ Main App imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Main App: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_structure()
