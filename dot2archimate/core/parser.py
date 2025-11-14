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
        nodes = {}
        edges = []
        graph_attrs = {}
        node_ids = set()  # Keep track of node IDs to avoid duplicates
        subgraphs = []

        # Remove comments and normalize whitespace
        content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Check if this is a Terraform graph
        is_terraform = 'provider[' in content or '[root]' in content
        
        # Extract graph attributes
        graph_attr_pattern = r'(?:digraph|graph)\s+(?:\w+\s+)?{([^{]*?)(?:subgraph|node|edge|"|\w+\s*\[|$)'
        graph_attr_match = re.search(graph_attr_pattern, content, re.DOTALL)
        if graph_attr_match:
            attr_text = graph_attr_match.group(1).strip()
            attrs = self._parse_graph_attributes(attr_text)
            graph_attrs.update(attrs)

        # Extract subgraphs
        subgraph_pattern = r'subgraph\s+"?(\w+)"?\s+{(.*?)}'
        for match in re.finditer(subgraph_pattern, content, re.DOTALL):
            subgraph_name = match.group(1)
            subgraph_content = match.group(2)
            subgraphs.append({
                'name': subgraph_name,
                'content': subgraph_content
            })

        # For Terraform graphs, extract nodes with special handling
        if is_terraform:
            # Extract nodes with attributes - Terraform style
            terraform_node_pattern = r'"(\[root\][^"]+)"\s*\[(.*?)\]'
            for match in re.finditer(terraform_node_pattern, content):
                node_id = match.group(1)
                attrs_str = match.group(2)
                
                # Skip nodes that are not actual resources
                if node_id in ['"true"', '"root"', '"]"', '"] (close)"'] or '[label =' in node_id or ', shape =' in node_id:
                    continue
                
                # Parse attributes
                attrs = self._parse_attributes(attrs_str)
                
                # Use label if available, otherwise use node_id
                label = attrs.get('label', node_id).strip('"')
                
                # Clean up label
                label = label.replace('\\', '')
                
                # Skip if we've already processed this node
                if node_id in nodes:
                    continue
                
                # Clean up node_id for display
                display_id = node_id.replace('[root] ', '').replace(' (expand)', '')
                
                # Extract the resource part from module references
                # For module resources like "module.vpc.google_compute_network.vpc"
                # Extract just the resource type and name
                if 'module.' in display_id:
                    logger.debug(f"Processing module node: {display_id}")
                    # Get all parts of the module path
                    parts = display_id.split('.')
                    logger.debug(f"Module parts: {parts}")
                    
                    # Make sure we have at least 3 parts (module.name.resource)
                    if len(parts) >= 3:
                        # Store original module path as a string
                        module_parts = parts[:-2] if len(parts) > 2 else [parts[0]]
                        module_path = '.'.join(module_parts)
                        logger.debug(f"Module path: {module_path}")
                        
                        # Get the resource part (last two components)
                        resource_parts = parts[-2:] if len(parts) >= 2 else [display_id]
                        resource_part = '.'.join(resource_parts)
                        logger.debug(f"Resource part: {resource_part}")
                        
                        # Add module information to attributes
                        attrs['module_path'] = module_path
                        
                        # Store both the full path and the resource part
                        display_id = resource_part
                        
                        # Update the label to show just the resource
                        if label == node_id:  # If label is the same as node_id, update it
                            label = resource_part
                
                logger.debug(f"Node attributes: {attrs}")
                nodes[node_id] = {
                    'id': node_id,
                    'display_id': display_id,
                    'label': label,
                    'attributes': attrs
                }
                node_ids.add(node_id)
        else:
            # Extract nodes with attributes - standard DOT style
            # DOT keywords to exclude
            dot_keywords = {'digraph', 'graph', 'subgraph', 'node', 'edge', 'strict'}
            
            # Strategy: Extract nodes from edges first, then find standalone node definitions
            # This ensures we only get actual nodes, not syntax elements
            
            # Step 1: Collect all node IDs from edges (they're definitely nodes)
            edge_node_ids = set()
            edge_preview_pattern = r'(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*->\s*(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))'
            for edge_match in re.finditer(edge_preview_pattern, content):
                for i in [1, 2, 3, 4]:
                    node_id = edge_match.group(i)
                    if node_id and node_id.lower() not in dot_keywords:
                        edge_node_ids.add(node_id)
            
            # Step 2: Find standalone node definitions
            # Pattern: node_id [attributes] where node_id is NOT part of an edge
            # We'll match: identifier followed by [attributes] that's NOT preceded by ->
            # More precise: match lines that look like node definitions
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # Skip empty lines, comments, and graph declarations
                if not line or line.startswith('//') or line.startswith('/*') or line.startswith('digraph') or line.startswith('graph') or line == '{' or line == '}':
                    continue
                
                # Skip edge definitions (they're handled separately)
                if '->' in line:
                    continue
                
                # Match node definition: node_id [attributes] or "node_id" [attributes]
                # Pattern: start of line, optional whitespace, node_id (quoted or unquoted), optional [attributes], optional semicolon
                node_match = re.match(r'^\s*(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))(?:\s*\[([^\]]*)\])?\s*;?\s*$', line)
                if node_match:
                    node_id = node_match.group(1) if node_match.group(1) else node_match.group(2)
                    attrs_str = node_match.group(3) if node_match.group(3) else ""
                    
                    if not node_id:
                        continue
                    
                    # Skip keywords
                    if node_id.lower() in dot_keywords:
                        continue
                    
                    # Parse attributes
                    attrs = self._parse_attributes(attrs_str)
                    
                    # Use label if available, otherwise use node_id
                    label = attrs.get('label', node_id).strip('"')
                    
                    # Skip if already processed
                    if node_id in nodes:
                        continue
                    
                    nodes[node_id] = {
                        'id': node_id,
                        'display_id': node_id,
                        'label': label,
                        'attributes': attrs
                    }
                    node_ids.add(node_id)
            
            # Step 3: Add nodes from edges that weren't found as standalone definitions
            for node_id in edge_node_ids:
                if node_id not in nodes:
                    nodes[node_id] = {
                        'id': node_id,
                        'display_id': node_id,
                        'label': node_id,
                        'attributes': {}
                    }
                    node_ids.add(node_id)

        # Extract edges
        if is_terraform:
            # Terraform-specific edge extraction
            edge_pattern = r'"(\[root\][^"]+)"\s*->\s*"(\[root\][^"]+)"'
            edge_matches = re.finditer(edge_pattern, content)
            
            for match in edge_matches:
                source_id = match.group(1)
                target_id = match.group(2)
                
                # Skip edges with non-existent nodes
                if source_id not in nodes or target_id not in nodes:
                    continue
                
                edges.append({
                    'source': source_id,
                    'target': target_id,
                    'attributes': {}
                })
        else:
            # Standard DOT edge extraction
            # Match: source -> target [attributes]
            # Handle both quoted and unquoted node IDs
            edge_pattern = r'(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*->\s*(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))(?:\s*\[([^\]]*)\])?'
            edge_matches = re.finditer(edge_pattern, content)
            
            for match in edge_matches:
                # Get source and target from either quoted or unquoted match
                source_id = match.group(1) if match.group(1) else match.group(2)
                target_id = match.group(3) if match.group(3) else match.group(4)
                attrs_str = match.group(5) if match.group(5) else ""
                
                if not source_id or not target_id:
                    continue
                
                # Skip edges with non-existent nodes
                if source_id not in nodes or target_id not in nodes:
                    continue
                
                # Parse attributes
                attrs = self._parse_attributes(attrs_str)
                
                edges.append({
                    'source': source_id,
                    'target': target_id,
                    'attributes': attrs
                })

        # Check for invalid syntax
        if not (nodes or edges) and 'digraph' in content:
            raise ValueError("Invalid DOT syntax")

        return {
            'nodes': nodes,
            'edges': edges,
            'graph_attrs': graph_attrs,
            'subgraphs': subgraphs,
            'is_terraform': is_terraform
        }

    def _parse_graph_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse graph attribute string into dictionary."""
        attrs = {}
        # Split by newline or semicolon
        lines = re.split(r'[;\n]', attr_string)
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                if key and value:
                    attrs[key] = value
        return attrs

    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse attribute string into dictionary."""
        attrs = {}
        # Split by comma, handling potential nested structures
        parts = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\w+)', attr_string)
        for key, value in parts:
            attrs[key] = value or key
        return attrs 