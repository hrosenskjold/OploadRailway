import os
from flask import Flask, render_template, request, jsonify
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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        try:
            # Unzip and read shapefile
            with shapefile.Reader(file_path) as shp:
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
            response = requests.post(arcgis_url, json={"features": features})
            if response.status_code == 200:
                return jsonify(message='File successfully uploaded and processed'), 200
            else:
                return jsonify(error='Failed to add features to ArcGIS layer'), 500
        except Exception as e:
            return jsonify(error=str(e)), 500
    else:
        return jsonify(error='Invalid file format, only .zip containing .shp is allowed'), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
