from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
from dotenv import load_dotenv
import numpy as np
import os

# Carrega variáveis de ambiente PRIMEIRO
load_dotenv()

# Configuração do Gemini DEVE vir depois do load_dotenv
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Nome correto da variável
model = genai.GenerativeModel('gemini-2.0-flash')

embedder = SentenceTransformer('all-MiniLM-L6-v2')


def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return " ".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        print(f"Erro ao ler {pdf_path}: {str(e)}")
        return ""


def split_text_into_chunks(text, chunk_size=200):
    if not text:
        return []
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def process_pdfs(pdfs_dir):
    course_indices = {}
    for course_name in os.listdir(pdfs_dir):
        course_path = os.path.join(pdfs_dir, course_name)
        if os.path.isdir(course_path):
            text_chunks = []
            for pdf_file in os.listdir(course_path):
                if pdf_file.endswith('.pdf'):
                    pdf_path = os.path.join(course_path, pdf_file)
                    text = extract_text_from_pdf(pdf_path)
                    if text:  # Só adiciona se extraiu texto
                        chunks = split_text_into_chunks(text)
                        text_chunks.extend(chunks)

            if text_chunks:  # Só cria índice se houver chunks
                embeddings = embedder.encode(text_chunks)
                index = faiss.IndexFlatL2(embeddings.shape[1])
                index.add(embeddings)
                course_indices[course_name] = {
                    "index": index,
                    "text_chunks": text_chunks
                }
    return course_indices


def get_available_courses():
    pdfs_dir = 'pdfs'  # Diretório onde os PDFs estão armazenados
    courses = []
    for item in os.listdir(pdfs_dir):
        if os.path.isdir(os.path.join(pdfs_dir, item)):
            pretty_name = ' '.join(word.capitalize() for word in item.split('-'))
            courses.append({'id': item, 'name': pretty_name})
    return courses


def ask_question(question, course_name, course_indices, top_k=3):
    # Verifica se o curso existe
    if course_name not in course_indices:
        return f"Curso '{course_name}' não encontrado!", {}

    index = course_indices[course_name]["index"]
    text_chunks = course_indices[course_name]["text_chunks"]

    # Busca chunks relevantes
    question_embedding = embedder.encode([question])
    distances, indices = index.search(question_embedding, top_k)

    relevant_chunks = [text_chunks[i] for i in indices[0]]
    context = "\n".join(relevant_chunks)

    # Prompt otimizado
    prompt = f"""
    Você é um assistente da escola SENAI.
    Responda de forma clara e direta usando APENAS o contexto fornecido.
    
    
    [Cursos disponíveis]
    {get_available_courses()}
    
    [CONTEXTO]
    {context}

    [PERGUNTA]
    {question}

    [INSTRUÇÕES]
    1. Seja conciso (1-2 parágrafos)
    2. Use linguagem acessível
    3. Se não souber, diga "Não encontrei essa informação no material"
    """

    try:
        response = model.generate_content(prompt)
        return response.text, {
            "course": course_name,
            "used_chunks": relevant_chunks
        }
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}", {}