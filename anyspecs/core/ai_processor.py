"""
AI-powered chat compression processor for AnySpecs CLI.
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils.logging import get_logger
from ..utils.specs_formatter import SpecsFormatter, validate_specs_file
from ..config.prompts import SYSTEM_PROMPT, CONTEXT_ANALYSIS_PROMPT
from ..ai_clients import create_ai_client, AVAILABLE_PROVIDERS

logger = get_logger('ai_processor')


class AIProcessor:
    """AI-powered chat compression processor."""
    
    def __init__(
        self, 
        provider: str,
        api_key: str, 
        model: str,
        **kwargs
    ):
        """Initialize AI processor with API configuration."""
        
        # Validate provider
        if provider not in AVAILABLE_PROVIDERS:
            raise ValueError(f"Unsupported AI provider: {provider}. Available: {list(AVAILABLE_PROVIDERS.keys())}")
        
        # Create AI client
        self.ai_client = create_ai_client(
            provider=provider,
            api_key=api_key,
            model=model,
            **kwargs
        )
        
        self.provider = provider
        self.specs_formatter = SpecsFormatter()
        self.logger = logger
    
    def compress_directory(
        self, 
        input_dir: Path, 
        output_dir: Path, 
        pattern: Optional[str] = None,
        batch_size: int = 1,
        verbose: bool = False
    ) -> bool:
        """Compress all chat files in a directory."""
        
        self.logger.info(f"Scanning directory: {input_dir}")
        
        # Find files to process
        files_to_process = self._find_files_to_process(input_dir, pattern)
        
        if not files_to_process:
            print("❌ No chat files found to compress")
            return False
        
        print(f"📁 Found {len(files_to_process)} files to process")
        
        # Process files
        success_count = 0
        total_count = len(files_to_process)
        
        for i, file_path in enumerate(files_to_process, 1):
            print(f"\n🤖 Processing {i}/{total_count}: {file_path.name}")
            
            try:
                success = self._compress_single_file(file_path, output_dir, verbose)
                if success:
                    success_count += 1
                    print(f"✅ Successfully compressed")
                else:
                    print(f"❌ Compression failed")
                    
            except Exception as e:
                print(f"❌ Error processing file: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()
        
        # Summary
        print(f"\n🎉 Compression completed: {success_count}/{total_count} files processed successfully")
        
        if success_count < total_count:
            print(f"⚠️  {total_count - success_count} files failed to process")
        
        return success_count > 0
    
    def _find_files_to_process(self, input_dir: Path, pattern: Optional[str] = None) -> List[Path]:
        """Find chat files to process in the directory."""
        files = []
        
        if pattern:
            # Use custom pattern
            search_pattern = str(input_dir / pattern)
            files = [Path(f) for f in glob.glob(search_pattern)]
        else:
            # Default patterns for common chat file formats
            patterns = [
                "*.md", "*.markdown",  # Markdown files
                "*.html",              # HTML exports
                "*.json",              # JSON exports
                "*.txt"                # Text files
            ]
            
            for pat in patterns:
                search_pattern = str(input_dir / pat)
                files.extend([Path(f) for f in glob.glob(search_pattern)])
        
        # Filter out .specs files (don't reprocess them)
        files = [f for f in files if not f.name.endswith('.specs')]
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return files
    
    def _compress_single_file(self, file_path: Path, output_dir: Path, verbose: bool = False) -> bool:
        """Compress a single chat file using AI."""
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if not file_content.strip():
                self.logger.warning(f"File is empty: {file_path}")
                return False
            
            # Generate AI prompt
            system_prompt = SYSTEM_PROMPT
            user_prompt = CONTEXT_ANALYSIS_PROMPT(file_path.name) + f"\n\n文件内容：\n{file_content}"
            
            if verbose:
                print(f"  📤 Sending to AI (content length: {len(file_content)} chars)")
            
            # Call AI depending on provider
            if self.provider == 'dify':
                # Use Dify workflow: upload the file then run workflow
                try:
                    # Save temp content to a file to upload
                    tmp_path = Path(file_path)
                    # Upload existing file and run workflow
                    file_id = getattr(self.ai_client, 'upload_file')(tmp_path)
                    if not file_id:
                        self.logger.error('Dify upload failed')
                        return False
                    result = getattr(self.ai_client, 'run_workflow')(file_id)
                    if not result:
                        self.logger.error('Dify workflow failed')
                        return False
                    # Construct a JSON response resembling .specs minimal fallback
                    outputs = result.get('data', {}).get('outputs', {}) if isinstance(result, dict) else {}
                    ai_response = json.dumps({
                        "version": "1.0",
                        "metadata": {
                            "name": self._extract_project_name(file_path.name),
                            "task_type": "chat_compression",
                            "createdAt": self._get_current_timestamp(),
                            "source_platform": "anyspecs_cli",
                            "analysis_model": "dify_workflow"
                        },
                        "receiver_instructions": {
                            "context_understanding": "Generated by Dify workflow",
                            "response_requirements": ["continue"],
                            "mandatory_reply": "Please continue",
                            "forbidden_actions": "None"
                        },
                        "raw_ai_response": json.dumps(outputs, ensure_ascii=False)
                    }, ensure_ascii=False)
                except Exception as e:
                    self.logger.error(f"Dify processing error: {e}")
                    return False
            else:
                ai_response = self.ai_client.process_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )
            
            if not ai_response:
                self.logger.error("Empty response from AI")
                return False
            
            if verbose:
                print(f"  📥 Received AI response (length: {len(ai_response)} chars)")
            
            # Parse and validate AI response
            specs_data = self._parse_ai_response(ai_response, file_path.name)
            
            if not specs_data:
                self.logger.error("Failed to parse AI response")
                return False
            
            # Generate output filename
            output_filename = self.specs_formatter.generate_specs_filename(
                original_filename=file_path.name,
                project_name=specs_data.get('metadata', {}).get('name')
            )
            
            output_path = output_dir / output_filename
            
            # Write .specs file
            success = self.specs_formatter.save_specs_file(specs_data, output_path)
            
            if success and verbose:
                print(f"  💾 Saved to: {output_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error compressing file {file_path}: {e}")
            return False
    
    def _parse_ai_response(self, ai_response: str, filename: str) -> Optional[Dict[str, Any]]:
        """Parse and validate AI response into .specs format."""
        
        try:
            # Try to parse as JSON first
            specs_data = json.loads(ai_response)
            
            # Validate the specs format
            if validate_specs_file(specs_data):
                return specs_data
            else:
                self.logger.warning("AI response doesn't match .specs format, creating fallback")
                
        except json.JSONDecodeError:
            self.logger.warning("AI response is not valid JSON, creating fallback")
        
        # Create fallback .specs format
        fallback_specs = {
            "version": "1.0",
            "metadata": {
                "name": self._extract_project_name(filename),
                "task_type": "chat_compression",
                "createdAt": self._get_current_timestamp(),
                "source_platform": "anyspecs_cli",
                "analysis_model": self.ai_client.model
            },
            "receiver_instructions": {
                "context_understanding": "理解压缩的聊天上下文",
                "response_requirements": ["继续对话", "保持上下文连贯性"],
                "mandatory_reply": "请继续对话",
                "forbidden_actions": "不要忽略之前的对话历史"
            },
            "raw_ai_response": ai_response
        }
        
        return fallback_specs
    
    def _extract_project_name(self, filename: str) -> str:
        """Extract project name from filename."""
        # Remove extension
        name = Path(filename).stem
        
        # Remove common prefixes
        for prefix in ['cursor-chat-', 'claude-chat-', 'kiro-chat-', 'chat-', 'export-']:
            if name.startswith(prefix):
                name = name[len(prefix):]
        
        # Remove timestamps
        import re
        name = re.sub(r'[-_]\d{4}-\d{2}-\d{2}.*$', '', name)
        name = re.sub(r'[-_]\d{8}[-_]\d{6}.*$', '', name)
        
        return name or "未知项目"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()