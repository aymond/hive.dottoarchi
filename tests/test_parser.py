import pytest
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot2archimate.core.parser import DotParser

def test_parse_simple_dot():
    """Test parsing a simple DOT string."""
    parser = DotParser()
    dot_string = '''
    digraph G {
        node1 [label="Application 1", type="application"];
        node2 [label="Application 2", type="application"];
        node1 -> node2 [label="uses"];
    }
    '''
    result = parser.parse_string(dot_string)
    
    # Check that the result has the expected structure
    assert 'nodes' in result
    assert 'edges' in result
    assert 'graph_attrs' in result
    
    # Check that the nodes were parsed correctly
    assert len(result['nodes']) == 2
    
    # Find nodes by ID
    node1 = next((n for n in result['nodes'] if n['id'] == 'node1'), None)
    node2 = next((n for n in result['nodes'] if n['id'] == 'node2'), None)
    
    assert node1 is not None
    assert node2 is not None
    
    # Check node attributes
    assert node1['attributes']['label'] == 'Application 1'
    assert node1['attributes']['type'] == 'application'
    assert node2['attributes']['label'] == 'Application 2'
    assert node2['attributes']['type'] == 'application'
    
    # Check that the edge was parsed correctly
    assert len(result['edges']) == 1
    edge = result['edges'][0]
    assert edge['source'] == 'node1'
    assert edge['target'] == 'node2'
    assert edge['attributes']['label'] == 'uses'

def test_parse_file(tmp_path):
    """Test parsing a DOT file."""
    # Create a temporary DOT file
    dot_file = tmp_path / "test.dot"
    dot_file.write_text('''
    digraph G {
        app1 [label="Web Application", type="application"];
        app2 [label="Database", type="application"];
        app1 -> app2 [label="reads/writes"];
    }
    ''')
    
    parser = DotParser()
    result = parser.parse_file(str(dot_file))
    
    # Check that the result has the expected structure
    assert 'nodes' in result
    assert 'edges' in result
    
    # Check that the nodes were parsed correctly
    assert len(result['nodes']) == 2
    
    # Check that the edge was parsed correctly
    assert len(result['edges']) == 1
    edge = result['edges'][0]
    assert edge['source'] == 'app1'
    assert edge['target'] == 'app2'
    assert edge['attributes']['label'] == 'reads/writes'

def test_invalid_dot():
    """Test parsing an invalid DOT string."""
    parser = DotParser()
    invalid_dot = '''
    digraph G {
        invalid syntax
    }
    '''
    
    # The parser should raise a ValueError for invalid DOT
    with pytest.raises(ValueError):
        parser.parse_string(invalid_dot) 