import requests


class GitHubClient:
    def __init__(self, token=None, session=None):
        self.token = token
        self.session = session or requests.Session()

    def get_repos(self, username, per_page=100):
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": per_page, "sort": "updated"}

        response = self.session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return None, "GitHub user not found or API limit reached."

        repos = [repo for repo in response.json() if not repo.get("fork")]
        if not repos:
            return None, "No usable repositories found."

        return repos, None
