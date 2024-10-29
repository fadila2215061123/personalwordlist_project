import os
from os.path import join, dirname
from dotenv import load_dotenv
from bson import ObjectId
from flask import (
    Flask, 
    request, 
    render_template, 
    redirect, 
    url_for, 
    jsonify
)
from pymongo import MongoClient
import requests
from datetime import datetime


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html',words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'b8e5abff-1314-4feb-9896-9f92a3e476fa'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    
    # Tidak ada definisi yang ditemukan
    if not definitions:
        return render_template('eror.html', keyword=keyword, suggestions=[])
    
    # API hanya mengembalikan saran kata, tanpa definisi yang valid
    if type(definitions[0]) is str:
        suggestions = definitions
        return render_template('eror.html', keyword=keyword, suggestions=suggestions)
    
    # Kata ditemukan, menampilkan halaman detail
    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )
    
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    
    doc = {
        'word': word,
        'definitions': definitions,
        'date' : datetime.now().strftime('%Y-%m-%d'),
    }
    db.words.insert_one(doc)
    
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

    
@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')

    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    
    return jsonify({
        'result': 'success',
        'msg': f'The word "{word}" and its examples were deleted!'
    })

    
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id' : str(example['_id']),
        })
    return jsonify({
        'result': 'success',
        'examples': examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    json_data = request.get_json()
    example = json_data.get('example')
    word = json_data.get('word')

    if not example or not word:
        return jsonify({'result': 'error', 'msg': 'Example or word is missing'})

    db.examples.insert_one({'word': word, 'example': example})
    return jsonify({'result': 'success', 'msg': 'Example saved successfully'})


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    json_data = request.get_json()
    word = json_data.get('word')
    example_id = json_data.get('id')

    if not word or not example_id:
        return jsonify({'result': 'error', 'msg': 'Word or example ID is missing'})


    db.examples.delete_one({'_id': ObjectId(example_id)})

    return jsonify({'result': 'success', 'msg': 'Example deleted successfully'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5004, debug=True)