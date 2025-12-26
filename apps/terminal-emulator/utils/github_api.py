"""
GitHub API - OAuth authentication and leaderboard management
Uses GitHub Contents API to store leaderboard as JSON in a repository
"""
import json
import requests
from typing import Optional, List, Dict
from datetime import datetime
import base64


class GitHubAPI:
    """
    GitHub API client for authentication and leaderboard operations.

    The leaderboard is stored as a JSON file in a GitHub repository.
    This eliminates the need for a backend server.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize GitHub API client.

        Args:
            client_id: GitHub OAuth app client ID
            client_secret: GitHub OAuth app client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None

    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        Exchange OAuth authorization code for access token.

        Args:
            code: Authorization code from GitHub OAuth callback

        Returns:
            Access token string, or None if exchange failed
        """
        url = "https://github.com/login/oauth/access_token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        headers = {"Accept": "application/json"}

        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                self.access_token = result["access_token"]
                return self.access_token
            else:
                print(f"OAuth error: {result.get('error_description', 'Unknown error')}")
                return None

        except requests.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return None

    def get_user_info(self) -> Optional[Dict]:
        """
        Get authenticated user's information.

        Returns:
            Dict with user info (login, name, avatar_url, etc.) or None
        """
        if not self.access_token:
            return None

        url = f"{self.BASE_URL}/user"
        headers = {"Authorization": f"token {self.access_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting user info: {e}")
            return None

    def get_leaderboard(self, repo_owner: str, repo_name: str, file_path: str) -> List[Dict]:
        """
        Fetch leaderboard from GitHub repository.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            file_path: Path to leaderboard JSON file in repo

        Returns:
            List of leaderboard entries (sorted by score desc)
        """
        url = f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{file_path}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.json()

            # Decode base64 content
            file_content = base64.b64decode(content["content"]).decode("utf-8")
            leaderboard = json.loads(file_content)

            # Sort by score descending
            leaderboard.sort(key=lambda x: x.get("score", 0), reverse=True)
            return leaderboard

        except requests.RequestException as e:
            print(f"Error fetching leaderboard: {e}")
            return []
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing leaderboard: {e}")
            return []

    def submit_score(
        self,
        repo_owner: str,
        repo_name: str,
        file_path: str,
        username: str,
        score: int,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Submit a score to the leaderboard.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            file_path: Path to leaderboard JSON file
            username: User's GitHub username
            score: Score to submit
            metadata: Optional metadata (command, duration, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.access_token:
            print("Error: Not authenticated")
            return False

        # Get current leaderboard
        current_leaderboard = self.get_leaderboard(repo_owner, repo_name, file_path)

        # Add new entry
        new_entry = {
            "username": username,
            "score": score,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        current_leaderboard.append(new_entry)

        # Sort and keep top 100
        current_leaderboard.sort(key=lambda x: x.get("score", 0), reverse=True)
        current_leaderboard = current_leaderboard[:100]

        # Get current file SHA (required for update)
        url = f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        headers = {"Authorization": f"token {self.access_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            current_sha = response.json()["sha"]
        except requests.RequestException:
            # File doesn't exist yet, create it
            current_sha = None

        # Update file
        content_json = json.dumps(current_leaderboard, indent=2)
        content_b64 = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")

        data = {
            "message": f"Add score: {username} - {score}",
            "content": content_b64,
            "branch": "main",
        }

        if current_sha:
            data["sha"] = current_sha

        try:
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            print(f"Score submitted successfully: {username} - {score}")
            return True
        except requests.RequestException as e:
            print(f"Error submitting score: {e}")
            return False
