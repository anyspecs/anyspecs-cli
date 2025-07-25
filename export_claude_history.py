#!/usr/bin/env python3
"""
Claude Code History Exporter with Upload Support

A CLI tool to export and upload Claude Code conversation history.
Can upload files directly to the backend server.
"""

import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime


def get_project_history_path():
    """Get the history path for the current project."""
    current_dir = os.getcwd()
    encoded_path = current_dir.replace('/', '-')
    history_base = Path.home() / '.claude' / 'projects'
    return history_base / encoded_path


def list_history_files(project_path):
    """List all history files for the project."""
    if not project_path.exists():
        return []
    
    history_files = []
    for file_path in project_path.glob('*.jsonl'):
        stat = file_path.stat()
        history_files.append({
            'path': file_path,
            'name': file_path.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime)
        })
    
    return sorted(history_files, key=lambda x: x['modified'], reverse=True)


def read_history_file(file_path):
    """Read and parse a JSONL history file."""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON on line {line_num}: {e}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    return entries


def export_history(output_file=None, format_type='json', limit=None):
    """Export the project history to a file."""
    history_path = get_project_history_path()
    
    if not history_path.exists():
        print(f"No Claude Code history found for this project.")
        print(f"Expected location: {history_path}")
        return None
    
    history_files = list_history_files(history_path)
    if not history_files:
        print("No history files found.")
        return None
    
    all_entries = []
    for file_info in history_files[:limit] if limit else history_files:
        entries = read_history_file(file_info['path'])
        for entry in entries:
            entry['_source_file'] = str(file_info['path'])
        all_entries.extend(entries)
    
    if not all_entries:
        print("No valid history entries found.")
        return None
    
    if output_file:
        if format_type == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_entries, f, indent=2, default=str)
        elif format_type == 'jsonl':
            with open(output_file, 'w', encoding='utf-8') as f:
                for entry in all_entries:
                    json.dump(entry, f, default=str)
                    f.write('\n')
        elif format_type == 'markdown':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Claude Code History\n\n")
                
                current_session = None
                
                for entry in all_entries:
                    entry_type = entry.get('type')
                    session_id = entry.get('sessionId')
                    
                    if session_id != current_session:
                        current_session = session_id
                        f.write(f"## Session: {session_id}\n\n")
                    
                    if entry_type == 'user':
                        content = entry.get('message', {}).get('content', 'No content')
                        timestamp = entry.get('timestamp', 'N/A')
                        f.write(f"### User ({timestamp})\n\n")
                        f.write(f"{content}\n\n")
                    elif entry_type == 'assistant':
                        content = entry.get('message', {}).get('content', 'No content')
                        timestamp = entry.get('timestamp', 'N/A')
                        f.write(f"### Assistant ({timestamp})\n\n")
                        f.write(f"{content}\n\n")
                    elif entry_type == 'tool':
                        tool_name = entry.get('tool', 'Unknown')
                        input_data = entry.get('input', {})
                        timestamp = entry.get('timestamp', 'N/A')
                        f.write(f"### Tool Call: {tool_name} ({timestamp})\n\n")
                        if input_data:
                            f.write(f"**Input:**\n```json\n{json.dumps(input_data, indent=2, default=str)}\n```\n\n")
                    elif entry_type == 'tool_result':
                        result = entry.get('result', {})
                        timestamp = entry.get('timestamp', 'N/A')
                        f.write(f"### Tool Result ({timestamp})\n\n")
                        if isinstance(result, dict):
                            if 'output' in result:
                                f.write(f"```\n{result['output']}\n```\n\n")
                            else:
                                f.write(f"```json\n{json.dumps(result, indent=2, default=str)}\n```\n\n")
                        else:
                            f.write(f"```\n{result}\n```\n\n")
                    
                    f.write("---\n\n")
        
        print(f"Exported {len(all_entries)} entries to {output_file}")
        return output_file
    else:
        return None


def upload_file_to_server(file_path, server_url, username, password):
    """Upload a file to the backend server."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    # First, authenticate to get token
    auth_url = f"{server_url.rstrip('/')}/api/login"
    auth_data = {
        'username': username,
        'password': password
    }
    
    try:
        auth_response = requests.post(auth_url, json=auth_data)
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return False
    
    # Upload the file
    upload_url = f"{server_url.rstrip('/')}/api/upload"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            upload_response = requests.post(upload_url, headers=headers, files=files)
            upload_response.raise_for_status()
        
        result = upload_response.json()
        print(f"Upload successful!")
        print(f"File URL: {server_url.rstrip('/')}{result['file']['url']}")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Export and upload Claude Code history")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=['json', 'jsonl', 'markdown'], 
                       default='json', help="Output format")
    parser.add_argument("-l", "--limit", type=int, 
                       help="Limit to N most recent history files")
    parser.add_argument("-s", "--summary", action="store_true", 
                       help="Show summary of available history files")
    parser.add_argument("--upload", action="store_true", 
                       help="Upload exported file to server")
    parser.add_argument("--server", default="http://localhost:4999",
                       help="Server URL for upload (default: http://localhost:4999)")
    parser.add_argument("--username", help="Username for server authentication")
    parser.add_argument("--password", help="Password for server authentication")
    
    args = parser.parse_args()
    
    history_path = get_project_history_path()
    
    if args.summary:
        history_files = list_history_files(history_path)
        if history_files:
            print(f"Found {len(history_files)} history files:")
            for file_info in history_files:
                print(f"  {file_info['name']} - {file_info['size']} bytes - {file_info['modified']}")
        else:
            print("No history files found.")
        return
    
    # Generate default filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"claude_history_{timestamp}.{args.format}"
    
    exported_file = export_history(args.output, args.format, args.limit)
    
    if exported_file and args.upload:
        if not args.username or not args.password:
            print("Error: --username and --password required for upload")
            return
        
        upload_file_to_server(exported_file, args.server, args.username, args.password)


if __name__ == "__main__":
    main()