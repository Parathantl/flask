from haystack.nodes import DensePassageRetriever
from haystack.document_stores import InMemoryDocumentStore

doc_dir = "/home/ubuntu/flask/python/content"
train_filename = "trainDPR.json"
dev_filename = "testDPR.json"

query_model = "facebook/dpr-question_encoder-single-nq-base"
passage_model = "facebook/dpr-ctx_encoder-single-nq-base"

save_dir = "/home/ubuntu/flask/python/saved_models"

## Initialize DPR model

retrieverDensePassage = DensePassageRetriever(
    document_store=InMemoryDocumentStore(),
    query_embedding_model=query_model,
    passage_embedding_model=passage_model,
    max_seq_len_query=64,
    max_seq_len_passage=256,
)

"""## Training
"""

# Start training our model and save it when it is finished

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
