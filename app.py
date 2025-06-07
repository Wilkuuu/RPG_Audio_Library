from flask import Flask, request, jsonify, send_file, Response, render_template
from flask_cors import CORS
from pymongo import MongoClient
import gridfs
import os
from werkzeug.utils import secure_filename
import json
from bson import ObjectId

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.RPG_audio_library
samples_collection = db.samples
scenes_collection = db.scenes
fs = gridfs.GridFS(db)

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
        # Save file to GridFS
        gridfs_id = fs.put(file, filename=filename, content_type=file.content_type)
        sample_data = {
            'name': request.form.get('name', filename),
            'filename': filename,
            'gridfs_id': str(gridfs_id),
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
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Convert string ID to ObjectId
        from bson.objectid import ObjectId
        sample_id = ObjectId(sample_id)

        # Update the sample in MongoDB
        result = samples_collection.update_one(
            {'_id': sample_id},
            {'$set': {
                'name': data.get('name'),
                'category': data.get('category'),
                'is_one_shot': data.get('is_one_shot', False)
            }}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Sample not found or no changes made'}), 404

        # Get the updated sample
        updated_sample = samples_collection.find_one({'_id': sample_id})
        updated_sample['_id'] = str(updated_sample['_id'])

        return jsonify(updated_sample), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/samples/<sample_id>', methods=['DELETE'])
def delete_sample(sample_id):
    try:
        # Convert string ID to ObjectId
        sample_id = ObjectId(sample_id)
        sample = samples_collection.find_one({'_id': sample_id})
        
        if sample:
            # Delete from GridFS if gridfs_id exists
            if 'gridfs_id' in sample:
                try:
                    fs.delete(ObjectId(sample['gridfs_id']))
                except Exception as e:
                    print(f"Error deleting from GridFS: {e}")
            
            # Delete from database
            result = samples_collection.delete_one({'_id': sample_id})
            if result.deleted_count > 0:
                return jsonify({'message': 'Sample deleted successfully'})
        
        return jsonify({'error': 'Sample not found'}), 404
    except Exception as e:
        print(f"Error in delete_sample: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    # Find the sample by filename
    sample = samples_collection.find_one({'filename': filename})
    if not sample or 'gridfs_id' not in sample:
        return jsonify({'error': 'Audio not found'}), 404
    try:
        gridfs_id = ObjectId(sample['gridfs_id'])
        file = fs.get(gridfs_id)
        return Response(file.read(), mimetype=file.content_type,
                        headers={"Content-Disposition": f"inline; filename={filename}"})
    except Exception as e:
        return jsonify({'error': 'Audio not found in GridFS'}), 404

@app.route('/api/scenes', methods=['POST'])
def create_scene():
    scene_data = request.json
    # Ensure samples have volume property
    if 'samples' in scene_data:
        for sample in scene_data['samples']:
            if isinstance(sample, dict):
                sample['volume'] = sample.get('volume', 100)
            else:
                scene_data['samples'] = [{'id': s, 'volume': 100} for s in scene_data['samples']]
                break
    result = scenes_collection.insert_one(scene_data)
    scene_data['_id'] = str(result.inserted_id)
    return jsonify(scene_data), 201

@app.route('/api/scenes', methods=['GET'])
def get_scenes():
    scenes = list(scenes_collection.find())
    for scene in scenes:
        scene['_id'] = str(scene['_id'])
    return jsonify(scenes)

@app.route('/api/scenes/<scene_id>', methods=['DELETE'])
def delete_scene(scene_id):
    try:
        scene_id = ObjectId(scene_id)
        result = scenes_collection.delete_one({'_id': scene_id})
        if result.deleted_count > 0:
            return jsonify({'message': 'Scene deleted successfully'})
        return jsonify({'error': 'Scene not found'}), 404
    except Exception as e:
        print(f"Error in delete_scene: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)