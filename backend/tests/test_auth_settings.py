class TestAuthSettingsRoutes:
    def test_register_login_and_update_integrations(self, client):
        register_payload = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        }

        register_response = client.post("/auth/register", json=register_payload)
        assert register_response.status_code == 201
        token = register_response.json()["token"]

        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["email"] == "test@example.com"

        settings_payload = {
            "linkedin_access_token": "linkedin-token",
            "linkedin_person_urn": "urn:li:person:123",
            "devto_api_key": "devto-key",
            "whatsapp_number": "+911234567890",
            "timezone": "Asia/Kolkata",
            "reminder_time": "09:00",
            "is_whatsapp_enabled": True,
            "ai_provider": "gemini",
            "gemini_api_key": "gemini-key",
            "openai_api_key": None,
            "perplexity_api_key": None,
            "publish_platforms": ["devto"],
        }

        settings_response = client.put(
            "/settings/integrations",
            json=settings_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert settings_response.status_code == 200
        body = settings_response.json()
        assert body["connected"]["devto"] is True
        assert body["connected"]["linkedin"] is True
        assert body["connected"]["whatsapp"] is True

    def test_settings_requires_authentication(self, client):
        response = client.get("/settings/integrations")
        assert response.status_code == 401
