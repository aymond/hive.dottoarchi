from typing import Dict, Any, List
import yaml
from logging import getLogger
import uuid
import re

logger = getLogger(__name__)

class ArchimateMapper:
    def __init__(self, config_path: str = None):
        self.mapping_rules = self._load_config(config_path) if config_path else {}
        self.element_ids = {}  # Store mapping between DOT IDs and ArchiMate IDs
        self.terraform_resource_types = {
            # AWS resources
            'aws_instance': 'technology-node',
            'aws_vpc': 'technology-node',
            'aws_subnet': 'technology-node',
            'aws_security_group': 'technology-node',
            'aws_route_table': 'technology-node',
            'aws_internet_gateway': 'technology-node',
            'aws_lb': 'technology-node',
            'aws_db_instance': 'technology-node',
            'aws_s3_bucket': 'technology-artifact',
            'aws_dynamodb_table': 'technology-artifact',
            'aws_lambda_function': 'application-function',
            'aws_api_gateway': 'application-interface',
            'aws_cloudfront_distribution': 'technology-service',
            'aws_cloudwatch': 'technology-service',
            'aws_sns_topic': 'technology-service',
            'aws_sqs_queue': 'technology-service',
            
            # Azure resources
            'azurerm_virtual_machine': 'technology-node',
            'azurerm_linux_virtual_machine': 'technology-node',
            'azurerm_windows_virtual_machine': 'technology-node',
            'azurerm_virtual_network': 'technology-node',
            'azurerm_subnet': 'technology-node',
            'azurerm_network_security_group': 'technology-node',
            'azurerm_route_table': 'technology-node',
            'azurerm_public_ip': 'technology-node',
            'azurerm_sql_server': 'technology-node',
            'azurerm_sql_database': 'technology-artifact',
            'azurerm_storage_account': 'technology-artifact',
            'azurerm_storage_container': 'technology-artifact',
            'azurerm_app_service': 'application-component',
            'azurerm_function_app': 'application-function',
            'azurerm_api_management': 'application-interface',
            'azurerm_application_gateway': 'technology-service',
            'azurerm_eventhub': 'technology-service',
            'azurerm_servicebus_namespace': 'technology-service',
            'azurerm_cosmosdb_account': 'technology-node',
            'azurerm_key_vault': 'technology-artifact',
            
            # GCP resources
            'google_compute_instance': 'technology-node',
            'google_compute_network': 'technology-node',
            'google_compute_subnetwork': 'technology-node',
            'google_compute_firewall': 'technology-node',
            'google_compute_router': 'technology-node',
            'google_compute_global_address': 'technology-node',
            'google_sql_database_instance': 'technology-node',
            'google_sql_database': 'technology-artifact',
            'google_storage_bucket': 'technology-artifact',
            'google_container_cluster': 'technology-node',
            'google_container_node_pool': 'technology-node',
            'google_cloud_run_service': 'application-component',
            'google_cloudfunctions_function': 'application-function',
            'google_cloud_scheduler_job': 'application-function',
            'google_pubsub_topic': 'technology-service',
            'google_pubsub_subscription': 'technology-service',
            'google_bigquery_dataset': 'technology-artifact',
            'google_bigquery_table': 'technology-artifact',
            'google_kms_key_ring': 'technology-artifact',
            
            # Generic Terraform resources
            'provider': 'technology-service',
            'var': 'business-actor',
            'data': 'business-object',
            'module': 'grouping',
            'output': 'business-object',
            'local': 'business-object'
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load mapping rules from configuration file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load mapping configuration: {e}")
            raise ValueError(f"Invalid configuration file: {e}")

    def map_to_archimate(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal graph representation to ArchiMate structure."""
        try:
            archimate_elements = []
            archimate_relationships = []
            
            # Check if this is a Terraform graph
            is_terraform = graph_data.get('is_terraform', False)
            
            logger.info(f"Processing graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
            logger.info(f"Is Terraform graph: {is_terraform}")

            # Map nodes to ArchiMate elements
            for node_id, node in graph_data['nodes'].items():
                try:
                    element = self._map_node(node, is_terraform)
                    if element:
                        archimate_elements.append(element)
                except Exception as e:
                    logger.error(f"Error mapping node {node_id}: {str(e)}")
                    raise

            # Map edges to ArchiMate relationships
            for edge in graph_data['edges']:
                try:
                    relationship = self._map_edge(edge, graph_data['nodes'], is_terraform)
                    if relationship:
                        archimate_relationships.append(relationship)
                except Exception as e:
                    logger.error(f"Error mapping edge {edge.get('source', 'unknown')} -> {edge.get('target', 'unknown')}: {str(e)}")
                    raise

            return {
                'elements': archimate_elements,
                'relationships': archimate_relationships
            }
        except Exception as e:
            logger.error(f"Mapping failed: {e}")
            raise ValueError(f"Failed to map to ArchiMate: {e}")

    def _map_node(self, node: Dict[str, Any], is_terraform: bool = False) -> Dict[str, Any]:
        """Map a single node to an ArchiMate element."""
        try:
            node_id = node['id']
            display_id = node.get('display_id', node_id)
            attributes = node['attributes']
            
            logger.debug(f"Mapping node in mapper: id={node_id}, display_id={display_id}")
            logger.debug(f"Node attributes in mapper: {attributes}")
            
            logger.info(f"Mapping node: id={node_id}, display_id={display_id}")
            
            # Determine element type
            node_type = self._determine_node_type(display_id, attributes, is_terraform)
            logger.info(f"Determined node type: {node_type}")
            
            if not node_type:
                logger.warning(f"Could not determine node type for {display_id}")
                return None

            archimate_id = str(uuid.uuid4())
            self.element_ids[node_id] = archimate_id

            # Get the node name from label or ID
            node_name = node.get('label', attributes.get('label', display_id))
            
            # Clean up Terraform node names
            if is_terraform and isinstance(node_name, str):
                logger.info(f"Original node name: {node_name}")
                # Remove [root] prefix if present
                if node_name.startswith('[root] '):
                    node_name = node_name[7:]
                # Remove (expand) suffix if present
                if ' (expand)' in node_name:
                    node_name = node_name.replace(' (expand)', '')
                # Handle provider nodes
                if node_name.startswith('provider['):
                    node_name = node_name.replace('provider[', '').replace(']', '')
                    node_name = node_name.replace('"', '')
                    node_name = f"Provider: {node_name}"
                logger.info(f"Cleaned node name: {node_name}")
            
            # Prepare documentation
            documentation = attributes.get('description', '')
            
            # Add module information to documentation if available
            if 'module_path' in attributes:
                logger.debug(f"Found module_path in attributes: {attributes['module_path']}")
                module_info = f"Module: {attributes['module_path']}"
                if documentation:
                    documentation = f"{documentation}\n\n{module_info}"
                else:
                    documentation = module_info
            
            # Extract properties (excluding certain keys)
            # Use a simple dictionary comprehension to extract properties
            properties = {k: v for k, v in attributes.items() if k not in ['type', 'label', 'description']}
            
            # Add module path as a property if it exists
            if 'module_path' in attributes:
                properties['module_path'] = attributes['module_path']
            
            logger.debug(f"Final properties: {properties}")

            return {
                'id': archimate_id,
                'type': node_type,
                'name': node_name,
                'documentation': documentation,
                'properties': properties
            }
        except Exception as e:
            logger.error(f"Error in _map_node for {node.get('id', 'unknown')}: {str(e)}", exc_info=True)
            raise

    def _map_edge(self, edge: Dict[str, Any], nodes: Dict[str, Dict[str, Any]], is_terraform: bool = False) -> Dict[str, Any]:
        """Map a single edge to an ArchiMate relationship."""
        source_id = edge['source']
        target_id = edge['target']
        attributes = edge['attributes']
        
        # Get source and target nodes
        source_node = nodes.get(source_id)
        target_node = nodes.get(target_id)
        
        if not source_node or not target_node:
            return None
        
        # Determine relationship type
        relationship_type = self._determine_relationship_type(attributes, source_node, target_node, is_terraform)
        
        # Get source and target ArchiMate IDs
        source_archimate_id = self.element_ids.get(source_id)
        target_archimate_id = self.element_ids.get(target_id)
        
        if not source_archimate_id or not target_archimate_id:
            return None

        return {
            'id': str(uuid.uuid4()),
            'type': relationship_type,
            'source': source_archimate_id,
            'target': target_archimate_id,
            'name': attributes.get('label', ''),
            'properties': self._extract_properties(attributes)
        }

    def _determine_node_type(self, node_id: str, attributes: Dict[str, str], is_terraform: bool = False) -> str:
        """Determine ArchiMate element type based on node attributes and ID."""
        try:
            logger.info(f"Determining node type for: {node_id}")
            
            # First check if the node has an explicit type attribute
            if 'type' in attributes:
                node_type = attributes['type'].lower()
                logger.info(f"Node has explicit type attribute: {node_type}")
                for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('nodes', {}).items():
                    if rule_type in node_type:
                        return rule['type']
                return node_type  # Return the type as is if no mapping found
            
            # For Terraform resources, determine type based on resource type
            if is_terraform:
                logger.info(f"Processing Terraform node: {node_id}")
                
                # Extract resource type from Terraform node ID
                terraform_pattern = r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)'
                match = re.search(terraform_pattern, node_id)
                
                # If it's a module, try to extract the actual resource type
                if 'module.' in node_id:
                    logger.info(f"Found module in node ID: {node_id}")
                    parts = node_id.split('.')
                    for part in parts:
                        if part.startswith(('aws_', 'azurerm_', 'azuread_', 'google_')):
                            logger.info(f"Extracted resource type from module: {part}")
                            resource_type = part
                            # Check if we have a mapping for this resource type
                            if resource_type in self.terraform_resource_types:
                                return self.terraform_resource_types[resource_type]
                    
                    # If we couldn't find a specific resource type but it's a module
                    if node_id.startswith('module.'):
                        logger.info(f"No specific resource type found, treating as module: {node_id}")
                        return 'application-component'
                
                if match:
                    resource_type = match.group(1)
                    logger.info(f"Extracted resource type: {resource_type}")
                    
                    # Check if we have a mapping for this resource type
                    if resource_type in self.terraform_resource_types:
                        logger.info(f"Found mapping for resource type: {resource_type} -> {self.terraform_resource_types[resource_type]}")
                        return self.terraform_resource_types[resource_type]
                    
                    # Handle variables
                    if resource_type == 'var':
                        logger.info("Resource type is a variable, mapping to business-actor")
                        return 'business-actor'
                    
                    # Handle modules
                    if resource_type == 'module':
                        logger.info("Resource type is a module, mapping to application-component")
                        return 'application-component'
                    
                    # Handle providers
                    if resource_type == 'provider':
                        logger.info("Resource type is a provider, mapping to technology-service")
                        return 'technology-service'
                    
                    # Handle cloud-specific resources by prefix
                    if resource_type.startswith('aws_'):
                        logger.info(f"Resource type is AWS, determining specific type for: {resource_type}")
                        return self._determine_aws_resource_type(resource_type)
                    elif resource_type.startswith('azurerm_') or resource_type.startswith('azuread_'):
                        logger.info(f"Resource type is Azure, determining specific type for: {resource_type}")
                        return self._determine_azure_resource_type(resource_type)
                    elif resource_type.startswith('google_'):
                        logger.info(f"Resource type is GCP, determining specific type for: {resource_type}")
                        return self._determine_gcp_resource_type(resource_type)
                
                # If all else fails but it's a Terraform node, default to technology-node
                logger.info(f"No specific type found for Terraform node, defaulting to technology-node: {node_id}")
                return 'technology-node'
            
            # Default case: try to determine based on shape attribute
            if 'shape' in attributes:
                shape = attributes['shape'].lower()
                logger.info(f"Determining type based on shape: {shape}")
                if shape == 'box':
                    return 'application-component'
                elif shape == 'ellipse':
                    return 'business-actor'
                elif shape == 'diamond':
                    return 'technology-service'
                elif shape == 'note':
                    return 'business-object'
            
            # If all else fails, default to application-component
            logger.info(f"No type determined, defaulting to application-component: {node_id}")
            return 'application-component'
        except Exception as e:
            logger.error(f"Error in _determine_node_type for {node_id}: {str(e)}")
            # Return a default type instead of raising to avoid crashing
            return 'application-component'

    def _determine_aws_resource_type(self, resource_type: str) -> str:
        """Determine ArchiMate element type for AWS resources."""
        # Compute resources
        if resource_type in ['aws_instance', 'aws_launch_template', 'aws_autoscaling_group']:
            return 'technology-node'
        # Network resources
        elif resource_type in ['aws_vpc', 'aws_subnet', 'aws_security_group', 'aws_route_table', 'aws_internet_gateway']:
            return 'technology-node'
        # Storage resources
        elif resource_type in ['aws_s3_bucket', 'aws_dynamodb_table', 'aws_ebs_volume']:
            return 'technology-artifact'
        # Database resources
        elif resource_type in ['aws_db_instance', 'aws_rds_cluster', 'aws_elasticache_cluster']:
            return 'technology-node'
        # Serverless resources
        elif resource_type in ['aws_lambda_function', 'aws_step_function']:
            return 'application-function'
        # API resources
        elif resource_type in ['aws_api_gateway', 'aws_api_gateway_rest_api']:
            return 'application-interface'
        # Service resources
        elif resource_type in ['aws_cloudfront_distribution', 'aws_cloudwatch', 'aws_sns_topic', 'aws_sqs_queue']:
            return 'technology-service'
        # Default to technology-node
        return 'technology-node'

    def _determine_azure_resource_type(self, resource_type: str) -> str:
        """Determine ArchiMate element type for Azure resources."""
        # Compute resources
        if resource_type in ['azurerm_virtual_machine', 'azurerm_linux_virtual_machine', 'azurerm_windows_virtual_machine', 'azurerm_virtual_machine_scale_set']:
            return 'technology-node'
        # Network resources
        elif resource_type in ['azurerm_virtual_network', 'azurerm_subnet', 'azurerm_network_security_group', 'azurerm_route_table', 'azurerm_public_ip']:
            return 'technology-node'
        # Storage resources
        elif resource_type in ['azurerm_storage_account', 'azurerm_storage_container', 'azurerm_storage_blob', 'azurerm_managed_disk']:
            return 'technology-artifact'
        # Database resources
        elif resource_type in ['azurerm_sql_server', 'azurerm_sql_database', 'azurerm_cosmosdb_account', 'azurerm_mysql_server']:
            return 'technology-node'
        # Serverless resources
        elif resource_type in ['azurerm_function_app', 'azurerm_logic_app_workflow']:
            return 'application-function'
        # API resources
        elif resource_type in ['azurerm_api_management', 'azurerm_api_management_api']:
            return 'application-interface'
        # Service resources
        elif resource_type in ['azurerm_application_gateway', 'azurerm_eventhub', 'azurerm_servicebus_namespace']:
            return 'technology-service'
        # Security resources
        elif resource_type in ['azurerm_key_vault', 'azuread_application', 'azuread_service_principal']:
            return 'technology-artifact'
        # Default to technology-node
        return 'technology-node'

    def _determine_gcp_resource_type(self, resource_type: str) -> str:
        """Determine ArchiMate element type for GCP resources."""
        # Compute resources
        if resource_type in ['google_compute_instance', 'google_compute_instance_template', 'google_compute_instance_group_manager']:
            return 'technology-node'
        # Network resources
        elif resource_type in ['google_compute_network', 'google_compute_subnetwork', 'google_compute_firewall', 'google_compute_router', 'google_compute_global_address']:
            return 'technology-node'
        # Storage resources
        elif resource_type in ['google_storage_bucket', 'google_bigquery_dataset', 'google_bigquery_table']:
            return 'technology-artifact'
        # Database resources
        elif resource_type in ['google_sql_database_instance', 'google_sql_database', 'google_spanner_instance']:
            return 'technology-node'
        # Serverless resources
        elif resource_type in ['google_cloudfunctions_function', 'google_cloud_run_service', 'google_cloud_scheduler_job']:
            return 'application-function'
        # API resources
        elif resource_type in ['google_cloud_endpoints_service', 'google_api_gateway_api', 'google_api_gateway_api_config']:
            return 'application-interface'
        # Service resources
        elif resource_type in ['google_pubsub_topic', 'google_pubsub_subscription', 'google_cloud_tasks_queue']:
            return 'technology-service'
        # Container resources
        elif resource_type in ['google_container_cluster', 'google_container_node_pool']:
            return 'technology-node'
        # Security resources
        elif resource_type in ['google_kms_key_ring', 'google_kms_crypto_key', 'google_service_account']:
            return 'technology-artifact'
        # Default to technology-node
        return 'technology-node'

    def _determine_relationship_type(self, attributes: Dict[str, str], source_node: Dict[str, Any], target_node: Dict[str, Any], is_terraform: bool = False) -> str:
        """Determine ArchiMate relationship type based on edge attributes."""
        # First check if the edge has an explicit type attribute
        if 'type' in attributes:
            rel_type = attributes['type'].lower()
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('relationships', {}).items():
                if rule_type in rel_type:
                    return rule['type']
            return rel_type  # Return the type as is if no mapping found
        
        # Check label for relationship hints
        elif 'label' in attributes:
            label = attributes['label'].lower()
            
            # Map common Terraform relationship labels to ArchiMate relationship types
            if 'uses' in label or 'read' in label:
                return 'serving-relationship'
            elif 'creates' in label or 'manages' in label:
                return 'assignment-relationship'
            elif 'depends' in label:
                return 'serving-relationship'
            elif 'triggers' in label:
                return 'triggering-relationship'
            elif 'flows' in label or 'writes' in label:
                return 'flow-relationship'
            
            # Check mapping rules
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('relationships', {}).items():
                if rule_type in label:
                    return rule['type']
        
        # For Terraform graphs, determine relationship type based on node types
        if is_terraform:
            source_id = source_node['id']
            target_id = target_node['id']
            source_attrs = source_node['attributes']
            target_attrs = target_node['attributes']
            
            # Variable to resource relationship
            if 'var.' in source_id:
                return 'assignment-relationship'
            
            # Resource to provider relationship
            if 'provider' in target_id:
                return 'serving-relationship'
            
            # Module relationships
            if 'module_path' in source_attrs or 'module_path' in target_attrs:
                # Resource within same module
                if (source_attrs.get('module_path') and 
                    target_attrs.get('module_path') and 
                    source_attrs['module_path'] == target_attrs['module_path']):
                    return 'composition-relationship'
                # Resource to its module
                elif 'module.' in source_id and not 'module_path' in target_attrs:
                    return 'composition-relationship'
                # Module to its resource
                elif 'module.' in target_id and not 'module_path' in source_attrs:
                    return 'composition-relationship'
                # Cross-module relationships
                elif (source_attrs.get('module_path') and 
                      target_attrs.get('module_path') and 
                      source_attrs['module_path'] != target_attrs['module_path']):
                    return 'serving-relationship'
            
            # Determine relationship based on cloud provider and resource types
            source_provider = self._get_cloud_provider(source_node.get('display_id', source_id))
            target_provider = self._get_cloud_provider(target_node.get('display_id', target_id))
            
            # If both resources are from the same cloud provider
            if source_provider and source_provider == target_provider:
                return self._determine_cloud_relationship(
                    source_node.get('display_id', source_id), 
                    target_node.get('display_id', target_id), 
                    source_provider
                )
            
            # Cross-cloud relationships (e.g., AWS to Azure)
            if source_provider and target_provider and source_provider != target_provider:
                return 'flow-relationship'
        
        # Default to flow-relationship
        return 'flow-relationship'
        
    def _get_cloud_provider(self, node_id: str) -> str:
        """Determine the cloud provider from a node ID."""
        # Strip any module prefixes to focus on the resource type
        if isinstance(node_id, str):
            # If we have a module reference, extract just the resource type
            if 'module.' in node_id:
                parts = node_id.split('.')
                # Make sure we have enough parts before accessing
                if len(parts) >= 2:
                    # For something like module.vpc.google_compute_network.vpc
                    # Try to extract the resource type (google_compute_network)
                    for part in parts:
                        if part.startswith(('aws_', 'azurerm_', 'azuread_', 'google_')):
                            node_id = part
                            break
            
            # Check for cloud provider prefixes
            if 'aws_' in node_id:
                return 'aws'
            elif 'azurerm_' in node_id or 'azuread_' in node_id:
                return 'azure'
            elif 'google_' in node_id:
                return 'gcp'
        
        return None
        
    def _determine_cloud_relationship(self, source_id: str, target_id: str, provider: str) -> str:
        """Determine relationship type based on cloud provider and resource types."""
        # Extract resource types
        source_type = re.search(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)', source_id)
        target_type = re.search(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)', target_id)
        
        if not source_type or not target_type:
            return 'flow-relationship'
            
        source_resource = source_type.group(1)
        target_resource = target_type.group(1)
        
        # AWS relationships
        if provider == 'aws':
            # Instance to network resources
            if source_resource == 'aws_instance' and target_resource in ['aws_vpc', 'aws_subnet', 'aws_security_group']:
                return 'serving-relationship'
            # Network hierarchy
            elif source_resource in ['aws_subnet', 'aws_security_group'] and target_resource == 'aws_vpc':
                return 'composition-relationship'
            # Database to storage
            elif source_resource == 'aws_db_instance' and target_resource in ['aws_ebs_volume', 'aws_s3_bucket']:
                return 'access-relationship'
            # Lambda to services
            elif source_resource == 'aws_lambda_function' and target_resource in ['aws_sqs_queue', 'aws_sns_topic', 'aws_dynamodb_table']:
                return 'access-relationship'
        
        # Azure relationships
        elif provider == 'azure':
            # VM to network resources
            if source_resource in ['azurerm_virtual_machine', 'azurerm_linux_virtual_machine', 'azurerm_windows_virtual_machine'] and target_resource in ['azurerm_virtual_network', 'azurerm_subnet', 'azurerm_network_security_group']:
                return 'serving-relationship'
            # Network hierarchy
            elif source_resource == 'azurerm_subnet' and target_resource == 'azurerm_virtual_network':
                return 'composition-relationship'
            # Database to storage
            elif source_resource in ['azurerm_sql_server', 'azurerm_cosmosdb_account'] and target_resource == 'azurerm_storage_account':
                return 'access-relationship'
            # Function to services
            elif source_resource == 'azurerm_function_app' and target_resource in ['azurerm_storage_account', 'azurerm_servicebus_namespace', 'azurerm_eventhub']:
                return 'access-relationship'
        
        # GCP relationships
        elif provider == 'gcp':
            # Instance to network resources
            if source_resource == 'google_compute_instance' and target_resource in ['google_compute_network', 'google_compute_subnetwork', 'google_compute_firewall']:
                return 'serving-relationship'
            # Network hierarchy
            elif source_resource == 'google_compute_subnetwork' and target_resource == 'google_compute_network':
                return 'composition-relationship'
            # Database to storage
            elif source_resource == 'google_sql_database_instance' and target_resource == 'google_storage_bucket':
                return 'access-relationship'
            # Function to services
            elif source_resource == 'google_cloudfunctions_function' and target_resource in ['google_pubsub_topic', 'google_storage_bucket', 'google_bigquery_dataset']:
                return 'access-relationship'
        
        # Default to flow-relationship for other cases
        return 'flow-relationship'

    def _extract_properties(self, attributes: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract additional properties from attributes."""
        return [
            {'key': k, 'value': v}
            for k, v in attributes.items()
            if k not in ['label', 'type', 'description', 'shape']
        ] 