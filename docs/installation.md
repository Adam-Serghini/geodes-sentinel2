# Installation

## Prerequisites

- Python 3.9 or higher
- pip or UV package manager
- Git (for development installation)

## Installing with UV (Recommended)

UV is a fast Python package manager that's 10-100x faster than pip.

```bash
# Install UV
pip install uv

# Clone the repository
git clone https://github.com/yourusername/geodes-sentinel2.git
cd geodes-sentinel2

# Create virtual environment
uv venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install the package
uv pip install -e .
```

## Installing with pip

```bash
# Clone the repository
git clone https://github.com/yourusername/geodes-sentinel2.git
cd geodes-sentinel2

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install the package
pip install -e .
```

## Installing from PyPI (Coming Soon)

```bash
pip install geodes-sentinel2
```

## Setting up API Key

1. Register at [GEODES portal](https://geodes-portal.cnes.fr) to get your API key
2. Create a `.env` file in your project directory:

```bash
cp .env.example .env
```

3. Edit `.env` and add your API key:

```
GEODES_API_KEY=your-api-key-here
```

Alternatively, you can set it as an environment variable:

```bash
export GEODES_API_KEY="your-api-key-here"  # Linux/Mac
# or
set GEODES_API_KEY=your-api-key-here  # Windows
```

## Verifying Installation

Test that the installation worked:

```bash
geodes-sentinel2 --version
geodes-sentinel2 info
```

## Development Installation

For development with all tools:

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Troubleshooting

### Module Not Found Errors

If you get import errors, make sure your virtual environment is activated:

```bash
which python  # Should show .venv/bin/python
```

### API Key Not Found

Make sure your `.env` file is in the current directory or set the environment variable:

```bash
echo $GEODES_API_KEY  # Should show your key
```

### Permission Errors

On Linux/Mac, you might need to make scripts executable:

```bash
chmod +x .venv/bin/geodes-sentinel2
```