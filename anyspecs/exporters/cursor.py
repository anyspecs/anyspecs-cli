"""
Cursor AI chat history extractor.
"""

import json
import sqlite3
import pathlib
from collections import defaultdict
from typing import Dict, Any, List, Iterable, Tuple

from ..core.extractors import BaseExtractor
from ..utils.paths import get_cursor_root, extract_project_name_from_path


class CursorExtractor(BaseExtractor):
    """Extractor for Cursor AI chat history."""
    
    def __init__(self):
        super().__init__('cursor')
    
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract all chat data from Cursor."""
        root = get_cursor_root()
        self.logger.debug(f"Using Cursor root: {root}")

        # map lookups
        ws_proj: Dict[str, Dict[str, Any]] = {}
        comp_meta: Dict[str, Dict[str, Any]] = {}
        comp2ws: Dict[str, str] = {}
        sessions: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"messages": []})

        # 1. Process workspace DBs first
        self.logger.debug("Processing workspace databases...")
        ws_count = 0
        for ws_id, db in self._get_workspaces(root):
            ws_count += 1
            self.logger.debug(f"Processing workspace {ws_id} - {db}")
            proj, meta = self._get_workspace_info(db)
            ws_proj[ws_id] = proj
            for cid, m in meta.items():
                comp_meta[cid] = m
                comp2ws[cid] = ws_id

            # Extract chat data from workspace's state.vscdb
            msg_count = 0
            for cid, role, text, db_path in self._extract_chat_from_item_table(db):
                sessions[cid]["messages"].append({"role": role, "content": text})
                if "db_path" not in sessions[cid]:
                    sessions[cid]["db_path"] = db_path
                msg_count += 1
                if cid not in comp_meta:
                    comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                    comp2ws[cid] = ws_id
            self.logger.debug(f"  - Extracted {msg_count} messages from workspace {ws_id}")

        self.logger.debug(f"Processed {ws_count} workspaces")

        # 2. Process global storage
        global_db = self._get_global_storage_path(root)
        if global_db:
            self.logger.debug(f"Processing global storage: {global_db}")
            # Extract bubbles from cursorDiskKV
            msg_count = 0
            for cid, role, text, db_path in self._extract_bubbles_from_disk_kv(global_db):
                sessions[cid]["messages"].append({"role": role, "content": text})
                if "db_path" not in sessions[cid]:
                    sessions[cid]["db_path"] = db_path
                msg_count += 1
                if cid not in comp_meta:
                    comp_meta[cid] = {"title": f"Chat {cid[:8]}", "createdAt": None, "lastUpdatedAt": None}
                    comp2ws[cid] = "(global)"
            self.logger.debug(f"  - Extracted {msg_count} messages from global cursorDiskKV bubbles")

            # Extract composer data
            comp_count = 0
            for cid, data, db_path in self._extract_composer_data(global_db):
                if cid not in comp_meta:
                    created_at = data.get("createdAt")
                    comp_meta[cid] = {
                        "title": f"Chat {cid[:8]}",
                        "createdAt": created_at,
                        "lastUpdatedAt": created_at
                    }
                    comp2ws[cid] = "(global)"

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
                        self.logger.debug(f"  - Added {msg_count} messages from composer {cid[:8]}")

            if comp_count > 0:
                self.logger.debug(f"  - Extracted data from {comp_count} composers in global cursorDiskKV")

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
        self.logger.debug(f"Total chat sessions extracted: {len(out)}")
        return out
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List available chat sessions with metadata."""
        chats = self.extract_chats()
        sessions = []
        
        for chat in chats:
            session_id = chat.get('session', {}).get('composerId', 'unknown')[:8]
            project_name = chat.get('project', {}).get('name', 'Unknown Project')
            msg_count = len(chat.get('messages', []))
            
            # Format date
            date_str = "Unknown date"
            created_at = chat.get('session', {}).get('createdAt')
            if created_at:
                try:
                    import datetime
                    if created_at > 1e10:  # milliseconds
                        created_at = created_at / 1000
                    date_obj = datetime.datetime.fromtimestamp(created_at)
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Get preview of first message
            preview = "No messages"
            messages = chat.get('messages', [])
            if messages:
                first_msg = messages[0].get('content', '')
                preview = first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
                preview = preview.replace('\n', ' ')
            
            sessions.append({
                'session_id': session_id,
                'project': project_name,
                'date': date_str,
                'message_count': msg_count,
                'preview': preview,
                'workspace_id': chat.get('workspace_id', 'unknown')
            })
        
        return sessions

    def _get_workspaces(self, base: pathlib.Path):
        """Get workspace databases."""
        ws_root = base / "User" / "workspaceStorage"
        if not ws_root.exists():
            return
        for folder in ws_root.iterdir():
            db = folder / "state.vscdb"
            if db.exists():
                yield folder.name, db

    def _get_global_storage_path(self, base: pathlib.Path) -> pathlib.Path:
        """Return path to the global storage state.vscdb."""
        global_db = base / "User" / "globalStorage" / "state.vscdb"
        if global_db.exists():
            return global_db

        # Legacy paths
        g_dirs = [base / "User" / "globalStorage" / "cursor.cursor",
                  base / "User" / "globalStorage" / "cursor"]
        for d in g_dirs:
            if d.exists():
                for file in d.glob("*.sqlite"):
                    return file

        return None

    def _j(self, cur: sqlite3.Cursor, table: str, key: str):
        """Helper to parse JSON from database."""
        cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except Exception as e:
                self.logger.debug(f"Failed to parse JSON for {key}: {e}")
        return None

    def _get_workspace_info(self, db: pathlib.Path):
        """Get workspace information."""
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            cur = con.cursor()

            # Get file paths from history entries to extract the project name
            proj = {"name": "(unknown)", "rootPath": "(unknown)"}
            ents = self._j(cur, "ItemTable", "history.entries") or []

            # Extract file paths from history entries, stripping the file:/// scheme
            paths = []
            for e in ents:
                resource = e.get("editor", {}).get("resource", "")
                if resource and resource.startswith("file:///"):
                    paths.append(resource[len("file:///"):])

            # If we found file paths, extract the project name using the longest common prefix
            if paths:
                import os
                common_prefix = os.path.commonprefix(paths)
                last_separator_index = common_prefix.rfind('/')
                if last_separator_index > 0:
                    project_root = common_prefix[:last_separator_index]
                    project_name = extract_project_name_from_path(project_root)
                    proj = {"name": project_name, "rootPath": "/" + project_root.lstrip('/')}

            # Try backup methods if we didn't get a project name
            if proj["name"] == "(unknown)":
                selected_root = self._j(cur, "ItemTable", "debug.selectedroot")
                if selected_root and isinstance(selected_root, str) and selected_root.startswith("file:///"):
                    path = selected_root[len("file:///"):]
                    if path:
                        root_path = "/" + path.strip("/")
                        project_name = extract_project_name_from_path(root_path)
                        if project_name:
                            proj = {"name": project_name, "rootPath": root_path}

            # composers meta
            comp_meta = {}
            cd = self._j(cur, "ItemTable", "composer.composerData") or {}
            for c in cd.get("allComposers", []):
                comp_meta[c["composerId"]] = {
                    "title": c.get("name", "(untitled)"),
                    "createdAt": c.get("createdAt"),
                    "lastUpdatedAt": c.get("lastUpdatedAt")
                }

            # Try to get composer info from workbench.panel.aichat.view.aichat.chatdata
            chat_data = self._j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata") or {}
            for tab in chat_data.get("tabs", []):
                tab_id = tab.get("tabId")
                if tab_id and tab_id not in comp_meta:
                    comp_meta[tab_id] = {
                        "title": f"Chat {tab_id[:8]}",
                        "createdAt": None,
                        "lastUpdatedAt": None
                    }
        except sqlite3.DatabaseError as e:
            self.logger.debug(f"Error getting workspace info from {db}: {e}")
            proj = {"name": "(unknown)", "rootPath": "(unknown)"}
            comp_meta = {}
        finally:
            if 'con' in locals():
                con.close()

        return proj, comp_meta

    def _extract_bubbles_from_disk_kv(self, db: pathlib.Path) -> Iterable[Tuple[str, str, str, str]]:
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
            self.logger.debug(f"Database error with {db}: {e}")
            return

        db_path_str = str(db)

        for k, v in cur.fetchall():
            try:
                if v is None:
                    continue

                b = json.loads(v)
            except Exception as e:
                self.logger.debug(f"Failed to parse bubble JSON for key {k}: {e}")
                continue

            txt = (b.get("text") or b.get("richText") or "").strip()
            if not txt:
                continue
            role = "user" if b.get("type") == 1 else "assistant"
            composerId = k.split(":")[1]  # Format is bubbleId:composerId:bubbleId
            yield composerId, role, txt, db_path_str

        con.close()

    def _extract_chat_from_item_table(self, db: pathlib.Path) -> Iterable[Tuple[str, str, str, str]]:
        """Yield (composerId, role, text, db_path) from ItemTable."""
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            cur = con.cursor()

            # Try to get chat data from workbench.panel.aichat.view.aichat.chatdata
            chat_data = self._j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata")
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
            composer_data = self._j(cur, "ItemTable", "composer.composerData")
            if composer_data:
                for comp in composer_data.get("allComposers", []):
                    comp_id = comp.get("composerId", "unknown")
                    messages = comp.get("messages", [])
                    for msg in messages:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        if content:
                            yield comp_id, role, content, str(db)

            # Also check for aiService entries
            prompts_data = self._j(cur, "ItemTable", "aiService.prompts")
            generations_data = self._j(cur, "ItemTable", "aiService.generations")

            if prompts_data or generations_data:
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
            self.logger.debug(f"Database error in ItemTable with {db}: {e}")
            return
        finally:
            if 'con' in locals():
                con.close()

    def _extract_composer_data(self, db: pathlib.Path) -> Iterable[Tuple[str, dict, str]]:
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
            self.logger.debug(f"Database error with {db}: {e}")
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
                self.logger.debug(f"Failed to parse composer data for key {k}: {e}")
                continue

        con.close() 