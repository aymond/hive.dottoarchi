from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, session
import os
import logging
import tempfile
import json
import uuid
import yaml
import secrets
import time
from datetime import timedelta
from pathlib import Path

from dot2archimate.core.parser import DotParser
from dot2archimate.core.mapper import ArchimateMapper
from dot2archimate.core.generator import ArchimateXMLGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configure secure session (minimal - we use file-based storage instead)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
# Note: We don't use Flask sessions for data storage, only for flash messages
# Flask sessions are cookie-based and have size limits, so we use file-based storage

# File-based storage for visualization data (since Flask sessions have size limits)
# Use /tmp in container or system temp directory
STORAGE_DIR = Path('/tmp') / 'dot2archimate_sessions'
try:
    STORAGE_DIR.mkdir(exist_ok=True, mode=0o755)
    logger.info(f"Session storage directory: {STORAGE_DIR}")
except Exception as e:
    logger.error(f"Failed to create storage directory {STORAGE_DIR}: {e}")
    # Fallback to system temp directory
    STORAGE_DIR = Path(tempfile.gettempdir()) / 'dot2archimate_sessions'
    STORAGE_DIR.mkdir(exist_ok=True, mode=0o755)
    logger.info(f"Using fallback storage directory: {STORAGE_DIR}")

SESSION_TIMEOUT = 3600  # 1 hour in seconds

def save_session_data(session_id: str, data: dict):
    """Save session data to a file."""
    try:
        file_path = STORAGE_DIR / f"{session_id}.json"
        logger.info(f"Attempting to save session {session_id} to {file_path}")
        
        # Ensure storage directory exists
        STORAGE_DIR.mkdir(exist_ok=True, mode=0o755)
        
        # Create a copy to avoid modifying the original
        save_data = {
            'archimate_data': data.get('archimate_data'),
            'xml_output': data.get('xml_output'),
            'filename': data.get('filename'),
            'created_at': time.time()
        }
        
        logger.debug(f"Session data prepared, archimate_data keys: {list(save_data.get('archimate_data', {}).keys())}")
        
        # Write file with explicit flush to ensure it's written
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, default=str)  # default=str handles any non-serializable types
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Verify file was created
        if not file_path.exists():
            raise IOError(f"File was not created: {file_path}")
        
        file_size = file_path.stat().st_size
        logger.info(f"Successfully saved session data to {file_path} (size: {file_size} bytes)")
        
        # Double-check we can read it back
        with open(file_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
            if 'archimate_data' not in test_data:
                raise ValueError("Saved file does not contain archimate_data")
        
        logger.info(f"Verified session file is readable: {file_path}")
    except Exception as e:
        logger.error(f"Error saving session data: {e}", exc_info=True)
        raise

def load_session_data(session_id: str) -> dict:
    """Load session data from a file."""
    try:
        file_path = STORAGE_DIR / f"{session_id}.json"
        logger.info(f"Loading session from: {file_path}")
        logger.info(f"Storage directory exists: {STORAGE_DIR.exists()}, is_dir: {STORAGE_DIR.is_dir()}")
        
        # List all files in storage directory for debugging
        if STORAGE_DIR.exists():
            files = list(STORAGE_DIR.glob("*.json"))
            logger.info(f"Files in storage directory: {[f.name for f in files]}")
        
        if not file_path.exists():
            logger.warning(f"Session file not found: {file_path} (absolute: {file_path.absolute()})")
            return None
        
        # Check if session has expired
        file_age = time.time() - file_path.stat().st_mtime
        if file_age > SESSION_TIMEOUT:
            logger.warning(f"Session {session_id} has expired (age: {file_age}s)")
            file_path.unlink()  # Delete expired session
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded session {session_id}")
        return data
    except Exception as e:
        logger.error(f"Error loading session data for {session_id}: {e}", exc_info=True)
        return None

def delete_session_data(session_id: str):
    """Delete session data file."""
    file_path = STORAGE_DIR / f"{session_id}.json"
    if file_path.exists():
        file_path.unlink()
        logger.debug(f"Deleted session data file {file_path}")

def cleanup_expired_sessions():
    """Clean up expired session files."""
    current_time = time.time()
    for file_path in STORAGE_DIR.glob("*.json"):
        try:
            file_age = current_time - file_path.stat().st_mtime
            if file_age > SESSION_TIMEOUT:
                file_path.unlink()
                logger.debug(f"Cleaned up expired session: {file_path.name}")
        except Exception as e:
            logger.warning(f"Error cleaning up session file {file_path}: {e}")

# Initialize components
parser = DotParser()
mapper = ArchimateMapper("config.yaml")
generator = ArchimateXMLGenerator()

# Load legal configuration
legal_config_path = os.path.join(os.path.dirname(__file__), 'config', 'legal_settings.yaml')
template_path = os.path.join(os.path.dirname(__file__), 'config', 'legal_settings.yml.template')
legal_config = {}

# First check for the actual config file
if os.path.exists(legal_config_path):
    try:
        with open(legal_config_path, 'r', encoding='utf-8') as file:
            legal_config = yaml.safe_load(file)
        logger.info("Loaded legal configuration from %s", legal_config_path)
    except Exception as e:
        logger.error("Error loading legal configuration: %s", str(e))
# If not found, check for the template
elif os.path.exists(template_path):
    logger.warning("No legal configuration found. Please copy %s to %s and update it with your information.",
                 template_path, legal_config_path)
    logger.info("Using template as reference (not for production use)")
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            legal_config = yaml.safe_load(file)
    except Exception as e:
        logger.error("Error loading template configuration: %s", str(e))
else:
    logger.warning("Legal configuration file not found at %s", legal_config_path)
    # Create default config directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        logger.info("Created config directory at %s", config_dir)

@app.route('/')
def index():
    """Render the main page."""
    copyright_year = legal_config.get('impressum', {}).get('copyright_year', '2025')
    return render_template('index.html', copyright_year=copyright_year)

@app.route('/convert', methods=['POST'])
def convert():
    """Convert DOT to ArchiMate XML."""
    try:
        # Check if this is an API request with JSON data
        if request.is_json:
            data = request.get_json()
            if 'archimate_data' in data:
                # Generate XML from the provided data
                xml_output = generator.generate_xml(data['archimate_data'])
                
                # Return the XML as a downloadable file
                response = Response(xml_output, mimetype='application/xml')
                response.headers['Content-Disposition'] = 'attachment; filename=archimate.xml'
                
                return response
        
        # Check if file was uploaded or text was pasted
        if 'file' in request.files and request.files['file'].filename:
            # Process uploaded file
            file = request.files['file']
            dot_string = file.read().decode('utf-8')
            filename = file.filename
            logger.info(f"Processing uploaded file: {filename}")
        elif request.form.get('dot_text'):
            # Process pasted text
            dot_string = request.form.get('dot_text')
            filename = "pasted_content.dot"
            logger.info("Processing pasted DOT content")
        else:
            flash('No file or text provided', 'error')
            return redirect(url_for('index'))
        
        # Process the conversion
        graph_data = parser.parse_string(dot_string)
        archimate_data = mapper.map_to_archimate(graph_data)
        xml_output = generator.generate_xml(archimate_data)
        
        # Default behavior: always visualize (unless explicitly requesting download)
        if request.form.get('download_only') != 'true':
            # Generate session ID and store data in file-based storage
            session_id = str(uuid.uuid4())
            session_data = {
                'archimate_data': archimate_data,  # Store as dict, not JSON string
                'xml_output': xml_output,
                'filename': os.path.splitext(filename)[0]
            }
            
            # Save to file-based storage
            try:
                save_session_data(session_id, session_data)
                
                # Verify the file exists before redirecting
                file_path = STORAGE_DIR / f"{session_id}.json"
                if not file_path.exists():
                    raise IOError(f"Session file was not created: {file_path}")
                
                logger.info(f"Created visualization session: {session_id}, storage: {STORAGE_DIR}, file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save session data: {e}", exc_info=True)
                flash(f"Error saving session: {str(e)}", 'error')
                return redirect(url_for('index'))
            
            # Clean up old sessions periodically
            cleanup_expired_sessions()
            
            logger.info(f"Redirecting to visualization for session: {session_id}")
            return redirect(url_for('visualize', session_id=session_id))
        
        # Return the XML as a downloadable file (only if download_only is explicitly requested)
        response = Response(xml_output, mimetype='application/xml')
        response.headers['Content-Disposition'] = f'attachment; filename={os.path.splitext(filename)[0]}.xml'
        
        logger.info(f"Successfully converted {filename}")
        return response
    
    except Exception as e:
        logger.error(f"Error converting: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/visualize/<session_id>')
def visualize(session_id):
    """Visualize ArchiMate data."""
    try:
        # Load data from file-based storage
        data = load_session_data(session_id)
        
        if not data:
            logger.warning(f"Session {session_id} not found - session may have expired")
            flash('Visualization session not found or has expired. Please convert your file again.', 'error')
            return redirect(url_for('index'))
        
        if 'archimate_data' not in data:
            logger.warning(f"Session {session_id} exists but data is missing or invalid")
            flash('Visualization data is incomplete. Please convert your file again.', 'error')
            return redirect(url_for('index'))
            
        try:
            archimate_data = data['archimate_data']  # Already a dict, not JSON string
            filename = data.get('filename', 'unnamed')
            copyright_year = legal_config.get('impressum', {}).get('copyright_year', '2025')
            
            return render_template('visualize.html', 
                                  filename=filename,
                                  elements=json.dumps(archimate_data['elements']),
                                  relationships=json.dumps(archimate_data['relationships']),
                                  copyright_year=copyright_year)
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to process data in session {session_id}: {e}")
            flash('Error processing visualization data. Please convert your file again.', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error visualizing: {str(e)}", exc_info=True)
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/archimate-data/<session_id>')
def get_archimate_data(session_id):
    """API endpoint to get ArchiMate data for visualization."""
    try:
        # Load data from file-based storage
        data = load_session_data(session_id)
        
        if not data:
            logger.warning(f"API: Session {session_id} not found")
            return jsonify({'error': 'Session not found or has expired'}), 404
        
        if 'archimate_data' not in data:
            logger.warning(f"API: Session {session_id} exists but data is missing or invalid")
            return jsonify({'error': 'Invalid or incomplete session data'}), 400
            
        try:
            archimate_data = data['archimate_data']  # Already a dict
            return jsonify(archimate_data)
        except (KeyError, TypeError) as e:
            logger.error(f"API: Failed to process data in session {session_id}: {e}")
            return jsonify({'error': 'Failed to process session data'}), 500
    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/download/<session_id>')
def download_xml(session_id):
    """Download XML file from session."""
    try:
        # Load data from file-based storage
        data = load_session_data(session_id)
        
        if not data:
            logger.warning(f"Download: Session {session_id} not found")
            flash('Session not found or has expired. Please convert your file again.', 'error')
            return redirect(url_for('index'))
        
        if 'xml_output' not in data:
            logger.warning(f"Download: Session {session_id} exists but XML data is missing")
            flash('XML data not found. Please convert your file again.', 'error')
            return redirect(url_for('index'))
        
        filename = data.get('filename', 'archimate')
        xml_output = data['xml_output']
        
        response = Response(xml_output, mimetype='application/xml')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.xml'
        
        logger.info(f"Downloaded XML for session: {session_id}")
        return response
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        flash(f"Error downloading file: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/impressum')
def impressum():
    """Render the Impressum (Legal Notice) page."""
    impressum_config = legal_config.get('impressum', {})
    return render_template('impressum.html', config=impressum_config)

@app.route('/privacy')
def privacy():
    """Render the Privacy Policy page."""
    privacy_config = legal_config.get('privacy', {})
    return render_template('privacy.html', config=privacy_config)

@app.route('/reference-architecture')
def reference_architecture():
    """Render the Reference Architecture page with example DOT files."""
    examples_dir = Path('/app/examples')
    if not examples_dir.exists():
        # Fallback to relative path for local development
        examples_dir = Path(__file__).parent.parent.parent.parent / 'examples'
    
    examples = []
    example_descriptions = {
        'sample.dot': {
            'title': 'Basic Example',
            'description': 'A simple example showing basic application and business layer relationships.',
            'use_case': 'Learning the basics of DOT to ArchiMate conversion'
        },
        'enterprise_architecture.dot': {
            'title': 'Enterprise Architecture',
            'description': 'A comprehensive enterprise architecture example showing business processes, application systems, and technology infrastructure.',
            'use_case': 'Enterprise architecture modeling, business-IT alignment'
        },
        'microservices_architecture.dot': {
            'title': 'Microservices Architecture',
            'description': 'A modern microservices architecture demonstrating API Gateway pattern, service discovery, and distributed data stores.',
            'use_case': 'Microservices architecture documentation, service mesh design'
        },
        'cloud_infrastructure.dot': {
            'title': 'Cloud Infrastructure',
            'description': 'A cloud infrastructure example (AWS-focused) showing compute, storage, networking, messaging, and security services.',
            'use_case': 'Cloud architecture documentation, infrastructure as code visualization'
        },
        'business_process.dot': {
            'title': 'Business Process',
            'description': 'A business process-focused diagram showing business actors, processes, services, and flows.',
            'use_case': 'Business process modeling, BPMN alternative, process documentation'
        },
        'application_integration.dot': {
            'title': 'Application Integration',
            'description': 'An integration architecture example showing legacy system integration, modern applications, and integration patterns.',
            'use_case': 'Integration architecture, legacy modernization, EAI documentation'
        },
        'three_tier_architecture.dot': {
            'title': 'Three-Tier Architecture',
            'description': 'A classic three-tier architecture showing presentation, application, and data tiers with infrastructure components.',
            'use_case': 'Traditional application architecture, scalability patterns'
        }
    }
    
    if examples_dir.exists():
        for file_path in sorted(examples_dir.glob('*.dot')):
            filename = file_path.name
            if filename in example_descriptions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    examples.append({
                        'filename': filename,
                        'title': example_descriptions[filename]['title'],
                        'description': example_descriptions[filename]['description'],
                        'use_case': example_descriptions[filename]['use_case'],
                        'size': len(content),
                        'preview': content[:500] + '...' if len(content) > 500 else content
                    })
                except Exception as e:
                    logger.error(f"Error reading example file {filename}: {e}")
    
    return render_template('reference_architecture.html', examples=examples)

@app.route('/example/<filename>')
def example_file(filename):
    """Serve an example DOT file."""
    examples_dir = Path('/app/examples')
    if not examples_dir.exists():
        # Fallback to relative path for local development
        examples_dir = Path(__file__).parent.parent.parent.parent / 'examples'
    
    file_path = examples_dir / filename
    
    # Security: ensure file is in examples directory and has .dot extension
    if not filename.endswith('.dot') or not file_path.exists() or not str(file_path).startswith(str(examples_dir)):
        flash('Example file not found.', 'error')
        return redirect(url_for('reference_architecture'))
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = Response(content, mimetype='text/plain')
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        return response
    except Exception as e:
        logger.error(f"Error serving example file {filename}: {e}", exc_info=True)
        flash(f"Error loading example file: {str(e)}", 'error')
        return redirect(url_for('reference_architecture'))

@app.route('/example/<filename>/convert', methods=['POST'])
def convert_example(filename):
    """Convert an example DOT file directly."""
    examples_dir = Path('/app/examples')
    if not examples_dir.exists():
        # Fallback to relative path for local development
        examples_dir = Path(__file__).parent.parent.parent.parent / 'examples'
    
    file_path = examples_dir / filename
    
    # Security: ensure file is in examples directory and has .dot extension
    if not filename.endswith('.dot') or not file_path.exists() or not str(file_path).startswith(str(examples_dir)):
        flash('Example file not found.', 'error')
        return redirect(url_for('reference_architecture'))
    
    try:
        # Read the example file
        with open(file_path, 'r', encoding='utf-8') as f:
            dot_content = f.read()
        
        # Process the conversion
        parser = DotParser()
        mapper = ArchimateMapper()
        generator = ArchimateXMLGenerator()
        
        graph_data = parser.parse_string(dot_content)
        archimate_data = mapper.map_to_archimate(graph_data)
        xml_output = generator.generate_xml(archimate_data)
        
        # Create session and save data
        session_id = str(uuid.uuid4())
        save_session_data(session_id, {
            'archimate_data': archimate_data,
            'xml_output': xml_output,
            'filename': filename.replace('.dot', '')
        })
        
        logger.info(f"Converted example file {filename} to session {session_id}")
        return redirect(url_for('visualize', session_id=session_id))
    except Exception as e:
        logger.error(f"Error converting example file {filename}: {e}", exc_info=True)
        flash(f"Error converting example: {str(e)}", 'error')
        return redirect(url_for('reference_architecture'))

@app.route('/health')
def health():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check if storage directory is accessible
        storage_accessible = STORAGE_DIR.exists() and os.access(STORAGE_DIR, os.W_OK)
        return jsonify({
            'status': 'healthy',
            'storage': 'accessible' if storage_accessible else 'inaccessible',
            'timestamp': time.time()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 503

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host=host, port=port) 