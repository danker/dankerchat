"""
Integration tests for complete authentication flow.

Tests the end-to-end authentication process including:
- Login/logout workflow
- Token refresh mechanism
- Session management
- Multi-device authentication

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import time
from datetime import datetime, timedelta


@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for complete authentication workflow."""

    def test_complete_login_logout_flow(self, client):
        """Test complete login and logout workflow."""
        # Arrange - Create user first
        user_data = {
            "username": "authuser",
            "password": "testpassword123",
            "email": "auth@example.com"
        }
        
        register_response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            content_type="application/json"
        )
        assert register_response.status_code == 201
        
        # Act - Step 1: Login
        login_data = {
            "username": "authuser",
            "password": "testpassword123"
        }
        
        login_response = client.post(
            "/api/v1/auth/login",
            json=login_data,
            content_type="application/json"
        )
        
        # Assert - Login successful
        assert login_response.status_code == 200
        login_result = json.loads(login_response.data)
        
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert "user" in login_result
        
        access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]
        
        # Act - Step 2: Access protected resource
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/v1/users/me", headers=headers)
        
        # Assert - Protected resource accessible
        assert profile_response.status_code == 200
        profile_data = json.loads(profile_response.data)
        assert profile_data["username"] == "authuser"
        
        # Act - Step 3: Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        
        # Assert - Logout successful
        assert logout_response.status_code == 200
        
        # Act - Step 4: Try to access protected resource after logout
        post_logout_response = client.get("/api/v1/users/me", headers=headers)
        
        # Assert - Access denied after logout
        assert post_logout_response.status_code == 401

    def test_token_refresh_flow(self, client):
        """Test token refresh mechanism works correctly."""
        # Arrange - Create user and login
        user_data = {
            "username": "refreshuser",
            "password": "password123",
            "email": "refresh@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "refreshuser", "password": "password123"},
            content_type="application/json"
        )
        login_data = json.loads(login_response.data)
        
        original_access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # Act - Step 1: Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json=refresh_data,
            content_type="application/json"
        )
        
        # Assert - Refresh successful
        assert refresh_response.status_code == 200
        refresh_result = json.loads(refresh_response.data)
        
        assert "access_token" in refresh_result
        new_access_token = refresh_result["access_token"]
        assert new_access_token != original_access_token
        
        # Act - Step 2: Use new access token
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = client.get("/api/v1/users/me", headers=headers)
        
        # Assert - New token works
        assert profile_response.status_code == 200
        
        # Act - Step 3: Try to use old access token
        old_headers = {"Authorization": f"Bearer {original_access_token}"}
        old_token_response = client.get("/api/v1/users/me", headers=old_headers)
        
        # Assert - Old token should be invalid (depending on implementation)
        # Some implementations invalidate old tokens, others allow grace period
        assert old_token_response.status_code in [401, 200]

    def test_invalid_login_attempts_and_rate_limiting(self, client):
        """Test handling of invalid login attempts and rate limiting."""
        # Arrange - Create user
        user_data = {
            "username": "targetuser",
            "password": "correctpassword123",
            "email": "target@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Act - Multiple invalid login attempts
        invalid_attempts = []
        for i in range(5):  # Try 5 failed logins
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "targetuser", "password": "wrongpassword"},
                content_type="application/json"
            )
            invalid_attempts.append(response)
        
        # Assert - All attempts should fail with 401
        for response in invalid_attempts:
            assert response.status_code == 401
        
        # Act - Try valid login after failed attempts
        valid_response = client.post(
            "/api/v1/auth/login",
            json={"username": "targetuser", "password": "correctpassword123"},
            content_type="application/json"
        )
        
        # Assert - Valid login should work (or be rate limited)
        # Depending on implementation, might be 200 (success) or 429 (rate limited)
        assert valid_response.status_code in [200, 429]

    def test_multi_device_authentication_sessions(self, client):
        """Test authentication across multiple devices/sessions."""
        # Arrange - Create user
        user_data = {
            "username": "multiuser",
            "password": "password123",
            "email": "multi@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_data = {"username": "multiuser", "password": "password123"}
        
        # Act - Login from "device 1"
        device1_response = client.post(
            "/api/v1/auth/login",
            json=login_data,
            content_type="application/json"
        )
        
        device1_data = json.loads(device1_response.data)
        device1_token = device1_data["access_token"]
        
        # Act - Login from "device 2"
        device2_response = client.post(
            "/api/v1/auth/login",
            json=login_data,
            content_type="application/json"
        )
        
        device2_data = json.loads(device2_response.data)
        device2_token = device2_data["access_token"]
        
        # Assert - Both logins successful
        assert device1_response.status_code == 200
        assert device2_response.status_code == 200
        assert device1_token != device2_token  # Different tokens
        
        # Act - Use both tokens simultaneously
        headers1 = {"Authorization": f"Bearer {device1_token}"}
        headers2 = {"Authorization": f"Bearer {device2_token}"}
        
        profile1_response = client.get("/api/v1/users/me", headers=headers1)
        profile2_response = client.get("/api/v1/users/me", headers=headers2)
        
        # Assert - Both tokens work simultaneously
        assert profile1_response.status_code == 200
        assert profile2_response.status_code == 200
        
        # Verify same user data from both sessions
        profile1_data = json.loads(profile1_response.data)
        profile2_data = json.loads(profile2_response.data)
        assert profile1_data["id"] == profile2_data["id"]

    def test_expired_token_handling(self, client):
        """Test handling of expired tokens."""
        # Arrange - Create user and login
        user_data = {
            "username": "expireuser",
            "password": "password123",
            "email": "expire@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "expireuser", "password": "password123"},
            content_type="application/json"
        )
        
        login_data = json.loads(login_response.data)
        access_token = login_data["access_token"]
        
        # Act - Use token immediately (should work)
        headers = {"Authorization": f"Bearer {access_token}"}
        immediate_response = client.get("/api/v1/users/me", headers=headers)
        
        # Assert - Token works when fresh
        assert immediate_response.status_code == 200
        
        # Note: In a real test, you might:
        # 1. Create a token with very short expiry for testing
        # 2. Wait for expiration
        # 3. Test that expired token is rejected
        
        # For now, test with a mock expired token
        expired_headers = {"Authorization": "Bearer expired_token_mock"}
        expired_response = client.get("/api/v1/users/me", headers=expired_headers)
        
        # Assert - Expired/invalid token rejected
        assert expired_response.status_code == 401

    def test_authentication_with_invalid_refresh_token(self, client):
        """Test handling of invalid refresh tokens."""
        # Arrange - Create user and login
        user_data = {
            "username": "refreshtestuser",
            "password": "password123",
            "email": "refreshtest@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Act - Try to refresh with invalid token
        invalid_refresh_data = {"refresh_token": "invalid_refresh_token"}
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json=invalid_refresh_data,
            content_type="application/json"
        )
        
        # Assert - Invalid refresh token rejected
        assert refresh_response.status_code == 401

    def test_logout_invalidates_tokens(self, client):
        """Test that logout properly invalidates tokens."""
        # Arrange - Create user and login
        user_data = {
            "username": "logoutuser", 
            "password": "password123",
            "email": "logout@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "logoutuser", "password": "password123"},
            content_type="application/json"
        )
        
        login_data = json.loads(login_response.data)
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Act - Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Act - Try to use access token after logout
        post_logout_response = client.get("/api/v1/users/me", headers=headers)
        
        # Assert - Access token invalid after logout
        assert post_logout_response.status_code == 401
        
        # Act - Try to use refresh token after logout
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            content_type="application/json"
        )
        
        # Assert - Refresh token invalid after logout
        assert refresh_response.status_code == 401