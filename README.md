# DOT to ArchiMate Converter

A robust and user-friendly application that automates the conversion of Graphviz .dot files into ArchiMate XML files, facilitating the integration of visual diagrams into enterprise architecture repositories.

## Features

- Convert Graphviz DOT files to ArchiMate XML format
- REST API for file uploads and text conversion
- Command-line interface for single file and batch processing
- Configurable mapping rules between DOT and ArchiMate elements
- Comprehensive error handling and logging

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/dot2archimate.git
cd dot2archimate

# Install the package
pip install -e .
```

## Usage

### API Server

Start the API server:

```bash
uvicorn dot2archimate.api.app:app --reload
```

The API will be available at:
- `http://localhost:8000/` - API information
- `http://localhost:8000/convert/file` - Convert DOT file to ArchiMate XML
- `http://localhost:8000/convert/text` - Convert DOT text to ArchiMate XML

### Command Line Interface

Convert a single file:

```bash
dot2archimate convert -i examples/sample.dot -o output.xml
```

Convert multiple files:

```bash
dot2archimate batch-convert -i examples/ -o output/
```

## Configuration

The mapping between DOT elements and ArchiMate elements is defined in `config.yaml`. You can customize this file to match your specific needs.

Example configuration:

```yaml
mapping_rules:
  nodes:
    application:
      type: "application-component"
      attributes:
        - label
        - description
    business:
      type: "business-actor"
      attributes:
        - label
        - description
  relationships:
    uses:
      type: "serving-relationship"
      attributes:
        - label
```

## Development

### Setup Development Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Tests

```bash
pytest
```

## Project Structure

```
dot2archimate/
├── dot2archimate/
│   ├── api/            # API endpoints
│   ├── core/           # Core conversion logic
│   ├── cli/            # Command-line interface
│   └── config/         # Configuration handling
├── tests/              # Test suite
├── examples/           # Example DOT files
├── config.yaml         # Default configuration
└── README.md           # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 