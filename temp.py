from flask import Flask, request, render_template, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import numpy as np
import trimesh

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'stl', 'obj', 'fbx', 'dae', 'ply'}
app.secret_key = 'your_secret_key'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def convert_to_stl(input_path, output_path):
    try:
        mesh = trimesh.load(input_path)
        mesh.export(output_path, file_type='stl')
    except Exception as e:
        raise RuntimeError(f"Error during conversion: {e}")


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
            try:
                file.save(filepath)

                stl_filename = filename.rsplit('.', 1)[0] + '.stl'
                stl_filepath = os.path.join(
                    app.config['UPLOAD_FOLDER'], stl_filename)

                # Convert to STL if needed
                if filename.rsplit('.', 1)[1].lower() != 'stl':
                    convert_to_stl(filepath, stl_filepath)
                    # Remove the original file after conversion
                    os.remove(filepath)
                else:
                    stl_filepath = filepath

                return redirect(url_for('process_file', filename=stl_filename))
            except Exception as e:
                flash(f'Error processing file: {e}')
                return redirect(request.url)
        else:
            flash('Invalid file type')
            return redirect(request.url)
    return render_template('index.html')


@app.route('/process/<filename>')
def process_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        # Load the STL file
        your_mesh = trimesh.load(filepath, file_type='stl')

        # Bounding Box Dimensions
        minx, maxx = your_mesh.bounds[0][0], your_mesh.bounds[1][0]
        miny, maxy = your_mesh.bounds[0][1], your_mesh.bounds[1][1]
        minz, maxz = your_mesh.bounds[0][2], your_mesh.bounds[1][2]

        x_dim = maxx - minx
        y_dim = maxy - miny
        z_dim = maxz - minz

        # Surface Area Calculation
        def calculate_surface_area(trimesh_mesh):
            return trimesh_mesh.area

        # Volume Calculation
        def calculate_volume(trimesh_mesh):
            return trimesh_mesh.volume

        surface_area = calculate_surface_area(your_mesh)
        volume = calculate_volume(your_mesh)

        # Optionally, delete the file after processing
        os.remove(filepath)

        return render_template('result.html', x_dim=x_dim, y_dim=y_dim, z_dim=z_dim, surface_area=surface_area, volume=volume, filename=filename)

    except Exception as e:
        flash(f'Error processing file: {e}')
        return redirect(url_for('upload_file'))


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
