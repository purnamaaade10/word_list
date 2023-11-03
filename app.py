from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)

password = 'learningx'
url = f'mongodb+srv://tes:{password}@cluster0.cyjbgzl.mongodb.net/?retryWrites=true&w=majority&appName=AtlasApp'

users = MongoClient(url)

database = users.dblearningx

@app.route('/')
def main():
    words_result = database.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,

        })
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "8e166fba-e2b9-4e89-a96e-9da80eeb4f60"
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    r = requests.get(url)
    definitions = r.json()

    if not definitions:
        return redirect(url_for(
            'main',
            msg=f'Could not find the word, "{keyword}"'
        ))
    
    if type(definitions[0]) is str:
        suggestions = ', '.join(definitions)
        return redirect(url_for(
            'main',
            msg=f'Could not find the word, "{keyword}", did you mean one of these words: {suggestions}'
        ))        

    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')

    doc = {
        'word': word, 
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%m-%d'),
    }

    database.words.insert_one(doc)

    return jsonify({
        'result': 'success',
        'msg': f'word {word} was saved!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    database.words.delete_one({'word': word})
    database.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'word {word} was deleted!',
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = database.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({'example': example.get('example'), 'id': str(example.get('_id')),})
    return jsonify({'result': 'success', 'examples': examples})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example,
    }
    database.examples.insert_one(doc)
    return jsonify({'result': 'success', 'msg': f'Your example {example} for the word {word} was saved!',})

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    database.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'success', 'msg': f'Your example word for {word} was deleted!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

