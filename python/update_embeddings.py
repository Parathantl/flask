from pydoc import doc
from haystack.document_stores import FAISSDocumentStore
from haystack.utils import convert_files_to_docs, fetch_archive_from_http, clean_wiki_text, print_answers

document_store = FAISSDocumentStore(faiss_index_factory_str="Flat")

# Let's first get some files that we want to use
docu_dir = "./api/routes/data/tutorial12"
s3_url = "https://bitbucket.org/parathant/rp-project/raw/ae286dd95c031cc4cdae3c20bc1ef8762f2b791a/dataset.zip"
fetch_archive_from_http(url=s3_url, output_dir=docu_dir)

# Convert files to dicts
docs = convert_files_to_docs(dir_path=docu_dir, clean_func=clean_wiki_text, split_paragraphs=True)
print(docs)
document_store.write_documents(docs)

