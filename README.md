# DOT to ArchiMate Converter

A robust and user-friendly application that automates the conversion of Graphviz .dot files into ArchiMate XML files, facilitating the integration of visual diagrams into enterprise architecture repositories.

## Features

- Convert DOT files to ArchiMate XML
- Support for various DOT formats
- Customizable mapping rules
- Support for Terraform graph output files
- Command-line interface
- Web interface

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

### Web Interface

Start the web interface:

```bash
dot2archimate web
```

Or with custom host and port:

```bash
dot2archimate web --host 0.0.0.0 --port 8080
```

The web interface will be available at:
- `http://localhost:5000/` (default) or the custom host/port you specified

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

### Terraform Integration

DOT to ArchiMate converter supports Terraform graph output files. You can convert your Terraform infrastructure to ArchiMate models for better visualization and documentation.

### How to use

1. Generate a Terraform graph:
   ```bash
   terraform graph > terraform_graph.dot
   ```

2. Convert the DOT file to ArchiMate XML:
   ```bash
   dot2archimate convert -i terraform_graph.dot -o terraform_architecture.xml
   ```

3. Import the XML file into your ArchiMate modeling tool (e.g., Archi).

### Mapping

The converter automatically detects Terraform-specific elements and maps them to ArchiMate concepts:

- AWS resources (e.g., `aws_instance`, `aws_vpc`) → Technology Node
- Variables (`var.*`) → Business Actor
- Providers → Technology Service
- Dependencies → Flow Relationship

You can customize these mappings in the `config.yaml` file.

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
    # Terraform specific mappings
    aws_instance:
      type: "technology-device"
      attributes:
        - label
        - shape
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
│   ├── web/            # Web interface
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