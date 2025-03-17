from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse
import os
import sys
import logging

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot2archimate.core.parser import DotParser
from dot2archimate.core.mapper import ArchimateMapper
from dot2archimate.core.generator import ArchimateXMLGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DOT to ArchiMate Converter",
    description="Convert Graphviz DOT files to ArchiMate XML format",
    version="0.1.0"
)

# Initialize components
parser = DotParser()
mapper = ArchimateMapper("config.yaml")
generator = ArchimateXMLGenerator()

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "DOT to ArchiMate Converter API",
        "endpoints": [
            {"path": "/convert/file", "method": "POST", "description": "Convert DOT file to ArchiMate XML"},
            {"path": "/convert/text", "method": "POST", "description": "Convert DOT text to ArchiMate XML"}
        ]
    }

@app.post("/convert/file", response_class=PlainTextResponse)
async def convert_file(file: UploadFile = File(...)):
    """Convert uploaded DOT file to ArchiMate XML."""
    try:
        logger.info(f"Processing file upload: {file.filename}")
        content = await file.read()
        dot_string = content.decode('utf-8')
        
        # Process the conversion
        graph_data = parser.parse_string(dot_string)
        archimate_data = mapper.map_to_archimate(graph_data)
        xml_output = generator.generate_xml(archimate_data)
        
        logger.info(f"Successfully converted file: {file.filename}")
        return xml_output
    except Exception as e:
        logger.error(f"Error converting file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/convert/text", response_class=PlainTextResponse)
async def convert_text(dot_content: str = Form(...)):
    """Convert DOT text content to ArchiMate XML."""
    try:
        logger.info("Processing DOT text content")
        # Process the conversion
        graph_data = parser.parse_string(dot_content)
        archimate_data = mapper.map_to_archimate(graph_data)
        xml_output = generator.generate_xml(archimate_data)
        
        logger.info("Successfully converted DOT text content")
        return xml_output
    except Exception as e:
        logger.error(f"Error converting text content: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 