"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test suite for the /activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_drama_club(self):
        """Test that Drama Club activity exists"""
        response = client.get("/activities")
        data = response.json()
        assert "Drama Club" in data


class TestSignupEndpoint:
    """Test suite for the signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        email = "test_student@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_activity_not_found(self):
        """Test signup with non-existent activity"""
        email = "test_student@mergington.edu"
        activity_name = "Non-existent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_already_registered(self):
        """Test signup when student is already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_with_url_encoded_activity_name(self):
        """Test signup with URL-encoded activity name (spaces)"""
        email = "test_student_2@mergington.edu"
        activity_name = "Drama Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify the student was actually added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_signup_updates_participant_list(self):
        """Test that signup actually adds participant to the list"""
        email = "new_student@mergington.edu"
        activity_name = "Programming Class"
        
        # Get initial participants
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Check updated count
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        
        assert updated_count == initial_count + 1
        assert email in updated_response.json()[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Test suite for the unregister endpoint"""

    def test_unregister_from_activity_success(self):
        """Test successful unregistration from an activity"""
        email = "test_unregister@mergington.edu"
        activity_name = "Art Club"
        
        # First, sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Then unregister
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_unregister_activity_not_found(self):
        """Test unregister with non-existent activity"""
        email = "test_student@mergington.edu"
        activity_name = "Non-existent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_not_signed_up(self):
        """Test unregister when student is not signed up"""
        email = "not_registered@mergington.edu"
        activity_name = "Basketball Club"
        
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes participant from the list"""
        email = "remove_me@mergington.edu"
        activity_name = "Debate Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Verify removal
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]

    def test_unregister_with_existing_participant(self):
        """Test unregistering an initially registered participant"""
        # michael@mergington.edu is initially in Chess Club
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify removal
        updated_response = client.get("/activities")
        assert email not in updated_response.json()[activity_name]["participants"]


class TestRootEndpoint:
    """Test suite for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivityData:
    """Test suite for validating activity data structure"""

    def test_all_activities_have_positive_max_participants(self):
        """Test that all activities have positive max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert activity_details["max_participants"] > 0

    def test_participants_count_does_not_exceed_max(self):
        """Test that participant count doesn't exceed max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert len(activity_details["participants"]) <= activity_details["max_participants"]

    def test_drama_club_has_initial_participants(self):
        """Test that Drama Club has initial participants"""
        response = client.get("/activities")
        data = response.json()
        assert len(data["Drama Club"]["participants"]) > 0
        assert "mia@mergington.edu" in data["Drama Club"]["participants"]
