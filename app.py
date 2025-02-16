from flask import Flask, render_template, request, jsonify
from finwise_bot import FinWiseBot
import json

app = Flask(__name__)
bot = FinWiseBot()

@app.route('/')
def home():
    return render_template('index.html', modes=bot.modes, commands=bot.commands)

@app.route('/api/command', methods=['POST'])
def process_command():
    data = request.json
    command = data.get('command', '')
    response = bot.process_command(command)
    return jsonify({'response': response})

@app.route('/api/mode', methods=['POST'])
def change_mode():
    data = request.json
    mode = data.get('mode', '')
    response = bot.process_command(f'mode {mode}')
    return jsonify({'response': response})

@app.route('/api/help')
def get_help():
    return jsonify({'help': bot.show_help()})

if __name__ == '__main__':
    app.run(debug=True) 