import pytest
from app import app, db, SwingLog
import json

@pytest.fixture
def client():
    """Sets up a test client for the Flask app"""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use an in-memory DB for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create tables in memory
        yield client  # Provide test client
        with app.app_context():
            db.drop_all()  # Clean up after tests

# 1. Test if API returns feedback successfully
def test_feedback_api(client):
    response = client.post("/feedback", 
                           data=json.dumps({"swing_issue": "My swing slices right"}), 
                           content_type="application/json")
    
    assert response.status_code == 200  # Check if request was successful
    data = response.get_json()
    assert "feedback" in data  # Ensure response contains AI-generated feedback
    assert isinstance(data["feedback"], str)  # Feedback should be a string

# 2. Test if invalid requests are handled properly
def test_feedback_invalid_request(client):
    response = client.post("/feedback", data=json.dumps({}), content_type="application/json")  # Missing "swing_issue"
    
    assert response.status_code == 500  # Expecting internal server error due to missing input

# 3. Test if feedback is logged correctly in the database
def test_feedback_logging(client):
    swing_issue = "My backswing is too fast"
    response = client.post("/feedback", 
                           data=json.dumps({"swing_issue": swing_issue}), 
                           content_type="application/json")
    
    assert response.status_code == 200  # Check if request was successful

    # Check if feedback is saved in the database
    with app.app_context():
        log_entry = SwingLog.query.filter_by(swing_issue=swing_issue).first()
        assert log_entry is not None  # Entry should exist
        assert isinstance(log_entry.feedback, str)  # Stored feedback should be a string

# 4. Test retrieving saved feedback logs
def test_logs_api(client):
    swing_issue = "My clubface is too open at impact"
    response = client.post("/feedback", 
                           data=json.dumps({"swing_issue": swing_issue}), 
                           content_type="application/json")
    assert response.status_code == 200  # Ensure feedback request succeeds

    # Now retrieve logs
    response = client.get("/logs")
    assert response.status_code == 200  # Check if request was successful
    data = response.get_json()
    assert isinstance(data, list)  # Logs should be returned as list
    assert len(data) > 0  # At least one log should exist
    assert any(log["swing_issue"] == swing_issue for log in data)  # Ensure logged issue exists