"""
LastPass Python CLI and API setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = "LastPass Python CLI and API Library"

setup(
    name="lastpass-py",
    version="1.0.0",
    author="LastPass Python Contributors",
    description="Complete Python implementation of LastPass CLI with API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dynacylabs/lastpass-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pycryptodome>=3.15.0",
    ],
    extras_require={
        "clipboard": ["pyperclip>=1.8.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "lpass=lastpass.cli:main",
        ],
    },
    package_data={
        "lastpass": ["py.typed"],
    },
    zip_safe=False,
)
