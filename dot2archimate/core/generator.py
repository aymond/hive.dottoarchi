from typing import Dict, Any
from lxml import etree
from logging import getLogger

logger = getLogger(__name__)

class ArchimateXMLGenerator:
    def __init__(self, config_path: str = None):
        self.nsmap = {
            'archimate': 'http://www.opengroup.org/xsd/archimate/3.0/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def generate_xml(self, archimate_data: Dict[str, Any]) -> str:
        """Generate ArchiMate XML from mapped data."""
        try:
            # Create root element
            root = etree.Element(
                f"{{{self.nsmap['archimate']}}}model",
                nsmap=self.nsmap
            )

            # Add schema location
            root.set(
                f"{{{self.nsmap['xsi']}}}schemaLocation",
                "http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.0/archimate3_Diagram.xsd"
            )

            # Add elements
            elements = etree.SubElement(root, f"{{{self.nsmap['archimate']}}}elements")
            for element in archimate_data['elements']:
                self._add_element(elements, element)

            # Add relationships
            relationships = etree.SubElement(root, f"{{{self.nsmap['archimate']}}}relationships")
            for relationship in archimate_data['relationships']:
                self._add_relationship(relationships, relationship)

            # Return formatted XML
            xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content = etree.tostring(
                root,
                pretty_print=True,
                encoding='unicode',
                xml_declaration=False
            )
            return xml_declaration + xml_content
        except Exception as e:
            logger.error(f"XML generation failed: {e}")
            raise ValueError(f"Failed to generate XML: {e}")

    def _add_element(self, parent: etree.Element, element: Dict[str, Any]):
        """Add an ArchiMate element to the XML tree."""
        elem = etree.SubElement(
            parent,
            f"{{{self.nsmap['archimate']}}}{element['type']}"
        )
        elem.set('id', element['id'])
        elem.set('name', element['name'])

        if element['documentation']:
            documentation = etree.SubElement(
                elem,
                f"{{{self.nsmap['archimate']}}}documentation"
            )
            documentation.text = element['documentation']

        if element['properties']:
            properties = etree.SubElement(
                elem,
                f"{{{self.nsmap['archimate']}}}properties"
            )
            
            # Handle properties as dictionary or list
            if isinstance(element['properties'], dict):
                for key, value in element['properties'].items():
                    property_elem = etree.SubElement(
                        properties,
                        f"{{{self.nsmap['archimate']}}}property"
                    )
                    property_elem.set('key', str(key))
                    property_elem.set('value', str(value))
            else:
                # Handle properties as list of dictionaries with 'key' and 'value'
                for prop in element['properties']:
                    property_elem = etree.SubElement(
                        properties,
                        f"{{{self.nsmap['archimate']}}}property"
                    )
                    property_elem.set('key', prop['key'])
                    property_elem.set('value', prop['value'])

    def _add_relationship(self, parent: etree.Element, relationship: Dict[str, Any]):
        """Add an ArchiMate relationship to the XML tree."""
        rel = etree.SubElement(
            parent,
            f"{{{self.nsmap['archimate']}}}{relationship['type']}"
        )
        rel.set('id', relationship['id'])
        rel.set('source', relationship['source'])
        rel.set('target', relationship['target'])

        if relationship['name']:
            rel.set('name', relationship['name'])

        if relationship['properties']:
            properties = etree.SubElement(
                rel,
                f"{{{self.nsmap['archimate']}}}properties"
            )
            for prop in relationship['properties']:
                property_elem = etree.SubElement(
                    properties,
                    f"{{{self.nsmap['archimate']}}}property"
                )
                property_elem.set('key', prop['key'])
                property_elem.set('value', prop['value']) 