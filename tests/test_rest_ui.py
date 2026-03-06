import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Mock RedisService and UIService before importing app from src.RestUI
with patch('services.RedisService.RedisService'), \
     patch('services.UIService.UIService.process_startup_files'):
    from src.RestUI import app

@pytest.fixture
def client():
    # We need to patch the ui_service before the app is fully initialized
    # to prevent the process_startup_files from running.
    with patch('src.RestUI.ui_service', new_callable=MagicMock) as mock_service:
        # Prevent process_startup_files from being called
        mock_service.process_startup_files.return_value = None
        yield TestClient(app)


@pytest.fixture
def mock_ui_service():
    # This mock is for tests where we want to control the ui_service behavior
    # within the test function itself.
    with patch('src.RestUI.ui_service', new_callable=MagicMock) as mock_service:
        yield mock_service

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_success(client):
    # Because the ui_service is already mocked in the client fixture,
    # we can access it through the app's dependency injection override.
    # However, for clarity and explicit mocking in tests, we can re-patch it
    # or rely on the initial patch. For this test, we will assume the client
    # fixture's patch is sufficient and we can control its behavior by re-patching.
    with patch('src.RestUI.ui_service') as mock_service:
        mock_service.chatToTwin.return_value = "Hello from the twin"
        
        response = client.post("/chat", json={"message": "Hello", "session_id": "123"})
        
        assert response.status_code == 200
        assert response.json() == {"response": "Hello from the twin", "session_id": "123"}
        mock_service.chatToTwin.assert_called_once_with("Hello", "123")

def test_chat_exception(client):
    with patch('src.RestUI.ui_service') as mock_service:
        mock_service.chatToTwin.side_effect = Exception("Something went wrong")
        
        response = client.post("/chat", json={"message": "Hello", "session_id": "12_3"})
        
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error during chat processing."}
