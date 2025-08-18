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

AnySpecs CLI is a unified command-line tool for exporting chat history from multiple AI assistants. It currently supports **Cursor AI**, **Claude Code**, **Codex cli**, **Augment** and **Kiro Records**, with support for various export formats including Markdown, HTML, and JSON.

## Features

- **Multi-Source Support**: Export from Cursor AI, Claude Code, Augment Code, Codex cli and Kiro Records(More to come)
- **Multiple Export Formats**: Markdown, HTML, and JSON
- **Project-Based and Workspace Filtering**: Export sessions by project or current directory
- **Flexible Session Management**: List, filter, and export specific sessions
- **Default Export Directory**: All exports save to `.anyspecs/` by default for organized storage
- **AI Summary**: Summarize chat history into a single file
- **Server Upload and Share**: Upload exported files to remote servers
- **Terminal history and files diff history**: Export terminal history and files diff history(WIP)

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
anyspecs list --source cursor/claude/kiro/augment/codex/all
```

### Export Chat Sessions

```bash
# Export current project's sessions to Markdown (default to .anyspecs/)
anyspecs export

# Export all sessions to HTML (default to .anyspecs/)
anyspecs export --all-projects --format html

# Export specific session
anyspecs export [--session-id abc123] [--format json]

# Export specific source sessions only(default is markdown) with custom output path
anyspecs export [--source claude/cursor/kiro/augment/codex] [--format markdown] [--output ./exports]
```

### Setup config

```bash
# Setup specific AI provider
anyspecs setup [aihubmix/kimi/minimax/ppio/dify]
# list all the providers
anyspecs setup --list
# reset all the providers
anyspecs setup --reset
```

### Compress

```bash
# Check out anyspecs compress --help for more information
anyspecs compress [--input anyspecs.md] [--output anyspecs.specs] [--provider aihubmix/kimi/minimax/ppio/dify] ....
```
### Upload to share your specs

> The default url is our official hub https://hub.anyspecs.cn/, you can also deploy the [ASAP](https://github.com/anyspecs/ASAP) on your own server and use it.

Before your first upload, your should get your token on https://hub.anyspecs.cn/setting generate your token via `生成访问令牌`, then export your token into your environment variable. eg: `export ANYSPECS_TOKEN="44xxxxxxxxxxxxxx7a82"`.

```bash
# Default url is https://hub.anyspecs.cn/, you can also specify your server.
# Check remote specs repo
anyspecs upload --list
# Search specific repo
anyspecs upload --search "My specs"
# Upload a file to remote server
anyspecs upload --file anyspecs.specs
# Upload a file to remote server with description
anyspecs upload --file anyspecs.specs --description "My specs"
```

### More Functions

```shell
anyspecs --help
# positional arguments:
#   {list,export,compress,upload,setup}
#                         Available commands
#     list                List all chat sessions
#     export              Export chat sessions
#     compress            AI-compress chat sessions into .specs format (auto-loads config)
#     upload              Upload files to AnySpecs hub service
#     setup               Setup and manage AI provider configurations
# options:
#   -h, --help            show this help message and exit
#   --verbose, -v         Enable verbose logging
```

## Supported Sources

- Cursor AI: from Cursor's local SQLite databases
- Claude Code: from Claude Code's JSONL history files
- Augment Code: from VSCode's history databases
- Codex cli: from Codex cli's history files
- Kiro Records: from summary directory of Kiro

History mainly includes:
- Workspace-specific conversations
- Global chat storage
- Composer data and bubble conversations
- Project context and metadata

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
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.0.5
- Add Codex cli support
- Add Dify workflow process
- Add upload to remote server support

### v0.0.4
- Add Augment Code support
- Add version option

### v0.0.3
- Add AI Summary support(PPIO, Minimax, Kimi)

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
