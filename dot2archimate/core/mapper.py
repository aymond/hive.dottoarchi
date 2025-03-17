from typing import Dict, Any, List
import yaml
from logging import getLogger
import uuid

logger = getLogger(__name__)

class ArchimateMapper:
    def __init__(self, config_path: str = None):
        self.mapping_rules = self._load_config(config_path) if config_path else {}
        self.element_ids = {}  # Store mapping between DOT IDs and ArchiMate IDs

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

            # Map nodes to ArchiMate elements
            for node in graph_data['nodes']:
                element = self._map_node(node)
                if element:
                    archimate_elements.append(element)

            # Map edges to ArchiMate relationships
            for edge in graph_data['edges']:
                relationship = self._map_edge(edge)
                if relationship:
                    archimate_relationships.append(relationship)

            return {
                'elements': archimate_elements,
                'relationships': archimate_relationships
            }
        except Exception as e:
            logger.error(f"Mapping failed: {e}")
            raise ValueError(f"Failed to map to ArchiMate: {e}")

    def _map_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Map a single node to an ArchiMate element."""
        node_type = self._determine_node_type(node['attributes'])
        if not node_type:
            return None

        archimate_id = str(uuid.uuid4())
        self.element_ids[node['id']] = archimate_id

        return {
            'id': archimate_id,
            'type': node_type,
            'name': node['attributes'].get('label', node['id']),
            'documentation': node['attributes'].get('description', ''),
            'properties': self._extract_properties(node['attributes'])
        }

    def _map_edge(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Map a single edge to an ArchiMate relationship."""
        relationship_type = self._determine_relationship_type(edge['attributes'])
        if not relationship_type:
            return None

        source_id = self.element_ids.get(edge['source'])
        target_id = self.element_ids.get(edge['target'])

        if not (source_id and target_id):
            return None

        return {
            'id': str(uuid.uuid4()),
            'type': relationship_type,
            'source': source_id,
            'target': target_id,
            'name': edge['attributes'].get('label', ''),
            'properties': self._extract_properties(edge['attributes'])
        }

    def _determine_node_type(self, attributes: Dict[str, str]) -> str:
        """Determine ArchiMate element type based on node attributes."""
        # Implementation depends on your mapping rules
        # This is a simple example
        if 'type' in attributes:
            node_type = attributes['type'].lower()
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('nodes', {}).items():
                if rule_type in node_type:
                    return rule['type']
        return 'application-component'  # Default type

    def _determine_relationship_type(self, attributes: Dict[str, str]) -> str:
        """Determine ArchiMate relationship type based on edge attributes."""
        # Implementation depends on your mapping rules
        if 'type' in attributes:
            rel_type = attributes['type'].lower()
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('relationships', {}).items():
                if rule_type in rel_type:
                    return rule['type']
        elif 'label' in attributes:
            label = attributes['label'].lower()
            for rule_type, rule in self.mapping_rules.get('mapping_rules', {}).get('relationships', {}).items():
                if rule_type in label:
                    return rule['type']
        return 'serving-relationship'  # Default type

    def _extract_properties(self, attributes: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract additional properties from attributes."""
        return [
            {'key': k, 'value': v}
            for k, v in attributes.items()
            if k not in ['label', 'type', 'description']
        ] 