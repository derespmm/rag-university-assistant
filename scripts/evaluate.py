# Evaluation script for measuring RAG quality. Loads a set of known
# question-answer pairs from data/sample_queries/, runs each question through
# the pipeline, and scores the results for retrieval accuracy and answer
# correctness. Used to tune chunk size, overlap, and the number of retrieved
# chunks (k).
