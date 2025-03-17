from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, session
import os
import logging
import tempfile
import json
import uuid

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

# Initialize components
parser = DotParser()
mapper = ArchimateMapper("config.yaml")
generator = ArchimateXMLGenerator()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

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
            # Store the data in session for visualization
            session_id = str(uuid.uuid4())
            session[session_id] = {
                'archimate_data': json.dumps(archimate_data),
                'filename': os.path.splitext(filename)[0]
            }
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
            flash('Visualization data not found', 'error')
            return redirect(url_for('index'))
        
        data = session[session_id]
        archimate_data = json.loads(data['archimate_data'])
        filename = data['filename']
        
        return render_template('visualize.html', 
                              filename=filename,
                              elements=json.dumps(archimate_data['elements']),
                              relationships=json.dumps(archimate_data['relationships']))
    
    except Exception as e:
        logger.error(f"Error visualizing: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/archimate-data/<session_id>')
def get_archimate_data(session_id):
    """API endpoint to get ArchiMate data for visualization."""
    if session_id not in session:
        return jsonify({'error': 'Data not found'}), 404
    
    data = session[session_id]
    archimate_data = json.loads(data['archimate_data'])
    
    return jsonify(archimate_data)

def create_app():
    """Create and configure the Flask app."""
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_flash_messages')
    app.config['SESSION_TYPE'] = 'filesystem'
    return app

if __name__ == '__main__':
    create_app().run(debug=True) 