import requests
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()
import os

class PushOver:
    def __init__(self):
        self.api_key = os.getenv("PUSHOVER_API_KEY")
        self.user_key = os.getenv("PUSHOVER_USER_KEY")
        self.url = "https://api.pushover.net/1/messages.json"
        if not self.api_key or not self.user_key:
            logger.error("Pushover API Key or User Key not found in environment variables.")
            raise ValueError("Pushover API Key or User Key not found.")
    def send_message(self, message):
        data = {
            "token": self.api_key,
            "user": self.user_key,
            "message": message
        }
        try:
            response = requests.post(self.url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"Pushover message sent successfully: {message}")
            else:
                logger.error(f"Failed to send Pushover message. Status code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while sending Pushover message: {e}", exc_info=True)

