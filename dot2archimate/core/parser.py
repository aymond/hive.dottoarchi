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
                    print(f"DEBUG: Processing module node: {display_id}")
                    # Get all parts of the module path
                    parts = display_id.split('.')
                    print(f"DEBUG: Parts: {parts}")
                    
                    # Make sure we have at least 3 parts (module.name.resource)
                    if len(parts) >= 3:
                        # Store original module path as a string
                        module_parts = parts[:-2] if len(parts) > 2 else [parts[0]]
                        module_path = '.'.join(module_parts)
                        print(f"DEBUG: Module path: {module_path}")
                        
                        # Get the resource part (last two components)
                        resource_parts = parts[-2:] if len(parts) >= 2 else [display_id]
                        resource_part = '.'.join(resource_parts)
                        print(f"DEBUG: Resource part: {resource_part}")
                        
                        # Add module information to attributes
                        attrs['module_path'] = module_path
                        
                        # Store both the full path and the resource part
                        display_id = resource_part
                        
                        # Update the label to show just the resource
                        if label == node_id:  # If label is the same as node_id, update it
                            label = resource_part
                
                print(f"DEBUG: Node attributes: {attrs}")
                nodes[node_id] = {
                    'id': node_id,
                    'display_id': display_id,
                    'label': label,
                    'attributes': attrs
                }
                node_ids.add(node_id)
        else:
            # Extract nodes with attributes - standard DOT style
            node_pattern = r'(?:^|\s)"?([^"\s\[]+)"?\s*(?:\[([^\]]*)\])?'
            for match in re.finditer(node_pattern, content):
                node_id = match.group(1)
                attrs_str = match.group(2) if match.group(2) else ""
                
                # Skip if this is an edge definition
                if "->" in node_id:
                    continue
                
                # Parse attributes
                attrs = self._parse_attributes(attrs_str)
                
                # Use label if available, otherwise use node_id
                label = attrs.get('label', node_id).strip('"')
                
                # Skip if we've already processed this node
                if node_id in nodes:
                    continue
                
                nodes[node_id] = {
                    'id': node_id,
                    'display_id': node_id,
                    'label': label,
                    'attributes': attrs
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
            edge_pattern = r'"?([^"\s]+)"?\s*->\s*"?([^"\s\[]+)"?\s*(?:\[([^\]]*)\])?'
            edge_matches = re.finditer(edge_pattern, content)
            
            for match in edge_matches:
                source_id = match.group(1)
                target_id = match.group(2)
                attrs_str = match.group(3) if match.group(3) else ""
                
                # Parse attributes
                attrs = self._parse_attributes(attrs_str)
                
                # Skip edges with non-existent nodes
                if source_id not in nodes or target_id not in nodes:
                    continue
                
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