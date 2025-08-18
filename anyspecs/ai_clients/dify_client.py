"""
Dify client for file-upload workflow compression.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from .base_client import BaseAIClient
from ..utils.logging import get_logger


logger = get_logger("dify_client")


class DifyClient(BaseAIClient):
    """Dify API client.

    Note: process_text is not used; Dify works via file upload + workflow run.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "",  # unused
        base_url: Optional[str] = None,
        timeout: int = 120,
        **kwargs,
    ):
        super().__init__(api_key, model, **kwargs)
        self.base_url = (base_url or "https://api.dify.ai/v1").rstrip("/")
        self.timeout = timeout
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })

    @property
    def provider_name(self) -> str:
        return "dify"

    def process_text(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        # Not applicable for Dify workflow in this integration
        self.logger.warning("process_text is not supported for Dify client in this context")
        return None

    def test_connection(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/files/upload", timeout=10)
            return resp.status_code in (200, 405)  # 405 for method not allowed is acceptable
        except Exception as e:
            self.logger.error(f"Dify connection test failed: {e}")
            return False

    def upload_file(self, file_path: Path, user: str = "anyspecs-cli") -> Optional[str]:
        upload_url = f"{self.base_url}/files/upload"
        try:
            original = file_path.name
            clean_filename = re.sub(r'[:<>"|?*]', '_', original)
            ext = file_path.suffix.lower()
            if ext in (".md", ".txt"):
                file_type = "TXT"; mime = "text/plain"
            elif ext == ".pdf":
                file_type = "PDF"; mime = "application/pdf"
            else:
                file_type = "TXT"; mime = "text/plain"

            with open(file_path, "rb") as f:
                files = {"file": (clean_filename, f, mime)}
                data = {"user": user, "type": file_type}
                resp = self.session.post(upload_url, files=files, data=data, timeout=self.timeout)
            if resp.status_code == 201:
                result = resp.json()
                return result.get("id")
            self.logger.error(f"Dify upload failed: HTTP {resp.status_code} - {resp.text}")
            return None
        except Exception as e:
            self.logger.error(f"Dify upload error: {e}")
            return None

    def run_workflow(self, file_id: str, user: str = "anyspecs-cli", response_mode: str = "blocking") -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/workflows/run"
        try:
            payload = {
                "inputs": {
                    "files": {
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": "document",
                    }
                },
                "response_mode": response_mode,
                "user": user,
            }
            headers = {"Content-Type": "application/json"}
            resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            self.logger.error(f"Dify workflow failed: HTTP {resp.status_code} - {resp.text}")
            return None
        except Exception as e:
            self.logger.error(f"Dify workflow error: {e}")
            return None


