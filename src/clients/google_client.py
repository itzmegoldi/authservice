from typing import Any

from google.auth.transport import requests
from google.oauth2 import id_token


class GoogleClient:
    def verify_id_token(self, token: str, audience: str) -> dict[str, Any]:
        return id_token.verify_oauth2_token(token, requests.Request(), audience)
