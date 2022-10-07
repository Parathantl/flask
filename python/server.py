from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.neo4j import init_driver
import os
from datetime import timedelta
from flask_jwt import JWT

from haystack.nodes import DensePassageRetriever
from haystack.pipelines import GenerativeQAPipeline, ExtractiveQAPipeline
from haystack.nodes import FARMReader, TransformersReader, Seq2SeqGenerator
from haystack.document_stores import ElasticsearchDocumentStore, FAISSDocumentStore

app = Flask(__name__)
CORS(app)

load_dotenv()

save_dir = "./saved_models"

document_store = FAISSDocumentStore.load(index_path="haystack_test_faiss", config_path="haystack_test_faiss_config")

retriever = DensePassageRetriever.load(load_dir=save_dir, document_store=document_store)

reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)

generator = Seq2SeqGenerator(model_name_or_path="vblagoje/bart_lfqa")

pipe = GenerativeQAPipeline(generator, retriever)

@app.route('/')
def home():
    return {"hello": "world"}

@app.route('/api/query', methods=['POST'])
def getQuery():
    
    form_data = request.get_json()
    query = form_data['query']
        
    prediction = pipe.run(query=query, params={"Retriever": {"top_k": 4}})
    
    answers_list = prediction['answers']
    answers = []
    scores = []
    
    for answer in answers_list:
        answers.append(answer.answer)
        scores.append(answer.score)

    return jsonify(list(zip(answers, scores)))

@app.route('/api/queryans', methods=['POST'])
def getQueryChatbot():
    form_data = request.get_json()
    query = form_data['query']

    prediction = pipe.run(query=query, params={"Retriever": {"top_k": 4}})

    answers_list = prediction['answers']
    answers = []
    
    for answer in answers_list:
        answers.append(answer.answer)

    return jsonify(list(zip(answers)))

if __name__=="__main__":
    app.run(host='0.0.0.0', port=80)
