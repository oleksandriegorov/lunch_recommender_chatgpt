from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def read_api_key() -> str:
    api_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..', 'keys', 'open_api_key.key')
    with open(api_key_path, 'r') as file:
        api_key = file.read().strip()
    logging.debug('API key successfully read.')
    return api_key

@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    prompt = generate_prompt(data)
    api_key = read_api_key()

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'gpt-4o',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 500,
            'temperature': 0.7
        }
    )

    if response.status_code == 200:
        recommendation = response.json()
        logging.debug('Received response from OpenAI API.')
        return jsonify(recommendation['choices'][0]['message']['content'])
    else:
        logging.error(f'Failed to get recommendation: {response.status_code} - {response.text}')
        return jsonify({'error': 'Не вдалося отримати рекомендацію'}), 500

def generate_prompt(data: dict) -> str:
    options = []
    if data.get('meat') == 'yes':
        options.append('мʼясні страви')
    if data.get('fish') == 'yes':
        options.append('рибні страви')
    if data.get('vegan') == 'yes':
        options.append('веганські страви')
    if not options:
        options.append('пісні страви')

    prompt = (
        f"Запропонуй один варіант обіду зважаючи на наступні умови: "
        f"{', '.join(options)}, калорійність до {data['calories']} ккал, "
        f"кількість страв {data['dishes']}, "
        f"{'напій включити' if data['drink'] == 'yes' else 'без напою'}, "
        f"інші рекомендації: {data['other_notes']}."
        " Після кожної страви надати кількість калорій та БЖВ. Але не надавай інгрідієнти та рецепт. Це занадто."
    )
    logging.debug(f'Generated prompt: {prompt}')
    return prompt

if __name__ == '__main__':
    logging.info('Starting Flask app...')
    app.run(host='0.0.0.0', port=80, debug=True)
