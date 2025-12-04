"""Quick script to check the embedding dimension of Qwen3-Embedding-0.6B"""

from sentence_transformers import SentenceTransformer

print("Loading Qwen3-Embedding-0.6B model...")
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
dimension = model.get_sentence_embedding_dimension()

print(f"\nEmbedding dimension: {dimension}")
print(f"\nUpdate your .env file with:")
print(f"PINECONE_DIMENSION={dimension}")

