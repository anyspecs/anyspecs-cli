<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/headerDark.svg" />
    <img src="assets/headerLight.svg" alt="AnySpecs CLI" />
  </picture>

***Code is cheap, Show me Any Specs.***
  
[:page_facing_up: 中文版本](https://github.com/anyspecs/anyspecs-cli/blob/main/README_zh.md) |
[:gear: Quick Start](#quick-start) |
[:thinking: Reporting Issues](https://github.com/anyspecs/anyspecs-cli/issues/new/choose)

</div>

AnySpecs CLI is a unified command-line tool for exporting chat history from multiple AI assistants. It currently supports **Cursor AI**, **Claude Code**, and **Kiro Records**, with support for various export formats including Markdown, HTML, and JSON.

## Features

- **Multi-Source Support**: Export from Cursor AI, Claude Code, and Kiro Records(More to come)
- **Multiple Export Formats**: Markdown, HTML, and JSON
- **Project-Based and Workspace Filtering**: Export sessions by project or current directory
- **Flexible Session Management**: List, filter, and export specific sessions
- **Default Export Directory**: All exports save to `.anyspecs/` by default for organized storage
- **Terminal history and files diff history**: Export terminal history and files diff history(WIP)
- **AI Summary**: Summarize chat history into a single file (WIP)
- **Server Upload and Share**: Upload exported files to remote servers (WIP)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/anyspecs/anyspecs-cli.git
cd anyspecs-cli

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Using pip

```bash
pip install anyspecs
```

## Quick Start

### List All Chat Sessions in this workspace

```bash
# List all chat sessions in this workspace from all sources
anyspecs list

# List only Cursor/Claude/Kiro sessions in this workspace
anyspecs list --source cursor/claude/kiro

# Show detailed information
anyspecs list --verbose
```

### Export Chat Sessions

```bash
# Export current project's sessions to Markdown (default to .anyspecs/)
anyspecs export

# Export all sessions to HTML (default to .anyspecs/)
anyspecs export --all-projects --format html

# Export specific session
anyspecs export --session-id abc123 --format json

# Export Claude sessions only
anyspecs export --source claude --format markdown

# Export Kiro records only
anyspecs export --source kiro --format html

# Export with custom output path
anyspecs export --output ./exports --format html

# Export and upload to server(WIP)
anyspecs export --format json --upload --server https://myserver.com --username user --password pass
```

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

### Kiro Records

Extracts and combines markdown documents from `.kiro` directory, including:
- File metadata (name, modification time)
- Automatic project summary detection

## Package Structure

```
anyspecs-cli/
├── anyspecs/
│   ├── __init__.py          # Main package
│   ├── cli.py               # CLI interface
│   ├── config.py           # Configuration management
│   ├── core/               # Core functionality
│   │   ├── extractors.py   # Base extractor classes
│   │   └── formatters.py   # Export formatters
│   ├── exporters/          # Source-specific extractors
│   │   ├── cursor.py       # Cursor AI extractor
│   │   └── claude.py       # Claude Code extractor
│   │   └── kiro.py         # Kiro Records extractor
│   └── utils/              # Utility modules
│       ├── logging.py      # Logging configuration
│       ├── paths.py        # Path utilities
│       └── upload.py       # Upload functionality
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/anyspecs/anyspecs-cli.git
cd anyspecs-cli

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black anyspecs/

# Type checking
mypy anyspecs/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.0.2
- Kiro Records support: Extract and export files from .kiro directory
- Default export directory: All exports now save to .anyspecs/ by default
- Workspace filtering: Cursor sessions now show only current workspace sessions in list command

### v0.0.1
- Initial release
- Support for Cursor AI and Claude Code
- Multiple export formats (Markdown, HTML, JSON)
- Upload functionality
- Project-based filtering
- Organized package structure

## Support

If you encounter any issues or have questions, please:

1. Check the [documentation](https://github.com/anyspecs/anyspecs-cli/wiki)
2. Search [existing issues](https://github.com/anyspecs/anyspecs-cli/issues)
3. Create a [new issue](https://github.com/anyspecs/anyspecs-cli/issues/new)
