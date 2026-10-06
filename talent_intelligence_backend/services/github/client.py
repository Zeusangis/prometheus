import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

API = "https://api.github.com"
MAX_REQUESTS = 40
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
BUDGET_SECONDS = 90
REQUEST_TIMEOUT = 5
USERNAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
REPO_NAME = re.compile(r"[A-Za-z0-9_.-]{1,100}")


class GitHubUnavailable(RuntimeError):
    """Only controlled, non-secret messages may be returned to a recruiter."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHubClient:
    def __init__(self):
        self.headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "TrueHire-evidence"}
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            self.headers["Authorization"] = "Bearer " + token
        self.opener = build_opener(NoRedirect())
        self.requests = 0
        self.deadline = time.monotonic() + BUDGET_SECONDS

    def get(self, path, params=None, *, empty_repo=False):
        if not path.startswith("/") or path.startswith("//") or "?" in path or "#" in path:
            raise GitHubUnavailable("Invalid GitHub evidence path.")
        remaining = self.deadline - time.monotonic()
        if self.requests >= MAX_REQUESTS or remaining <= 0:
            raise GitHubUnavailable("GitHub evidence collection reached its request or time limit. Retry later.")
        self.requests += 1
        request = Request(API + path + ("?" + urlencode(params) if params else ""), headers=self.headers)
        try:
            with self.opener.open(request, timeout=min(REQUEST_TIMEOUT, remaining)) as response:
                # Bounded streaming avoids loading arbitrary large trees/blobs into memory.
                chunks, size = [], 0
                while True:
                    if time.monotonic() >= self.deadline:
                        raise GitHubUnavailable("GitHub evidence collection reached its time limit. Retry later.")
                    chunk = response.read(min(65536, MAX_RESPONSE_BYTES + 1 - size))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise GitHubUnavailable("GitHub evidence response exceeded the size limit.")
                data = json.loads(b"".join(chunks))
                return data, response.headers
        except HTTPError as error:
            if error.code == 409 and empty_repo:
                return [], {}
            if error.code in {403, 429}:
                raise GitHubUnavailable("GitHub access or rate limit prevented analysis. Retry later.") from error
            if error.code == 404:
                raise GitHubUnavailable("GitHub profile or public repository was not found.") from error
            raise GitHubUnavailable("GitHub evidence is temporarily unavailable. Retry later.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise GitHubUnavailable("GitHub could not be reached. Retry later.") from error
        except (ValueError, UnicodeError) as error:
            raise GitHubUnavailable("GitHub returned invalid evidence data.") from error


def require_dict(value):
    if not isinstance(value, dict):
        raise GitHubUnavailable("GitHub returned invalid evidence data.")
    return value


def require_list(value):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise GitHubUnavailable("GitHub returned invalid evidence data.")
    return value


def nonnegative_int(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GitHubUnavailable("GitHub returned invalid evidence counts.")
    return value
