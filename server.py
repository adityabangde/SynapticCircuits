from flask import Flask, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Sample circuit data - this is what Gemini would generate
SAMPLE_CIRCUITS = {
    "simple_led": {
        "name": "Simple LED Circuit",
        "components": [
            {
                "id": "V1",
                "type": "voltage_source",
                "value": "9V",
                "polarity": "dc"
            },
            {
                "id": "R1",
                "type": "resistor",
                "value": "330Ω"
            },
            {
                "id": "LED1",
                "type": "led",
                "value": "Red LED"
            }
        ],
        "connections": [
            {"from": "V1.positive", "to": "R1.1"},
            {"from": "R1.2", "to": "LED1.anode"},
            {"from": "LED1.cathode", "to": "V1.negative"}
        ]
    },
    "transistor_switch": {
        "name": "NPN Transistor Switch",
        "components": [
            {
                "id": "V1",
                "type": "voltage_source",
                "value": "12V",
                "polarity": "dc"
            },
            {
                "id": "R1",
                "type": "resistor",
                "value": "1kΩ"
            },
            {
                "id": "R2",
                "type": "resistor",
                "value": "10kΩ"
            },
            {
                "id": "Q1",
                "type": "transistor",
                "transistor_type": "npn",
                "value": "2N2222"
            },
            {
                "id": "LED1",
                "type": "led",
                "value": "Red LED"
            }
        ],
        "connections": [
            {"from": "V1.positive", "to": "R1.1"},
            {"from": "R1.2", "to": "LED1.anode"},
            {"from": "LED1.cathode", "to": "Q1.collector"},
            {"from": "Q1.emitter", "to": "V1.negative"},
            {"from": "R2.1", "to": "Q1.base"},
            {"from": "R2.2", "to": "V1.negative"}
        ]
    },
    "voltage_divider": {
        "name": "Voltage Divider",
        "components": [
            {
                "id": "V1",
                "type": "voltage_source",
                "value": "12V",
                "polarity": "dc"
            },
            {
                "id": "R1",
                "type": "resistor",
                "value": "10kΩ"
            },
            {
                "id": "R2",
                "type": "resistor",
                "value": "10kΩ"
            },
            {
                "id": "GND",
                "type": "ground",
                "value": ""
            }
        ],
        "connections": [
            {"from": "V1.positive", "to": "R1.1"},
            {"from": "R1.2", "to": "R2.1"},
            {"from": "R2.2", "to": "GND.terminal"},
            # {"from": "V1.negative", "to": "GND.terminal"}
        ]
    }
}

# Embedded HTML (so you don't need a separate file)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Circuit Visualizer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .controls {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        select, button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        select {
            background: white;
            border: 2px solid #667eea;
            color: #333;
        }
        button {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.3);
        }
        .canvas-container {
            padding: 30px;
            display: flex;
            justify-content: center;
            background: #ffffff;
        }
        canvas {
            border: 2px solid #e9ecef;
            border-radius: 10px;
            background: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .info {
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 2px solid #e9ecef;
        }
        .legend {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: white;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .legend-symbol {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            background: #f1f3f5;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Circuit Visualizer</h1>
            <p>AI-Powered Circuit Diagram Generator</p>
        </div>
        
        <div class="controls">
            <select id="circuitSelect">
                <option value="">Select a circuit...</option>
            </select>
            <button onclick="loadCircuit()">Load Circuit</button>
            <button onclick="clearCanvas()">Clear</button>
        </div>
        
        <div class="canvas-container">
            <canvas id="circuitCanvas" width="1200" height="700"></canvas>
        </div>
        
        <div class="info">
            <h3>Component Legend</h3>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-symbol">R</div>
                    <span>Resistor (Rectangle)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol">⊖⊕</div>
                    <span>Voltage Source (Circle)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol">▶</div>
                    <span>LED (Triangle)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol">Q</div>
                    <span>Transistor NPN (↓ arrow)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol">Q</div>
                    <span>Transistor PNP (↑ arrow)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-symbol">⏚</div>
                    <span>Ground</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('circuitCanvas');
        const ctx = canvas.getContext('2d');
        const API_URL = '/api';  // Changed to relative URL
        
        let currentCircuit = null;
        let componentPositions = {};

        // Load available circuits on page load
        async function loadCircuitList() {
            try {
                const response = await fetch(`${API_URL}/circuits`);
                const data = await response.json();
                const select = document.getElementById('circuitSelect');
                
                data.circuits.forEach(circuitId => {
                    const option = document.createElement('option');
                    option.value = circuitId;
                    option.textContent = circuitId.replace(/_/g, ' ').toUpperCase();
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading circuits:', error);
                alert('Could not connect to backend.');
            }
        }

        // Load selected circuit
        async function loadCircuit() {
            const circuitId = document.getElementById('circuitSelect').value;
            if (!circuitId) return;
            
            try {
                const response = await fetch(`${API_URL}/circuit/${circuitId}`);
                currentCircuit = await response.json();
                visualizeCircuit(currentCircuit);
            } catch (error) {
                console.error('Error loading circuit:', error);
            }
        }

        // Auto-layout algorithm
        function calculateLayout(circuit) {
            const positions = {};
            const components = circuit.components;
            const connections = circuit.connections;
            
            const layers = [];
            const visited = new Set();
            
            const sources = components.filter(c => c.type === 'voltage_source');
            
            if (sources.length > 0) {
                layers.push(sources.map(s => s.id));
                sources.forEach(s => visited.add(s.id));
            }
            
            let currentLayer = layers[0] || [];
            while (visited.size < components.length) {
                const nextLayer = [];
                
                currentLayer.forEach(compId => {
                    connections.forEach(conn => {
                        const from = conn.from.split('.')[0];
                        const to = conn.to.split('.')[0];
                        
                        if (from === compId && !visited.has(to)) {
                            nextLayer.push(to);
                            visited.add(to);
                        }
                    });
                });
                
                if (nextLayer.length === 0) {
                    components.forEach(c => {
                        if (!visited.has(c.id)) {
                            nextLayer.push(c.id);
                            visited.add(c.id);
                        }
                    });
                }
                
                if (nextLayer.length > 0) {
                    layers.push(nextLayer);
                }
            }
            
            const layerSpacing = 200;
            const componentSpacing = 150;
            const startX = 100;
            const startY = 150;
            
            layers.forEach((layer, layerIndex) => {
                const y = startY + layerIndex * layerSpacing;
                layer.forEach((compId, index) => {
                    const x = startX + index * componentSpacing + (canvas.width - (layer.length * componentSpacing)) / 2;
                    positions[compId] = { x, y };
                });
            });
            
            return positions;
        }

        function drawResistor(x, y, label, value) {
            ctx.strokeStyle = '#2c3e50';
            ctx.lineWidth = 2;
            ctx.strokeRect(x - 30, y - 15, 60, 30);
            ctx.fillStyle = '#2c3e50';
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('R', x, y + 5);
            ctx.font = '12px Arial';
            ctx.fillText(label, x, y - 25);
            ctx.fillText(value, x, y + 35);
            return {
                '1': { x: x - 30, y: y },
                '2': { x: x + 30, y: y }
            };
        }

        function drawVoltageSource(x, y, label, value) {
            ctx.strokeStyle = '#e74c3c';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, 25, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillStyle = '#e74c3c';
            ctx.font = 'bold 18px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('+', x - 8, y + 6);
            ctx.fillText('-', x + 8, y + 6);
            ctx.font = '12px Arial';
            ctx.fillStyle = '#2c3e50';
            ctx.fillText(label, x, y - 35);
            ctx.fillText(value, x, y + 45);
            return {
                'positive': { x: x, y: y - 25 },
                'negative': { x: x, y: y + 25 }
            };
        }

        function drawLED(x, y, label, value) {
            ctx.strokeStyle = '#e67e22';
            ctx.fillStyle = '#e67e22';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, y - 20);
            ctx.lineTo(x - 20, y + 15);
            ctx.lineTo(x + 20, y + 15);
            ctx.closePath();
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x - 20, y + 15);
            ctx.lineTo(x + 20, y + 15);
            ctx.stroke();
            ctx.fillStyle = '#2c3e50';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(label, x, y - 30);
            ctx.fillText(value, x, y + 35);
            return {
                'anode': { x: x, y: y - 20 },
                'cathode': { x: x, y: y + 15 }
            };
        }

        function drawTransistor(x, y, label, type) {
            ctx.strokeStyle = '#3498db';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, y - 30);
            ctx.lineTo(x, y + 30);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x - 30, y);
            ctx.lineTo(x, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, y - 15);
            ctx.lineTo(x + 30, y - 30);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, y + 15);
            ctx.lineTo(x + 30, y + 30);
            ctx.stroke();
            ctx.fillStyle = '#3498db';
            ctx.beginPath();
            if (type === 'npn') {
                ctx.moveTo(x + 30, y + 30);
                ctx.lineTo(x + 20, y + 25);
                ctx.lineTo(x + 25, y + 20);
            } else {
                ctx.moveTo(x + 5, y + 10);
                ctx.lineTo(x, y + 20);
                ctx.lineTo(x + 10, y + 15);
            }
            ctx.closePath();
            ctx.fill();
            ctx.fillStyle = '#2c3e50';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(label, x, y - 40);
            ctx.fillText(type.toUpperCase(), x, y + 50);
            return {
                'base': { x: x - 30, y: y },
                'collector': { x: x + 30, y: y - 30 },
                'emitter': { x: x + 30, y: y + 30 }
            };
        }

        function drawGround(x, y, label) {
            ctx.strokeStyle = '#2c3e50';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, y - 20);
            ctx.lineTo(x, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x - 20, y);
            ctx.lineTo(x + 20, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x - 15, y + 5);
            ctx.lineTo(x + 15, y + 5);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x - 10, y + 10);
            ctx.lineTo(x + 10, y + 10);
            ctx.stroke();
            ctx.fillStyle = '#2c3e50';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(label, x, y + 30);
            return {
                'terminal': { x: x, y: y - 20 }
            };
        }

        function drawWire(x1, y1, x2, y2) {
            ctx.strokeStyle = '#34495e';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            const midY = (y1 + y2) / 2;
            ctx.lineTo(x1, midY);
            ctx.lineTo(x2, midY);
            ctx.lineTo(x2, y2);
            ctx.stroke();
            ctx.fillStyle = '#34495e';
            ctx.beginPath();
            ctx.arc(x1, y1, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(x2, y2, 3, 0, Math.PI * 2);
            ctx.fill();
        }

        function visualizeCircuit(circuit) {
            clearCanvas();
            componentPositions = calculateLayout(circuit);
            const terminals = {};
            
            circuit.components.forEach(comp => {
                const pos = componentPositions[comp.id];
                if (!pos) return;
                let terminalPos;
                switch (comp.type) {
                    case 'resistor':
                        terminalPos = drawResistor(pos.x, pos.y, comp.id, comp.value);
                        break;
                    case 'voltage_source':
                        terminalPos = drawVoltageSource(pos.x, pos.y, comp.id, comp.value);
                        break;
                    case 'led':
                        terminalPos = drawLED(pos.x, pos.y, comp.id, comp.value);
                        break;
                    case 'transistor':
                        terminalPos = drawTransistor(pos.x, pos.y, comp.id, comp.transistor_type);
                        break;
                    case 'ground':
                        terminalPos = drawGround(pos.x, pos.y, comp.id);
                        break;
                }
                if (terminalPos) {
                    Object.keys(terminalPos).forEach(terminal => {
                        terminals[`${comp.id}.${terminal}`] = terminalPos[terminal];
                    });
                }
            });
            
            circuit.connections.forEach(conn => {
                const fromPos = terminals[conn.from];
                const toPos = terminals[conn.to];
                if (fromPos && toPos) {
                    drawWire(fromPos.x, fromPos.y, toPos.x, toPos.y);
                }
            });
            
            ctx.fillStyle = '#2c3e50';
            ctx.font = 'bold 20px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(circuit.name, 20, 30);
        }

        function clearCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }

        loadCircuitList();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/circuits', methods=['GET'])
def get_circuits():
    """Get list of all available circuits"""
    return jsonify({
        "circuits": list(SAMPLE_CIRCUITS.keys())
    })

@app.route('/api/circuit/<circuit_id>', methods=['GET'])
def get_circuit(circuit_id):
    """Get specific circuit by ID"""
    if circuit_id in SAMPLE_CIRCUITS:
        return jsonify(SAMPLE_CIRCUITS[circuit_id])
    return jsonify({"error": "Circuit not found"}), 404

@app.route('/api/parse', methods=['POST'])
def parse_gemini_output():
    """
    This endpoint will eventually receive Gemini's text output
    and convert it to structured JSON
    """
    # TODO: Integrate with Gemini API
    return jsonify({"message": "Gemini integration coming soon"})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Circuit Visualizer Backend Starting...")
    print("=" * 50)
    print("\n✅ Server running at: http://localhost:5000")
    print("\n📋 Available endpoints:")
    print("   GET  /                    - Main web interface")
    print("   GET  /api/circuits        - List all circuits")
    print("   GET  /api/circuit/<id>    - Get specific circuit")
    print("   POST /api/parse           - Parse Gemini output (TODO)")
    print("\n💡 Open your browser and go to: http://localhost:5000")
    print("=" * 50)
    print()
    app.run(debug=True, port=5000)