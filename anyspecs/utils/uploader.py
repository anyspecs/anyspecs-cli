"""
Reusable upload client for AnySpecs CLI.
"""

from __future__ import annotations

import requests
from pathlib import Path
from typing import Optional


class AnySpecsUploadClient:
    """AnySpecs file upload client"""

    def __init__(
        self,
        base_url: str = "https://hub.anyspecs.cn/",
        token: Optional[str] = None,
        use_http: bool = False,
    ):
        """Initialize client.

        Args:
            base_url: API base URL
            token: User access token (bearer-like string)
            use_http: Force using HTTP instead of HTTPS (diagnostics only)
        """
        self.base_url = base_url.rstrip("/")
        if use_http and self.base_url.startswith("https://"):
            self.base_url = self.base_url.replace("https://", "http://", 1)

        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AnySpecs-Upload-Client/1.0.0",
            "Accept": "application/json",
        })
        if self.token:
            self.session.headers.update({"Authorization": self.token})

    def set_token(self, token: str) -> None:
        self.token = token
        self.session.headers.update({"Authorization": token})

    def test_connection(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/api/status", timeout=10)
            if resp.status_code != 200:
                print(f"❌ Connection failed: HTTP {resp.status_code}")
                return False
            data = resp.json()
            if not data.get("success"):
                print(f"❌ Connection failed: {data.get('message', 'Unknown error')}")
                return False
            print(
                f"✅ Connection successful! System name: {data.get('data', {}).get('system_name', 'Unknown')}"
            )
            return True
        except requests.exceptions.SSLError as e:  # type: ignore[attr-defined]
            print(f"❌ SSL connection error: {e}")
            print("💡 This might be due to:")
            print("   - Network firewall blocking SSL connections")
            print("   - SSL certificate issues")
            print("   - Network instability")
            print("💡 Try using --http flag for testing: anyspecs upload --http --list")
            return False
        except requests.exceptions.Timeout as e:  # type: ignore[attr-defined]
            print(f"❌ Connection timeout: {e}")
            print("💡 The server might be slow or network is unstable")
            return False
        except requests.exceptions.ConnectionError as e:  # type: ignore[attr-defined]
            print(f"❌ Connection error: {e}")
            print("💡 Please check:")
            print("   - Network connection")
            print("   - Server URL is correct")
            print("   - Server is running")
            return False
        except requests.exceptions.RequestException as e:  # type: ignore[attr-defined]
            print(f"❌ Connection error: {e}")
            return False

    def validate_token(self) -> bool:
        if not self.token:
            print("❌ Access token not set")
            return False
        try:
            resp = self.session.get(f"{self.base_url}/api/file/")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    print("✅ Token validation successful!")
                    print("   Can access file management functionality")
                    return True
                print(f"❌ Token validation failed: {data.get('message', 'Unknown error')}")
                return False
            if resp.status_code == 401:
                print("❌ Token validation failed: Unauthorized access")
                return False
            print(f"❌ Token validation failed: HTTP {resp.status_code}")
            if resp.text:
                try:
                    err = resp.json()
                    print(f"   Error message: {err.get('message', 'Unknown error')}")
                except Exception:
                    print(f"   Response content: {resp.text}")
            return False
        except requests.exceptions.RequestException as e:  # type: ignore[attr-defined]
            print(f"❌ Token validation error: {e}")
            return False

    def upload_file(self, file_path: str, description: str = "") -> bool:
        if not self.token:
            print("❌ Access token not set")
            return False
        p = Path(file_path)
        if not p.exists():
            print(f"❌ File does not exist: {p}")
            return False
        if not p.is_file():
            print(f"❌ Not a valid file: {p}")
            return False
        size = p.stat().st_size
        if size == 0:
            print(f"❌ File is empty: {p}")
            return False

        print(f"📁 Preparing to upload file: {p.name}")
        print(f"   Size: {self._format_file_size(size)}")
        print(f"   Description: {description or 'No description'}")

        try:
            files = {"file": (p.name, open(p, "rb"), "application/octet-stream")}
            data = {"description": description} if description else {}
            resp = self.session.post(f"{self.base_url}/api/file/", files=files, data=data)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    print("✅ File upload successful!")
                    return True
                print(f"❌ Upload failed: {result.get('message', 'Unknown error')}")
                return False
            print(f"❌ Upload failed: HTTP {resp.status_code}")
            if resp.text:
                try:
                    err = resp.json()
                    print(f"   Error message: {err.get('message', 'Unknown error')}")
                except Exception:
                    print(f"   Response content: {resp.text}")
            return False
        except requests.exceptions.RequestException as e:  # type: ignore[attr-defined]
            print(f"❌ Upload request error: {e}")
            return False
        except Exception as e:
            print(f"❌ Upload process error: {e}")
            return False

    def list_files(self, page: int = 0, search: str = "") -> bool:
        if not self.token:
            print("❌ Access token not set")
            return False
        try:
            params = {"p": page}
            if search:
                params["keyword"] = search
            if search:
                resp = self.session.get(f"{self.base_url}/api/file/search", params=params)
            else:
                resp = self.session.get(f"{self.base_url}/api/file/", params=params)
            if resp.status_code != 200:
                print(f"❌ Failed to get file list: HTTP {resp.status_code}")
                return False
            result = resp.json()
            if not result.get("success"):
                print(f"❌ Failed to get file list: {result.get('message', 'Unknown error')}")
                return False
            files = result.get("data", [])
            if not files:
                print("📋 No files available")
                return True
            print(f"📋 File list (Page {page + 1}):")
            print("-" * 80)
            print(f"{'ID':<4} {'Filename':<30} {'Size':<10} {'Uploader':<15} {'Upload Time':<20}")
            print("-" * 80)
            for info in files:
                file_id = info.get("id", "N/A")
                filename_full = info.get("filename", "N/A")
                filename = (
                    filename_full[:28] + ".." if len(filename_full) > 30 else filename_full
                )
                uploader_full = info.get("uploader", "N/A")
                uploader = (
                    uploader_full[:13] + ".." if len(uploader_full) > 15 else uploader_full
                )
                upload_time = info.get("upload_time", "N/A")
                print(f"{file_id:<4} {filename:<30} {'N/A':<10} {uploader:<15} {upload_time:<20}")
            print("-" * 80)
            print(f"Total: {len(files)} files")
            return True
        except requests.exceptions.RequestException as e:  # type: ignore[attr-defined]
            print(f"❌ Error getting file list: {e}")
            return False

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"


