from flask import Flask, request, jsonify
from flask_cors import CORS
from database_postgres import save_submission, get_submission, get_all_submissions, init_db
from youtube import get_video_id, fetch_transcript, summarize

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the database
init_db()

@app.route('/api/submissions', methods=['POST'])
def create_submission():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
            
        submission_id = save_submission(text)
        return jsonify({
            'id': submission_id,
            'message': 'Submission saved successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
def get_submission_by_id(submission_id):
    try:
        submission = get_submission(submission_id)
        if submission:
            return jsonify(submission)
        return jsonify({'error': 'Submission not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
def list_submissions():
    try:
        submissions = get_all_submissions()
        return jsonify(submissions)
    except Exception as e:
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 