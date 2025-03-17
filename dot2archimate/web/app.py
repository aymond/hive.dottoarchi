from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, session
import os
import logging
import tempfile
import json
import uuid
import yaml
import secrets
from datetime import timedelta

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

# Configure secure session
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_USE_SIGNER'] = True

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
        
        # Check if visualization is requested
        if request.form.get('visualize') == 'true':
            # Make session permanent to extend its lifetime
            session.permanent = True
            
            # Store the data in session for visualization
            session_id = str(uuid.uuid4())
            session[session_id] = {
                'archimate_data': json.dumps(archimate_data),
                'filename': os.path.splitext(filename)[0]
            }
            
            # Force session to be saved
            session.modified = True
            
            logger.info(f"Created visualization session: {session_id}")
            return redirect(url_for('visualize', session_id=session_id))
        
        # Return the XML as a downloadable file
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
        if session_id not in session:
            logger.warning(f"Session {session_id} not found - session may have expired")
            flash('Visualization session not found or has expired. Please convert your file again.', 'error')
            return redirect(url_for('index'))
        
        data = session[session_id]
        if not data or 'archimate_data' not in data:
            logger.warning(f"Session {session_id} exists but data is missing or invalid")
            flash('Visualization data is incomplete. Please convert your file again.', 'error')
            return redirect(url_for('index'))
            
        try:
            archimate_data = json.loads(data['archimate_data'])
            filename = data.get('filename', 'unnamed')
            copyright_year = legal_config.get('impressum', {}).get('copyright_year', '2025')
            
            # Reset session expiry by marking as modified
            session.modified = True
            
            return render_template('visualize.html', 
                                  filename=filename,
                                  elements=json.dumps(archimate_data['elements']),
                                  relationships=json.dumps(archimate_data['relationships']),
                                  copyright_year=copyright_year)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON data in session {session_id}")
            flash('Error processing visualization data. Please convert your file again.', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error visualizing: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/archimate-data/<session_id>')
def get_archimate_data(session_id):
    """API endpoint to get ArchiMate data for visualization."""
    try:
        if session_id not in session:
            logger.warning(f"API: Session {session_id} not found")
            return jsonify({'error': 'Session not found or has expired'}), 404
        
        data = session[session_id]
        if not data or 'archimate_data' not in data:
            logger.warning(f"API: Session {session_id} exists but data is missing or invalid")
            return jsonify({'error': 'Invalid or incomplete session data'}), 400
            
        try:
            archimate_data = json.loads(data['archimate_data'])
            # Reset session expiry
            session.modified = True
            return jsonify(archimate_data)
        except json.JSONDecodeError:
            logger.error(f"API: Failed to decode JSON data in session {session_id}")
            return jsonify({'error': 'Failed to decode session data'}), 500
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(debug=True) 