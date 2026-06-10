# backend/tests/test_auth_settings.py

import httpx
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="package")


@pytest.fixture(autouse=True)
async def cleanup_database_before_test(app_module):
    await app_module.db.users.delete_many(
        {"email": "test@example.com"}
    )

    await app_module.db.integration_settings.delete_many(
        {"user_id": {"$exists": True}}
    )

    yield

    await app_module.db.users.delete_many(
        {"email": "test@example.com"}
    )


class TestAuthSettingsRoutes:

    async def test_register_login_and_update_integrations(self, app_module):
        """End-to-End verification of auth, session access, and system updates."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_module.app), base_url="http://test") as client:

            # 1. Registration Test
            register_payload = {
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123",
            }
            register_response = await client.post("/auth/register", json=register_payload)
            assert register_response.status_code == 201
            token = register_response.json()["token"]
            assert token is not None

            # 2. Login Verification
            login_response = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "password123"},
            )
            assert login_response.status_code == 200
            assert login_response.json()["user"]["email"] == "test@example.com"

            # 3. Settings Form Updating
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

            settings_response = await client.put(
                "/settings/integrations",
                json=settings_payload,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert settings_response.status_code == 200
            body = settings_response.json()

            assert body["connected"]["devto"] is True
            assert body["connected"]["linkedin"] is True
            assert body["connected"]["whatsapp"] is True

            # 4. State Document Validation Check
            user_doc = await app_module.db.users.find_one({"email": "test@example.com"})
            assert user_doc is not None

    async def test_settings_requires_authentication(self, app_module):
        """Verify endpoint blocks requests missing a valid Bearer token."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_module.app), base_url="http://test") as client:
            response = await client.get("/settings/integrations")
            assert response.status_code == 401
