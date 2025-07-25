"""
Setup script for AnySpec CLI.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = "AnySpec CLI - Universal Chat History Export Tool"

# Read requirements
requirements_file = this_directory / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#') and not line.startswith('-')
        ]

setup(
    name="anyspec-cli",
    version="1.0.0",
    author="AnySpec Team",
    author_email="team@anyspec.dev",
    description="Universal Chat History Export Tool for AI Assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anyspec/anyspec-cli",
    project_urls={
        "Bug Tracker": "https://github.com/anyspec/anyspec-cli/issues",
        "Documentation": "https://github.com/anyspec/anyspec-cli/wiki",
        "Source Code": "https://github.com/anyspec/anyspec-cli",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "rich": [
            "rich>=13.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "anyspec=anyspec.cli:main",
            "anyspec-cli=anyspec.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "chat", "export", "ai", "assistant", "cursor", "claude", 
        "history", "backup", "markdown", "html", "json"
    ],
) 