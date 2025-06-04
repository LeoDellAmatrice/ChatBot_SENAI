from flask import Flask, request, jsonify, render_template
from utils import process_all_courses, ask_question
import os

app = Flask(__name__)
app.config['PDFS_DIR'] = 'pdfs'

# Processar todos os cursos ao iniciar
GLOBAL_INDEX = process_all_courses(app.config['PDFS_DIR'])


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')

    response = ask_question(
        question=question,
        global_index=GLOBAL_INDEX
    )

    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(debug=True)