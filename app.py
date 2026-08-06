from flask import Flask, render_template, request, jsonify, send_from_directory, session
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder='.')
app.secret_key = 'ваш_секретный_ключ_для_сессий'  # замените на что-то своё

# Используем /tmp для хранения файла (доступно для записи на Vercel)
MESSAGES_FILE = '/tmp/messages.json'
ADMIN_PASSWORD = '9qwe232'

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
    return render_template('chat.html')

@app.route('/get_messages')
def get_messages():
    messages = load_messages()
    return jsonify(messages[-50:])

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        name = request.form.get('name', 'Аноним').strip()
        message = request.form.get('message', '').strip()
        if not message:
            return jsonify({'status': 'error', 'message': 'Сообщение не может быть пустым'}), 400

        messages = load_messages()
        messages.append({
            'name': name,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        save_messages(messages)
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Ошибка в send_message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------- Админ-панель ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # Проверяем пароль: через GET-параметр, POST-параметр или сессию
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
        else:
            return "Неверный пароль", 403

    # Если уже авторизован по сессии – пропускаем
    if not session.get('admin'):
        # Если GET-запрос с паролем в URL (для удобства)
        if request.args.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
        else:
            # Показываем форму ввода пароля
            return '''
            <form method="post">
                <input type="password" name="password" placeholder="Введите пароль">
                <input type="submit" value="Войти">
            </form>
            '''

    # Обработка сохранения нового JSON
    if request.method == 'POST' and 'json_content' in request.form:
        new_json = request.form['json_content']
        try:
            data = json.loads(new_json)  # проверяем, что это валидный JSON
            if not isinstance(data, list):
                return "JSON должен быть массивом", 400
            save_messages(data)
            return "Данные обновлены! <a href='/admin'>Вернуться</a>"
        except json.JSONDecodeError as e:
            return f"Ошибка в JSON: {e}", 400

    # Отображаем текущий JSON в текстовом поле
    messages = load_messages()
    current_json = json.dumps(messages, ensure_ascii=False, indent=2)
    
    # Также отобразим список сообщений для удобства
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Админ-панель чата</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        textarea {{ width: 100%; height: 400px; font-family: monospace; }}
        .message-list {{ margin-top: 20px; border-top: 1px solid #ccc; }}
        .message-item {{ padding: 5px; border-bottom: 1px solid #eee; }}
        .delete-btn {{ color: red; cursor: pointer; margin-left: 10px; }}
    </style>
    </head>
    <body>
    <h1>Админ-панель чата</h1>
    <p>Редактируйте JSON-файл напрямую. Будьте аккуратны!</p>
    <form method="post">
        <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
        <textarea name="json_content">{current_json}</textarea>
        <br>
        <input type="submit" value="Сохранить изменения">
    </form>

    <div class="message-list">
        <h2>Список сообщений (для быстрого удаления)</h2>
        <ul>
    '''
    for i, msg in enumerate(messages):
        html += f'''
        <li class="message-item">
            [{msg.get('timestamp', '')}] <b>{msg.get('name', '')}</b>: {msg.get('message', '')}
            <a href="/admin/delete/{i}?password={ADMIN_PASSWORD}" class="delete-btn" onclick="return confirm('Удалить это сообщение?')">[X]</a>
        </li>
        '''
    html += '''
        </ul>
    </div>
    <p><a href="/chat">Вернуться в чат</a></p>
    </body>
    </html>
    '''
    return html

# Удаление конкретного сообщения по индексу
@app.route('/admin/delete/<int:index>')
def delete_message(index):
    if request.args.get('password') != ADMIN_PASSWORD:
        return "Неверный пароль", 403
    messages = load_messages()
    if 0 <= index < len(messages):
        deleted = messages.pop(index)
        save_messages(messages)
        return f"Сообщение от {deleted.get('name')} удалено. <a href='/admin'>Вернуться</a>"
    else:
        return "Сообщение не найдено", 404

# ---------- Статические файлы ----------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if not path:
        return send_from_directory('.', 'index.html')
    if os.path.exists(path) and not os.path.isdir(path):
        return send_from_directory('.', path)
    return "Страница не найдена", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
