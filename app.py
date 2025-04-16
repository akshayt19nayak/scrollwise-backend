from flask import Flask, request, jsonify
from flask_cors import CORS
from database_postgres import save_submission, get_submission, get_all_submissions, init_db

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

if __name__ == '__main__':
    app.run(debug=True, port=5000) 