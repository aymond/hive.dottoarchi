from typing import Dict, Any, List, Tuple
import graphviz
from logging import getLogger
import re

logger = getLogger(__name__)

class DotParser:
    def __init__(self):
        self.graph = None

    def parse_string(self, dot_string: str) -> Dict[str, Any]:
        """Parse a DOT string into an internal representation."""
        try:
            # Create a temporary file to use graphviz's parsing
            self.graph = graphviz.Source(dot_string)
            parsed_data = self._parse_dot_content(dot_string)
            return parsed_data
        except Exception as e:
            logger.error(f"Failed to parse DOT string: {e}")
            raise ValueError(f"Invalid DOT format: {e}")

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a DOT file into an internal representation."""
        try:
            with open(file_path, 'r') as f:
                return self.parse_string(f.read())
        except Exception as e:
            logger.error(f"Failed to parse DOT file {file_path}: {e}")
            raise ValueError(f"Failed to parse DOT file: {e}")

    def _parse_dot_content(self, content: str) -> Dict[str, Any]:
        """Parse DOT content using regex to extract nodes and edges."""
        nodes = []
        edges = []
        graph_attrs = {}
        node_ids = set()  # Keep track of node IDs to avoid duplicates

        # Remove comments and normalize whitespace
        content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.DOTALL)
        content = ' '.join(content.split())

        # Extract graph attributes
        graph_attr_pattern = r'graph\s*\[(.*?)\]'
        graph_attr_match = re.search(graph_attr_pattern, content)
        if graph_attr_match:
            attrs = self._parse_attributes(graph_attr_match.group(1))
            graph_attrs.update(attrs)

        # Extract nodes
        node_pattern = r'([a-zA-Z0-9_]+)\s*\[(.*?)\]'
        for match in re.finditer(node_pattern, content):
            node_id = match.group(1)
            attrs = self._parse_attributes(match.group(2))
            if node_id not in node_ids:
                nodes.append({
                    'id': node_id,
                    'attributes': attrs
                })
                node_ids.add(node_id)

        # Extract edges
        edge_pattern = r'([a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_]+)\s*\[(.*?)\]'
        for match in re.finditer(edge_pattern, content):
            source = match.group(1)
            target = match.group(2)
            attrs = self._parse_attributes(match.group(3))
            edges.append({
                'source': source,
                'target': target,
                'attributes': attrs
            })

        # Check for invalid syntax
        if not (nodes or edges) and 'digraph' in content:
            raise ValueError("Invalid DOT syntax")

        return {
            'nodes': nodes,
            'edges': edges,
            'graph_attrs': graph_attrs
        }

    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse attribute string into dictionary."""
        attrs = {}
        # Split by comma, handling potential nested structures
        parts = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\w+)', attr_string)
        for key, value in parts:
            attrs[key] = value or key
        return attrs 