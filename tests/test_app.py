import pytest
from app import generate_prompt, read_api_key, recommend
from flask import Flask, request
import json

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/recommend', methods=['POST'])
    def recommend_test():
        return recommend()

    with app.test_client() as client:
        yield client

def test_generate_prompt():
    data = {
        'meat': 'yes',
        'fish': 'no',
        'vegan': 'no',
        'calories': '2000',
        'dishes': '3',
        'drink': 'yes',
        'other_notes': 'Ніякого цукру'
    }
    expected_prompt = (
        "Запропонуй один варіант обіду зважаючи на наступні умови: мʼясні страви, "
        "калорійність до 2000 ккал, кількість страв 3, напій включити, "
        "інші рекомендації: Ніякого цукру. "
        "Після кожної страви надати кількість калорій та БЖВ. Але не надавай інгрідієнти та рецепт. Це занадто."
    )
    assert generate_prompt(data) == expected_prompt

def test_read_api_key(mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data='test_api_key'))
    api_key = read_api_key()
    assert api_key == 'test_api_key'

def test_recommend_success(client, mocker):
    # Створення макету відповіді, яка буде серіалізована у JSON
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'choices': [{
            'message': {
                'content': 'Recommended meal plan'
            }
        }]
    }
    mock_response.status_code = 200

    # Патчинг requests.post, щоб повертати mock_response
    mocker.patch('requests.post', return_value=mock_response)

    data = {
        'meat': 'yes',
        'fish': 'no',
        'vegan': 'no',
        'calories': '2000',
        'dishes': '3',
        'drink': 'yes',
        'other_notes': 'Ніякого цукру'
    }
    
    response = client.post('/recommend', json=data)
    assert response.status_code == 200
    assert b'Recommended meal plan' in response.data


def test_recommend_failure(client, mocker):
    mocker.patch('requests.post').return_value.status_code = 500
    mocker.patch('requests.post').return_value.text = 'Internal Server Error'

    data = {
        'meat': 'yes',
        'fish': 'no',
        'vegan': 'no',
        'calories': '2000',
        'dishes': '3',
        'drink': 'yes',
        'other_notes': 'Ніякого цукру'
    }
    
    response = client.post('/recommend', json=data)
    assert response.status_code == 500
    assert 'Не вдалося отримати рекомендацію' in response.json.get('error')
