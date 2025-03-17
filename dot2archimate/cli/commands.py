import click
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dot2archimate.core.parser import DotParser
from dot2archimate.core.mapper import ArchimateMapper
from dot2archimate.core.generator import ArchimateXMLGenerator

@click.group()
def cli():
    """DOT to ArchiMate converter CLI"""
    pass

@cli.command()
@click.option('--input', '-i', required=True, help='Input DOT file path')
@click.option('--output', '-o', required=True, help='Output ArchiMate XML file path')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def convert(input, output, config):
    """Convert a DOT file to ArchiMate XML"""
    try:
        logger.info(f"Converting {input} to {output}")
        
        # Initialize components
        parser = DotParser()
        mapper = ArchimateMapper(config)
        generator = ArchimateXMLGenerator()

        # Process the conversion
        graph_data = parser.parse_file(input)
        archimate_data = mapper.map_to_archimate(graph_data)
        xml_output = generator.generate_xml(archimate_data)

        # Write output
        with open(output, 'w', encoding='utf-8') as f:
            f.write(xml_output)

        logger.info(f"Successfully converted {input} to {output}")
        click.echo(f"Successfully converted {input} to {output}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--input-dir', '-i', required=True, help='Input directory containing DOT files')
@click.option('--output-dir', '-o', required=True, help='Output directory for ArchiMate XML files')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def batch_convert(input_dir, output_dir, config):
    """Convert multiple DOT files to ArchiMate XML"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Batch converting files from {input_dir} to {output_dir}")
        
        # Initialize components
        parser = DotParser()
        mapper = ArchimateMapper(config)
        generator = ArchimateXMLGenerator()

        # Process all .dot files in the input directory
        converted_count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith('.dot'):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename.replace('.dot', '.xml'))

                logger.info(f"Converting {filename}")
                
                # Process the conversion
                graph_data = parser.parse_file(input_path)
                archimate_data = mapper.map_to_archimate(graph_data)
                xml_output = generator.generate_xml(archimate_data)

                # Write output
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_output)

                converted_count += 1
                click.echo(f"Converted {filename}")

        logger.info(f"Batch conversion completed: {converted_count} files converted")
        click.echo(f"Batch conversion completed: {converted_count} files converted")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli() 