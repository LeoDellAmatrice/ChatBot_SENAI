from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
from dotenv import load_dotenv
import numpy as np
import os

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')  # Modelo com contexto grande

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


def process_all_courses(pdfs_dir):
    """Cria um índice único com todo o conteúdo"""
    all_chunks = []
    all_metadata = []  # Armazena metadados sobre a origem de cada chunk

    for course_name in os.listdir(pdfs_dir):
        course_path = os.path.join(pdfs_dir, course_name)
        if os.path.isdir(course_path):
            for file in os.listdir(course_path):
                if file.endswith('.pdf'):
                    pdf_path = os.path.join(course_path, file)
                    text = extract_text_from_pdf(pdf_path)
                    if text:
                        chunks = split_text_into_chunks(text)
                        all_chunks.extend(chunks)
                        # Adiciona metadados identificando o curso de origem
                        all_metadata.extend([course_name] * len(chunks))

    # Cria índice unificado
    embeddings = embedder.encode(all_chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return {
        "index": index,
        "text_chunks": all_chunks,
        "metadata": all_metadata
    }


def ask_question(question, global_index):
    """Busca chunks relevantes e pergunta ao Gemini"""
    try:
        # Busca chunks relevantes em todo o conteúdo
        question_embedding = embedder.encode([question])
        distances, indices = global_index["index"].search(question_embedding, 10)  # Top 10 chunks

        # Pega os chunks mais relevantes
        relevant_chunks = [global_index["text_chunks"][i] for i in indices[0]]

        # Combina em um único contexto
        context = "\n\n".join(relevant_chunks)

        # Gera prompt completo para o Gemini
        prompt = f"""
        Você é um assistente especializado do SENAI. 
        Sua função é responder perguntas sobre os cursos técnicos oferecidos.
        Responda diretamente, sem rodeios, e baseie-se apenas no contexto fornecido.
        não diga que está usando um contexto.
        Responda de forma clara e direta, sem mencionar que está usando um contexto.
        Responda como um bom assistente, seja Humano.
        
        Aqui estão as informações disponíveis:

        ### CONTEXTO COMPLETO (material de todos os cursos):
        {context}

        ### PERGUNTA DO USUÁRIO:
        {question}

        ### INSTRUÇÕES:
        1. Responda de forma clara e direta
        2. Baseie-se apenas no contexto fornecido
        3. Se a pergunta for sobre cursos disponíveis, liste todos mencionados no contexto
        4. Se não encontrar informação, diga "Não tenho informações suficientes"
        5. Nunca mencione que está usando um contexto
        """

        # Chama o Gemini
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erro ao processar pergunta: {str(e)}"