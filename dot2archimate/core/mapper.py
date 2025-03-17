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

            # Map nodes to ArchiMate elements
            for node_id, node in graph_data['nodes'].items():
                element = self._map_node(node, is_terraform)
                if element:
                    archimate_elements.append(element)

            # Map edges to ArchiMate relationships
            for edge in graph_data['edges']:
                relationship = self._map_edge(edge, graph_data['nodes'], is_terraform)
                if relationship:
                    archimate_relationships.append(relationship)

            return {
                'elements': archimate_elements,
                'relationships': archimate_relationships
            }
        except Exception as e:
            logger.error(f"Mapping failed: {e}")
            raise ValueError(f"Failed to map to ArchiMate: {e}")

    def _map_node(self, node: Dict[str, Any], is_terraform: bool = False) -> Dict[str, Any]:
        """Map a single node to an ArchiMate element."""
        node_id = node['id']
        display_id = node.get('display_id', node_id)
        attributes = node['attributes']
        
        # Determine element type
        node_type = self._determine_node_type(display_id, attributes, is_terraform)
        if not node_type:
            return None

        archimate_id = str(uuid.uuid4())
        self.element_ids[node_id] = archimate_id

        # Get the node name from label or ID
        node_name = node.get('label', attributes.get('label', display_id))
        
        # Clean up Terraform node names
        if is_terraform and isinstance(node_name, str):
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

        return {
            'id': archimate_id,
            'type': node_type,
            'name': node_name,
            'documentation': attributes.get('description', ''),
            'properties': self._extract_properties(attributes)
        }

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
        # First check if the node has an explicit type attribute
        if 'type' in attributes:
            node_type = attributes['type'].lower()
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('nodes', {}).items():
                if rule_type in node_type:
                    return rule['type']
            return node_type  # Return the type as is if no mapping found
        
        # For Terraform resources, determine type based on resource type
        if is_terraform:
            # Extract resource type from Terraform node ID
            terraform_pattern = r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)'
            match = re.search(terraform_pattern, node_id)
            if match:
                resource_type = match.group(1)
                # Check if we have a mapping for this resource type
                if resource_type in self.terraform_resource_types:
                    return self.terraform_resource_types[resource_type]
                
                # Handle variables
                if resource_type == 'var':
                    return 'business-actor'
                
                # Handle providers
                if resource_type == 'provider':
                    return 'technology-service'
            
            # Handle special cases
            if 'provider' in node_id:
                return 'technology-service'
            if 'var.' in node_id:
                return 'business-actor'
            if 'module.' in node_id:
                return 'grouping'
            if 'data.' in node_id:
                return 'business-object'
            
            # Use shape to determine type if available
            if 'shape' in attributes:
                shape = attributes['shape'].lower()
                if shape == 'box':
                    return 'technology-node'
                elif shape == 'diamond':
                    return 'technology-service'
                elif shape == 'note':
                    return 'business-actor'
                elif shape == 'ellipse':
                    return 'application-component'
                elif shape == 'hexagon':
                    return 'technology-artifact'
        
        # Default to application component if no specific type is determined
        return 'application-component'

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
            source_type = source_node['attributes'].get('type', '')
            target_type = target_node['attributes'].get('type', '')
            
            # Variable to resource relationship
            if 'var' in source_node['id'] and 'aws_' in target_node['id']:
                return 'assignment-relationship'
            
            # Resource to provider relationship
            if 'aws_' in source_node['id'] and 'provider' in target_node['id']:
                return 'serving-relationship'
        
        # Default to flow-relationship
        return 'flow-relationship'

    def _extract_properties(self, attributes: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract additional properties from attributes."""
        return [
            {'key': k, 'value': v}
            for k, v in attributes.items()
            if k not in ['label', 'type', 'description', 'shape']
        ] 