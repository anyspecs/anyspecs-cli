"""
Unified CLI interface for AnySpecs chat history export tool.
"""

import argparse
import sys
import pathlib
import datetime
import os
from typing import Dict, Any, List, Optional

from .utils.logging import setup_logging
from .utils.paths import get_project_name
from .exporters.cursor import CursorExtractor
from .exporters.claude import ClaudeExtractor
from .exporters.kiro import KiroExtractor
from .exporters.augment import AugmentExtractor
from .exporters.codex import CodexExtractor
from .core.formatters import JSONFormatter, MarkdownFormatter, HTMLFormatter
from . import __version__
from .utils.uploader import AnySpecsUploadClient


class AnySpecsCLI:
    """Main CLI class for AnySpecs."""
    
    def __init__(self):
        self.extractors = {
            'cursor': CursorExtractor(),
            'claude': ClaudeExtractor(),
            'kiro': KiroExtractor(),
            'augment': AugmentExtractor(),
            'codex': CodexExtractor()
        }
        self.formatters = {
            'json': JSONFormatter(),
            'markdown': MarkdownFormatter(),
            'md': MarkdownFormatter(),
            'html': HTMLFormatter()
        }
        self.logger = None
    
    def run(self, args: List[str] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        # Setup logging
        self.logger = setup_logging(verbose=getattr(parsed_args, 'verbose', False))
        
        if parsed_args.command is None:
            parser.print_help()
            return 1
        
        try:
            if parsed_args.command == 'list':
                return self._list_command(parsed_args)
            elif parsed_args.command == 'export':
                return self._export_command(parsed_args)
            elif parsed_args.command == 'compress':
                return self._compress_command(parsed_args)
            elif parsed_args.command == 'setup':
                return self._setup_command(parsed_args)
            elif parsed_args.command == 'upload':
                return self._upload_command(parsed_args)
            else:
                parser.print_help()
                return 1
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            if getattr(parsed_args, 'verbose', False):
                import traceback
                traceback.print_exc()
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='AnySpecs CLI - Code is Cheap, Show me Any Specs',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s list                                    # List all chat sessions from all sources
  %(prog)s list --source cursor                   # List only Cursor sessions(Also works for augment, claude code, kiro and codex)
  %(prog)s export --source claude --format json   # Export Claude sessions as json to .anyspecs/ Default is markdown
  %(prog)s export --session-id abc123 --format html --output chat.html # Export a specific session as html to chat.html
  %(prog)s setup kimi                             # Configure Kimi API key and model  
  %(prog)s setup ppio                             # Configure PPIO API key and model
  %(prog)s setup --list                           # List all configured AI providers
  %(prog)s setup --reset                          # Reset all AI configurations
  %(prog)s compress                               # Use default configured provider for compression
  %(prog)s compress --provider kimi               # Override with specific provider
  %(prog)s compress --api-key YOUR_KEY --model gpt-4  # Override with command line options
  %(prog)s compress --input .anyspecs --output .compressed  # Specify input/output directories
  # Upload (token from env: export ANYSPECS_TOKEN=YOUR_TOKEN)
  %(prog)s upload --list                             # List files on hub
  %(prog)s upload --file path/to/file [--description "desc"] # Upload to anyspecs hub.
  %(prog)s upload --url http://your-server:3000 --file path/to/file # Specify your server

Note: After first-time setup, API keys and models are auto-saved to .env file and config.
      Subsequent runs will automatically load these settings unless overridden.
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Global options
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        
        # list command
        list_parser = subparsers.add_parser('list', help='List all chat sessions')
        list_parser.add_argument('--source', '-s', 
                               choices=['cursor', 'claude', 'kiro', 'augment', 'codex', 'all'], 
                               default='all',
                               help='Source to list sessions from (default: all)')
        list_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
        
        # export command
        export_parser = subparsers.add_parser('export', help='Export chat sessions')
        export_parser.add_argument('--source', '-s',
                                 choices=['cursor', 'claude', 'kiro', 'augment', 'codex', 'all'],
                                 default='all',
                                 help='Source to export from (default: all)')
        export_parser.add_argument('--format', '-f', 
                                 choices=['json', 'markdown', 'md', 'html'], 
                                 default='markdown',
                                 help='Export format (default: markdown)')
        export_parser.add_argument('--output', '-o', 
                                 type=pathlib.Path,
                                 help='Output directory or file path (default: .anyspecs/)')
        export_parser.add_argument('--session-id', '--session',
                                 help='Specify session ID (if not specified, export all)')
        export_parser.add_argument('--project', '-p',
                                 help='Filter by project name')
        export_parser.add_argument('--all-projects', '-a', action='store_true',
                                 help='Export all projects\' sessions (default: only export current project)')
        export_parser.add_argument('--limit', '-l',
                                 type=int,
                                 help='Limit export count')
        export_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
        

        
        # compress command  
        compress_parser = subparsers.add_parser('compress', 
                                               help='AI-compress chat sessions into .specs format (auto-loads config)')
        compress_parser.add_argument('--input', '-i', 
                                   type=pathlib.Path,
                                   default=pathlib.Path('.anyspecs'),
                                   help='Input directory to scan for chat files (default: .anyspecs/)')
        compress_parser.add_argument('--output', '-o',
                                   type=pathlib.Path,
                                   help='Output directory for .specs files (default: same as input)')
        compress_parser.add_argument('--provider', '-p',
                                   choices=['aihubmix', 'kimi', 'minimax', 'ppio', 'dify'],
                                   help='AI provider to use (default: auto-loaded from .env/config)')
        compress_parser.add_argument('--api-key', '--key',
                                   help='AI API key (overrides .env/config, or use ANYSPECS_AI_API_KEY env var)')
        compress_parser.add_argument('--model', '-m',
                                   help='AI model to use (overrides .env/config settings)')
        compress_parser.add_argument('--temperature', '-t',
                                   type=float,
                                   default=0.3,
                                   help='AI temperature (default: 0.3)')
        compress_parser.add_argument('--max-tokens',
                                   type=int,
                                   default=10000,
                                   help='Maximum tokens (default: 10000)')
        compress_parser.add_argument('--pattern', '--filter',
                                   help='File pattern to match (e.g., "*.md", "*cursor*")')
        compress_parser.add_argument('--batch-size', '--batch',
                                   type=int,
                                   default=1,
                                   help='Number of files to process in parallel (default: 1)')
        compress_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
        
        # upload command
        upload_parser = subparsers.add_parser('upload', help='Upload files to AnySpecs hub service')
        upload_parser.add_argument('--url', default='https://hub.anyspecs.cn/',
                                   help='API base URL (default: https://hub.anyspecs.cn/)')
        upload_parser.add_argument('--file', help='File path to upload')
        upload_parser.add_argument('--description', default='', help='File description')
        upload_parser.add_argument('--list', action='store_true', help='List files')
        upload_parser.add_argument('--search', help='Search file keyword')
        upload_parser.add_argument('--page', type=int, default=0, help='Page number (starting from 0)')
        upload_parser.add_argument('--http', action='store_true', help='Force use HTTP instead of HTTPS for testing')
        upload_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')

        # setup command
        setup_parser = subparsers.add_parser('setup', help='Setup and manage AI provider configurations')
        setup_parser.add_argument('provider',
                                choices=['aihubmix', 'kimi', 'minimax', 'ppio', 'dify'],
                                nargs='?',
                                help='AI provider to setup (saves to .env and config files)')
        setup_parser.add_argument('--reset', action='store_true',
                                help='Reset all AI configurations (clears .env and config)')
        setup_parser.add_argument('--list', action='store_true',
                                help='List all configured providers with their settings')
        
        return parser
    
    def _list_command(self, args) -> int:
        """Execute the list command."""
        print("🔍 Searching for chat records...")
        
        # Collect sessions from all requested sources
        all_sessions = []
        sources_to_check = ['cursor', 'claude', 'kiro', 'augment', 'codex'] if args.source == 'all' else [args.source]
        
        for source in sources_to_check:
            extractor = self.extractors[source]
            try:
                sessions = extractor.list_sessions()
                for session in sessions:
                    session['source'] = source
                all_sessions.extend(sessions)
                self.logger.info(f"Found {len(sessions)} sessions from {source}")
            except Exception as e:
                self.logger.warning(f"Error extracting from {source}: {e}")
        
        if not all_sessions:
            print("❌ No chat records found")
            print("💡 Please ensure corresponding IDE is installed and you have used the AI assistants")
            return 1
        
        print(f"✅ Found {len(all_sessions)} chat sessions\n")
        
        # Group by project and source
        projects = {}
        for session in all_sessions:
            key = f"{session['project']} ({session['source']})"
            if key not in projects:
                projects[key] = []
            projects[key].append(session)
        
        for project_key, project_sessions in projects.items():
            print(f"📁 {project_key} ({len(project_sessions)} sessions)")
            
            for session in project_sessions[:5]:  # Only show the first 5
                session_id = session['session_id']
                msg_count = session['message_count']
                date_str = session['date']
                
                print(f"  🆔 {session_id} | 📅 {date_str} | 💬 {msg_count} messages")
                if args.verbose:
                    preview = session.get('preview', 'No preview')
                    print(f"     💭 {preview}")
            
            if len(project_sessions) > 5:
                print(f"     ... and {len(project_sessions) - 5} more sessions")
            print()
        
        return 0
    
    def _export_command(self, args) -> int:
        """Execute the export command."""
        print("🔍 Searching for chat records...")
        
        # Collect chats from all requested sources
        all_chats = []
        sources_to_check = ['cursor', 'claude', 'kiro', 'augment', 'codex'] if args.source == 'all' else [args.source]
        
        for source in sources_to_check:
            extractor = self.extractors[source]
            try:
                chats = extractor.extract_chats()
                # Format chats for export
                for chat in chats:
                    formatted_chat = extractor.format_chat_for_export(chat)
                    all_chats.append(formatted_chat)
                self.logger.info(f"Extracted {len(chats)} chats from {source}")
            except Exception as e:
                self.logger.warning(f"Error extracting from {source}: {e}")
        
        if not all_chats:
            print("❌ No chat records found")
            return 1
        
        # Apply filters
        filtered_chats = self._apply_filters(all_chats, args)
        
        if not filtered_chats:
            print("❌ No chat records match the specified filters")
            return 1
        
        print(f"📊 Preparing to export {len(filtered_chats)} chat sessions (format: {args.format})")
        
        # Get formatter
        formatter = self.formatters[args.format]
        
        # Export
        if len(filtered_chats) == 1:
            return self._export_single_chat(filtered_chats[0], formatter, args)
        else:
            return self._export_multiple_chats(filtered_chats, formatter, args)
    
    def _apply_filters(self, chats: List[Dict[str, Any]], args) -> List[Dict[str, Any]]:
        """Apply filters to the chat list."""
        filtered_chats = chats
        
        # Session ID filter
        if args.session_id:
            filtered_chats = [c for c in filtered_chats if c.get('session_id', '').startswith(args.session_id)]
            if not filtered_chats:
                print(f"❌ No chat records found with session ID starting with '{args.session_id}'")
                return []
        
        # Project filtering logic
        if args.project:
            # User explicitly specified a project
            filtered_chats = [c for c in filtered_chats 
                             if args.project.lower() in c.get('project', {}).get('name', '').lower()]
            if not filtered_chats:
                print(f"❌ No chat records found with project name containing '{args.project}'")
                return []
            print(f"📋 Filtering by specified project: {args.project}")
        elif not args.all_projects:
            # Default to only exporting sessions for the current project
            current_project = get_project_name()
            filtered_chats = [c for c in filtered_chats 
                             if current_project.lower() in c.get('project', {}).get('name', '').lower()]
            if not filtered_chats:
                print(f"❌ No chat records found for current project '{current_project}'")
                print(f"💡 Use --all-projects to export all projects' sessions, or use --project to specify another project")
                return []
            print(f"📋 Defaulting to current project: {current_project}")
        else:
            # User explicitly requested to export all projects
            print("📋 Exporting all projects' sessions")
        
        # Limit
        if args.limit:
            filtered_chats = filtered_chats[:args.limit]
        
        return filtered_chats
    
    def _export_single_chat(self, chat: Dict[str, Any], formatter, args) -> int:
        """Export a single chat."""
        session_id = chat.get('session_id', 'unknown')[:8]
        project_name = chat.get('project', {}).get('name', 'unknown').replace(' ', '_')
        source = chat.get('source', 'unknown')
        
        # Determine output path - default to .anyspecs directory
        if args.output:
            output_base = args.output
        else:
            output_base = pathlib.Path.cwd() / '.anyspecs'
            output_base.mkdir(exist_ok=True)  # Create .anyspecs directory if it doesn't exist
        
        if output_base.is_dir() or not output_base.suffix:
            # Generate a filename
            filename = f"{source}-chat-{project_name}-{session_id}"
            output_path = output_base / filename if output_base.is_dir() else pathlib.Path(str(output_base) + f"-{session_id}")
        else:
            output_path = output_base
        
        # Add extension if needed
        if not output_path.suffix:
            output_path = output_path.with_suffix(formatter.get_file_extension())
        
        try:
            content = formatter.format(chat)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Export successful: {output_path}")
            print(f"📄 File size: {output_path.stat().st_size} bytes")
            
            return 0
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return 1
    
    def _export_multiple_chats(self, chats: List[Dict[str, Any]], formatter, args) -> int:
        """Export multiple chats."""
        if args.output:
            output_base = args.output
        else:
            output_base = pathlib.Path.cwd() / '.anyspecs'
        
        if not output_base.is_dir():
            output_base.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_base}")
        
        success_count = 0
        for i, chat in enumerate(chats, 1):
            # Generate filename
            session_id = chat.get('session_id', '')[:8] or f'chat{i:03d}'
            project_name = chat.get('project', {}).get('name', 'unknown').replace(' ', '_')
            source = chat.get('source', 'unknown')
            
            # Add timestamp to differentiate files
            timestamp = ""
            if chat.get('date'):
                try:
                    date_obj = datetime.datetime.fromtimestamp(chat['date'])
                    timestamp = date_obj.strftime("-%Y%m%d-%H%M%S")
                except:
                    timestamp = f"-{int(chat['date'])}"
            else:
                timestamp = f"-{i:03d}"
            
            filename = f"{source}-chat-{project_name}-{session_id}{timestamp}"
            output_path = output_base / filename
            
            # Add extension if needed
            if not output_path.suffix:
                output_path = output_path.with_suffix(formatter.get_file_extension())
            
            try:
                content = formatter.format(chat)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ {i}/{len(chats)}: {output_path.name}")
                success_count += 1
            except Exception as e:
                print(f"❌ {i}/{len(chats)}: Export failed - {e}")
        
        print(f"\n🎉 Batch export completed! {success_count}/{len(chats)} files exported to: {output_base}")
        
        return 0 if success_count > 0 else 1
    

    def _upload_command(self, args) -> int:
        """Execute the upload command (token read from ANYSPECS_TOKEN)."""
        token = os.environ.get('ANYSPECS_TOKEN')
        client = AnySpecsUploadClient(args.url, token, args.http)

        if not token:
            print("⚠️  No ANYSPECS_TOKEN environment variable found")
            print("💡  Please set: export ANYSPECS_TOKEN=YOUR_TOKEN")
            print("💡  Or use interactive mode to enter token manually")
            # Fall back to interactive mode
            client.interactive_mode()
            return 0

        # Validate token first
        if not client.validate_token():
            return 1

        # Dispatch operations
        if args.file:
            return 0 if client.upload_file(str(args.file), args.description) else 1
        if args.list:
            return 0 if client.list_files(args.page) else 1
        if args.search:
            return 0 if client.list_files(args.page, args.search) else 1

        # If no specific op, just test connection and show help summary
        client.test_connection()
        print("Use one of: --file, --list, --search")
        return 0

    def _compress_command(self, args) -> int:
        """Execute the compress command."""
        print("🤖 AI chat compression starting...")
        
        # Import required modules
        try:
            from .core.ai_processor import AIProcessor
            from .config.ai_config import ai_config
        except ImportError:
            print("❌ Required modules not found. Please ensure all dependencies are installed.")
            return 1
        
        # Validate input directory
        input_dir = args.input
        if not input_dir.exists():
            print(f"❌ Input directory does not exist: {input_dir}")
            return 1
        
        # Set output directory (default to same as input)
        output_dir = args.output or input_dir
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine provider to use
        provider = args.provider
        
        # If no provider specified via args, try to get from config
        if not provider:
            provider = ai_config.get_default_provider()
            if not provider:
                print("❌ No AI provider specified and no default provider configured.")
                print("💡 Let's set up your first AI provider...")
                # Use aihubmix as default for first setup
                provider = 'aihubmix'
        
        # Check if provider is configured, if not run interactive setup
        if not ai_config.is_configured(provider):
            print(f"🔧 {provider.upper()} is not configured yet.")
            print("Let's set it up...")
            
            success = ai_config.setup_interactive(provider)
            if not success:
                print("❌ Configuration failed. Cannot proceed with compression.")
                return 1
            
            print()  # Add spacing after setup
        
        # Get provider configuration (already includes .env file priority)
        provider_config = ai_config.get_provider_config(provider)
        
        # Override with command line arguments if provided (highest priority)
        api_key = args.api_key or provider_config.get('api_key')
        model = args.model or provider_config.get('model')
        # Provider-specific base URL for dify
        base_url = provider_config.get('base_url')
        temperature = getattr(args, 'temperature', None)
        if temperature is None:
            temperature = provider_config.get('temperature', 0.3)
        max_tokens = getattr(args, 'max_tokens', None)
        if max_tokens is None:
            max_tokens = provider_config.get('max_tokens', 10000)
        
        # Final validation
        if not api_key:
            print("❌ No API key found. Please configure the provider or provide --api-key.")
            return 1
        
        if not model:
            print("❌ No model specified. Please configure the provider or provide --model.")
            return 1
        
        # Show configuration being used
        print(f"🔧 Using provider: {provider}")
        print(f"🤖 Using model: {model}")
        if args.verbose:
            print(f"🌡️  Temperature: {temperature}")
            print(f"🔢 Max tokens: {max_tokens}")
            print(f"📁 Input directory: {input_dir}")
            print(f"📁 Output directory: {output_dir}")
        
        try:
            # Initialize AI processor
            # Prepare additional config parameters
            extra_config = {}
            
            # Add MiniMax specific parameters
            if provider == 'minimax':
                group_id = provider_config.get('group_id')
                if group_id:
                    extra_config['group_id'] = group_id
                    if args.verbose:
                        print(f"🏷️  Group ID: {group_id}")
                else:
                    print("⚠️  Warning: MiniMax group_id not configured. Please run 'anyspecs setup minimax' to configure it.")
            
            processor = AIProcessor(
                provider=provider,
                api_key=api_key,
                model=model or "",
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url if provider == 'dify' else None,
                **extra_config
            )
            
            # Process files
            success = processor.compress_directory(
                input_dir=input_dir,
                output_dir=output_dir,
                pattern=args.pattern,
                batch_size=args.batch_size,
                verbose=args.verbose
            )
            
            return 0 if success else 1
            
        except Exception as e:
            print(f"❌ Compression failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _setup_command(self, args) -> int:
        """Execute the setup command."""
        
        try:
            from .config.ai_config import ai_config
        except ImportError:
            print("❌ AI config module not found. Please ensure all dependencies are installed.")
            return 1
        
        # Handle list option
        if args.list:
            return self._list_ai_providers()
        
        # Handle reset option
        if args.reset:
            return self._reset_ai_config()
        
        # Check if provider is specified
        if not args.provider:
            print("❌ Provider is required when not using --list or --reset")
            print("💡 Available providers: aihubmix, kimi, minimax, ppio")
            print("💡 Use 'anyspecs setup --list' to see configured providers")
            return 1
        
        # Setup specific provider
        provider = args.provider
        print(f"🔧 Setting up {provider.upper()} AI provider...")
        
        success = ai_config.setup_interactive(provider)
        return 0 if success else 1
    
    def _list_ai_providers(self) -> int:
        """List all configured AI providers."""
        
        try:
            from .config.ai_config import ai_config
        except ImportError:
            print("❌ AI config module not found.")
            return 1
        
        configured_providers = ai_config.list_configured_providers()
        
        if not configured_providers:
            print("❌ No AI providers configured yet.")
            print("💡 Use 'anyspecs setup <provider>' to configure a provider.")
            return 1
        
        print("🤖 Configured AI Providers:")
        print("=" * 40)
        
        for provider_info in configured_providers:
            status = "✅ (default)" if provider_info['is_default'] else "✅"
            print(f"{status} {provider_info['provider'].upper()}")
            print(f"   Model: {provider_info['model']}")
            print()
        
        return 0
    
    def _reset_ai_config(self) -> int:
        """Reset AI configuration."""
        
        try:
            from .config.ai_config import ai_config
        except ImportError:
            print("❌ AI config module not found.")
            return 1
        
        try:
            confirm = input("⚠️  This will reset all AI configurations. Continue? (y/N): ").strip().lower()
            if confirm not in ('y', 'yes'):
                print("❌ Reset cancelled.")
                return 1
            
            success = ai_config.reset_config()
            if success:
                print("✅ AI configuration reset successfully.")
                return 0
            else:
                print("❌ Failed to reset AI configuration.")
                return 1
                
        except KeyboardInterrupt:
            print("\n❌ Reset cancelled by user.")
            return 1


def main():
    """Main entry point."""
    cli = AnySpecsCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main()) 