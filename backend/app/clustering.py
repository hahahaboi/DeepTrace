import numpy as np
import hashlib
import logging
from typing import List, Optional, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from sklearn.cluster import HDBSCAN

from . import models

logger = logging.getLogger("deeptrace.clustering")
logging.basicConfig(level=logging.INFO)

def generate_fallback_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Generates a deterministic pseudo-embedding vector derived from MD5 hashing of text
    when the sentence-transformers model is offline or network is restricted.
    """
    seed = int(hashlib.md5(text.encode('utf-8')).hexdigest()[:8], 16)
    np.random.seed(seed)
    vector = np.random.normal(0, 1, dim)
    # Normalize to unit length
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()

class EmbeddingClient:
    """
    Singleton client to manage the loading of the sentence-transformers model
    and generation of vector embeddings.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingClient, cls).__new__(cls, *args, **kwargs)
            cls._instance._model = None
            cls._instance._load_failed = False
        return cls._instance
        
    @property
    def model(self):
        if self._model is None and not self._load_failed:
            try:
                logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'...")
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"SentenceTransformer load failed ({e}). Falling back to deterministic vector generation.")
                self._load_failed = True
                self._model = False
        return self._model
        
    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
            
        m = self.model
        if m:
            try:
                embeddings = m.encode(texts)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"Encoding failed ({e}). Using fallback vector generation.")
                
        # Fallback for offline execution
        return [generate_fallback_embedding(t) for t in texts]


def cluster_failures(embeddings: List[List[float]], min_cluster_size: int = 2) -> List[int]:
    """
    Clusters a list of vector embeddings using HDBSCAN.
    
    Returns:
        List[int]: A list of cluster labels corresponding to each embedding.
                   Noise points are assigned a label of -1.
    """
    if len(embeddings) < min_cluster_size:
        logger.info(f"Fewer than {min_cluster_size} embeddings provided. All points treated as noise.")
        return [-1] * len(embeddings)
        
    X = np.array(embeddings)
    hdb = HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    labels = hdb.fit_predict(X)
    return labels.tolist()


def generate_cluster_metadata(failures: List[models.PipelineFailure]) -> Tuple[str, str]:
    """
    Algorithmic generation of failure cluster title and summary description.
    """
    job_names = [f.job_name for f in failures if f.job_name]
    step_names = [f.step_name for f in failures if f.step_name]
    reasons = [f.failure_reason for f in failures if f.failure_reason]
    
    common_job = Counter(job_names).most_common(1)[0][0] if job_names else "Unknown Job"
    common_step = f" / {Counter(step_names).most_common(1)[0][0]}" if step_names else ""
    title = f"Failure Cluster: {common_job}{common_step}"
    
    unique_reasons = list(set([r for r in reasons if r]))[:3]
    reasons_str = "; ".join(unique_reasons) if unique_reasons else "No specific error message extracted"
    summary = f"Group of {len(failures)} failures sharing similar log patterns. Representative samples: {reasons_str}"
    
    return title, summary


def process_and_cluster_failures(db: Session, min_cluster_size: int = 2) -> int:
    """
    End-to-end database failure processing pipeline:
    1. Fetches pipeline failures lacking log embeddings and generates them.
    2. Fetches all unclustered failures with embeddings.
    3. Groups similar failures using HDBSCAN.
    4. Computes cluster centroids (representative embeddings) and saves clusters in DB.
    5. Links failures to their respective cluster IDs.
    
    Returns:
        int: Number of new clusters created.
    """
    # Step 1: Generate missing embeddings
    unembedded_failures = db.query(models.PipelineFailure).filter(
        models.PipelineFailure.log_embedding == None,
        (models.PipelineFailure.log_summary != None) | (models.PipelineFailure.failure_reason != None)
    ).all()
    
    if unembedded_failures:
        logger.info(f"Generating embeddings for {len(unembedded_failures)} pipeline failures...")
        client = EmbeddingClient()
        texts = []
        for f in unembedded_failures:
            text = f"{f.job_name} {f.step_name or ''}: {f.failure_reason or ''}\n{f.log_summary or ''}".strip()
            texts.append(text)
            
        embeddings = client.embed(texts)
        for f, emb in zip(unembedded_failures, embeddings):
            f.log_embedding = emb
        db.commit()
        
    # Step 2: Fetch all unclustered failures
    unclustered_failures = db.query(models.PipelineFailure).filter(
        models.PipelineFailure.log_embedding != None,
        models.PipelineFailure.cluster_id == None
    ).all()
    
    if len(unclustered_failures) < min_cluster_size:
        logger.info(f"Not enough unclustered failures ({len(unclustered_failures)}) to cluster.")
        return 0
        
    embeddings = [f.log_embedding for f in unclustered_failures]
    
    # Step 3: Run clustering
    labels = cluster_failures(embeddings, min_cluster_size=min_cluster_size)
    
    # Map failures to their cluster labels
    label_to_failures = {}
    for f, label in zip(unclustered_failures, labels):
        if label == -1:
            continue
        label_to_failures.setdefault(label, []).append(f)
        
    new_clusters_count = 0
    
    # Step 4: Save clusters and link failures
    for label, failures in label_to_failures.items():
        title, summary = generate_cluster_metadata(failures)
        
        embs = np.array([f.log_embedding for f in failures])
        centroid = embs.mean(axis=0).tolist()
        
        cluster = models.FailureCluster(
            title=title,
            summary=summary,
            representative_embedding=centroid
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)
        
        for f in failures:
            f.cluster_id = cluster.id
        db.commit()
        
        new_clusters_count += 1
        logger.info(f"Created failure cluster {cluster.id}: '{cluster.title}' with {len(failures)} items.")
        
    return new_clusters_count
