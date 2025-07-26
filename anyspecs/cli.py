"""
Unified CLI interface for AnySpecs chat history export tool.
"""

import argparse
import sys
import pathlib
import datetime
from typing import Dict, Any, List, Optional

from .utils.logging import setup_logging
from .utils.paths import get_project_name
from .utils.upload import upload_file_to_server
from .exporters.cursor import CursorExtractor
from .exporters.claude import ClaudeExtractor
from .exporters.kiro import KiroExtractor
from .core.formatters import JSONFormatter, MarkdownFormatter, HTMLFormatter


class AnySpecsCLI:
    """Main CLI class for AnySpecs."""
    
    def __init__(self):
        self.extractors = {
            'cursor': CursorExtractor(),
            'claude': ClaudeExtractor(),
            'kiro': KiroExtractor()
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
            description='AnySpecs CLI - Universal Chat History Export Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Chat Export
  %(prog)s list                                    # List all chat sessions from all sources
  %(prog)s list --source cursor                   # List only Cursor sessions
  %(prog)s export --format markdown               # Export current project's sessions to .anyspecs/
  %(prog)s export --source claude --format json   # Export Claude sessions to .anyspecs/
  %(prog)s export --session-id abc123 --format html --output chat.html
  %(prog)s export --project myproject --format json --upload --server http://localhost:4999

  # AI Configuration (First-time setup)
  %(prog)s setup aihubmix                         # Configure Aihubmix API key and model
  %(prog)s setup kimi                             # Configure Kimi API key and model  
  %(prog)s setup minimax                          # Configure MiniMax API key, model and Group ID
  %(prog)s setup ppio                             # Configure PPIO API key and model
  %(prog)s setup --list                           # List all configured AI providers
  %(prog)s setup --reset                          # Reset all AI configurations

  # AI Compression (Auto-load from config)
  %(prog)s compress                               # Use default configured provider for compression
  %(prog)s compress --provider kimi               # Override with specific provider
  %(prog)s compress --api-key YOUR_KEY --model gpt-4  # Override with command line options
  %(prog)s compress --dry-run --verbose           # Preview files to be compressed
  %(prog)s compress --input .anyspecs --output .compressed  # Specify input/output directories

Note: After first-time setup, API keys and models are auto-saved to .env file and config.
      Subsequent runs will automatically load these settings unless overridden.
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Global options
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        
        # list command
        list_parser = subparsers.add_parser('list', help='List all chat sessions')
        list_parser.add_argument('--source', '-s', 
                               choices=['cursor', 'claude', 'kiro', 'all'], 
                               default='all',
                               help='Source to list sessions from (default: all)')
        list_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
        
        # export command
        export_parser = subparsers.add_parser('export', help='Export chat sessions')
        export_parser.add_argument('--source', '-s',
                                 choices=['cursor', 'claude', 'kiro', 'all'],
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
        
        # Upload options
        export_parser.add_argument('--upload', action='store_true',
                                 help='Upload exported file to server')
        export_parser.add_argument('--server', default="http://localhost:4999",
                                 help='Server URL for upload (default: http://localhost:4999)')
        export_parser.add_argument('--username', help='Username for server authentication')
        export_parser.add_argument('--password', help='Password for server authentication')
        
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
                                   choices=['aihubmix', 'kimi', 'minimax', 'ppio'],
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
        compress_parser.add_argument('--dry-run', action='store_true',
                                   help='Show what would be compressed without actually doing it')
        compress_parser.add_argument('--verbose', '-v', action='store_true', help='Display detailed information')
        
        # setup command
        setup_parser = subparsers.add_parser('setup', help='Setup and manage AI provider configurations')
        setup_parser.add_argument('provider',
                                choices=['aihubmix', 'kimi', 'minimax', 'ppio'],
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
        sources_to_check = ['cursor', 'claude', 'kiro'] if args.source == 'all' else [args.source]
        
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
            print("💡 Please ensure Cursor and/or Claude Code are installed and you have used the AI assistants")
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
        sources_to_check = ['cursor', 'claude', 'kiro'] if args.source == 'all' else [args.source]
        
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
            
            # Upload if requested
            if args.upload:
                return self._upload_file(output_path, args)
            
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
        
        # Upload if requested (upload the directory as a zip)
        if args.upload and success_count > 0:
            return self._upload_directory(output_base, args)
        
        return 0 if success_count > 0 else 1
    
    def _upload_file(self, file_path: pathlib.Path, args) -> int:
        """Upload a single file."""
        if not args.username or not args.password:
            print("❌ Error: --username and --password required for upload")
            return 1
        
        success = upload_file_to_server(file_path, args.server, args.username, args.password)
        return 0 if success else 1
    
    def _upload_directory(self, directory_path: pathlib.Path, args) -> int:
        """Upload a directory as a zip file."""
        import shutil
        
        if not args.username or not args.password:
            print("❌ Error: --username and --password required for upload")
            return 1
        
        # Create a zip file
        zip_path = directory_path.with_suffix('.zip')
        try:
            shutil.make_archive(str(directory_path), 'zip', directory_path)
            print(f"📦 Created zip file: {zip_path}")
            
            success = upload_file_to_server(zip_path, args.server, args.username, args.password)
            
            # Clean up zip file
            zip_path.unlink()
            
            return 0 if success else 1
        except Exception as e:
            print(f"❌ Error creating zip file: {e}")
            return 1
    
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
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_config
            )
            
            # Process files
            success = processor.compress_directory(
                input_dir=input_dir,
                output_dir=output_dir,
                pattern=args.pattern,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
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