# Development Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- git

### Development Setup

```bash
# Clone the repository
git clone https://github.com/anyspecs/anyspecs-cli.git
cd anyspecs-cli

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## 📦 Building and Publishing

### Modern Build System (pyproject.toml)

We use `pyproject.toml` as the primary configuration file, following modern Python packaging standards.

#### Build Distribution Packages

```bash
# Install build tools
pip install build twine

# Build source distribution and wheel
python -m build

# Check the built packages
python -m twine check dist/*
```

#### Install from Local Build

```bash
# Install from wheel
pip install dist/anyspecs_cli-*.whl

# Or install in editable mode for development
pip install -e .
```

#### Publish to PyPI

```bash
# Upload to Test PyPI first
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests with coverage
pytest

# Run specific tests
pytest tests/test_extractors.py

# Run tests with verbose output
pytest -v
```

### Test Markers

- `pytest -m unit`: Run only unit tests
- `pytest -m integration`: Run only integration tests
- `pytest -m "not slow"`: Skip slow tests

## 🔧 Code Quality Tools

### Formatting

```bash
# Format code with black
black anyspecs/

# Sort imports with isort
isort anyspecs/
```

### Linting

```bash
# Lint with flake8
flake8 anyspecs/

# Lint with ruff (modern alternative)
ruff check anyspecs/

# Fix issues automatically
ruff check --fix anyspecs/
```

### Type Checking

```bash
# Type check with mypy
mypy anyspecs/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 📁 Project Structure

```
anyspecs-cli/
├── anyspecs/                    # Main package
│   ├── __init__.py            # Package entry point
│   ├── cli.py                 # Unified CLI interface
│   ├── config.py              # Configuration management
│   ├── py.typed               # Type hints marker
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── extractors.py      # Base extractor classes
│   │   └── formatters.py      # Export formatters
│   ├── exporters/             # Source-specific extractors
│   │   ├── __init__.py
│   │   ├── cursor.py          # Cursor AI extractor
│   │   └── claude.py          # Claude Code extractor
│   └── utils/                 # Utility modules
│       ├── __init__.py
│       ├── logging.py         # Logging configuration
│       ├── paths.py           # Path utilities
│       └── upload.py          # Upload functionality
├── tests/                     # Test suite (create when needed)
├── docs/                      # Documentation (create when needed)
├── pyproject.toml             # Modern package configuration
├── requirements.txt           # Dependencies
├── MANIFEST.in                # File inclusion rules
├── .gitignore                 # Git ignore rules
├── .pre-commit-config.yaml    # Pre-commit hooks
├── README.md                  # Main documentation
├── CHANGELOG.md               # Version history
├── DEVELOPMENT.md             # This file
└── LICENSE                    # MIT License
```

## 🔄 Release Process

### Version Management

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.1`
4. Push tag: `git push origin v1.0.1`

### Build and Release

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build new packages
python -m build

# Check packages
python -m twine check dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## 🧩 Adding New Features

### Adding a New AI Assistant Source

1. Create new extractor in `anyspecs/exporters/`
2. Inherit from `BaseExtractor`
3. Implement required methods
4. Add to `__init__.py`
5. Update CLI to include new source
6. Add tests

### Adding a New Export Format

1. Create new formatter in `anyspecs/core/formatters.py`
2. Inherit from `BaseFormatter`
3. Implement required methods
4. Add to CLI options
5. Add tests

## 🐛 Debugging

### Enable Verbose Logging

```bash
anyspecs --verbose list
anyspecs export --verbose --source cursor
```

### Common Issues

1. **Import errors**: Check if package is installed in editable mode
2. **Command not found**: Reinstall with `pip install -e .`
3. **Permission errors**: Check file permissions and paths

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run quality checks: `pre-commit run --all-files`
5. Commit changes: `git commit -m "Description"`
6. Push to branch: `git push origin feature-name`
7. Create Pull Request

## 📋 Configuration

### pyproject.toml vs setup.py

We use `pyproject.toml` instead of `setup.py` for:
- ✅ Modern Python packaging standard (PEP 517/518)
- ✅ Single configuration file for build and tools
- ✅ Better dependency isolation
- ✅ Declarative configuration
- ✅ Tool-specific configurations in one place

### Key Benefits

1. **Isolated builds**: Build dependencies are isolated
2. **Reproducible builds**: Consistent across environments
3. **Modern toolchain**: Compatible with latest packaging tools
4. **Type safety**: Includes `py.typed` marker for type hints
5. **Quality tools**: Pre-configured linting, formatting, testing 