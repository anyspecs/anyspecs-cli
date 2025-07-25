# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern pyproject.toml configuration
- Type hints support (py.typed marker)
- Pre-commit hooks configuration
- Enhanced development tools configuration
- Kiro Records support: Extract and export markdown files from .kiro directory
- Default export directory: All exports now save to .anyspecs/ by default

## [0.0.1] - 2025-07-25

### Added
- Initial release of AnySpecs CLI
- Support for Cursor AI chat history extraction
- Support for Claude Code chat history extraction
- Support for Kiro Records extraction from .kiro directory
- Multiple export formats: Markdown, HTML, JSON
- Project-based filtering and session management
- Upload functionality to remote servers
- Unified CLI interface with `anyspec` command
- Well-organized package structure with modular design

### Features
- **Multi-Source Support**: Extract from Cursor AI, Claude Code, and Kiro Records
- **Export Formats**: Markdown (.md), HTML (.html), JSON (.json)
- **Project Filtering**: Filter by current project or specify custom projects
- **Session Management**: List, filter, and export specific chat sessions
- **Upload Support**: Upload exported files to remote servers
- **Verbose Logging**: Detailed logging for debugging

### Commands
- `anyspecs list`: List all available chat sessions
- `anyspecs export`: Export chat sessions with various options

### Package Structure
- `anyspecs.core`: Core functionality (extractors, formatters)
- `anyspecs.exporters`: Source-specific extractors (cursor, claude)
- `anyspecs.utils`: Utility modules (logging, paths, upload)
- `anyspecs.cli`: Unified command-line interface 