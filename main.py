import os
from flask import Flask, render_template, request, jsonify
import zipfile
import shapefile
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16 MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello')
def hello():
    return jsonify(message="Hallo World!")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(error='No file part'), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify(error='No selected file'), 400
    
    if file and file.filename.endswith('.zip'):
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(zip_path)
        
        try:
            # Unzip the uploaded file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all contents to a temporary directory
                zip_ref.extractall(app.config['UPLOAD_FOLDER'])
            
            # Find .shp and .dbf files in the extracted directory
            shp_file = None
            dbf_file = None
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                if filename.endswith('.shp'):
                    shp_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                elif filename.endswith('.dbf'):
                    dbf_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if shp_file and dbf_file:
                # Read shapefile
                with shapefile.Reader(shp_file, dbf=dbf_file) as shp:
                    features = []
                    for sr in shp.shapeRecords():
                        geom = sr.shape.__geo_interface__
                        props = sr.record.as_dict()
                        features.append({
                            "geometry": geom,
                            "attributes": props
                        })
                
                # Add features to ArcGIS layer
                arcgis_url = 'https://services6.arcgis.com/QHir1urgnGYroCLG/arcgis/rest/services/PG_versioneret_110624/FeatureServer/0/addFeatures'
                #response = requests.post(arcgis_url, json={"features": features})
                response = requests.post(url, data={"features": json.dumps([feature]), "f": "json"})

                if response.status_code == 200:
                    return jsonify(message='File successfully uploaded and processed'), 200
                else:
                    return jsonify(error='Failed to add features to ArcGIS layer'), 500
            
            else:
                return jsonify(error='Shapefile (.shp) or DBF (.dbf) file not found in uploaded zip'), 400
        
        except Exception as e:
            return jsonify(error=str(e)), 500
        
        finally:
            # Clean up: Delete uploaded zip and extracted files
            if os.path.exists(zip_path):
                os.remove(zip_path)
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    else:
        return jsonify(error='Invalid file format, only .zip containing .shp and .dbf is allowed'), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
