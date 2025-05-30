from flask import Flask, request, jsonify, render_template, send_from_directory
import sys
import os
import subprocess
import json
import ssl
from flask_cors import CORS

 
app = Flask(__name__)
CORS(app) 
# Path to TripoSR directory
triposr_path = r"C:\project\app15\flask\TripoSR"

# Create templates directory for HTML templates
os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)

# Add CORS headers to allow access from Flutter app
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/process_image', methods=['POST', 'OPTIONS'])
def process_image():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
        
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    
    # Save the uploaded image temporarily
    temp_dir = os.path.join(triposr_path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, "temp_image.jpg")
    file.save(temp_path)
    
    # Create output directory
    output_dir = os.path.join(triposr_path, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Run TripoSR as a subprocess using the command pattern
        cmd = [
            sys.executable,  # Python executable
            os.path.join(triposr_path, "run.py"),  # Path to run.py
            temp_path,  # Path to input image
            "--output-dir", output_dir  # Output directory
        ]
        
        print(f"Executing command: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=triposr_path  # Set working directory to TripoSR path
        )
        
        if result.returncode != 0:
            print(f"Error running TripoSR: {result.stderr}")
            return jsonify({'error': f"TripoSR execution failed: {result.stderr}"}), 500
        
        # Get the output file path (assuming it's the same filename in the output directory)
        output_filename = os.path.basename(temp_path)
        output_base = os.path.splitext(output_filename)[0]
        
        # Look for output files in the output directory
        output_files = []
        for file in os.listdir(output_dir):
            if file.startswith(output_base) or "temp_image" in file:
                output_files.append(os.path.join(output_dir, file))
        
        response_data = {
            'success': True,
            'message': result.stdout,
            'output_files': output_files
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Attempt to clean up the temporary file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Failed to remove temporary file: {e}")

# Add static route to serve the obj file specifically
@app.route('/get_model')
def get_model():
    obj_file_path = os.path.join(triposr_path, "output", "0", "mesh.obj")
    print(f"Serving OBJ file from: {obj_file_path}")
    
    if not os.path.exists(obj_file_path):
        print(f"ERROR: OBJ file not found at: {obj_file_path}")
        return jsonify({'error': 'Model file not found'}), 404
    
    # Log that we're serving the file
    print(f"Successfully serving OBJ file")
    
    # Return the actual file
    return send_from_directory(os.path.join(triposr_path, "output", "0"), "mesh.obj")

# Add route for the 3D viewer
@app.route('/Tviewer')
def viewer():
    obj_file_path = os.path.join(triposr_path, "output", "0", "mesh.obj")
    
    # Check if the file exists
    if not os.path.exists(obj_file_path):
        return "Model file not found at " + obj_file_path + ". Process an image first.", 404
        
    return render_template('viewer.html')

# Create the viewer.html template
with open(os.path.join(os.path.dirname(__file__), "templates", "viewer.html"), "w") as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D OBJ Viewer</title>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; background-color: #111; }
        canvas { width: 100%; height: 100%; display: block; }
        #info {
            position: absolute;
            top: 10px;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            pointer-events: none;
            z-index: 100;
            font-size: 14px;
        }
        #debug {
            position: absolute;
            top: 40px;
            width: 100%;
            text-align: center;
            color: #ff8800;
            font-family: monospace;
            pointer-events: none;
            z-index: 100;
            font-size: 12px;
        }
        #controls {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 5px;
            color: white;
            font-family: Arial, sans-serif;
            z-index: 100;
        }
        button {
            margin: 5px;
            padding: 5px 10px;
            cursor: pointer;
        }
        input[type="range"] {
            width: 100px;
            margin: 0 10px;
        }
        .toggle-button {
            background-color: #444;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 10px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .toggle-button.active {
            background-color: #4CAF50;
        }
        .control-group {
            margin-bottom: 10px;
        }
        .fullscreen-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(0,0,0,0.7);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 12px;
            cursor: pointer;
            z-index: 200;
        }
        .export-button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 10px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .export-button:hover {
            background-color: #45a049;
        }
        .dropdown {
            position: relative;
            display: inline-block;
        }
        .dropdown-content {
            display: none;
            position: absolute;
            right: 0;
            bottom: 100%;
            background-color: rgba(0,0,0,0.9);
            min-width: 160px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5);
            z-index: 201;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        .dropdown-content a {
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            display: block;
            cursor: pointer;
        }
        .dropdown-content a:hover {
            background-color: rgba(255,255,255,0.1);
        }
        .dropdown:hover .dropdown-content {
            display: block;
        }
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 300;
            display: none;
        }
        .notification.success {
            border-left: 4px solid #4CAF50;
        }
        .notification.error {
            border-left: 4px solid #f44336;
        }
        .controls-buttons {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
        }
    </style>
</head>
<body>
    <div id="info">Three.js OBJ Viewer</div>
    <div id="debug"></div>
    <div id="notification" class="notification"></div>
    
    <button id="fullscreenBtn" class="fullscreen-button">
        <span id="fullscreenIcon">⛶</span>
    </button>
    
    <div id="controls">
        <div class="control-group">
            <label>Scale: </label>
            <input type="range" id="scale" min="0.1" max="2" step="0.1" value="1">
            <span id="scaleValue">1.0</span>
        </div>
        <div class="control-group">
            <label>View Mode: </label>
            <button id="normalBtn" class="toggle-button active">Normal</button>
            <button id="wireframeBtn" class="toggle-button">Wireframe</button>
            <button id="hybridBtn" class="toggle-button">Hybrid</button>
        </div>
        <div class="control-group">
            <label>Lighting: </label>
            <button id="lightingBtn" class="toggle-button active">On</button>
            <input type="range" id="lightIntensity" min="0" max="2" step="0.1" value="1">
            <span id="lightValue">1.0</span>
        </div>
        <div class="control-group controls-buttons">
            <button id="resetBtn">Reset View</button>
            <div class="dropdown">
                <button class="export-button">Export</button>
                <div class="dropdown-content">
                    <a id="exportOBJ">OBJ Format</a>
                    <a id="exportSTL">STL Format</a>
                    <a id="exportGLTF">GLTF Format</a>
                    <a id="exportPLY">PLY Format</a>
                    <a id="exportScreenshot">Screenshot (PNG)</a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Import Three.js libraries using ES modules -->
    <script type="importmap">
    {
        "imports": {
            "three": "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.157.0/three.module.min.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.157.0/examples/jsm/"
        }
    }
    </script>
    
    <script type="module">
        import * as THREE from 'three';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
        import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
        import { OBJExporter } from 'three/addons/exporters/OBJExporter.js';
        import { STLExporter } from 'three/addons/exporters/STLExporter.js';
        import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
        import { PLYExporter } from 'three/addons/exporters/PLYExporter.js';
        
        // Debug element
        const debugElement = document.getElementById('debug');
        const notificationElement = document.getElementById('notification');
        
        // Initialize Three.js scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x111111);
        
        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        // Add directional lights
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);
        
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight2.position.set(-1, -1, -1);
        scene.add(directionalLight2);
        
        // Add point lights for better illumination
        const pointLight1 = new THREE.PointLight(0xffffff, 0.5);
        pointLight1.position.set(5, 5, 5);
        scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xffffff, 0.3);
        pointLight2.position.set(-5, -3, 2);
        scene.add(pointLight2);
        
        // Store all lights in an array for easy manipulation
        const lights = [ambientLight, directionalLight, directionalLight2, pointLight1, pointLight2];
        
        // Set up camera
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 5;
        
        // Set up renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(renderer.domElement);
        
        // Add orbit controls for rotation and zoom
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.25;
        controls.enableZoom = true;
        
        // Variable to store the loaded model
        let model;
        let modelMeshes = [];
        
        // Add a grid helper for reference
        const gridHelper = new THREE.GridHelper(10, 10);
        scene.add(gridHelper);
        
        // Add axes helper
        const axesHelper = new THREE.AxesHelper(5);
        scene.add(axesHelper);
        
        // OBJ file path
        const objFilePath = '/get_model';
        console.log(`Attempting to load model from: ${objFilePath}`);
        debugElement.textContent = `Attempting to load model from: ${objFilePath}`;
        
        // Load OBJ file
        const objLoader = new OBJLoader();
        objLoader.load(objFilePath, 
            // Success callback
            function(object) {
                console.log('Model loaded successfully');
                debugElement.textContent = 'Model loaded successfully';
                model = object;
                
                // Center the model
                const box = new THREE.Box3().setFromObject(object);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                console.log('Model dimensions:', size);
                console.log('Model center:', center);
                
                // Set model position to center
                object.position.x = -center.x;
                object.position.y = -center.y;
                object.position.z = -center.z;
                
                // Add a default material if none exists and store meshes
                object.traverse(function(child) {
                    if (child instanceof THREE.Mesh) {
                        modelMeshes.push(child);
                        
                        if (!child.material) {
                            child.material = new THREE.MeshStandardMaterial({
                                color: 0xcccccc,
                                metalness: 0.1,
                                roughness: 0.7,
                            });
                        }
                        
                        // Store the original material for switching between view modes
                        child.userData.originalMaterial = child.material.clone();
                        
                        console.log('Mesh found in model:', child);
                    }
                });
                
                // Add to scene
                scene.add(object);
                
                // Adjust camera position based on model size
                const maxDim = Math.max(size.x, size.y, size.z);
                camera.position.z = maxDim * 2;
                camera.lookAt(0, 0, 0);
                
                // Update controls
                controls.update();
                
                // Enable export buttons
                document.querySelectorAll('.export-button, .dropdown-content a').forEach(button => {
                    button.classList.add('active');
                });
            }, 
            // Progress callback
            function(xhr) {
                const percentComplete = xhr.loaded / xhr.total * 100;
                console.log(`Loading: ${Math.round(percentComplete)}%`);
                debugElement.textContent = `Loading: ${Math.round(percentComplete)}%`;
            },
            // Error callback
            function(error) {
                console.error('Error loading model:', error);
                debugElement.textContent = `Error loading model: ${error.message || 'Unknown error'}`;
                document.getElementById('info').textContent = 'Error loading model';
                document.getElementById('info').style.color = 'red';
            }
        );
        
        // Handle window resize
        window.addEventListener('resize', function() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // Handle scale control
        const scaleSlider = document.getElementById('scale');
        const scaleValue = document.getElementById('scaleValue');
        
        scaleSlider.addEventListener('input', function() {
            const value = parseFloat(this.value);
            scaleValue.textContent = value.toFixed(1);
            
            if (model) {
                model.scale.set(value, value, value);
            }
        });
        
        // View mode control functions
        function setNormalView() {
            if (!modelMeshes.length) return;
            
            modelMeshes.forEach(mesh => {
                mesh.material = mesh.userData.originalMaterial.clone();
            });
            
            // Update buttons
            document.getElementById('normalBtn').classList.add('active');
            document.getElementById('wireframeBtn').classList.remove('active');
            document.getElementById('hybridBtn').classList.remove('active');
        }
        
        function setWireframeView() {
            if (!modelMeshes.length) return;
            
            modelMeshes.forEach(mesh => {
                mesh.material = new THREE.MeshBasicMaterial({
                    color: 0x00ff00,
                    wireframe: true
                });
            });
            
            // Update buttons
            document.getElementById('normalBtn').classList.remove('active');
            document.getElementById('wireframeBtn').classList.add('active');
            document.getElementById('hybridBtn').classList.remove('active');
        }
        
        function setHybridView() {
            if (!modelMeshes.length) return;
            
            modelMeshes.forEach(mesh => {
                // Clone the original material
                const material = mesh.userData.originalMaterial.clone();
                
                // Create a wireframe material
                const wireframeMaterial = new THREE.MeshBasicMaterial({
                    color: 0x00ff00,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.3
                });
                
                // Create a multi-material
                mesh.material = [material, wireframeMaterial];
            });
            
            // Update buttons
            document.getElementById('normalBtn').classList.remove('active');
            document.getElementById('wireframeBtn').classList.remove('active');
            document.getElementById('hybridBtn').classList.add('active');
        }
        
        // Add event listeners for view mode buttons
        document.getElementById('normalBtn').addEventListener('click', setNormalView);
        document.getElementById('wireframeBtn').addEventListener('click', setWireframeView);
        document.getElementById('hybridBtn').addEventListener('click', setHybridView);
        
        // Lighting control
        const lightingBtn = document.getElementById('lightingBtn');
        const lightIntensity = document.getElementById('lightIntensity');
        const lightValue = document.getElementById('lightValue');
        
        // Toggle lighting on/off
        lightingBtn.addEventListener('click', function() {
            const isActive = this.classList.contains('active');
            
            if (isActive) {
                // Turn off lights
                lights.forEach(light => {
                    light.intensity = 0;
                });
                this.classList.remove('active');
            } else {
                // Turn on lights
                const intensity = parseFloat(lightIntensity.value);
                updateLightIntensity(intensity);
                this.classList.add('active');
            }
        });
        
        // Update light intensity
        function updateLightIntensity(value) {
            lightValue.textContent = value.toFixed(1);
            
            if (lightingBtn.classList.contains('active')) {
                ambientLight.intensity = value * 0.5;
                directionalLight.intensity = value * 0.8;
                directionalLight2.intensity = value * 0.5;
                pointLight1.intensity = value * 0.5;
                pointLight2.intensity = value * 0.3;
            }
        }
        
        lightIntensity.addEventListener('input', function() {
            const value = parseFloat(this.value);
            updateLightIntensity(value);
        });
        
        // Reset button
        document.getElementById('resetBtn').addEventListener('click', function() {
            if (model) {
                model.scale.set(1, 1, 1);
                scaleSlider.value = 1;
                scaleValue.textContent = "1.0";
                
                // Reset lighting
                lightIntensity.value = 1;
                updateLightIntensity(1);
                lightingBtn.classList.add('active');
                
                // Reset to normal view
                setNormalView();
                
                // Reset camera and controls
                controls.reset();
            }
        });
        
        // Fullscreen handling
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const fullscreenIcon = document.getElementById('fullscreenIcon');
        
        fullscreenBtn.addEventListener('click', toggleFullScreen);
        
        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.error(`Error attempting to enable full-screen mode: ${err.message}`);
                });
                fullscreenIcon.textContent = '⛶';
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                    fullscreenIcon.textContent = '⛶';
                }
            }
        }
        
        // Handle fullscreen change
        document.addEventListener('fullscreenchange', function() {
            if (document.fullscreenElement) {
                fullscreenIcon.textContent = '✕';
            } else {
                fullscreenIcon.textContent = '⛶';
            }
        });
        
        // Show notification
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.style.display = 'block';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        // Save file helper function
        function saveFile(content, fileName, fileType) {
            const blob = new Blob([content], { type: fileType });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = fileName;
            link.click();
            URL.revokeObjectURL(link.href);
        }
        
        // Export functions
        function exportOBJ() {
            if (!model) {
                showNotification('No model loaded to export', 'error');
                return;
            }
            
            try {
                const exporter = new OBJExporter();
                const result = exporter.parse(model);
                saveFile(result, 'model.obj', 'text/plain');
                showNotification('OBJ file exported successfully');
            } catch (error) {
                console.error('Error exporting OBJ:', error);
                showNotification('Error exporting OBJ: ' + error.message, 'error');
            }
        }
        
        function exportSTL() {
            if (!model) {
                showNotification('No model loaded to export', 'error');
                return;
            }
            
            try {
                const exporter = new STLExporter();
                const result = exporter.parse(model, { binary: true });
                saveFile(result, 'model.stl', 'application/octet-stream');
                showNotification('STL file exported successfully');
            } catch (error) {
                console.error('Error exporting STL:', error);
                showNotification('Error exporting STL: ' + error.message, 'error');
            }
        }
        
        function exportGLTF() {
            if (!model) {
                showNotification('No model loaded to export', 'error');
                return;
            }
            
            try {
                const exporter = new GLTFExporter();
                exporter.parse(
                    model,
                    function(result) {
                        if (result instanceof ArrayBuffer) {
                            saveFile(result, 'model.glb', 'application/octet-stream');
                        } else {
                            const output = JSON.stringify(result, null, 2);
                            saveFile(output, 'model.gltf', 'application/json');
                        }
                        showNotification('GLTF file exported successfully');
                    },
                    function(error) {
                        console.error('Error exporting GLTF:', error);
                        showNotification('Error exporting GLTF: ' + error.message, 'error');
                    },
                    { binary: false }
                );
            } catch (error) {
                console.error('Error exporting GLTF:', error);
                showNotification('Error exporting GLTF: ' + error.message, 'error');
            }
        }
        
        function exportPLY() {
            if (!model) {
                showNotification('No model loaded to export', 'error');
                return;
            }
            
            try {
                const exporter = new PLYExporter();
                exporter.parse(
                    model,
                    function(result) {
                        saveFile(result, 'model.ply', 'application/octet-stream');
                        showNotification('PLY file exported successfully');
                    },
                    { binary: true }
                );
            } catch (error) {
                console.error('Error exporting PLY:', error);
                showNotification('Error exporting PLY: ' + error.message, 'error');
            }
        }
        
        function exportScreenshot() {
            try {
                // Temporarily hide UI elements
                const infoElement = document.getElementById('info');
                const debugElement = document.getElementById('debug');
                const controlsElement = document.getElementById('controls');
                const fullscreenBtn = document.getElementById('fullscreenBtn');
                
                infoElement.style.display = 'none';
                debugElement.style.display = 'none';
                controlsElement.style.display = 'none';
                fullscreenBtn.style.display = 'none';
                
                // Render the scene
                renderer.render(scene, camera);
                
                // Create a screenshot
                const dataURL = renderer.domElement.toDataURL('image/png');
                
                // Create a link and trigger download
                const link = document.createElement('a');
                link.href = dataURL;
                link.download = 'screenshot.png';
                link.click();
                
                // Show elements again
                infoElement.style.display = 'block';
                debugElement.style.display = 'block';
                controlsElement.style.display = 'block';
                fullscreenBtn.style.display = 'block';
                
                showNotification('Screenshot exported successfully');
            } catch (error) {
                console.error('Error exporting screenshot:', error);
                showNotification('Error exporting screenshot: ' + error.message, 'error');
            }
        }
        
        // Attach export event listeners
        document.getElementById('exportOBJ').addEventListener('click', exportOBJ);
        document.getElementById('exportSTL').addEventListener('click', exportSTL);
        document.getElementById('exportGLTF').addEventListener('click', exportGLTF);
        document.getElementById('exportPLY').addEventListener('click', exportPLY);
        document.getElementById('exportScreenshot').addEventListener('click', exportScreenshot);
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        animate();
        
        // Auto-detect if coming from Flutter by checking for a specific URL parameter
        window.addEventListener('load', function() {
            const params = new URLSearchParams(window.location.search);
            if (params.get('fromFlutter') === 'true') {
                // If coming from Flutter, automatically go fullscreen after a short delay
                setTimeout(() => {
                    toggleFullScreen();
                }, 1000);
            }
        });
    </script>
</body>
</html>""")

if __name__ == '__main__':
    print(f"Starting Flask server. TripoSR path: {triposr_path}")
    
    # Option 1: Run with HTTP but with CORS headers (already added above)
    # app.run(host='0.0.0.0', port=5000, debug=True)
    
    # Option 2: Run with HTTPS
    # Generate certificates with:
    # openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    # Place these files in the same directory as this script
    
    # Check if certificate files exist
    cert_path = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'key.pem')
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        # Run with HTTPS
        print("Using HTTPS with SSL certificates")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)
    else:
        # Run with HTTP
        print("WARNING: Running without HTTPS. Generate certificates for secure connection.")
        app.run(host='0.0.0.0', port=5000, debug=True)