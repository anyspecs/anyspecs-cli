"""
Export formatters for different output formats.
"""

import json
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any

from ..utils.logging import get_logger

logger = get_logger('formatters')


class BaseFormatter(ABC):
    """Base class for all formatters."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f'formatters.{name}')
    
    @abstractmethod
    def format(self, chat: Dict[str, Any]) -> str:
        """Format a chat session for export."""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this format."""
        pass


class JSONFormatter(BaseFormatter):
    """JSON formatter."""
    
    def __init__(self):
        super().__init__('json')
    
    def format(self, chat: Dict[str, Any]) -> str:
        """Format chat as JSON."""
        return json.dumps(chat, indent=2, ensure_ascii=False, default=str)
    
    def get_file_extension(self) -> str:
        return '.json'


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter."""
    
    def __init__(self):
        super().__init__('markdown')
    
    def format(self, chat: Dict[str, Any]) -> str:
        """Format chat as Markdown."""
        try:
            # Format date for display
            date_display = "Unknown date"
            if chat.get('date'):
                try:
                    date_obj = datetime.datetime.fromtimestamp(chat['date'])
                    date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    self.logger.warning(f"Error formatting date: {e}")
            
            # Get project info
            project_name = chat.get('project', {}).get('name', 'Unknown Project')
            project_path = chat.get('project', {}).get('rootPath', 'Unknown Path')
            session_id = chat.get('session_id', 'Unknown')
            source = chat.get('source', 'Unknown')
            
            # Build the Markdown content
            markdown_lines = []
            
            # Title and metadata
            markdown_lines.append(f"# Chat Export: {project_name}")
            markdown_lines.append("")
            markdown_lines.append("## Chat Information")
            markdown_lines.append("")
            markdown_lines.append(f"- **Project**: {project_name}")
            markdown_lines.append(f"- **Path**: `{project_path}`")
            markdown_lines.append(f"- **Date**: {date_display}")
            markdown_lines.append(f"- **Session ID**: `{session_id}`")
            markdown_lines.append(f"- **Source**: {source}")
            markdown_lines.append("")
            
            # Messages
            messages = chat.get('messages', [])
            
            if not messages:
                markdown_lines.append("## Conversation History")
                markdown_lines.append("")
                markdown_lines.append("No messages found in this conversation.")
            else:
                markdown_lines.append("## Conversation History")
                markdown_lines.append("")
                
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    if not content or not isinstance(content, str):
                        content = "Content unavailable"
                    
                    # Add role header
                    role_display = "👤 **User**" if role == "user" else "🤖 **Assistant**"
                    markdown_lines.append(f"### {role_display}")
                    markdown_lines.append("")
                    
                    # Process content - preserve code blocks and formatting
                    processed_content = content.strip()
                    
                    # If content contains code blocks, keep them as-is
                    if "```" in processed_content:
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
            markdown_lines.append(f"*Exported from {source} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

            return "\n".join(markdown_lines)
            
        except Exception as e:
            self.logger.error(f"Error generating Markdown: {e}", exc_info=True)
            return f"""# Error Generating Chat Export

**Error**: {e}

Please try again or contact support if the problem persists.

---
"""

    def get_file_extension(self) -> str:
        return '.md'


class HTMLFormatter(BaseFormatter):
    """HTML formatter."""
    
    def __init__(self):
        super().__init__('html')
    
    def format(self, chat: Dict[str, Any]) -> str:
        """Format chat as HTML."""
        try:
            # Format date for display
            date_display = "Unknown date"
            if chat.get('date'):
                try:
                    date_obj = datetime.datetime.fromtimestamp(chat['date'])
                    date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    self.logger.warning(f"Error formatting date: {e}")
            
            # Get project info
            project_name = chat.get('project', {}).get('name', 'Unknown Project')
            project_path = chat.get('project', {}).get('rootPath', 'Unknown Path')
            session_id = chat.get('session_id', 'Unknown')
            source = chat.get('source', 'Unknown')
            
            # Build the HTML content
            messages_html = ""
            messages = chat.get('messages', [])
            
            if not messages:
                messages_html = "<p>No messages found in this conversation.</p>"
            else:
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    if not content or not isinstance(content, str):
                        content = "Content unavailable"
                    
                    # Simple HTML escaping
                    escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    
                    # Convert markdown code blocks
                    processed_content = ""
                    in_code_block = False
                    for line in escaped_content.split('\n'):
                        if line.strip().startswith("```"):
                            if not in_code_block:
                                processed_content += "<pre><code>"
                                in_code_block = True
                                line = line.strip()[3:]  # Remove the first ``` marker
                            else:
                                processed_content += "</code></pre>\n"
                                in_code_block = False
                                line = ""  # Skip the closing ``` line
                        
                        if in_code_block:
                            processed_content += line + "\n"
                        else:
                            processed_content += line + "<br>"
                    
                    # Close any unclosed code block at the end
                    if in_code_block:
                        processed_content += "</code></pre>"
                    
                    avatar = "👤" if role == "user" else "🤖"
                    name = "User" if role == "user" else "Assistant"
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
    <title>Chat Export - {project_name}</title>
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
        <h1>Chat Export: {project_name}</h1>
    </div>
    <div class="chat-info">
        <div class="info-item"><span class="info-label">Project:</span> <span>{project_name}</span></div>
        <div class="info-item"><span class="info-label">Path:</span> <span>{project_path}</span></div>
        <div class="info-item"><span class="info-label">Date:</span> <span>{date_display}</span></div>
        <div class="info-item"><span class="info-label">Session ID:</span> <span>{session_id}</span></div>
        <div class="info-item"><span class="info-label">Source:</span> <span>{source}</span></div>
    </div>
    <h2>Conversation History</h2>
    <div class="messages">
{messages_html}
    </div>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 0.9em; color: #666;">
        <p>Exported from {source} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>"""
            
            return html
        except Exception as e:
            self.logger.error(f"Error generating HTML: {e}", exc_info=True)
            return f"<html><body><h1>Error generating chat export</h1><p>Error: {e}</p></body></html>"
    
    def get_file_extension(self) -> str:
        return '.html' 