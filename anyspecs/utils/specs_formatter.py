"""
.specs file format handler and validator.
Based on the TypeScript reference implementation.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .logging import get_logger

logger = get_logger('specs_formatter')


class SpecsFormatter:
    """Handler for .specs file format operations."""
    
    def __init__(self):
        self.logger = logger
    
    def generate_specs_filename(
        self, 
        original_filename: str, 
        project_name: Optional[str] = None
    ) -> str:
        """Generate .specs filename based on original file and project name."""
        
        timestamp = datetime.now().isoformat().replace(':', '-').replace('T', '_').split('.')[0]
        
        # Extract meaningful project name
        base_name = self._extract_project_name(original_filename, project_name)
        
        # Sanitize filename
        base_name = self._sanitize_filename(base_name)
        
        return f"{base_name}_context_{timestamp}.specs"
    
    def _extract_project_name(
        self, 
        original_filename: str, 
        parsed_project_name: Optional[str] = None
    ) -> str:
        """Extract meaningful project name from filename or parsed data."""
        
        # Use parsed project name if available and meaningful
        if (parsed_project_name and 
            parsed_project_name.strip() and 
            parsed_project_name != "未知项目" and
            parsed_project_name != "Unknown Project"):
            return parsed_project_name.strip()
        
        # Extract from original filename
        if original_filename and original_filename.strip():
            safe_original_name = original_filename.strip()
            
            # Remove file extension
            extracted = re.sub(r'\.[^/.]+$', '', safe_original_name)
            
            # Remove common timestamp patterns
            extracted = re.sub(r'_\d{4}-\d{2}-\d{2}.*$', '', extracted)
            extracted = re.sub(r'_\d{8}_\d{6}.*$', '', extracted)
            extracted = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}.*$', '', extracted)
            
            # Remove common prefixes
            extracted = re.sub(r'^(conversation|chat|context|export|cursor-chat|claude-chat|kiro-chat)[-_]?', '', extracted, flags=re.IGNORECASE)
            
            # If we have meaningful content, use it
            if 0 < len(extracted) < 50:
                return extracted
        
        # Default name
        return "AI分析结果"
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename by removing invalid characters."""
        
        if not name or not isinstance(name, str):
            return "未命名"
        
        return (name
                # Keep Chinese, English, numbers, underscore, hyphen, space
                .replace('/', '_').replace('\\', '_').replace(':', '_')
                .replace('*', '_').replace('?', '_').replace('"', '_')
                .replace('<', '_').replace('>', '_').replace('|', '_')
                # Replace multiple spaces/special chars with single underscore
                .replace(' ', '_')
                # Remove leading/trailing underscores
                .strip('_')
                # Limit length
                [:30])
    
    def save_specs_file(self, specs_data: Dict[str, Any], file_path: Path) -> bool:
        """Save specs data to file."""
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Format JSON content with proper indentation
            json_content = json.dumps(specs_data, ensure_ascii=False, indent=2)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            self.logger.info(f"Saved .specs file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save .specs file {file_path}: {e}")
            return False
    
    def load_specs_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse .specs file."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            specs_data = json.loads(content)
            
            if validate_specs_file(specs_data):
                return specs_data
            else:
                self.logger.warning(f"Invalid .specs format in file: {file_path}")
                return None
                
        except FileNotFoundError:
            self.logger.error(f".specs file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in .specs file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading .specs file {file_path}: {e}")
            return None
    
    def parse_api_response_to_specs(
        self, 
        raw_response: str, 
        file_name: str
    ) -> Dict[str, Any]:
        """Parse AI API response into .specs format."""
        
        if not raw_response or not isinstance(raw_response, str):
            raise ValueError("API response is empty or invalid format")
        
        # Try to parse as JSON first
        try:
            json_data = json.loads(raw_response)
            if validate_specs_file(json_data):
                return json_data
            else:
                self.logger.warning("AI response doesn't match .specs format, creating wrapper")
        except json.JSONDecodeError:
            self.logger.warning("AI response is not valid JSON, creating wrapper")
        
        # Create wrapper .specs format for non-JSON or invalid responses
        project_name = self._extract_project_name(file_name, None)
        
        wrapper_specs = {
            "version": "1.0",
            "metadata": {
                "name": project_name,
                "task_type": "general_chat",
                "createdAt": datetime.now().isoformat(),
                "source_file": file_name,
                "analysis_model": "unknown"
            },
            "receiver_instructions": {
                "context_understanding": "理解压缩的聊天上下文",
                "response_requirements": ["继续对话"],
                "mandatory_reply": "请继续对话",
                "forbidden_actions": "不要忽略之前的对话历史"
            },
            "raw_ai_response": raw_response
        }
        
        return wrapper_specs


def validate_specs_file(data: Any) -> bool:
    """Validate .specs file format."""
    
    if not isinstance(data, dict):
        return False
    
    # Check required fields
    if 'metadata' not in data:
        return False
    
    metadata = data['metadata']
    if not isinstance(metadata, dict):
        return False
    
    # Check required metadata fields
    required_metadata_fields = ['name', 'task_type']
    for field in required_metadata_fields:
        if field not in metadata:
            return False
    
    # Check receiver_instructions exists (required field)
    if 'receiver_instructions' not in data:
        return False
    
    receiver_instructions = data['receiver_instructions']
    if not isinstance(receiver_instructions, dict):
        return False
    
    # Validate task_type values
    valid_task_types = ['chat_compression', 'code_project', 'general_chat']
    if metadata.get('task_type') not in valid_task_types:
        return False
    
    # If task_type is code_project, assets should be present
    if metadata.get('task_type') == 'code_project':
        if 'assets' not in data:
            logger.warning("code_project task_type should include 'assets' field")
    
    # If task_type is chat_compression, chat_compression should be present
    if metadata.get('task_type') == 'chat_compression':
        if 'chat_compression' not in data:
            logger.warning("chat_compression task_type should include 'chat_compression' field")
    
    return True


def create_minimal_specs(
    name: str,
    task_type: str = "general_chat",
    content: str = ""
) -> Dict[str, Any]:
    """Create a minimal valid .specs file."""
    
    return {
        "version": "1.0",
        "metadata": {
            "name": name,
            "task_type": task_type,
            "createdAt": datetime.now().isoformat()
        },
        "receiver_instructions": {
            "context_understanding": "理解提供的上下文",
            "response_requirements": ["继续对话"],
            "mandatory_reply": "请继续对话",
            "forbidden_actions": "不要忽略上下文"
        },
        "content": content if content else "无内容"
    }


def merge_specs_files(specs_list: list[Dict[str, Any]], merged_name: str) -> Dict[str, Any]:
    """Merge multiple .specs files into one."""
    
    if not specs_list:
        return create_minimal_specs(merged_name)
    
    # Use first file as base
    merged = specs_list[0].copy()
    merged['metadata']['name'] = merged_name
    merged['metadata']['createdAt'] = datetime.now().isoformat()
    merged['metadata']['merged_from'] = len(specs_list)
    
    # Collect all content
    merged_content = []
    
    for i, specs in enumerate(specs_list):
        source_name = specs.get('metadata', {}).get('name', f'source_{i}')
        merged_content.append(f"=== {source_name} ===")
        
        # Add raw_ai_response if present
        if 'raw_ai_response' in specs:
            merged_content.append(specs['raw_ai_response'])
        
        # Add chat_compression summary if present
        if 'chat_compression' in specs:
            compression = specs['chat_compression']
            if 'context_summary' in compression:
                summary = compression['context_summary']
                merged_content.append(f"主要话题: {summary.get('main_topic', 'N/A')}")
                merged_content.append(f"当前任务: {summary.get('current_task', 'N/A')}")
        
        merged_content.append("")  # Empty line separator
    
    merged['merged_content'] = "\n".join(merged_content)
    
    return merged