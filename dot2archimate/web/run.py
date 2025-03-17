#!/usr/bin/env python3
"""
Run script for the DOT to ArchiMate web application.
"""
import os
import argparse
from dot2archimate.web.app import create_app

def main():
    """Run the web application."""
    parser = argparse.ArgumentParser(description='Run the DOT to ArchiMate web application')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main() 