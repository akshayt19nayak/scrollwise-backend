from flask import Flask, request, jsonify
from flask_cors import CORS
from database_postgres import (
    save_bookmark, get_bookmark, get_all_bookmarks, init_db,
    create_collection, get_all_collections, create_tag, get_all_tags,
    update_bookmark, get_bookmarks_by_tag_id, get_bookmarks_by_collection_id
)
from youtube import get_video_id, fetch_transcript, summarize
import traceback
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the database
init_db()

@app.route('/api/bookmarks', methods=['POST'])
def create_bookmark():
    try:
        data = request.get_json()
        text = data.get('text')
        title = data.get('title')
        collection_id = data.get('collection_id')
        tag_ids = data.get('tag_ids', [])
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
            
        bookmark_id = save_bookmark(text, title, collection_id, tag_ids)
        return jsonify({
            'id': bookmark_id,
            'message': 'Bookmark saved successfully'
        }), 201
        
    except Exception as e:
        print("ERROR in create_bookmark:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookmarks/<int:bookmark_id>', methods=['GET'])
def get_bookmark_by_id(bookmark_id):
    try:
        bookmark = get_bookmark(bookmark_id)
        if bookmark:
            return jsonify(bookmark)
        return jsonify({'error': 'Bookmark not found'}), 404
    except Exception as e:
        print("ERROR in get_bookmark_by_id:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookmarks', methods=['GET'])
def list_bookmarks():
    try:
        bookmarks = get_all_bookmarks()
        return jsonify(bookmarks)
    except Exception as e:
        print("ERROR in list_bookmarks:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookmarks/<int:bookmark_id>', methods=['PUT'])
def update_bookmark_by_id(bookmark_id):
    try:
        data = request.get_json()
        title = data.get('title')
        collection_id = data.get('collection_id')
        tag_ids = data.get('tag_ids')
        
        update_bookmark(bookmark_id, title, collection_id, tag_ids)
        return jsonify({'message': 'Bookmark updated successfully'})
    except Exception as e:
        print("ERROR in update_bookmark_by_id:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections', methods=['GET'])
def list_collections():
    try:
        collections = get_all_collections()
        return jsonify(collections)
    except Exception as e:
        print("ERROR in list_collections:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections', methods=['POST'])
def create_new_collection():
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Collection name is required'}), 400
            
        collection_id = create_collection(name)
        return jsonify({
            'id': collection_id,
            'message': 'Collection created successfully'
        }), 201
    except Exception as e:
        print("ERROR in create_new_collection:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags', methods=['GET'])
def list_tags():
    try:
        tags = get_all_tags()
        return jsonify(tags)
    except Exception as e:
        print("ERROR in list_tags:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags', methods=['POST'])
def create_new_tag():
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Tag name is required'}), 400
            
        tag_id = create_tag(name)
        return jsonify({
            'id': tag_id,
            'message': 'Tag created successfully'
        }), 201
    except Exception as e:
        print("ERROR in create_new_tag:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def get_summary():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # First check if it's a valid YouTube URL
        video_id = get_video_id(text)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        # Fetch the transcript
        transcript = fetch_transcript(text)
        if transcript.startswith("An error occurred"):
            return jsonify({'error': transcript}), 400
        
        # Generate the summary
        summary = summarize(text)
        return jsonify({'summary': summary})
        
    except Exception as e:
        print("ERROR in get_summary:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags/<int:tag_id>/bookmarks', methods=['GET'])
def get_bookmarks_by_tag(tag_id):
    try:
        bookmarks = get_bookmarks_by_tag_id(tag_id)
        return jsonify(bookmarks)
    except Exception as e:
        print("ERROR in get_bookmarks_by_tag:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<int:collection_id>/bookmarks', methods=['GET'])
def get_bookmarks_by_collection(collection_id):
    try:
        bookmarks = get_bookmarks_by_collection_id(collection_id)
        return jsonify(bookmarks)
    except Exception as e:
        print("ERROR in get_bookmarks_by_collection:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 