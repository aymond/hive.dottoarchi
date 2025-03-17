import os
import yaml
from typing import Dict, Any

class Settings:
    """Settings class for dot2archimate."""
    
    def __init__(self, config_path: str = None):
        """Initialize settings from config file."""
        self.config_path = config_path or os.environ.get('DOT2ARCHIMATE_CONFIG', 'config.yaml')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            # Return default configuration if file not found
            return {
                'mapping_rules': {
                    'nodes': {
                        'application': {
                            'type': 'application-component',
                            'attributes': ['label', 'description']
                        },
                        'business': {
                            'type': 'business-actor',
                            'attributes': ['label', 'description']
                        },
                        'technology': {
                            'type': 'technology-node',
                            'attributes': ['label', 'description']
                        }
                    },
                    'relationships': {
                        'uses': {
                            'type': 'serving-relationship',
                            'attributes': ['label']
                        },
                        'flows': {
                            'type': 'flow-relationship',
                            'attributes': ['label']
                        }
                    }
                },
                'archimate': {
                    'namespace': 'http://www.opengroup.org/xsd/archimate/3.0/',
                    'schema_location': 'http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.0/archimate3_Diagram.xsd'
                }
            }
    
    def get_mapping_rules(self) -> Dict[str, Any]:
        """Get mapping rules from configuration."""
        return self.config.get('mapping_rules', {})
    
    def get_archimate_namespace(self) -> str:
        """Get ArchiMate namespace from configuration."""
        return self.config.get('archimate', {}).get('namespace', 'http://www.opengroup.org/xsd/archimate/3.0/')
    
    def get_archimate_schema_location(self) -> str:
        """Get ArchiMate schema location from configuration."""
        return self.config.get('archimate', {}).get('schema_location', 
            'http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.0/archimate3_Diagram.xsd')
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self.config = config 