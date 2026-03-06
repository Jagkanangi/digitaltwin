import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True, scope="session")
def mock_redis():
    """
    Globally mock redis.Redis to prevent ConnectionError during tests.
    This fixture is autouse=True and session-scoped, so it applies to all tests.
    """
    with patch("redis.Redis") as mock:
        mock_client = MagicMock()
        # Mock ping to return True so RedisService initialization succeeds
        mock_client.ping.return_value = True
        mock.return_value = mock_client
        yield mock_client
