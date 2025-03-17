document.addEventListener('DOMContentLoaded', function() {
    // Initialize Cytoscape
    const cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(name)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'background-color': '#ffffff',
                    'border-width': 1,
                    'border-color': '#333333',
                    'shape': 'rectangle',
                    'width': 'label',
                    'height': 'label',
                    'padding': '10px'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#999999',
                    'target-arrow-color': '#999999',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(name)',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10,
                    'font-size': '10px'
                }
            },
            // ArchiMate element styles
            {
                selector: 'node[type="business-actor"]',
                style: {
                    'background-color': '#ffe6cc',
                    'border-color': '#d79b00'
                }
            },
            {
                selector: 'node[type="business-object"]',
                style: {
                    'background-color': '#fff2cc',
                    'border-color': '#d6b656'
                }
            },
            {
                selector: 'node[type="application-component"]',
                style: {
                    'background-color': '#d5e8d4',
                    'border-color': '#82b366'
                }
            },
            {
                selector: 'node[type="application-function"]',
                style: {
                    'background-color': '#b9e0a5',
                    'border-color': '#82b366'
                }
            },
            {
                selector: 'node[type="technology-node"]',
                style: {
                    'background-color': '#dae8fc',
                    'border-color': '#6c8ebf'
                }
            },
            {
                selector: 'node[type="technology-service"]',
                style: {
                    'background-color': '#b1ddf0',
                    'border-color': '#6c8ebf'
                }
            },
            {
                selector: 'node[type="technology-artifact"]',
                style: {
                    'background-color': '#d0cee2',
                    'border-color': '#9673a6'
                }
            },
            // Relationship styles
            {
                selector: 'edge[type="flow-relationship"]',
                style: {
                    'line-color': '#999999',
                    'target-arrow-color': '#999999'
                }
            },
            {
                selector: 'edge[type="serving-relationship"]',
                style: {
                    'line-color': '#82b366',
                    'target-arrow-color': '#82b366'
                }
            },
            {
                selector: 'edge[type="assignment-relationship"]',
                style: {
                    'line-color': '#d79b00',
                    'target-arrow-color': '#d79b00'
                }
            },
            {
                selector: 'edge[type="composition-relationship"]',
                style: {
                    'line-color': '#6c8ebf',
                    'target-arrow-color': '#6c8ebf',
                    'line-style': 'solid'
                }
            },
            {
                selector: 'edge[type="access-relationship"]',
                style: {
                    'line-color': '#9673a6',
                    'target-arrow-color': '#9673a6',
                    'line-style': 'dashed'
                }
            }
        ],
        layout: {
            name: 'preset'
        }
    });

    // Create nodes from elements
    elements.forEach(element => {
        cy.add({
            group: 'nodes',
            data: {
                id: element.id,
                name: element.name,
                type: element.type,
                documentation: element.documentation || ''
            }
        });
    });

    // Create edges from relationships
    relationships.forEach(relationship => {
        cy.add({
            group: 'edges',
            data: {
                id: relationship.id,
                source: relationship.source,
                target: relationship.target,
                name: relationship.name || '',
                type: relationship.type
            }
        });
    });

    // Apply layout
    cy.layout({
        name: 'dagre',
        rankDir: 'TB',
        padding: 50,
        spacingFactor: 1.5,
        animate: true,
        animationDuration: 500
    }).run();

    // Fit the graph to the viewport
    cy.fit();

    // Add event listeners for controls
    document.getElementById('zoom-in').addEventListener('click', function() {
        cy.zoom({
            level: cy.zoom() * 1.2,
            renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
        });
    });

    document.getElementById('zoom-out').addEventListener('click', function() {
        cy.zoom({
            level: cy.zoom() / 1.2,
            renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
        });
    });

    document.getElementById('fit').addEventListener('click', function() {
        cy.fit();
    });

    document.getElementById('download-png').addEventListener('click', function() {
        const png = cy.png({
            output: 'blob',
            bg: 'white',
            scale: 2
        });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(png);
        link.download = `${filename}_archimate.png`;
        link.click();
    });

    document.getElementById('download-xml').addEventListener('click', function() {
        // Get the session ID from the URL
        const sessionId = window.location.pathname.split('/').pop();
        
        // Fetch the XML directly
        fetch(`/api/archimate-data/${sessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Create a request to convert the data to XML
                return fetch('/convert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        archimate_data: data
                    })
                });
            })
            .then(response => response.blob())
            .then(blob => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${filename}.xml`;
                link.click();
            })
            .catch(error => {
                console.error('Error downloading XML:', error);
                alert('Error downloading XML. Please try again.');
            });
    });

    // Add tooltips to nodes
    cy.on('mouseover', 'node', function(e) {
        const node = e.target;
        const type = node.data('type').replace(/-/g, ' ');
        const name = node.data('name');
        const documentation = node.data('documentation');
        
        const tooltip = document.createElement('div');
        tooltip.className = 'cy-tooltip';
        tooltip.innerHTML = `
            <div class="cy-tooltip-header">${name}</div>
            <div class="cy-tooltip-type">${type}</div>
            ${documentation ? `<div class="cy-tooltip-doc">${documentation}</div>` : ''}
        `;
        
        document.body.appendChild(tooltip);
        
        const updateTooltipPosition = function(e) {
            tooltip.style.left = `${e.originalEvent.pageX + 10}px`;
            tooltip.style.top = `${e.originalEvent.pageY + 10}px`;
        };
        
        updateTooltipPosition(e);
        cy.on('mousemove', updateTooltipPosition);
        
        node.on('mouseout', function() {
            tooltip.remove();
            cy.off('mousemove', updateTooltipPosition);
        });
    });

    // Add CSS for tooltips
    const style = document.createElement('style');
    style.textContent = `
        .cy-tooltip {
            position: absolute;
            z-index: 1000;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            max-width: 250px;
            font-size: 12px;
        }
        .cy-tooltip-header {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .cy-tooltip-type {
            color: #666;
            font-style: italic;
            margin-bottom: 5px;
            text-transform: capitalize;
        }
        .cy-tooltip-doc {
            border-top: 1px solid #eee;
            padding-top: 5px;
            margin-top: 5px;
        }
    `;
    document.head.appendChild(style);
}); 