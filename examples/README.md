# Example DOT Files for ArchiMate Conversion

This directory contains example DOT files demonstrating various architecture patterns and use cases for conversion to ArchiMate format.

## Available Examples

### 1. `sample.dot` (Basic Example)
A simple example showing basic application and business layer relationships.

**Use Case:** Learning the basics of DOT to ArchiMate conversion

### 2. `enterprise_architecture.dot`
A comprehensive enterprise architecture example showing:
- Business processes (Order Processing, Payment Processing, Fulfillment)
- Application systems (CRM, Order Management, Payment Gateway)
- Technology infrastructure (Web Server, Application Server, Database)
- Complete flow from business to technology layers

**Use Case:** Enterprise architecture modeling, business-IT alignment

### 3. `microservices_architecture.dot`
A modern microservices architecture demonstrating:
- API Gateway pattern
- Service discovery and registry
- Inter-service communication
- Message-driven architecture
- Distributed data stores
- Caching strategies

**Use Case:** Microservices architecture documentation, service mesh design

### 4. `cloud_infrastructure.dot`
A cloud infrastructure example (AWS-focused) showing:
- Cloud compute services (EC2, Lambda, ECS)
- Cloud storage (S3, RDS, DynamoDB, EFS)
- Networking (VPC, Subnets, Load Balancer, CDN)
- Messaging services (SQS, SNS)
- Security (Security Groups, IAM)
- Monitoring (CloudWatch)

**Use Case:** Cloud architecture documentation, infrastructure as code visualization

### 5. `business_process.dot`
A business process-focused diagram showing:
- Business actors (Customer, Sales Rep, Warehouse Staff)
- Business processes (Lead Generation, Sales, Order Processing)
- Business services and objects
- Process flows and dependencies

**Use Case:** Business process modeling, BPMN alternative, process documentation

### 6. `application_integration.dot`
An integration architecture example showing:
- Legacy system integration (ERP, Mainframe)
- Modern applications (CRM, E-Commerce)
- Integration patterns (ESB, API Gateway, Message Broker)
- Data transformation and orchestration
- External service integration

**Use Case:** Integration architecture, legacy modernization, EAI documentation

### 7. `three_tier_architecture.dot`
A classic three-tier architecture showing:
- Presentation tier (Web Server, CDN)
- Application tier (Application Servers, Business Logic)
- Data tier (Primary/Replica Database, Cache, File Storage)
- Infrastructure components (Load Balancer, Firewall)

**Use Case:** Traditional application architecture, scalability patterns

### 8. `terraform/terraform_graph.dot`
A Terraform infrastructure graph showing:
- AWS resources (EC2, VPC, Security Groups)
- Resource dependencies
- Provider relationships

**Use Case:** Infrastructure as Code visualization, Terraform documentation

## How to Use

### Convert a Single File
```bash
dot2archimate convert -i examples/enterprise_architecture.dot -o output/enterprise_architecture.xml
```

### Convert All Examples
```bash
dot2archimate batch-convert -i examples/ -o output/
```

### Using Docker
```bash
docker run -v $(pwd)/examples:/app/examples -v $(pwd)/output:/app/output dot2archimate batch-convert -i /app/examples -o /app/output
```

## ArchiMate Element Types

The examples demonstrate various ArchiMate element types:

### Business Layer
- **Business Actor**: `type="business"` with `shape="ellipse"`
- **Business Process**: `type="business"` with `shape="box"`
- **Business Object**: `type="business"` with `shape="note"`

### Application Layer
- **Application Component**: `type="application"` with `shape="box"`
- **Application Function**: `type="application"` with `shape="box"` (for functions)
- **Application Interface**: `type="application"` with `shape="diamond"` (for APIs/Gateways)

### Technology Layer
- **Technology Node**: `type="technology"` with `shape="box"`
- **Technology Service**: `type="technology"` with `shape="diamond"`
- **Technology Artifact**: `type="technology"` with `shape="box"` (for storage)

### Relationships
- **Serving Relationship**: `label="uses"`, `label="provides data to"`
- **Flow Relationship**: `label="sends"`, `label="routes to"`
- **Access Relationship**: `label="stores in"`, `label="reads from"`
- **Composition Relationship**: `label="part of"`, `label="hosts"`
- **Assignment Relationship**: `label="runs on"`, `label="deployed in"`

## Tips for Creating Your Own DOT Files

1. **Use descriptive labels**: Make node and edge labels clear and meaningful
2. **Consistent naming**: Use consistent naming conventions for similar elements
3. **Layer separation**: Organize your diagram by ArchiMate layers (Business, Application, Technology)
4. **Relationship types**: Use appropriate relationship labels to get correct ArchiMate relationship types
5. **Comments**: Use comments (`//`) to document your diagram
6. **Grouping**: Use subgraphs for logical grouping (though they may not map directly to ArchiMate)

## Customization

You can customize the mapping by editing `config.yaml` to match your specific needs. For example:
- Change default element types
- Add custom resource type mappings
- Modify relationship type mappings

## Contributing

Feel free to add more examples that demonstrate specific patterns or use cases!

