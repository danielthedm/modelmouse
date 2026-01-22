from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="modelmouse",
    version="0.1.0",
    author="Daniel Leslie",
    description="Standalone CLI tool for LLM model benchmarking and recommendations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danielleslie/modelmouse",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "typer>=0.9.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "anthropic>=0.75.0",
        "openai>=2.0.0",
        "google-genai>=1.0.0",
        "mistralai>=1.0.0",
        "groq>=0.9.0",
        "httpx>=0.27.0",
        "numpy>=1.26.0",
        "rich>=13.0.0",
        "tabulate>=0.9.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "modelmouse=modelmouse.cli:app",
        ],
    },
)
