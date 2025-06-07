from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.RPG_audio_library
samples_collection = db.samples
scenes_collection = db.scenes

# Ensure upload directory exists
UPLOAD_FOLDER = 'audio_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/samples', methods=['POST'])
def upload_sample():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        sample_data = {
            'name': request.form.get('name', filename),
            'filename': filename,
            'is_one_shot': request.form.get('is_one_shot', 'false').lower() == 'true',
            'category': request.form.get('category', 'uncategorized')
        }

        result = samples_collection.insert_one(sample_data)
        sample_data['_id'] = str(result.inserted_id)
        
        return jsonify(sample_data), 201

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/samples', methods=['GET'])
def get_samples():
    samples = list(samples_collection.find())
    for sample in samples:
        sample['_id'] = str(sample['_id'])
    return jsonify(samples)

@app.route('/api/samples/<sample_id>', methods=['GET'])
def get_sample(sample_id):
    sample = samples_collection.find_one({'_id': sample_id})
    if sample:
        sample['_id'] = str(sample['_id'])
        return jsonify(sample)
    return jsonify({'error': 'Sample not found'}), 404

@app.route('/api/samples/<sample_id>', methods=['PUT'])
def update_sample(sample_id):
    data = request.json
    result = samples_collection.update_one(
        {'_id': sample_id},
        {'$set': data}
    )
    if result.modified_count:
        return jsonify({'message': 'Sample updated successfully'})
    return jsonify({'error': 'Sample not found'}), 404

@app.route('/api/samples/<sample_id>', methods=['DELETE'])
def delete_sample(sample_id):
    sample = samples_collection.find_one({'_id': sample_id})
    if sample:
        # Delete the file
        file_path = os.path.join(UPLOAD_FOLDER, sample['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        samples_collection.delete_one({'_id': sample_id})
        return jsonify({'message': 'Sample deleted successfully'})
    return jsonify({'error': 'Sample not found'}), 404

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/scenes', methods=['POST'])
def create_scene():
    scene_data = request.json
    result = scenes_collection.insert_one(scene_data)
    scene_data['_id'] = str(result.inserted_id)
    return jsonify(scene_data), 201

@app.route('/api/scenes', methods=['GET'])
def get_scenes():
    scenes = list(scenes_collection.find())
    for scene in scenes:
        scene['_id'] = str(scene['_id'])
    return jsonify(scenes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)