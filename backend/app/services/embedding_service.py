import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any


class EmbeddingService:
    """Generate and manage embeddings for column matching"""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

    def generate_column_embeddings(self, columns: List[Dict[str, Any]]) -> np.ndarray:
        """Generate embeddings for column descriptions"""
        texts = []
        for col in columns:
            # Create rich description for embedding
            desc = f"{col['name']} ({col['dtype']})"

            # Add example values for context
            if 'stats' in col:
                if 'top_values' in col['stats'] and col['stats']['top_values']:
                    top_vals = [str(v[0]) for v in col['stats']['top_values'][:3]]
                    desc += f" examples: {', '.join(top_vals)}"
                elif 'min' in col['stats'] and 'max' in col['stats']:
                    desc += f" range: {col['stats']['min']} to {col['stats']['max']}"

            texts.append(desc)

        embeddings = self.model.encode(texts)
        return embeddings

    def save_embeddings(self, embeddings: np.ndarray, path: str):
        """Save embeddings as binary file"""
        num_columns, dim = embeddings.shape

        with open(path, 'wb') as f:
            # Header
            f.write(num_columns.to_bytes(4, 'little'))
            f.write(dim.to_bytes(4, 'little'))

            # Embeddings (float32)
            f.write(embeddings.astype(np.float32).tobytes())

    def load_embeddings(self, path: str) -> np.ndarray:
        """Load embeddings from binary file"""
        with open(path, 'rb') as f:
            num_columns = int.from_bytes(f.read(4), 'little')
            dim = int.from_bytes(f.read(4), 'little')

            # Read all embeddings at once
            emb_bytes = f.read(num_columns * dim * 4)  # float32 = 4 bytes
            embeddings = np.frombuffer(emb_bytes, dtype=np.float32)
            embeddings = embeddings.reshape(num_columns, dim)

            return embeddings

    def search_similar_columns(self, query: str, embedding_path: str,
                                schema: dict, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most relevant columns for NL query"""
        query_emb = self.model.encode([query])[0]
        column_embs = self.load_embeddings(embedding_path)

        # Cosine similarity
        similarities = np.dot(column_embs, query_emb) / (
            np.linalg.norm(column_embs, axis=1) * np.linalg.norm(query_emb)
        )

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [
            {
                'column': schema['columns'][i],
                'similarity': float(similarities[i])
            }
            for i in top_indices
        ]
