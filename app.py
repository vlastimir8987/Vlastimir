from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder='.')  # шаблоны в корне

MESSAGES_FILE = 'messages.json'

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/get_messages')
def get_messages():
    messages = load_messages()
    return jsonify(messages[-50:])

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name', 'Аноним').strip()
    message = request.form.get('message', '').strip()
    if not message:
        return jsonify({'status': 'error', 'message': 'Сообщение не может быть пустым'})

    messages = load_messages()
    messages.append({
        'name': name,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
    save_messages(messages)
    return jsonify({'status': 'ok'})

# (блок if __name__ == '__main__' можно оставить для локального запуска, но Vercel его игнорирует)
