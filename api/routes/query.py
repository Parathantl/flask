from flask import Blueprint, current_app, request, jsonify
from flask_jwt import current_identity

from haystack.nodes import DensePassageRetriever
from haystack.utils import fetch_archive_from_http
from haystack.document_stores import InMemoryDocumentStore
from haystack.utils import convert_files_to_docs, fetch_archive_from_http, clean_wiki_text
from haystack.nodes import Seq2SeqGenerator

from haystack.document_stores import FAISSDocumentStore
from haystack.pipelines import GenerativeQAPipeline

query_routes = Blueprint("query", __name__, url_prefix="/api/query")

doc_dir = "./api/routes/content"
train_filename = "answersDPR.json"
dev_filename = "answersDPR.json"

query_model = "facebook/dpr-question_encoder-single-nq-base"
passage_model = "facebook/dpr-ctx_encoder-single-nq-base"

save_dir = "./api/routes/data/saved_models/dpr"

retrieverDensePassage = DensePassageRetriever(
    document_store=InMemoryDocumentStore(),
    query_embedding_model=query_model,
    passage_embedding_model=passage_model,
    max_seq_len_query=64,
    max_seq_len_passage=256,
)

retrieverDensePassage.train(
    data_dir=doc_dir,
    train_filename=train_filename,
    dev_filename=dev_filename,
    test_filename=dev_filename,
    n_epochs=1,
    batch_size=16,
    grad_acc_steps=8,
    save_dir=save_dir,
    evaluate_every=3000,
    embed_title=True,
    num_positives=1,
    num_hard_negatives=1,
)

document_store_1 = FAISSDocumentStore(faiss_index_factory_str="Flat")

# Let's first get some files that we want to use
docu_dir = "./api/routes/data/tutorial12"
s3_url = "https://bitbucket.org/parathant/rp-project/raw/bc3925e7dc8d5e5925b9be2668ba0438506e3a95/dataset.zip"
fetch_archive_from_http(url=s3_url, output_dir=docu_dir)

# Convert files to dicts
docs = convert_files_to_docs(dir_path=docu_dir, clean_func=clean_wiki_text, split_paragraphs=True)

# Now, let's write the dicts containing documents to our DB.
document_store_1.write_documents(docs)

reloaded_retriever = DensePassageRetriever.load(load_dir=save_dir, document_store=document_store_1)

document_store_1.update_embeddings(reloaded_retriever)

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