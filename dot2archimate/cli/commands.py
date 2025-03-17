import click
import os
import sys
import logging
import subprocess

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

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to run the server on')
@click.option('--port', type=int, default=5000, help='Port to run the server on')
@click.option('--debug', is_flag=True, help='Run in debug mode')
def web(host, port, debug):
    """Launch the web interface"""
    try:
        from dot2archimate.web.app import app
        
        click.echo(f"Starting web interface at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except ImportError:
        click.echo("Error: Flask is not installed. Please install it with 'pip install flask'", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting web interface: {str(e)}")
        click.echo(f"Error starting web interface: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--show', is_flag=True, help='Show current legal settings')
@click.option('--create', is_flag=True, help='Create default legal settings')
@click.option('--section', type=click.Choice(['impressum', 'privacy', 'all']), default='all', help='Section to update')
@click.option('--company-name', help='Company or individual name')
@click.option('--street', help='Street address')
@click.option('--zip-city', help='ZIP code and city')
@click.option('--country', help='Country')
@click.option('--phone', help='Phone number')
@click.option('--email', help='Email address')
@click.option('--copyright-year', help='Copyright year')
@click.option('--hoster', help='Hosting provider (privacy section only)')
def legal_config(show, create, section, company_name, street, zip_city, country, phone, email, copyright_year, hoster):
    """Manage legal settings for the web interface"""
    from dot2archimate.cli.legal_config import load_config, create_default_config, save_config, show_config
    
    try:
        if show:
            show_config()
            return
        
        if create:
            if save_config(create_default_config()):
                click.echo("Default legal configuration created successfully.")
                show_config()
            else:
                click.echo("Failed to create default legal configuration.")
            return
        
        # If neither show nor create, treat as update
        config = load_config()
        
        # Initialize config if it doesn't exist
        if not config:
            config = create_default_config()
        
        # Update impressum settings
        if section == 'impressum' or section == 'all':
            if 'impressum' not in config:
                config['impressum'] = {}
                
            if company_name:
                config['impressum']['company_name'] = company_name
            if street:
                config['impressum']['street'] = street
            if zip_city:
                config['impressum']['zip_city'] = zip_city
            if country:
                config['impressum']['country'] = country
            if phone:
                config['impressum']['phone'] = phone
            if email:
                config['impressum']['email'] = email
            if copyright_year:
                config['impressum']['copyright_year'] = copyright_year
        
        # Update privacy settings
        if section == 'privacy' or section == 'all':
            if 'privacy' not in config:
                config['privacy'] = {}
                
            if company_name:
                config['privacy']['company_name'] = company_name
            if street:
                config['privacy']['street'] = street
            if zip_city:
                config['privacy']['zip_city'] = zip_city
            if country:
                config['privacy']['country'] = country
            if phone:
                config['privacy']['phone'] = phone
            if email:
                config['privacy']['email'] = email
            if copyright_year:
                config['privacy']['copyright_year'] = copyright_year
            if hoster:
                config['privacy']['hoster'] = hoster
        
        # Check if any updates were provided
        if not any([company_name, street, zip_city, country, phone, email, copyright_year, hoster]):
            click.echo("No updates provided. Use --help to see available options.")
            return
        
        # Save the updated configuration
        if save_config(config):
            click.echo("Legal configuration updated successfully.")
            show_config()
        else:
            click.echo("Failed to update legal configuration.")
            
    except Exception as e:
        logger.error(f"Error managing legal configuration: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli() 