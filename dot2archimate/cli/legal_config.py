import argparse
import os
import sys
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_config_path():
    """Get the path to the legal_settings.yaml file."""
    # Determine the package directory
    if getattr(sys, 'frozen', False):
        # If the application is frozen (e.g., PyInstaller)
        package_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Otherwise, get the directory of this script
        current_file = os.path.abspath(__file__)
        cli_dir = os.path.dirname(current_file)
        package_dir = os.path.dirname(os.path.dirname(cli_dir))
    
    # Path to the config file
    config_dir = os.path.join(package_dir, 'web', 'config')
    config_path = os.path.join(config_dir, 'legal_settings.yaml')
    template_path = os.path.join(config_dir, 'legal_settings.yml.template')
    
    # Create the config directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        logger.info(f"Created config directory at {config_dir}")
    
    return config_path, template_path

def load_config():
    """Load the legal configuration."""
    config_path, template_path = get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading legal configuration: {str(e)}")
            return {}
    else:
        if os.path.exists(template_path):
            logger.warning(f"Config file not found at {config_path}")
            logger.info(f"You can create it by copying the template: cp {template_path} {config_path}")
        else:
            logger.warning(f"Neither config file nor template found")
        return {}

def save_config(config):
    """Save the legal configuration."""
    config_path, _ = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

def create_default_config():
    """Create a default legal configuration."""
    _, template_path = get_config_path()
    
    # Try to load from template if it exists
    if os.path.exists(template_path):
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                template_config = yaml.safe_load(file)
                logger.info(f"Created configuration based on template: {template_path}")
                return template_config
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            # Fall back to hardcoded default
    
    # Default hardcoded configuration
    logger.info("Creating hardcoded default configuration")
    return {
        'impressum': {
            'company_name': 'Your Company Name',
            'street': 'Your Street Address',
            'zip_city': 'Your ZIP and City',
            'country': 'Your Country',
            'phone': 'Your Phone Number',
            'email': 'your.email@example.com',
            'copyright_year': '2025'
        },
        'privacy': {
            'company_name': 'Your Company Name',
            'street': 'Your Street Address',
            'zip_city': 'Your ZIP and City',
            'country': 'Your Country',
            'phone': 'Your Phone Number',
            'email': 'your.email@example.com',
            'copyright_year': '2025',
            'hoster': 'Your Hosting Provider'
        }
    }

def update_config(args):
    """Update the legal configuration."""
    config = load_config()
    
    # Initialize config if it doesn't exist
    if not config:
        config = create_default_config()
    
    # Update impressum settings
    if args.section == 'impressum' or args.section == 'all':
        if not 'impressum' in config:
            config['impressum'] = {}
            
        if args.company_name:
            config['impressum']['company_name'] = args.company_name
        if args.street:
            config['impressum']['street'] = args.street
        if args.zip_city:
            config['impressum']['zip_city'] = args.zip_city
        if args.country:
            config['impressum']['country'] = args.country
        if args.phone:
            config['impressum']['phone'] = args.phone
        if args.email:
            config['impressum']['email'] = args.email
        if args.copyright_year:
            config['impressum']['copyright_year'] = args.copyright_year
    
    # Update privacy settings
    if args.section == 'privacy' or args.section == 'all':
        if not 'privacy' in config:
            config['privacy'] = {}
            
        if args.company_name:
            config['privacy']['company_name'] = args.company_name
        if args.street:
            config['privacy']['street'] = args.street
        if args.zip_city:
            config['privacy']['zip_city'] = args.zip_city
        if args.country:
            config['privacy']['country'] = args.country
        if args.phone:
            config['privacy']['phone'] = args.phone
        if args.email:
            config['privacy']['email'] = args.email
        if args.copyright_year:
            config['privacy']['copyright_year'] = args.copyright_year
        if args.hoster:
            config['privacy']['hoster'] = args.hoster
    
    # Save the updated configuration
    if save_config(config):
        print("Legal configuration updated successfully.")
    else:
        print("Failed to update legal configuration.")

def show_config():
    """Display the current legal configuration."""
    config = load_config()
    
    if not config:
        print("No configuration found. You can create one with the 'update' command.")
        return
    
    print("\n=== Legal Configuration ===\n")
    
    if 'impressum' in config:
        print("IMPRESSUM SETTINGS:")
        impressum = config['impressum']
        print(f"  Company Name: {impressum.get('company_name', 'Not set')}")
        print(f"  Street: {impressum.get('street', 'Not set')}")
        print(f"  ZIP/City: {impressum.get('zip_city', 'Not set')}")
        print(f"  Country: {impressum.get('country', 'Not set')}")
        print(f"  Phone: {impressum.get('phone', 'Not set')}")
        print(f"  Email: {impressum.get('email', 'Not set')}")
        print(f"  Copyright Year: {impressum.get('copyright_year', 'Not set')}")
        print()
    
    if 'privacy' in config:
        print("PRIVACY SETTINGS:")
        privacy = config['privacy']
        print(f"  Company Name: {privacy.get('company_name', 'Not set')}")
        print(f"  Street: {privacy.get('street', 'Not set')}")
        print(f"  ZIP/City: {privacy.get('zip_city', 'Not set')}")
        print(f"  Country: {privacy.get('country', 'Not set')}")
        print(f"  Phone: {privacy.get('phone', 'Not set')}")
        print(f"  Email: {privacy.get('email', 'Not set')}")
        print(f"  Copyright Year: {privacy.get('copyright_year', 'Not set')}")
        print(f"  Hosting Provider: {privacy.get('hoster', 'Not set')}")
        print()

def main():
    parser = argparse.ArgumentParser(description='Manage legal settings for the DOT to ArchiMate Converter.')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show current legal settings')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create default legal settings')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update legal settings')
    update_parser.add_argument('--section', choices=['impressum', 'privacy', 'all'], default='all',
                              help='Section to update')
    update_parser.add_argument('--company-name', help='Company or individual name')
    update_parser.add_argument('--street', help='Street address')
    update_parser.add_argument('--zip-city', help='ZIP code and city')
    update_parser.add_argument('--country', help='Country')
    update_parser.add_argument('--phone', help='Phone number')
    update_parser.add_argument('--email', help='Email address')
    update_parser.add_argument('--copyright-year', help='Copyright year')
    update_parser.add_argument('--hoster', help='Hosting provider (privacy section only)')
    
    args = parser.parse_args()
    
    if args.command == 'show':
        show_config()
    elif args.command == 'create':
        if save_config(create_default_config()):
            print("Default legal configuration created successfully.")
            show_config()
        else:
            print("Failed to create default legal configuration.")
    elif args.command == 'update':
        update_config(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 