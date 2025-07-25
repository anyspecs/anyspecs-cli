"""
File upload functionality.
"""

import os
import requests
from pathlib import Path
from typing import Optional

from .logging import get_logger

logger = get_logger('upload')


def upload_file_to_server(
    file_path: Path, 
    server_url: str, 
    username: str, 
    password: str
) -> bool:
    """
    Upload a file to the backend server.
    
    Args:
        file_path: Path to the file to upload
        server_url: Server URL
        username: Username for authentication
        password: Password for authentication
    
    Returns:
        True if upload successful, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist")
        return False
    
    # First, authenticate to get token
    auth_url = f"{server_url.rstrip('/')}/api/login"
    auth_data = {
        'username': username,
        'password': password
    }
    
    try:
        logger.info(f"Authenticating with server: {auth_url}")
        auth_response = requests.post(auth_url, json=auth_data)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        logger.info("Authentication successful")
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication failed: {e}")
        return False
    
    # Upload the file
    upload_url = f"{server_url.rstrip('/')}/api/upload"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        logger.info(f"Uploading file to: {upload_url}")
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            upload_response = requests.post(upload_url, headers=headers, files=files)
            upload_response.raise_for_status()
        
        result = upload_response.json()
        logger.info("Upload successful!")
        logger.info(f"File URL: {server_url.rstrip('/')}{result['file']['url']}")
        return True
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Upload failed: {e}")
        return False 