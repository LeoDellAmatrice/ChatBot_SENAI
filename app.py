from flask import Flask, request, jsonify, render_template
from utils import process_pdfs, ask_question
import os

app = Flask(__name__)
app.config['PDFS_DIR'] = 'pdfs'

# Processar PDFs ao iniciar
COURSE_INDICES = process_pdfs(app.config['PDFS_DIR'])


@app.route('/')
def home():
    cursos = list(COURSE_INDICES.keys())
    return render_template('index.html', cursos=cursos)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data['question']
    course_name = data['course']

    if course_name not in COURSE_INDICES:
        return jsonify({"error": "Curso não encontrado!"}), 404

    response, debug_data = ask_question(question, course_name, COURSE_INDICES)
    return jsonify({
        "response": response,
        "debug": debug_data
    })


if __name__ == '__main__':
    app.run(debug=True)