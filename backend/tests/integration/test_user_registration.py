"""
Integration tests for complete user registration flow.

Tests the end-to-end user registration process including:
- Account creation
- Email validation (if implemented)
- Initial user setup
- Default role assignment

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
from datetime import datetime


@pytest.mark.integration
class TestUserRegistrationFlow:
    """Integration tests for complete user registration workflow."""

    def test_complete_user_registration_success_flow(self, client):
        """Test complete successful user registration from start to finish."""
        # Arrange
        registration_data = {
            "username": "newuser123",
            "password": "securepassword123",
            "email": "newuser@example.com",
            "display_name": "New User"
        }
        
        # Act - Step 1: Register new user
        register_response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            content_type="application/json"
        )
        
        # Assert - Registration successful
        assert register_response.status_code == 201
        user_data = json.loads(register_response.data)
        
        # Validate user was created properly
        assert user_data["username"] == "newuser123"
        assert user_data["email"] == "newuser@example.com"
        assert user_data["display_name"] == "New User"
        assert user_data["is_active"] is True
        assert "id" in user_data
        assert "created_at" in user_data
        assert "role" in user_data
        
        # Validate default role assignment
        assert user_data["role"]["name"] in ["user", "member"]  # Default role
        
        # Act - Step 2: Verify user can login immediately after registration
        login_data = {
            "username": "newuser123",
            "password": "securepassword123"
        }
        
        login_response = client.post(
            "/api/v1/auth/login",
            json=login_data,
            content_type="application/json"
        )
        
        # Assert - Login successful
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["user"]["id"] == user_data["id"]
        
        # Act - Step 3: Verify user can access profile immediately
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        profile_response = client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        # Assert - Profile access successful
        assert profile_response.status_code == 200
        profile_data = json.loads(profile_response.data)
        assert profile_data["id"] == user_data["id"]
        assert profile_data["username"] == "newuser123"

    def test_user_registration_with_duplicate_username_fails(self, client):
        """Test that registering with existing username fails gracefully."""
        # Arrange
        first_user = {
            "username": "duplicateuser",
            "password": "password123",
            "email": "first@example.com"
        }
        
        second_user = {
            "username": "duplicateuser",  # Same username
            "password": "differentpass",
            "email": "second@example.com"
        }
        
        # Act - Register first user
        first_response = client.post(
            "/api/v1/auth/register",
            json=first_user,
            content_type="application/json"
        )
        
        # Assert - First user registered successfully
        assert first_response.status_code == 201
        
        # Act - Try to register second user with same username
        second_response = client.post(
            "/api/v1/auth/register", 
            json=second_user,
            content_type="application/json"
        )
        
        # Assert - Second registration fails with conflict
        assert second_response.status_code == 409
        
        # Verify first user can still login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "duplicateuser", "password": "password123"},
            content_type="application/json"
        )
        assert login_response.status_code == 200

    def test_user_registration_with_duplicate_email_fails(self, client):
        """Test that registering with existing email fails gracefully."""
        # Arrange
        first_user = {
            "username": "user1",
            "password": "password123",
            "email": "shared@example.com"
        }
        
        second_user = {
            "username": "user2",
            "password": "password123",
            "email": "shared@example.com"  # Same email
        }
        
        # Act - Register first user
        first_response = client.post(
            "/api/v1/auth/register",
            json=first_user,
            content_type="application/json"
        )
        
        # Assert - First user registered successfully
        assert first_response.status_code == 201
        
        # Act - Try to register second user with same email
        second_response = client.post(
            "/api/v1/auth/register",
            json=second_user,
            content_type="application/json"
        )
        
        # Assert - Second registration fails
        assert second_response.status_code in [409, 400]  # Conflict or bad request

    def test_user_registration_creates_default_preferences(self, client):
        """Test that user registration sets up default user preferences."""
        # Arrange
        user_data = {
            "username": "prefuser",
            "password": "password123",
            "email": "pref@example.com"
        }
        
        # Act - Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            content_type="application/json"
        )
        
        # Assert - User created successfully
        assert register_response.status_code == 201
        
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "prefuser", "password": "password123"},
            content_type="application/json"
        )
        login_data = json.loads(login_response.data)
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        
        # Check user profile has expected defaults
        profile_response = client.get("/api/v1/users/me", headers=headers)
        profile_data = json.loads(profile_response.data)
        
        # Validate default settings
        assert profile_data["is_active"] is True
        assert profile_data["role"]["name"] in ["user", "member"]  # Default role
        
        # User should be able to access public channels immediately
        channels_response = client.get("/api/v1/channels", headers=headers)
        assert channels_response.status_code == 200

    def test_user_registration_validates_password_strength(self, client):
        """Test that user registration enforces password requirements."""
        # Test cases for password validation
        weak_passwords = [
            "short",          # Too short
            "12345678",       # Only numbers
            "password",       # Common weak password
            "ALLUPPERCASE",   # Only uppercase
            "alllowercase",   # Only lowercase
        ]
        
        for weak_password in weak_passwords:
            # Arrange
            user_data = {
                "username": f"user_{weak_password[:4]}",
                "password": weak_password,
                "email": f"{weak_password[:4]}@example.com"
            }
            
            # Act
            response = client.post(
                "/api/v1/auth/register",
                json=user_data,
                content_type="application/json"
            )
            
            # Assert - Weak password rejected
            assert response.status_code == 400

    def test_user_registration_validates_email_format(self, client):
        """Test that user registration validates email format."""
        # Test cases for invalid email formats
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@missinglocal.com",
            "spaces @domain.com",
            "double@@domain.com",
            "toolong" + "x" * 255 + "@domain.com"
        ]
        
        for invalid_email in invalid_emails:
            # Arrange
            user_data = {
                "username": f"user_{hash(invalid_email) % 1000}",
                "password": "validpassword123",
                "email": invalid_email
            }
            
            # Act
            response = client.post(
                "/api/v1/auth/register",
                json=user_data,
                content_type="application/json"
            )
            
            # Assert - Invalid email rejected
            assert response.status_code == 400

    def test_user_registration_handles_database_errors_gracefully(self, client):
        """Test that registration handles database errors gracefully."""
        # This test would simulate database connection issues
        # In a real implementation, you might mock the database layer
        # to simulate various error conditions
        
        # Arrange - Simulate user registration during database issues
        user_data = {
            "username": "dbtest",
            "password": "password123", 
            "email": "dbtest@example.com"
        }
        
        # Act - This would normally succeed, but simulated DB issues might cause 500
        response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            content_type="application/json"
        )
        
        # Assert - Should handle gracefully (not crash)
        # Either success (201) or proper error response (500, but not a crash)
        assert response.status_code in [201, 500, 503]
        
        if response.status_code in [500, 503]:
            # Verify error response is well-formatted
            error_data = json.loads(response.data)
            assert "error" in error_data or "message" in error_data

    def test_concurrent_user_registrations_handle_race_conditions(self, client):
        """Test that concurrent registrations with same username are handled properly."""
        # This test simulates race conditions during user registration
        # In practice, you'd use threading or async testing for true concurrency
        
        # Arrange
        base_user = {
            "username": "raceuser",
            "password": "password123",
            "email": "race@example.com"
        }
        
        # Act - Simulate rapid successive registration attempts
        # (In real concurrent testing, these would run simultaneously)
        responses = []
        for i in range(3):
            user_data = base_user.copy()
            user_data["email"] = f"race{i}@example.com"  # Different emails
            
            response = client.post(
                "/api/v1/auth/register",
                json=user_data,
                content_type="application/json"
            )
            responses.append(response)
        
        # Assert - Only one registration should succeed
        success_count = sum(1 for r in responses if r.status_code == 201)
        conflict_count = sum(1 for r in responses if r.status_code == 409)
        
        assert success_count == 1  # Exactly one success
        assert conflict_count >= 1  # At least one conflict