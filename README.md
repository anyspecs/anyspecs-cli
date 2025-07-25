# AnySpec CLI - Universal Chat History Export Tool

AnySpec CLI is a unified command-line tool for exporting chat history from multiple AI assistants. It currently supports **Cursor AI** and **Claude Code**, with support for various export formats including Markdown, HTML, and JSON.

## Features

- **Multi-Source Support**: Export from Cursor AI and Claude Code
- **Multiple Export Formats**: Markdown, HTML, and JSON
- **Project-Based Filtering**: Export sessions by project or current directory
- **Session Management**: List, filter, and export specific chat sessions
- **Upload Support**: Upload exported files to remote servers
- **Organized Package Structure**: Clean, modular codebase with separate packages for different functionality

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/anyspec/anyspec-cli.git
cd anyspec-cli

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Using pip (when published)

```bash
pip install anyspec-cli
```

## Quick Start

### List All Chat Sessions

```bash
# List all chat sessions from all sources
anyspec list

# List only Cursor sessions
anyspec list --source cursor

# List only Claude sessions  
anyspec list --source claude

# Show detailed information
anyspec list --verbose
```

### Export Chat Sessions

```bash
# Export current project's sessions to Markdown (default)
anyspec export

# Export all sessions to HTML
anyspec export --all-projects --format html

# Export specific session
anyspec export --session-id abc123 --format json

# Export Claude sessions only
anyspec export --source claude --format markdown

# Export with custom output path
anyspec export --output ./exports --format html

# Export and upload to server
anyspec export --format json --upload --server https://myserver.com --username user --password pass
```

## Usage Examples

### Basic Usage

```bash
# List all available chat sessions
anyspec list

# Export current project's chat history to Markdown
anyspec export

# Export all projects to HTML format
anyspec export --all-projects --format html
```

### Advanced Usage

```bash
# Export specific project's sessions
anyspec export --project myproject --format json

# Export last 10 sessions only
anyspec export --limit 10 --format markdown

# Export specific session to custom location
anyspec export --session-id abc123 --output ~/Documents/chat-export.html --format html

# Export and upload to remote server
anyspec export --format json --upload \
  --server https://api.example.com \
  --username myuser \
  --password mypass
```

## Command Reference

### Global Options

- `--verbose, -v`: Enable verbose logging
- `--help, -h`: Show help message

### List Command

```bash
anyspec list [OPTIONS]
```

**Options:**
- `--source, -s {cursor,claude,all}`: Source to list sessions from (default: all)
- `--verbose, -v`: Display detailed information

### Export Command

```bash
anyspec export [OPTIONS]
```

**Options:**
- `--source, -s {cursor,claude,all}`: Source to export from (default: all)
- `--format, -f {json,markdown,md,html}`: Export format (default: markdown)
- `--output, -o PATH`: Output directory or file path
- `--session-id, --session ID`: Export specific session ID
- `--project, -p NAME`: Filter by project name
- `--all-projects, -a`: Export all projects' sessions
- `--limit, -l NUMBER`: Limit number of sessions to export
- `--upload`: Upload exported file to server
- `--server URL`: Server URL for upload (default: http://localhost:4999)
- `--username USER`: Username for server authentication
- `--password PASS`: Password for server authentication

## Supported Sources

### Cursor AI

Extracts chat history from Cursor's local SQLite databases, including:
- Workspace-specific conversations
- Global chat storage
- Composer data and bubble conversations
- Project context and metadata

### Claude Code

Extracts chat history from Claude Code's JSONL history files, including:
- User messages and AI responses
- Tool calls and results
- Session metadata
- Project context

## Export Formats

### Markdown (.md)

Clean, readable format with:
- Project information header
- Conversation history with role indicators
- Code block preservation
- Timestamps and metadata

### HTML (.html)

Rich web format with:
- Styled conversation display
- User/Assistant message differentiation
- Code syntax highlighting
- Responsive design

### JSON (.json)

Structured data format with:
- Complete conversation data
- Metadata and timestamps
- Project information
- Source attribution

## Package Structure

```
anyspec-cli/
├── anyspec/
│   ├── __init__.py          # Main package
│   ├── cli.py               # CLI interface
│   ├── config.py           # Configuration management
│   ├── core/               # Core functionality
│   │   ├── extractors.py   # Base extractor classes
│   │   └── formatters.py   # Export formatters
│   ├── exporters/          # Source-specific extractors
│   │   ├── cursor.py       # Cursor AI extractor
│   │   └── claude.py       # Claude Code extractor
│   └── utils/              # Utility modules
│       ├── logging.py      # Logging configuration
│       ├── paths.py        # Path utilities
│       └── upload.py       # Upload functionality
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Configuration

AnySpec CLI stores configuration in `~/.anyspec/config.json`. You can customize:

- Default export format
- Default output directory
- Source preferences
- Server settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/anyspec/anyspec-cli.git
cd anyspec-cli

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black anyspec/

# Type checking
mypy anyspec/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- Support for Cursor AI and Claude Code
- Multiple export formats (Markdown, HTML, JSON)
- Upload functionality
- Project-based filtering
- Organized package structure

## Support

If you encounter any issues or have questions, please:

1. Check the [documentation](https://github.com/anyspec/anyspec-cli/wiki)
2. Search [existing issues](https://github.com/anyspec/anyspec-cli/issues)
3. Create a [new issue](https://github.com/anyspec/anyspec-cli/issues/new)
