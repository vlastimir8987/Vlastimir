from flask import Flask, render_template, request, jsonify, send_from_directory
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

# ---------- Чат и API ----------
@app.route('/chat')
def chat_page():
    return render_template('chat.html')   # теперь чат доступен по /chat

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

# ---------- Статические файлы ----------
# Для всех остальных запросов (например, /index.html, /videos.html, /images/...)
# отдаём файлы из корня проекта.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if not path:
        # Если запрос к корню, отдаём index.html
        return send_from_directory('.', 'index.html')
    # Проверяем, существует ли файл
    if os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory('.', path)
    else:
        # Если файл не найден, можно вернуть 404
        return "Страница не найдена", 404

# ---------- Запуск (для локального тестирования) ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
