from flask import Flask, request, render_template, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import numpy as np
from stl import mesh
import cadquery as cq
import trimesh

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'stl', 'step', 'obj', 'ply'}  # Allow STL, STEP, OBJ, and PLY files
app.config['SECRET_KEY'] = 'supersecretkey'  # For flash messages

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to convert STEP to STL using CadQuery
def convert_step_to_stl(step_path, stl_path):
    try:
        # Load the STEP file into a CadQuery object
        shape = cq.importers.importStep(step_path)
        # Export the CadQuery object to an STL file
        cq.exporters.export(shape, stl_path)
        flash(f'Successfully converted {os.path.basename(step_path)} to STL.')
        return True
    except Exception as e:
        flash(f'Error converting STEP to STL: {str(e)}')
        return False

# Function to convert OBJ to STL using Trimesh
def convert_obj_to_stl(obj_path, stl_path):
    try:
        # Load the OBJ file using trimesh
        mesh = trimesh.load(obj_path)
        # Export the mesh to STL
        mesh.export(stl_path)
        flash(f'Successfully converted {os.path.basename(obj_path)} to STL.')
        return True
    except Exception as e:
        flash(f'Error converting OBJ to STL: {str(e)}')
        return False

# Function to convert PLY to STL using Trimesh
def convert_ply_to_stl(ply_path, stl_path):
    try:
        # Load the PLY file using trimesh
        mesh = trimesh.load(ply_path)
        # Export the mesh to STL
        mesh.export(stl_path)
        flash(f'Successfully converted {os.path.basename(ply_path)} to STL.')
        return True
    except Exception as e:
        flash(f'Error converting PLY to STL: {str(e)}')
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Check file extension and convert if necessary
            if filename.lower().endswith('.step'):
                stl_filename = filename.rsplit('.', 1)[0] + '.stl'
                stl_path = os.path.join(app.config['UPLOAD_FOLDER'], stl_filename)
                if convert_step_to_stl(filepath, stl_path):
                    return redirect(url_for('process_file', filename=stl_filename))
            elif filename.lower().endswith('.obj'):
                stl_filename = filename.rsplit('.', 1)[0] + '.stl'
                stl_path = os.path.join(app.config['UPLOAD_FOLDER'], stl_filename)
                if convert_obj_to_stl(filepath, stl_path):
                    return redirect(url_for('process_file', filename=stl_filename))
            elif filename.lower().endswith('.ply'):
                stl_filename = filename.rsplit('.', 1)[0] + '.stl'
                stl_path = os.path.join(app.config['UPLOAD_FOLDER'], stl_filename)
                if convert_ply_to_stl(filepath, stl_path):
                    return redirect(url_for('process_file', filename=stl_filename))
            elif filename.lower().endswith('.stl'):
                return redirect(url_for('process_file', filename=filename))
    return render_template('index.html')

@app.route('/process/<filename>')
def process_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Load the STL file
    your_mesh = mesh.Mesh.from_file(filepath)

    # Bounding Box Dimensions
    minx = your_mesh.x.min()
    maxx = your_mesh.x.max()
    miny = your_mesh.y.min()
    maxy = your_mesh.y.max()
    minz = your_mesh.z.min()
    maxz = your_mesh.z.max()

    x_dim = maxx - minx
    y_dim = maxy - miny
    z_dim = maxz - minz

    # Surface Area Calculation
    def calculate_surface_area(stl_mesh):
        triangles = stl_mesh.vectors
        a = triangles[:, 1] - triangles[:, 0]
        b = triangles[:, 2] - triangles[:, 0]
        cross_product = np.cross(a, b)
        area = np.linalg.norm(cross_product, axis=1) / 2
        return np.sum(area)

    # Volume Calculation
    def calculate_volume(stl_mesh):
        triangles = stl_mesh.vectors
        a = triangles[:, 0]
        b = triangles[:, 1]
        c = triangles[:, 2]
        volume = np.abs(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6
        return np.sum(volume)

    surface_area = calculate_surface_area(your_mesh)
    volume = calculate_volume(your_mesh)

    return render_template('result.html', x_dim=x_dim, y_dim=y_dim, z_dim=z_dim, surface_area=surface_area, volume=volume, filename=filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
