from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity
import os
from haystack.nodes import DensePassageRetriever
from haystack.utils import fetch_archive_from_http
from haystack.utils import convert_files_to_docs, fetch_archive_from_http, clean_wiki_text
from haystack.nodes import Seq2SeqGenerator

from haystack.document_stores import FAISSDocumentStore
from haystack.pipelines import GenerativeQAPipeline
from haystack.document_stores import ElasticsearchDocumentStore
import shutil

query_routes = Blueprint("query", __name__, url_prefix="/api/query")

save_dir = "./saved_models"

# document_store_1 = FAISSDocumentStore(faiss_index_factory_str="Flat", similarity="dot_product")

doc_store = ElasticsearchDocumentStore(host="localhost", username="", password="", index="document")

# Let's first get some files that we want to use
docu_dir = "./api/routes/data/tutorial12"
s3_url = "https://bitbucket.org/parathant/rp-project/raw/bc3925e7dc8d5e5925b9be2668ba0438506e3a95/dataset.zip"
fetch_archive_from_http(url=s3_url, output_dir=docu_dir)

# Convert files to dicts
docs = convert_files_to_docs(dir_path=docu_dir, clean_func=clean_wiki_text, split_paragraphs=True)

# Now, let's write the dicts containing documents to our DB.
doc_store.write_documents(docs)

reloaded_retriever = DensePassageRetriever.load(load_dir=save_dir, document_store=doc_store)

doc_store.update_embeddings(reloaded_retriever)

# Reader/Generator
generator = Seq2SeqGenerator(model_name_or_path="vblagoje/bart_lfqa")

pipe = GenerativeQAPipeline(generator, reloaded_retriever)

@query_routes.route('/', methods=['POST'])
def getQuery():
    form_data = request.get_json()['results']

    query = form_data['query']

    print(
        pipe.run(
            query=query, params={"Retriever": {"top_k": 5}}
        )
    )
    return 0