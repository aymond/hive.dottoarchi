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

### Using Docker

You can also run the DOT to ArchiMate Converter using Docker:

```bash
# Build the Docker image
docker build -t dot2archimate .

# Run the web interface
docker run -p 5000:5000 dot2archimate

# Or run with a specific command
docker run dot2archimate convert -i examples/sample.dot -o output.xml

# Mount volumes for persistent storage and easy access to files
docker run -p 5000:5000 -v $(pwd)/examples:/app/examples -v $(pwd)/output:/app/output dot2archimate

# Configure legal settings
docker run -it dot2archimate legal-config --create
```

For detailed Docker instructions, see [DOCKER.md](DOCKER.md).

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

#### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  dot2archimate:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./examples:/app/examples
      - ./output:/app/output
      - ./config:/app/dot2archimate/web/config
```

Then run:

```bash
docker-compose up -d
```

#### Environment Variables

You can pass environment variables to configure the application:

```bash
docker run -p 5000:5000 -e SECRET_KEY=your_secret_key dot2archimate
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

Configure legal information for the web interface:

```bash
# Show current legal settings
dot2archimate legal-config --show

# Create default legal settings
dot2archimate legal-config --create

# Update specific fields
dot2archimate legal-config --company-name "Your Company" --email "contact@example.com"

# Update only impressum section
dot2archimate legal-config --section impressum --street "123 Main St" --zip-city "10115 Berlin"

# Update only privacy section
dot2archimate legal-config --section privacy --hoster "AWS Cloud Services"
```

You can also manually configure the legal settings by copying the template:

```bash
# Copy the template
cp dot2archimate/web/config/legal_settings.yml.template dot2archimate/web/config/legal_settings.yaml

# Edit the file with your information
nano dot2archimate/web/config/legal_settings.yaml
```

Note: The `legal_settings.yaml` file contains personal information and is excluded from version control in `.gitignore`.

### Terraform Integration

DOT to ArchiMate converter supports Terraform graph output files. You can convert your Terraform infrastructure to ArchiMate models for better visualization and documentation.

#### Terraform Module Support

The converter handles Terraform modules by preserving the module structure in the ArchiMate model. Module paths are included in the documentation of elements and displayed in the visualization.

- Module resources (e.g., `module.vpc.google_compute_network.vpc`) are mapped with the module path preserved
- Module names (e.g., `module.vpc`) are mapped to Application Component elements
- Module structure is represented in the visualization, showing the relationship between modules and their resources

### How to use

1. Generate a Terraform graph:
   ```bash
   terraform graph > terraform_graph.dot
   ```

   For graphs with modules, you can use the expand option:
   ```bash
   terraform graph -type=plan -draw-cycles > terraform_graph.dot
   ```

2. Convert the DOT file to ArchiMate XML:
   ```bash
   dot2archimate convert -i terraform_graph.dot -o terraform_architecture.xml
   ```

3. Import the XML file into your ArchiMate modeling tool (e.g., Archi).

### Mapping

The converter automatically detects Terraform-specific elements and maps them to ArchiMate concepts:

- AWS resources (e.g., `aws_instance`, `aws_vpc`) → Technology Node
- Azure resources (e.g., `azurerm_virtual_machine`, `azurerm_virtual_network`) → Technology Node
- GCP resources (e.g., `google_compute_instance`, `google_compute_network`) → Technology Node
- Variables (`var.*`) → Business Actor
- Providers → Technology Service
- Dependencies → Flow Relationship

#### Cloud Provider Specific Mappings

##### AWS Resources
- Compute resources (e.g., `aws_instance`) → Technology Node
- Network resources (e.g., `aws_vpc`, `aws_subnet`) → Technology Node
- Storage resources (e.g., `aws_s3_bucket`) → Technology Artifact
- Serverless resources (e.g., `aws_lambda_function`) → Application Function
- API resources (e.g., `aws_api_gateway`) → Application Interface
- Service resources (e.g., `aws_sns_topic`) → Technology Service

##### Azure Resources
- Compute resources (e.g., `azurerm_virtual_machine`) → Technology Node
- Network resources (e.g., `azurerm_virtual_network`) → Technology Node
- Storage resources (e.g., `azurerm_storage_account`) → Technology Artifact
- Serverless resources (e.g., `azurerm_function_app`) → Application Function
- API resources (e.g., `azurerm_api_management`) → Application Interface
- Service resources (e.g., `azurerm_eventhub`) → Technology Service

##### GCP Resources
- Compute resources (e.g., `google_compute_instance`) → Technology Node
- Network resources (e.g., `google_compute_network`) → Technology Node
- Storage resources (e.g., `google_storage_bucket`) → Technology Artifact
- Serverless resources (e.g., `google_cloudfunctions_function`) → Application Function
- API resources (e.g., `google_cloud_endpoints_service`) → Application Interface
- Service resources (e.g., `google_pubsub_topic`) → Technology Service

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
├── config/             # Docker configuration files
├── config.yaml         # Default configuration
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker image definition
├── DOCKER.md           # Docker documentation
└── README.md           # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 