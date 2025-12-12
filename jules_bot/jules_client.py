import json
import logging
from datetime import datetime

"""Jules API Client."""
import requests

logger = logging.getLogger(__name__)

class JulesClient:
    """Client for interacting with the Jules API."""

    BASE_URL = "https://jules.googleapis.com/v1alpha"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.log_file = "jules_api.log"

    def _log_response(self, endpoint: str, response_data: dict):
        """Logs raw API responses to a file for debugging."""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "endpoint": endpoint,
                "response": response_data
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("Failed to log API response: %s", e)

    def list_sessions(self, page_size: int = 10) -> dict:
        """Fetches a list of sessions."""
        url = f"{self.BASE_URL}/sessions"
        params = {"pageSize": page_size}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._log_response("list_sessions", data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching sessions: %s", e)
            return {}

    def get_session(self, session_id: str) -> dict:
        """Fetches details for a specific session."""
        # Strip "sessions/" prefix if present
        clean_id = session_id.replace("sessions/", "")

        url = f"{self.BASE_URL}/sessions/{clean_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._log_response(f"get_session/{clean_id}", data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching session %s: %s", clean_id, e)
            return {}

    def list_activities(self, session_id: str, page_size: int = 30) -> dict:
        """
        Fetches activities for a specific session.
        session_id can be the raw ID or 'sessions/ID'.
        """
        # Strip "sessions/" prefix if present
        clean_id = session_id.replace("sessions/", "")

        url = f"{self.BASE_URL}/sessions/{clean_id}/activities"
        params = {"pageSize": page_size}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._log_response(f"list_activities/{clean_id}", data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching activities for session %s: %s", clean_id, e)
            return {}

    def create_session(self, repo_owner: str, repo_name: str, prompt: str, branch: str = "main") -> dict:
        """Creates a new session."""
        url = f"{self.BASE_URL}/sessions"
        payload = {
            "sourceContext": {
                "source": f"sources/github/{repo_owner}/{repo_name}",
                "githubRepoContext": {
                    "startingBranch": branch
                }
            },
            "prompt": prompt
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            self._log_response("create_session", data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error creating session: %s", e)
            if e.response is not None:
                logger.error("API Response: %s", e.response.text)
            return {}
