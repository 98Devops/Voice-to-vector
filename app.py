from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from memory_manager import MemoryManager
import json

app = Flask(__name__)
CORS(app)

memory_manager = MemoryManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/store_voice_note', methods=['POST'])
def store_voice_note_api():
    if request.is_json:
        data = request.get_json()
        transcribed_text = data.get('text')
        structured_tags = data.get('tags', []) 
        action_items = data.get('action_items', []) 
        sentiment = data.get('sentiment', 'neutral') 

        if isinstance(structured_tags, str):
            try:
                structured_tags = json.loads(structured_tags) 
                if not isinstance(structured_tags, list):
                    structured_tags = []
            except json.JSONDecodeError:
                structured_tags = [tag.strip() for tag in structured_tags.split(',') if tag.strip()]
        elif not isinstance(structured_tags, list):
            structured_tags = [] 

        if isinstance(action_items, str):
            try:
                action_items = json.loads(action_items)
                if not isinstance(action_items, list):
                    action_items = []
            except json.JSONDecodeError:
                action_items = []
        elif not isinstance(action_items, list): 
            action_items = []

        print(f"Received text for storage: {transcribed_text[:70]}...")
        print(f"Received tags for storage: {structured_tags}")
        print(f"Received action items for storage: {action_items}")
        print(f"Received sentiment for storage: {sentiment}")

        if not transcribed_text:
            return jsonify({"error": "No text provided for storage"}), 400

        success, message = memory_manager.store_voice_note(transcribed_text, structured_tags, action_items, sentiment)

        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    else:
        return jsonify({"error": "Request must be JSON"}), 400

@app.route('/search_voice_notes', methods=['POST'])
def search_voice_notes_api():
    if request.is_json:
        query = request.get_json().get('query')
        if not query:
            return jsonify({"error": "No query provided"}), 400

        print(f"Received search query: {query}")
        results = memory_manager.search_voice_notes(query)
        return jsonify({"results": results}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)