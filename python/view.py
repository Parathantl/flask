from flask import Flask, render_template, request
import os

from datetime import timedelta

from flask import Flask
from flask.helpers import send_from_directory
from flask_cors import CORS

from flask_jwt import JWT

from api.exceptions.notfound import NotFoundException

from api.exceptions.badrequest import BadRequestException
from api.exceptions.validation import ValidationException

from api.neo4j import init_driver

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
from haystack.utils import fetch_archive_from_http
from haystack.utils import convert_files_to_docs, fetch_archive_from_http, clean_wiki_text
from haystack.nodes import Seq2SeqGenerator

from haystack.document_stores import FAISSDocumentStore
from haystack.pipelines import GenerativeQAPipeline
from haystack.document_stores import ElasticsearchDocumentStore

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

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

document_store = FAISSDocumentStore(sql_url="sqlite:////home/ubuntu/flask/python/faiss_document_store.db", faiss_index_factory_str="Flat")

# Let's first get some files that we want to use
docu_dir = "./api/routes/data/tutorial12"
s3_url = "https://bitbucket.org/parathant/rp-project/raw/ae286dd95c031cc4cdae3c20bc1ef8762f2b791a/dataset.zip"
fetch_archive_from_http(url=s3_url, output_dir=docu_dir)

# Convert files to dicts
docs = convert_files_to_docs(dir_path=docu_dir, clean_func=clean_wiki_text, split_paragraphs=True)

# Now, let's write the dicts containing documents to our DB.
document_store.write_documents(docs)

reloaded_retriever = DensePassageRetriever.load(load_dir=save_dir, document_store=document_store)

document_store.update_embeddings(reloaded_retriever)

document_store.save("my_faiss")

# Reader/Generator
generator = Seq2SeqGenerator(model_name_or_path="vblagoje/bart_lfqa")

pipe = GenerativeQAPipeline(generator, reloaded_retriever)

@app.route('/')
def home():
    return {"hello": "world"}

@app.route('/api/query', methods=['POST'])
def getQuery():
    form_data = request.get_json()['results']

    query = form_data['query']

    pipe.run(query=query, params={"Retriever": {"top_k": 5}})

    return 0

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3001))
    app.run(debug=True, host='0.0.0.0', port=port)
