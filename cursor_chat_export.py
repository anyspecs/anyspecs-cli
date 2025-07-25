#!/usr/bin/env python3
"""
Cursor Chat Export CLI Tool

A standalone CLI tool for exporting Cursor AI chat history.
Supports HTML, Markdown, and JSON export formats.
"""

import json
import uuid
import logging
import datetime
import os
import platform
import sqlite3
import argparse
import pathlib
import sys
from collections import defaultdict
from typing import Dict, Any, Iterable, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

################################################################################
# Cursor storage roots
################################################################################
def cursor_root() -> pathlib.Path:
    h = pathlib.Path.home()
    s = platform.system()
    if s == "Darwin":   return h / "Library" / "Application Support" / "Cursor"
    if s == "Windows":  return h / "AppData" / "Roaming" / "Cursor"
    if s == "Linux":    return h / ".config" / "Cursor"
    raise RuntimeError(f"Unsupported OS: {s}")

################################################################################
# Helpers (从 server.py 复制)
################################################################################
def j(cur: sqlite3.Cursor, table: str, key: str):
    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    row = cur.fetchone()
    if row:
        try:    return json.loads(row[0])
        except Exception as e: 
            logger.debug(f"Failed to parse JSON for {key}: {e}")
    return None

def iter_bubbles_from_disk_kv(db: pathlib.Path) -> Iterable[tuple[str,str,str,str]]:
    """Yield (composerId, role, text, db_path) from cursorDiskKV table."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not cur.fetchone():
            con.close()
            return
        
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'")
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error with {db}: {e}")
        return
    
    db_path_str = str(db)
    
    for k, v in cur.fetchall():
        try:
            if v is None:
                continue
                
            b = json.loads(v)
        except Exception as e:
            logger.debug(f"Failed to parse bubble JSON for key {k}: {e}")
            continue
        
        txt = (b.get("text") or b.get("richText") or "").strip()
        if not txt:         continue
        role = "user" if b.get("type") == 1 else "assistant"
        composerId = k.split(":")[1]  # Format is bubbleId:composerId:bubbleId
        yield composerId, role, txt, db_path_str
    
    con.close()

def iter_chat_from_item_table(db: pathlib.Path) -> Iterable[tuple[str,str,str,str]]:
    """Yield (composerId, role, text, db_path) from ItemTable."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        
        # Try to get chat data from workbench.panel.aichat.view.aichat.chatdata
        chat_data = j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata")
        if chat_data and "tabs" in chat_data:
            for tab in chat_data.get("tabs", []):
                tab_id = tab.get("tabId", "unknown")
                for bubble in tab.get("bubbles", []):
                    bubble_type = bubble.get("type")
                    if not bubble_type:
                        continue
                    
                    # Extract text from various possible fields
                    text = ""
                    if "text" in bubble:
                        text = bubble["text"]
                    elif "content" in bubble:
                        text = bubble["content"]
                    
                    if text and isinstance(text, str):
                        role = "user" if bubble_type == "user" else "assistant"
                        yield tab_id, role, text, str(db)
        
        # Check for composer data
        composer_data = j(cur, "ItemTable", "composer.composerData")
        if composer_data:
            for comp in composer_data.get("allComposers", []):
                comp_id = comp.get("composerId", "unknown")
                messages = comp.get("messages", [])
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if content:
                        yield comp_id, role, content, str(db)
        
        # Also check for aiService entries - Fix extraction logic
        # Get prompts and generations data and combine into a conversation
        prompts_data = j(cur, "ItemTable", "aiService.prompts")
        generations_data = j(cur, "ItemTable", "aiService.generations")
        
        if prompts_data or generations_data:
            # Create a combined session ID
            combined_id = "aiService_combined"
            
            # Add user prompts
            if isinstance(prompts_data, list):
                for item in prompts_data:
                    if isinstance(item, dict) and "text" in item:
                        text = item.get("text", "").strip()
                        if text:
                            yield combined_id, "user", text, str(db)
            
            # Add AI generations
            if isinstance(generations_data, list):
                for item in generations_data:
                    if isinstance(item, dict) and "textDescription" in item:
                        text = item.get("textDescription", "").strip()
                        if text:
                            yield combined_id, "assistant", text, str(db)
    
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error in ItemTable with {db}: {e}")
        return
    finally:
        if 'con' in locals():
            con.close()

def iter_composer_data(db: pathlib.Path) -> Iterable[tuple[str,dict,str]]:
    """Yield (composerId, composerData, db_path) from cursorDiskKV table."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'")
        if not cur.fetchone():
            con.close()
            return
        
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
    except sqlite3.DatabaseError as e:
        logger.debug(f"Database error with {db}: {e}")
        return
    
    db_path_str = str(db)
    
    for k, v in cur.fetchall():
        try:
            if v is None:
                continue
                
            composer_data = json.loads(v)
            composer_id = k.split(":")[1]
            yield composer_id, composer_data, db_path_str
            
        except Exception as e:
            logger.debug(f"Failed to parse composer data for key {k}: {e}")
            continue
    
    con.close()

################################################################################
# Workspace discovery 
################################################################################
def workspaces(base: pathlib.Path):
    ws_root = base / "User" / "workspaceStorage"
    if not ws_root.exists():
        return
    for folder in ws_root.iterdir():
        db = folder / "state.vscdb"
        if db.exists():
            yield folder.name, db

def extract_project_name_from_path(root_path, debug=False):
    """Extract a project name from a path, skipping user directories."""
    if not root_path or root_path == '/':
        return "Root"
        
    path_parts = [p for p in root_path.split('/') if p]
    
    # Skip common user directory patterns
    project_name = None
    home_dir_patterns = ['Users', 'home']
    
    # Get current username for comparison
    current_username = os.path.basename(os.path.expanduser('~'))
    
    # Find user directory in path
    username_index = -1
    for i, part in enumerate(path_parts):
        if part in home_dir_patterns:
            username_index = i + 1
            break
    
    # If this is just /Users/username with no deeper path, don't use username as project
    if username_index >= 0 and username_index < len(path_parts) and path_parts[username_index] == current_username:
        if len(path_parts) <= username_index + 1:
            return "Home Directory"
    
    if username_index >= 0 and username_index + 1 < len(path_parts):
        # First try specific project directories we know about by name
        known_projects = ['genaisf', 'cursor-view', 'cursor', 'cursor-apps', 'universal-github', 'inquiry']
        
        # Look at the most specific/deepest part of the path first
        for i in range(len(path_parts)-1, username_index, -1):
            if path_parts[i] in known_projects:
                project_name = path_parts[i]
                if debug:
                    logger.debug(f"Found known project name from specific list: {project_name}")
                break
        
        # If no known project found, use the last part of the path as it's likely the project directory
        if not project_name and len(path_parts) > username_index + 1:
            # Check if we have a structure like /Users/username/Documents/codebase/project_name
            if 'Documents' in path_parts and 'codebase' in path_parts:
                doc_index = path_parts.index('Documents')
                codebase_index = path_parts.index('codebase')
                
                # If there's a path component after 'codebase', use that as the project name
                if codebase_index + 1 < len(path_parts):
                    project_name = path_parts[codebase_index + 1]
                    if debug:
                        logger.debug(f"Found project name in Documents/codebase structure: {project_name}")
            
            # If no specific structure found, use the last component of the path
            if not project_name:
                project_name = path_parts[-1]
                if debug:
                    logger.debug(f"Using last path component as project name: {project_name}")
        
        # Skip username as project name
        if project_name == current_username:
            project_name = 'Home Directory'
            if debug:
                logger.debug(f"Avoided using username as project name")
        
        # Skip common project container directories
        project_containers = ['Documents', 'Projects', 'Code', 'workspace', 'repos', 'git', 'src', 'codebase']
        if project_name in project_containers:
            # Don't use container directories as project names
            # Try to use the next component if available
            container_index = path_parts.index(project_name)
            if container_index + 1 < len(path_parts):
                project_name = path_parts[container_index + 1]
                if debug:
                    logger.debug(f"Skipped container dir, using next component as project name: {project_name}")
        
        # If we still don't have a project name, use the first non-system directory after username
        if not project_name and username_index + 1 < len(path_parts):
            system_dirs = ['Library', 'Applications', 'System', 'var', 'opt', 'tmp']
            for i in range(username_index + 1, len(path_parts)):
                if path_parts[i] not in system_dirs and path_parts[i] not in project_containers:
                    project_name = path_parts[i]
                    if debug:
                        logger.debug(f"Using non-system dir as project name: {project_name}")
                    break
    else:
        # If not in a user directory, use the basename
        project_name = path_parts[-1] if path_parts else "Root"
        if debug:
            logger.debug(f"Using basename as project name: {project_name}")
    
    # Final check: don't return username as project name
    if project_name == current_username:
        project_name = "Home Directory"
        if debug:
            logger.debug(f"Final check: replaced username with 'Home Directory'")
    
    return project_name if project_name else "Unknown Project"

def workspace_info(db: pathlib.Path):
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()

        # Get file paths from history entries to extract the project name
        proj = {"name": "(unknown)", "rootPath": "(unknown)"}
        ents = j(cur,"ItemTable","history.entries") or []
        
        # Extract file paths from history entries, stripping the file:/// scheme
        paths = []
        for e in ents:
            resource = e.get("editor", {}).get("resource", "")
            if resource and resource.startswith("file:///"):
                paths.append(resource[len("file:///"):])
        
        # If we found file paths, extract the project name using the longest common prefix
        if paths:
            logger.debug(f"Found {len(paths)} paths in history entries")
            
            # Get the longest common prefix
            common_prefix = os.path.commonprefix(paths)
            logger.debug(f"Common prefix: {common_prefix}")
            
            # Find the last directory separator in the common prefix
            last_separator_index = common_prefix.rfind('/')
            if last_separator_index > 0:
                project_root = common_prefix[:last_separator_index]
                logger.debug(f"Project root from common prefix: {project_root}")
                
                # Extract the project name using the helper function
                project_name = extract_project_name_from_path(project_root, debug=True)
                
                proj = {"name": project_name, "rootPath": "/" + project_root.lstrip('/')}
        
        # Try backup methods if we didn't get a project name
        if proj["name"] == "(unknown)":
            logger.debug("Trying backup methods for project name")
            
            # Check debug.selectedroot as a fallback
            selected_root = j(cur, "ItemTable", "debug.selectedroot")
            if selected_root and isinstance(selected_root, str) and selected_root.startswith("file:///"):
                path = selected_root[len("file:///"):]
                if path:
                    root_path = "/" + path.strip("/")
                    logger.debug(f"Project root from debug.selectedroot: {root_path}")
                    
                    # Extract the project name using the helper function
                    project_name = extract_project_name_from_path(root_path, debug=True)
                    
                    if project_name:
                        proj = {"name": project_name, "rootPath": root_path}

        # composers meta
        comp_meta={}
        cd = j(cur,"ItemTable","composer.composerData") or {}
        for c in cd.get("allComposers",[]):
            comp_meta[c["composerId"]] = {
                "title": c.get("name","(untitled)"),
                "createdAt": c.get("createdAt"),
                "lastUpdatedAt": c.get("lastUpdatedAt")
            }
        
        # Try to get composer info from workbench.panel.aichat.view.aichat.chatdata
        chat_data = j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
        for tab in chat_data.get("tabs", []):
            tab_id = tab.get("tabId")
            if tab_id and tab_id not in comp_meta:
                comp_meta[tab_id] = {
                    "title": f"Chat {tab_id[:8]}",
                    "createdAt": None,
                    "lastUpdatedAt": None
                }
    except sqlite3.DatabaseError as e:
        logger.debug(f"Error getting workspace info from {db}: {e}")
        proj = {"name": "(unknown)", "rootPath": "(unknown)"}
        comp_meta = {}
    finally:
        if 'con' in locals():
            con.close()
            
    return proj, comp_meta

################################################################################
# GlobalStorage
################################################################################
def global_storage_path(base: pathlib.Path) -> pathlib.Path:
    """Return path to the global storage state.vscdb."""
    global_db = base / "User" / "globalStorage" / "state.vscdb"
    if global_db.exists():
        return global_db
    
    # Legacy paths
    g_dirs = [base/"User"/"globalStorage"/"cursor.cursor",
              base/"User"/"globalStorage"/"cursor"]
    for d in g_dirs:
        if d.exists():
            for file in d.glob("*.sqlite"):
                return file
    
    return None

################################################################################
# Current project detection
################################################################################
def get_current_project_name() -> str:
    """Get the current project name"""
    try:
        current_dir = pathlib.Path.cwd()
        project_name = current_dir.name
        
        # Skip common container directory names
        container_dirs = ['Documents', 'Projects', 'Code', 'workspace', 'repos', 'git', 'src', 'codebase']
        if project_name in container_dirs and current_dir.parent.exists():
            project_name = current_dir.parent.name
        
        return project_name
    except Exception:
        return "unknown"

################################################################################
# Extraction pipeline
################################################################################
def extract_chats() -> list[Dict[str,Any]]:
    root = cursor_root()
    logger.debug(f"Using Cursor root: {root}")

    # map lookups
    ws_proj  : Dict[str,Dict[str,Any]] = {}
    comp_meta: Dict[str,Dict[str,Any]] = {}
    comp2ws  : Dict[str,str]           = {}
    sessions : Dict[str,Dict[str,Any]] = defaultdict(lambda: {"messages":[]})

    # 1. Process workspace DBs first
    logger.debug("Processing workspace databases...")
    ws_count = 0
    for ws_id, db in workspaces(root):
        ws_count += 1
        logger.debug(f"Processing workspace {ws_id} - {db}")
        proj, meta = workspace_info(db)
        ws_proj[ws_id] = proj
        for cid, m in meta.items():
            comp_meta[cid] = m
            comp2ws[cid] = ws_id
        
        # Extract chat data from workspace's state.vscdb
        msg_count = 0
        for cid, role, text, db_path in iter_chat_from_item_table(db):
            # Add the message
            sessions[cid]["messages"].append({"role": role, "content": text})
            # Make sure to record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
            msg_count += 1
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = ws_id
        logger.debug(f"  - Extracted {msg_count} messages from workspace {ws_id}")
    
    logger.debug(f"Processed {ws_count} workspaces")

    # 2. Process global storage
    global_db = global_storage_path(root)
    if global_db:
        logger.debug(f"Processing global storage: {global_db}")
        # Extract bubbles from cursorDiskKV
        msg_count = 0
        for cid, role, text, db_path in iter_bubbles_from_disk_kv(global_db):
            sessions[cid]["messages"].append({"role": role, "content": text})
            # Record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
            msg_count += 1
            if cid not in comp_meta:
                comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                comp2ws[cid] = "(global)"
        logger.debug(f"  - Extracted {msg_count} messages from global cursorDiskKV bubbles")
        
        # Extract composer data
        comp_count = 0
        for cid, data, db_path in iter_composer_data(global_db):
            if cid not in comp_meta:
                created_at = data.get("createdAt")
                comp_meta[cid] = {
                    "title": f"Chat {cid[:8]}",
                    "createdAt": created_at,
                    "lastUpdatedAt": created_at
                }
                comp2ws[cid] = "(global)"
            
            # Record the database path
            if "db_path" not in sessions[cid]:
                sessions[cid]["db_path"] = db_path
                
            # Extract conversation from composer data
            conversation = data.get("conversation", [])
            if conversation:
                msg_count = 0
                for msg in conversation:
                    msg_type = msg.get("type")
                    if msg_type is None:
                        continue
                    
                    # Type 1 = user, Type 2 = assistant
                    role = "user" if msg_type == 1 else "assistant"
                    content = msg.get("text", "")
                    if content and isinstance(content, str):
                        sessions[cid]["messages"].append({"role": role, "content": content})
                        msg_count += 1
                
                if msg_count > 0:
                    comp_count += 1
                    logger.debug(f"  - Added {msg_count} messages from composer {cid[:8]}")
        
        if comp_count > 0:
            logger.debug(f"  - Extracted data from {comp_count} composers in global cursorDiskKV")

    # 3. Build final list
    out = []
    for cid, data in sessions.items():
        if not data["messages"]:
            continue
        ws_id = comp2ws.get(cid, "(unknown)")
        project = ws_proj.get(ws_id, {"name": "(unknown)", "rootPath": "(unknown)"})
        meta = comp_meta.get(cid, {"title": "(untitled)", "createdAt": None, "lastUpdatedAt": None})
        
        # Create the output object with the db_path included
        chat_data = {
            "project": project,
            "session": {"composerId": cid, **meta},
            "messages": data["messages"],
            "workspace_id": ws_id,
        }
        
        # Add the database path if available
        if "db_path" in data:
            chat_data["db_path"] = data["db_path"]
            
        out.append(chat_data)
    
    # Sort by last updated time if available
    out.sort(key=lambda s: s["session"].get("lastUpdatedAt") or 0, reverse=True)
    logger.debug(f"Total chat sessions extracted: {len(out)}")
    return out

def format_chat_for_export(chat):
    """Format the chat data for export."""
    try:
        # Generate a unique ID for this chat if it doesn't have one
        session_id = str(uuid.uuid4())
        if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
            session_id = chat['session'].get('composerId', session_id)
        
        # Format date from createdAt timestamp or use current date
        date = int(datetime.datetime.now().timestamp())
        if 'session' in chat and chat['session'] and isinstance(chat['session'], dict):
            created_at = chat['session'].get('createdAt')
            if created_at and isinstance(created_at, (int, float)):
                # Convert from milliseconds to seconds
                date = created_at / 1000
        
        # Ensure project has expected fields
        project = chat.get('project', {})
        if not isinstance(project, dict):
            project = {}
            
        # Get workspace_id from chat
        workspace_id = chat.get('workspace_id', 'unknown')
        
        # Get the database path information
        db_path = chat.get('db_path', 'Unknown database path')
            
        # Ensure messages exist and are properly formatted
        messages = chat.get('messages', [])
        if not isinstance(messages, list):
            messages = []
        
        # Create properly formatted chat object
        return {
            'project': project,
            'messages': messages,
            'date': date,
            'session_id': session_id,
            'workspace_id': workspace_id,
            'db_path': db_path
        }
    except Exception as e:
        logger.error(f"Error formatting chat: {e}")
        # Return a minimal valid object if there's an error
        return {
            'project': {'name': 'Error', 'rootPath': '/'},
            'messages': [],
            'date': int(datetime.datetime.now().timestamp()),
            'session_id': str(uuid.uuid4()),
            'workspace_id': 'error',
            'db_path': 'Error retrieving database path'
        }

################################################################################
# 导出功能 (从 server.py 复制并修改)
################################################################################

def generate_standalone_markdown(chat):
    """Generate a standalone Markdown representation of the chat."""
    logger.info(f"Generating Markdown for session ID: {chat.get('session_id', 'N/A')}")
    try:
        # Format date for display
        date_display = "Unknown date"
        if chat.get('date'):
            try:
                date_obj = datetime.datetime.fromtimestamp(chat['date'])
                date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.warning(f"Error formatting date: {e}")
        
        # Get project info
        project_name = chat.get('project', {}).get('name', 'Unknown Project')
        project_path = chat.get('project', {}).get('rootPath', 'Unknown Path')
        session_id = chat.get('session_id', 'Unknown')
        logger.info(f"Project: {project_name}, Path: {project_path}, Date: {date_display}")
        
        # Build the Markdown content
        markdown_lines = []
        
        # Title and metadata
        markdown_lines.append(f"# Cursor Chat: {project_name}")
        markdown_lines.append("")
        markdown_lines.append("## Chat Information")
        markdown_lines.append("")
        markdown_lines.append(f"- **Project**: {project_name}")
        markdown_lines.append(f"- **Path**: `{project_path}`")
        markdown_lines.append(f"- **Date**: {date_display}")
        markdown_lines.append(f"- **Session ID**: `{session_id}`")
        markdown_lines.append("")
        
        # Messages
        messages = chat.get('messages', [])
        logger.info(f"Found {len(messages)} messages for the chat.")
        
        if not messages:
            logger.warning("No messages found in the chat object to generate Markdown.")
            markdown_lines.append("## Conversation History")
            markdown_lines.append("")
            markdown_lines.append("No messages found in this conversation.")
        else:
            markdown_lines.append("## Conversation History")
            markdown_lines.append("")
            
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                logger.debug(f"Processing message {i+1}/{len(messages)} - Role: {role}, Content length: {len(content)}")
                
                if not content or not isinstance(content, str):
                    logger.warning(f"Message {i+1} has invalid content: {content}")
                    content = "Content unavailable"
                
                # Add role header
                role_display = "👤 **You**" if role == "user" else "🤖 **Cursor Assistant**"
                markdown_lines.append(f"### {role_display}")
                markdown_lines.append("")
                
                # Process content - preserve code blocks and formatting
                processed_content = content.strip()
                
                # If content contains code blocks, keep them as-is
                # Otherwise, format as regular text
                if "```" in processed_content:
                    # Already has code blocks, use as-is
                    markdown_lines.append(processed_content)
                else:
                    # Split by lines and handle potential code snippets
                    lines = processed_content.split('\n')
                    in_code_block = False
                    
                    for line in lines:
                        line = line.rstrip()
                        
                        # Detect inline code or potential code lines
                        if (line.strip().startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ', 
                                                   'const ', 'let ', 'var ', 'function ', '{', '}', '//', '#')) or
                            '=' in line and any(keyword in line for keyword in ['function', 'const', 'let', 'var', '=>']) or
                            line.strip().endswith((';', '{', '}', ':', '))'))):
                            
                            if not in_code_block:
                                markdown_lines.append("```")
                                in_code_block = True
                            markdown_lines.append(line)
                        else:
                            if in_code_block:
                                markdown_lines.append("```")
                                in_code_block = False
                            if line.strip():  # Non-empty line
                                markdown_lines.append(line)
                            else:  # Empty line
                                markdown_lines.append("")
                    
                    # Close any open code block
                    if in_code_block:
                        markdown_lines.append("```")
                
                markdown_lines.append("")
                markdown_lines.append("---")  # Separator between messages
                markdown_lines.append("")
        
        # Footer
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")

        markdown_content = "\n".join(markdown_lines)
        logger.info(f"Finished generating Markdown. Total length: {len(markdown_content)}")
        return markdown_content
        
    except Exception as e:
        logger.error(f"Error generating Markdown for session {chat.get('session_id', 'N/A')}: {e}", exc_info=True)
        # Return a markdown formatted error message
        return f"""# Error Generating Chat Export

**Error**: {e}

Please try again or contact support if the problem persists.

---

"""

def generate_standalone_html(chat):
    """Generate a standalone HTML representation of the chat."""
    logger.info(f"Generating HTML for session ID: {chat.get('session_id', 'N/A')}")
    try:
        # Format date for display
        date_display = "Unknown date"
        if chat.get('date'):
            try:
                date_obj = datetime.datetime.fromtimestamp(chat['date'])
                date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.warning(f"Error formatting date: {e}")
        
        # Get project info
        project_name = chat.get('project', {}).get('name', 'Unknown Project')
        project_path = chat.get('project', {}).get('rootPath', 'Unknown Path')
        logger.info(f"Project: {project_name}, Path: {project_path}, Date: {date_display}")
        
        # Build the HTML content
        messages_html = ""
        messages = chat.get('messages', [])
        logger.info(f"Found {len(messages)} messages for the chat.")
        
        if not messages:
            logger.warning("No messages found in the chat object to generate HTML.")
            messages_html = "<p>No messages found in this conversation.</p>"
        else:
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                logger.debug(f"Processing message {i+1}/{len(messages)} - Role: {role}, Content length: {len(content)}")
                
                if not content or not isinstance(content, str):
                    logger.warning(f"Message {i+1} has invalid content: {content}")
                    content = "Content unavailable"
                
                # Simple HTML escaping
                escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                # Convert markdown code blocks (handle potential nesting issues simply)
                processed_content = ""
                in_code_block = False
                for line in escaped_content.split('\n'):
                    if line.strip().startswith("```"):
                        if not in_code_block:
                            processed_content += "<pre><code>"
                            in_code_block = True
                            # Remove the first ``` marker
                            line = line.strip()[3:] 
                        else:
                            processed_content += "</code></pre>\n"
                            in_code_block = False
                            line = "" # Skip the closing ``` line
                    
                    if in_code_block:
                         # Inside code block, preserve spacing and add line breaks
                        processed_content += line + "\n" 
                    else:
                        # Outside code block, use <br> for newlines
                        processed_content += line + "<br>"
                
                # Close any unclosed code block at the end
                if in_code_block:
                    processed_content += "</code></pre>"
                
                avatar = "👤" if role == "user" else "🤖"
                name = "You" if role == "user" else "Cursor Assistant"
                bg_color = "#f0f7ff" if role == "user" else "#f0fff7"
                border_color = "#3f51b5" if role == "user" else "#00796b"
                
                messages_html += f"""
                <div class="message" style="margin-bottom: 20px;">
                    <div class="message-header" style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div class="avatar" style="width: 32px; height: 32px; border-radius: 50%; background-color: {border_color}; color: white; display: flex; justify-content: center; align-items: center; margin-right: 10px;">
                            {avatar}
                        </div>
                        <div class="sender" style="font-weight: bold;">{name}</div>
                    </div>
                    <div class="message-content" style="padding: 15px; border-radius: 8px; background-color: {bg_color}; border-left: 4px solid {border_color}; margin-left: {0 if role == 'user' else '40px'}; margin-right: {0 if role == 'assistant' else '40px'};">
                        {processed_content} 
                    </div>
                </div>
                """

        # Create the complete HTML document
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor Chat - {project_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 20px auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .header {{ background: linear-gradient(90deg, #f0f7ff 0%, #f0fff7 100%); color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
        .chat-info {{ display: flex; flex-wrap: wrap; gap: 10px 20px; margin-bottom: 20px; background-color: #f9f9f9; padding: 12px 15px; border-radius: 8px; font-size: 0.9em; }}
        .info-item {{ display: flex; align-items: center; }}
        .info-label {{ font-weight: bold; margin-right: 5px; color: #555; }}
        pre {{ background-color: #eef; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #ddd; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; }}
        code {{ background-color: transparent; padding: 0; border-radius: 0; font-family: inherit; }}
        .message-content pre code {{ background-color: transparent; }}
        .message-content {{ word-wrap: break-word; overflow-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Cursor Chat: {project_name}</h1>
    </div>
    <div class="chat-info">
        <div class="info-item"><span class="info-label">Project:</span> <span>{project_name}</span></div>
        <div class="info-item"><span class="info-label">Path:</span> <span>{project_path}</span></div>
        <div class="info-item"><span class="info-label">Date:</span> <span>{date_display}</span></div>
        <div class="info-item"><span class="info-label">Session ID:</span> <span>{chat.get('session_id', 'Unknown')}</span></div>
    </div>
    <h2>Conversation History</h2>
    <div class="messages">
{messages_html}
    </div>
</body>
</html>"""
        
        logger.info(f"Finished generating HTML. Total length: {len(html)}")
        return html
    except Exception as e:
        logger.error(f"Error generating HTML for session {chat.get('session_id', 'N/A')}: {e}", exc_info=True)
        # Return an HTML formatted error message
        return f"<html><body><h1>Error generating chat export</h1><p>Error: {e}</p></body></html>"

def export_chat_to_file(chat, format_type: str, output_path: pathlib.Path):
    """Export a single chat to file in the specified format."""
    formatted_chat = format_chat_for_export(chat)
    
    if format_type.lower() in ['json']:
        content = json.dumps(formatted_chat, indent=2, ensure_ascii=False)
        if not output_path.suffix:
            output_path = output_path.with_suffix('.json')
    elif format_type.lower() in ['markdown', 'md']:
        content = generate_standalone_markdown(formatted_chat)
        if not output_path.suffix:
            output_path = output_path.with_suffix('.md')
    elif format_type.lower() in ['html']:
        content = generate_standalone_html(formatted_chat)
        if not output_path.suffix:
            output_path = output_path.with_suffix('.html')
    else:
        raise ValueError(f"Unsupported format: {format_type}")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path

################################################################################
# CLI main function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Cursor Chat Export CLI - Export Cursor AI chat history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                     # List all chat sessions
  %(prog)s export --format markdown # Export current project's sessions to Markdown
  %(prog)s export --all-projects --format markdown # Export all projects' sessions to Markdown
  %(prog)s export --session-id abc123 --format html --output chat.html
  %(prog)s export --project cursor-view --format json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List all chat sessions')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export chat sessions')
    export_parser.add_argument('--format', '-f', 
                             choices=['json', 'markdown', 'md', 'html'], 
                             default='markdown',
                             help='Export format (default: markdown)')
    export_parser.add_argument('--output', '-o', 
                             type=pathlib.Path,
                             help='Output directory or file path')
    export_parser.add_argument('--session-id', '-s',
                             help='Specify session ID (if not specified, export all)')
    export_parser.add_argument('--project', '-p',
                             help='Filter by project name')
    export_parser.add_argument('--all-projects', '-a', action='store_true',
                             help='Export all projects\' sessions (default: only export current project)')
    export_parser.add_argument('--limit', '-l',
                             type=int,
                             help='Limit export count')
    export_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    # Set log level
    if hasattr(args, 'verbose') and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.command == 'list':
            return list_chats(args)
        elif args.command == 'export':
            return export_chats(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1

def list_chats(args):
    """List all chat sessions"""
    print("🔍 Searching Cursor chat records...")
    
    chats = extract_chats()
    
    if not chats:
        print("❌ No chat records found")
        print("💡 Please ensure Cursor is installed and you have used the AI assistant")
        return 1
    
    print(f"✅ Found {len(chats)} chat sessions\n")
    
    # Group by project
    projects = {}
    for chat in chats:
        project_name = chat.get('project', {}).get('name', 'Unknown Project')
        if project_name not in projects:
            projects[project_name] = []
        projects[project_name].append(chat)
    
    for project_name, project_chats in projects.items():
        print(f"📁 {project_name} ({len(project_chats)} sessions)")
        
        for chat in project_chats[:5]:  # Only show the first 5
            session_id = chat.get('session_id', 'unknown')[:8]
            msg_count = len(chat.get('messages', []))
            
            # Format date
            date_str = "Unknown date"
            if chat.get('date'):
                try:
                    date_obj = datetime.datetime.fromtimestamp(chat['date'])
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Display preview of the first message
            preview = "No messages"
            messages = chat.get('messages', [])
            if messages:
                first_msg = messages[0].get('content', '')
                preview = first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
                preview = preview.replace('\n', ' ')
            
            print(f"  🆔 {session_id} | 📅 {date_str} | 💬 {msg_count} messages")
            if args.verbose:
                print(f"     💭 {preview}")
        
        if len(project_chats) > 5:
            print(f"     ... and {len(project_chats) - 5} more sessions")
        print()
    
    return 0

def export_chats(args):
    """Export chat sessions"""
    print("🔍 Searching Cursor chat records...")
    
    chats = extract_chats()
    
    if not chats:
        print("❌ No chat records found")
        return 1
    
    # Apply filters
    filtered_chats = chats
    
    if args.session_id:
        filtered_chats = [c for c in filtered_chats if c.get('session_id', '').startswith(args.session_id)]
        if not filtered_chats:
            print(f"❌ No chat records found with session ID starting with '{args.session_id}'")
            return 1
    
    # Project filtering logic
    if args.project:
        # User explicitly specified a project
        filtered_chats = [c for c in filtered_chats 
                         if args.project.lower() in c.get('project', {}).get('name', '').lower()]
        if not filtered_chats:
            print(f"❌ No chat records found with project name containing '{args.project}'")
            return 1
        print(f"📋 Filtering by specified project: {args.project}")
    elif not args.all_projects:
        # Default to only exporting sessions for the current project
        current_project = get_current_project_name()
        filtered_chats = [c for c in filtered_chats 
                         if current_project.lower() in c.get('project', {}).get('name', '').lower()]
        if not filtered_chats:
            print(f"❌ No chat records found for current project '{current_project}'")
            print(f"💡 Use --all-projects to export all projects' sessions, or use --project to specify another project")
            return 1
        print(f"📋 Defaulting to current project: {current_project}")
    else:
        # User explicitly requested to export all projects
        print("📋 Exporting all projects' sessions")
    
    if args.limit:
        filtered_chats = filtered_chats[:args.limit]
    
    print(f"📊 Preparing to export {len(filtered_chats)} chat sessions (format: {args.format})")
    
    # Determine output path
    output_base = args.output or pathlib.Path.cwd()
    
    if len(filtered_chats) == 1:
        # Single file
        chat = filtered_chats[0]
        session_id = chat.get('session_id', 'unknown')[:8]
        project_name = chat.get('project', {}).get('name', 'unknown').replace(' ', '_')
        
        if output_base.is_dir() or not output_base.suffix:
            # If it's a directory or doesn't have an extension, generate a filename
            filename = f"cursor-chat-{project_name}-{session_id}"
            output_path = output_base / filename if output_base.is_dir() else pathlib.Path(str(output_base) + f"-{session_id}")
        else:
            output_path = output_base
        
        try:
            final_path = export_chat_to_file(chat, args.format, output_path)
            print(f"✅ Export successful: {final_path}")
            print(f"📄 File size: {final_path.stat().st_size} bytes")
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return 1
    
    else:
        # Multiple files
        if not output_base.is_dir():
            output_base.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_base}")
        
        for i, chat in enumerate(filtered_chats, 1):
            # Get session_id, if not generate one
            session_id = chat.get('session_id', '')
            if session_id:
                session_id = session_id[:8]
            else:
                session_id = f'chat{i:03d}'
            
            project_name = chat.get('project', {}).get('name', 'unknown').replace(' ', '_')
            
            # Add timestamp to differentiate multiple files
            timestamp = ""
            session = chat.get('session', {})
            # Try to use the timestamp from the session (prefer createdAt)
            date_timestamp = session.get('createdAt') or session.get('lastUpdatedAt')
            
            if date_timestamp:
                try:
                    # Timestamp is in milliseconds, so we need to divide by 1000
                    date_obj = datetime.datetime.fromtimestamp(date_timestamp / 1000)
                    timestamp = date_obj.strftime("-%Y%m%d-%H%M%S")
                except Exception as e:
                    # If timestamp format is invalid, use the original value
                    timestamp = f"-{int(date_timestamp)}"
            else:
                # If no date, use the index
                timestamp = f"-{i:03d}"
            
            filename = f"cursor-chat-{project_name}-{session_id}{timestamp}"
            output_path = output_base / filename
            
            try:
                final_path = export_chat_to_file(chat, args.format, output_path)
                print(f"✅ {i}/{len(filtered_chats)}: {final_path.name}")
            except Exception as e:
                print(f"❌ {i}/{len(filtered_chats)}: Export failed - {e}")
        
        print(f"\n🎉 Batch export completed! Files saved in: {output_base}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 