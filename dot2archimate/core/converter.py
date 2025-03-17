import logging
from dot2archimate.core.parser import DotParser
from dot2archimate.core.mapper import ArchimateMapper
from dot2archimate.core.generator import ArchimateXMLGenerator

class Converter:
    """Converter for DOT to ArchiMate."""

    def __init__(self, config_path=None):
        self.logger = logging.getLogger(__name__)
        self.parser = DotParser()
        self.mapper = ArchimateMapper(config_path)
        self.generator = ArchimateXMLGenerator()

    def convert(self, input_file, output_file):
        """Convert a DOT file to an ArchiMate XML file."""
        self.logger.info(f"Converting {input_file} to {output_file}")
        
        # Parse DOT file
        dot_data = self.parser.parse_file(input_file)
        
        # Map DOT elements to ArchiMate elements
        archimate_data = self.mapper.map_to_archimate(dot_data)
        
        # Generate ArchiMate XML
        self.generator.generate_xml(archimate_data, output_file)
        
        self.logger.info(f"Successfully converted {input_file} to {output_file}") 