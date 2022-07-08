from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from api.neo4j import init_driver
import os
from datetime import timedelta
from flask_jwt import JWT

from api.routes.auth import auth_routes
from api.routes.account import account_routes
from api.routes.movies import movie_routes
from api.routes.genres import genre_routes
from api.routes.people import people_routes
from api.routes.status import status_routes

from api.routes.courses import course_routes
from api.routes.mentors import mentor_routes
from api.routes.companies import company_routes

from haystack.nodes import DensePassageRetriever
from haystack.pipelines import GenerativeQAPipeline, ExtractiveQAPipeline
from haystack.nodes import FARMReader, TransformersReader, Seq2SeqGenerator
from haystack.document_stores import ElasticsearchDocumentStore, FAISSDocumentStore

app = Flask(__name__)
CORS(app)

load_dotenv()

app.config.from_mapping(
    NEO4J_URI=os.getenv('NEO4J_URI'),
    NEO4J_USERNAME=os.getenv('NEO4J_USERNAME'),
    NEO4J_PASSWORD=os.getenv('NEO4J_PASSWORD'),
    NEO4J_DATABASE=os.getenv('NEO4J_DATABASE'),
    SECRET_KEY=os.getenv('JWT_SECRET'),
    JWT_AUTH_HEADER_PREFIX="Bearer",
    JWT_VERIFY_CLAIMS="signature",
    JWT_EXPIRATION_DELTA=timedelta(360)
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

with app.app_context():
    init_driver(
        app.config.get('NEO4J_URI'),
        app.config.get('NEO4J_USERNAME'),
        app.config.get('NEO4J_PASSWORD'),
    )

    # JWT
def authenticate(username, password):
    pass

def identify(payload):
    payload["userId"] = payload["sub"]
    return payload

jwt = JWT(app, authenticate, identify)

# Register Routes
app.register_blueprint(auth_routes)
app.register_blueprint(account_routes)
app.register_blueprint(genre_routes)
app.register_blueprint(movie_routes)
app.register_blueprint(people_routes)
app.register_blueprint(status_routes)

app.register_blueprint(course_routes)
app.register_blueprint(company_routes)
app.register_blueprint(mentor_routes)

save_dir = "./saved_models"

# document_store = FAISSDocumentStore.load(index_path="haystack_test_faiss", config_path="haystack_test_faiss_config")

document_store = ElasticsearchDocumentStore(host="localhost", username="", password="", index="document")

retriever = DensePassageRetriever.load(load_dir=save_dir, document_store=document_store)

reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)

pipe = ExtractiveQAPipeline(reader, retriever)

@app.route('/')
def home():
    return {"hello": "world"}

@app.route('/api/query', methods=['POST'])
def getQuery():
   form_data = request.get_json()

   print("form_data:", form_data)

   query = form_data['query']

   print("query:", query)

   prediction = pipe.run(query=query, params={"Retriever": {"top_k": 10}, "Reader": {"top_k": 5}})
   
   print("prediction:", prediction)
   
   return 0

if __name__=="__main__":
    app.run(host='0.0.0.0', port=80)
