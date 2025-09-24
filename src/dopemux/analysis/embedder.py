"""Document embedding and indexing system with Voyage AI support."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        MilvusClient,
        connections,
        utility,
    )

    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    print("⚠️ Milvus not available. Install with: pip install pymilvus")

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB not available. Install with: pip install chromadb")

try:
    import voyageai

    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False
    print("⚠️ Voyage AI not available. Install with: pip install voyageai")

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available. Install with: pip install openai")


@dataclass
class EmbeddedUnit:
    """Represents a unit with its embedding."""

    unit_id: str
    doc_uri: str
    doc_type: str
    entity_type: str
    title: str
    text: str
    embedding: List[float]
    created_at: Optional[str]
    tags: List[str]
    similarity_hash: str


@dataclass
class DuplicateCluster:
    """Represents a cluster of duplicate or near-duplicate units."""

    cluster_id: str
    primary_unit_id: str
    duplicate_unit_ids: List[str]
    similarity_scores: List[float]
    resolution: str  # 'keep_primary', 'merge', 'manual_review'


class DocumentEmbedder:
    """Handles embedding generation, indexing, and similarity detection using Voyage Context-3 and Milvus."""

    def __init__(
        self,
        model_name: str = "voyage-context-3",
        similarity_threshold: float = 0.92,
        jaccard_threshold: float = 0.82,
        milvus_host: str = "localhost",
        milvus_port: str = "19530",
        milvus_uri: Optional[str] = None,
    ):
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.jaccard_threshold = jaccard_threshold
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.milvus_uri = milvus_uri  # File-based URI for Milvus Lite
        self.embeddings_db = None
        self.embedded_units: List[EmbeddedUnit] = []
        self.duplicate_clusters: List[DuplicateCluster] = []
        self.collection = None
        self.milvus_client = None  # For Milvus Lite client

        # Initialize vector database (prefer Milvus, fallback to ChromaDB)
        if MILVUS_AVAILABLE:
            self._init_milvus()
        elif CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            print("⚠️ No vector database available. Install pymilvus or chromadb.")

        # Initialize embedding client based on model
        if model_name.startswith("voyage"):
            if VOYAGE_AVAILABLE:
                self.voyage_client = voyageai.Client()
                self.embedding_provider = "voyage"
                print(f"✅ Using Voyage AI with model: {model_name}")
            else:
                raise ImportError(
                    "Voyage AI not available. Install with: pip install voyageai"
                )
        else:
            if OPENAI_AVAILABLE:
                self.openai_client = openai.OpenAI()
                self.embedding_provider = "openai"
                print(f"✅ Using OpenAI with model: {model_name}")
            else:
                raise ImportError(
                    "OpenAI not available. Install with: pip install openai"
                )

    def _init_milvus(self) -> None:
        """Initialize Milvus for vector storage (supports both server and Lite modes)."""
        try:
            if self.milvus_uri:
                # Use Milvus Lite with file-based storage
                self.milvus_client = MilvusClient(self.milvus_uri)
                print(f"✅ Connected to Milvus Lite at {self.milvus_uri}")
                self._setup_milvus_lite_collection()
            else:
                # Use traditional server-based Milvus
                connections.connect(
                    "default", host=self.milvus_host, port=self.milvus_port
                )
                print(
                    f"✅ Connected to Milvus server at {self.milvus_host}:{self.milvus_port}"
                )
                self._setup_milvus_server_collection()

        except Exception as e:
            print(f"❌ Error setting up Milvus: {e}")
            if CHROMADB_AVAILABLE:
                print("🔄 Falling back to ChromaDB...")
                self._init_chromadb()
            else:
                raise e

    def _setup_milvus_lite_collection(self):
        """Set up collection for Milvus Lite."""
        collection_name = "document_units"

        # Check if collection exists
        collections = self.milvus_client.list_collections()
        if collection_name not in collections:
            # Create collection schema
            schema = {
                "fields": [
                    {
                        "name": "id",
                        "type": "VarChar",
                        "max_length": 255,
                        "is_primary": True,
                    },
                    {
                        "name": "vector",
                        "type": "FloatVector",
                        "dim": 1024,
                    },  # voyage-context-3
                    {"name": "doc_uri", "type": "VarChar", "max_length": 500},
                    {"name": "doc_type", "type": "VarChar", "max_length": 100},
                    {"name": "title", "type": "VarChar", "max_length": 500},
                    {"name": "content", "type": "VarChar", "max_length": 65535},
                    {"name": "tags", "type": "VarChar", "max_length": 1000},
                ],
                "index_params": {
                    "index_type": "HNSW",
                    "metric_type": "COSINE",
                    "params": {"M": 16, "efConstruction": 256},
                },
            }

            self.milvus_client.create_collection(
                collection_name=collection_name,
                dimension=1024,  # voyage-context-3 dimension
                auto_id=False,
            )
            print(f"✅ Created Milvus Lite collection: {collection_name}")
        else:
            print(f"✅ Using existing Milvus Lite collection: {collection_name}")

        self.collection_name = collection_name

    def _setup_milvus_server_collection(self):
        """Set up collection for traditional Milvus server."""
        collection_name = "document_units"

        # Check if collection exists
        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
            print(f"✅ Using existing Milvus collection: {collection_name}")
        else:
            # Create new collection
            fields = [
                FieldSchema(
                    name="unit_id",
                    dtype=DataType.VARCHAR,
                    max_length=100,
                    is_primary=True,
                ),
                FieldSchema(
                    name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024
                ),  # Voyage Context-3 is 1024-dim
                FieldSchema(name="doc_uri", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="entity_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(
                    name="similarity_hash", dtype=DataType.VARCHAR, max_length=100
                ),
            ]

            schema = CollectionSchema(
                fields, "Document processing units with embeddings"
            )
            self.collection = Collection(collection_name, schema)

            # Create index for efficient similarity search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self.collection.create_index("embedding", index_params)
            print(f"✅ Created Milvus collection: {collection_name}")

        # Load collection for search
        self.collection.load()

    def _init_chromadb(self) -> None:
        """Initialize ChromaDB for vector storage."""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path="build/vector_db", settings=Settings(anonymized_telemetry=False)
            )

            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="document_units", metadata={"hnsw:space": "cosine"}
            )

            print("✅ ChromaDB initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None

    def embed_atomic_units(self, units_file: str) -> List[EmbeddedUnit]:
        """Generate embeddings for atomic units using Voyage Context-3."""
        print(f"🔮 Generating embeddings from {units_file} using {self.model_name}")

        if not Path(units_file).exists():
            print(f"⚠️ File {units_file} not found")
            return []

        # Load atomic units
        units = []
        with open(units_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    units.append(json.loads(line))

        print(f"📊 Processing {len(units)} units for embedding")

        # Process units in batches (Voyage AI has different batch limits)
        batch_size = 50 if self.embedding_provider == "voyage" else 100
        for i in range(0, len(units), batch_size):
            batch = units[i : i + batch_size]
            self._process_batch(batch)
            print(
                f"✅ Processed batch {i//batch_size + 1}/{(len(units)-1)//batch_size + 1}"
            )

        print(f"🎯 Generated {len(self.embedded_units)} embeddings")
        return self.embedded_units

    def _process_batch(self, units: List[Dict]) -> None:
        """Process a batch of units for embedding."""
        # Prepare texts for embedding
        texts = []
        unit_data = []

        for unit in units:
            # Create embedding text by combining title and content
            embedding_text = self._prepare_embedding_text(unit)
            texts.append(embedding_text)
            unit_data.append(unit)

        try:
            # Generate embeddings based on provider
            if self.embedding_provider == "voyage":
                embeddings = self._generate_voyage_embeddings(texts)
            else:
                embeddings = self._generate_openai_embeddings(texts)

            # Process embeddings
            for i, embedding in enumerate(embeddings):
                unit = unit_data[i]

                # Create embedded unit
                embedded_unit = EmbeddedUnit(
                    unit_id=unit["unit_id"],
                    doc_uri=unit["doc_uri"],
                    doc_type=unit["doc_type"],
                    entity_type=unit["entity_type"],
                    title=unit["title"],
                    text=unit["text"],
                    embedding=embedding,
                    created_at=unit.get("created_at"),
                    tags=unit.get("tags", []),
                    similarity_hash=self._generate_similarity_hash(unit["text"]),
                )

                self.embedded_units.append(embedded_unit)

                # Store in vector database
                if self.collection:
                    self._store_in_vectordb(embedded_unit)

        except Exception as e:
            print(f"⚠️ Error generating embeddings: {e}")

    def _generate_voyage_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Voyage AI."""
        try:
            # Voyage Context-3 supports up to 32K context length
            response = self.voyage_client.embed(
                texts=texts,
                model=self.model_name,
                input_type="document",  # Use 'document' for indexing, 'query' for search
            )

            return [embedding for embedding in response.embeddings]

        except Exception as e:
            print(f"⚠️ Voyage AI embedding failed: {e}")
            raise

    def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI (fallback)."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.model_name, input=texts
            )

            return [embedding_data.embedding for embedding_data in response.data]

        except Exception as e:
            print(f"⚠️ OpenAI embedding failed: {e}")
            raise

    def _prepare_embedding_text(self, unit: Dict) -> str:
        """Prepare text for embedding generation with Voyage Context-3 optimization."""
        # Combine title and text with context
        title = unit.get("title", "")
        text = unit.get("text", "")
        doc_type = unit.get("doc_type", "")
        entity_type = unit.get("entity_type", "")
        tags = unit.get("tags", [])

        # Create structured text for embedding
        embedding_parts = []

        if title:
            embedding_parts.append(f"Title: {title}")

        if doc_type:
            embedding_parts.append(f"Document Type: {doc_type}")

        if entity_type:
            embedding_parts.append(f"Entity Type: {entity_type}")

        if tags:
            embedding_parts.append(f"Tags: {', '.join(tags)}")

        if text:
            # Voyage Context-3 supports up to 32K tokens (much larger than OpenAI)
            max_chars = 25000  # More generous limit for Voyage
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            embedding_parts.append(f"Content: {text}")

        return "\\n".join(embedding_parts)

    def _generate_similarity_hash(self, text: str) -> str:
        """Generate MinHash for Jaccard similarity comparison."""
        # Implement MinHash for better fuzzy similarity detection
        # This is a simplified version - could use datasketch library for full MinHash
        normalized_text = text.lower().strip()
        import re

        # Create shingles (n-grams) for better similarity detection
        words = re.findall(r"\\b\\w+\\b", normalized_text)
        shingles = set()

        # Create 3-grams of words
        for i in range(len(words) - 2):
            shingle = " ".join(words[i : i + 3])
            shingles.add(shingle)

        # Sort shingles for consistent hashing
        sorted_shingles = sorted(list(shingles))

        # Take first 20 shingles for hash
        combined = " ".join(sorted_shingles[:20])
        return hashlib.md5(combined.encode()).hexdigest()

    def _store_in_vectordb(self, embedded_unit: EmbeddedUnit) -> None:
        """Store embedded unit in vector database (Milvus or ChromaDB)."""
        if not self.collection:
            return

        try:
            if MILVUS_AVAILABLE and hasattr(self.collection, "insert"):
                # Milvus storage
                data = [
                    {
                        "unit_id": embedded_unit.unit_id,
                        "embedding": embedded_unit.embedding,
                        "doc_uri": embedded_unit.doc_uri,
                        "doc_type": embedded_unit.doc_type,
                        "entity_type": embedded_unit.entity_type,
                        "title": embedded_unit.title,
                        "text": embedded_unit.text[:10000],  # Truncate if too long
                        "created_at": embedded_unit.created_at or "",
                        "tags": ",".join(embedded_unit.tags),
                        "similarity_hash": embedded_unit.similarity_hash,
                    }
                ]

                self.collection.insert(data)
                self.collection.flush()  # Ensure data is persisted

            else:
                # ChromaDB storage (fallback)
                metadata = {
                    "doc_uri": embedded_unit.doc_uri,
                    "doc_type": embedded_unit.doc_type,
                    "entity_type": embedded_unit.entity_type,
                    "title": embedded_unit.title,
                    "created_at": embedded_unit.created_at or "",
                    "tags": ",".join(embedded_unit.tags),
                    "similarity_hash": embedded_unit.similarity_hash,
                }

                self.collection.add(
                    ids=[embedded_unit.unit_id],
                    embeddings=[embedded_unit.embedding],
                    documents=[embedded_unit.text],
                    metadatas=[metadata],
                )

        except Exception as e:
            print(f"⚠️ Error storing in vector DB: {e}")

    def detect_duplicates(self) -> List[DuplicateCluster]:
        """Detect duplicate and near-duplicate units using both cosine and Jaccard similarity."""
        print("🔍 Detecting duplicates using cosine similarity and MinHash...")

        processed_units = set()
        clusters = []

        for i, unit in enumerate(self.embedded_units):
            if unit.unit_id in processed_units:
                continue

            # Find similar units using both methods
            similar_units = self._find_similar_units(unit, self.embedded_units[i + 1 :])

            if similar_units:
                # Create cluster
                cluster_id = f"cluster_{len(clusters):04d}"

                # Determine primary unit (newest and most specific)
                all_units = [unit] + similar_units
                primary_unit = self._select_primary_unit(all_units)

                duplicate_ids = [
                    u.unit_id for u in all_units if u.unit_id != primary_unit.unit_id
                ]
                similarity_scores = [
                    self._calculate_similarity(primary_unit, u) for u in all_units[1:]
                ]

                cluster = DuplicateCluster(
                    cluster_id=cluster_id,
                    primary_unit_id=primary_unit.unit_id,
                    duplicate_unit_ids=duplicate_ids,
                    similarity_scores=similarity_scores,
                    resolution=self._determine_resolution(similarity_scores),
                )

                clusters.append(cluster)

                # Mark all units as processed
                for unit_in_cluster in all_units:
                    processed_units.add(unit_in_cluster.unit_id)
            else:
                # Mark single unit as processed
                processed_units.add(unit.unit_id)

        self.duplicate_clusters = clusters
        print(f"🎯 Found {len(clusters)} duplicate clusters")
        return clusters

    def _find_similar_units(
        self, target_unit: EmbeddedUnit, candidate_units: List[EmbeddedUnit]
    ) -> List[EmbeddedUnit]:
        """Find units similar to the target unit using both cosine and Jaccard similarity."""
        similar_units = []

        for candidate in candidate_units:
            # Calculate cosine similarity
            cosine_similarity = self._calculate_similarity(target_unit, candidate)

            # Calculate Jaccard similarity using MinHash approximation
            jaccard_similarity = self._calculate_jaccard_similarity(
                target_unit, candidate
            )

            # Check similarity hash for faster fuzzy matching
            hash_match = target_unit.similarity_hash == candidate.similarity_hash

            # Apply thresholds from original playbook
            if (
                cosine_similarity >= self.similarity_threshold
                or jaccard_similarity >= self.jaccard_threshold
                or hash_match
            ):
                similar_units.append(candidate)

        return similar_units

    def _calculate_jaccard_similarity(
        self, unit1: EmbeddedUnit, unit2: EmbeddedUnit
    ) -> float:
        """Calculate Jaccard similarity using simplified approach."""
        # Extract words from both texts
        import re

        words1 = set(re.findall(r"\\b\\w+\\b", unit1.text.lower()))
        words2 = set(re.findall(r"\\b\\w+\\b", unit2.text.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_similarity(self, unit1: EmbeddedUnit, unit2: EmbeddedUnit) -> float:
        """Calculate cosine similarity between two embedded units."""
        if not unit1.embedding or not unit2.embedding:
            return 0.0

        # Convert to numpy arrays
        vec1 = np.array(unit1.embedding)
        vec2 = np.array(unit2.embedding)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _select_primary_unit(self, units: List[EmbeddedUnit]) -> EmbeddedUnit:
        """Select the primary unit from a cluster (newest and most specific)."""
        # Score units based on recency and specificity weights from playbook
        scored_units = []

        for unit in units:
            score = 0

            # Recency score (if date available)
            if unit.created_at:
                try:
                    from datetime import datetime

                    date = datetime.fromisoformat(
                        unit.created_at.replace("Z", "+00:00")
                    )
                    days_old = (datetime.now() - date).days
                    recency_score = max(0, 365 - days_old) / 365  # Higher for newer
                    score += recency_score * 0.3
                except:
                    pass

            # Specificity score using original playbook weights
            specificity_score = self._calculate_specificity_score(unit)
            score += specificity_score * 0.7

            scored_units.append((score, unit))

        # Return unit with highest score
        scored_units.sort(key=lambda x: x[0], reverse=True)
        return scored_units[0][1]

    def _calculate_specificity_score(self, unit: EmbeddedUnit) -> float:
        """Calculate specificity score using EXACT original playbook weights."""
        import re

        # Original playbook weights: ids 0.3, numbers 0.2, code/table 0.3, section depth 0.2
        score = 0.0
        text = unit.text

        # IDs presence (weight: 0.3) - Look for explicit IDs
        id_patterns = [
            r"\\b(ADR|RFC|FEATURE)[-_]\\d+\\b",
            r"\\b[A-Z]{2,}-\\d+\\b",  # General ID patterns
            r"\\b(COMP|SYS|RES)[-_][A-F0-9]{8}\\b",  # Generated IDs
        ]

        has_ids = False
        for pattern in id_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                has_ids = True
                break

        if has_ids:
            score += 0.3

        # Numbers presence (weight: 0.2) - Proportional to number density
        numbers = re.findall(r"\\b\\d+\\b", text)
        if len(text) > 0:
            number_density = len(numbers) / max(len(text.split()), 1)
            # Normalize: high number density gets full 0.2 weight
            normalized_numbers = min(number_density * 50, 1.0)  # Scale factor
            score += normalized_numbers * 0.2

        # Code/table presence (weight: 0.3) - Structured content
        has_structured_content = False

        # Code blocks
        if "```" in text or re.search(r"`[^`]+`", text):
            has_structured_content = True

        # Tables (markdown or other formats)
        if ("|" in text and text.count("|") > 2) or re.search(r"\\n\\s*\\|", text):
            has_structured_content = True

        # JSON/XML/YAML structures
        if any(
            marker in text for marker in ["{", "[", "<", ":", "yaml", "json", "xml"]
        ):
            has_structured_content = True

        if has_structured_content:
            score += 0.3

        # Section depth (weight: 0.2) - Based on heading hierarchy depth
        section_depth_score = 0.0

        # Check section path depth
        section_path = getattr(unit, "section_path", []) or []
        if section_path:
            # Deeper sections are more specific
            depth = len(section_path)
            section_depth_score = min(
                depth / 5.0, 1.0
            )  # Normalize: 5+ levels = max score

        # Check heading depth in title
        title = unit.title or ""
        heading_level = 0
        if title.startswith("#"):
            heading_level = len(title) - len(title.lstrip("#"))
        elif re.search(r"^\\d+(\\.\\d+)*\\s", title):  # Numbered sections like "5.2.1"
            parts = re.findall(r"\\d+", title.split()[0])
            heading_level = len(parts)

        if heading_level > 0:
            title_depth_score = min(
                heading_level / 4.0, 1.0
            )  # Normalize: 4+ levels = max score
            section_depth_score = max(section_depth_score, title_depth_score)

        score += section_depth_score * 0.2

        # Ensure score doesn't exceed 1.0 (all weights: 0.3 + 0.2 + 0.3 + 0.2 = 1.0 max)
        return min(score, 1.0)

    def _determine_resolution(self, similarity_scores: List[float]) -> str:
        """Determine how to resolve duplicate cluster."""
        if not similarity_scores:
            return "keep_primary"

        avg_similarity = sum(similarity_scores) / len(similarity_scores)

        if avg_similarity >= 0.98:
            return "keep_primary"  # Very high similarity, safe to dedupe
        elif avg_similarity >= 0.95:
            return "merge"  # High similarity, consider merging
        else:
            return "manual_review"  # Medium similarity, needs review

    def query_similar_units(
        self, query_text: str, k: int = 15, filters: Optional[Dict] = None
    ) -> List[Tuple[EmbeddedUnit, float]]:
        """Query for similar units using vector search (top-k 8-15 as per playbook)."""
        if not self.collection:
            print("⚠️ Vector search not available")
            return []

        try:
            # Generate embedding for query based on provider
            if self.embedding_provider == "voyage":
                response = self.voyage_client.embed(
                    texts=[query_text],
                    model=self.model_name,
                    input_type="query",  # Use 'query' for search
                )
                query_embedding = response.embeddings[0]
            else:
                response = self.openai_client.embeddings.create(
                    model=self.model_name, input=[query_text]
                )
                query_embedding = response.data[0].embedding

            similar_units = []

            if MILVUS_AVAILABLE and hasattr(self.collection, "search"):
                # Milvus search
                search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

                # Build filter expression for Milvus
                filter_expr = None
                if filters:
                    filter_conditions = []
                    for key, value in filters.items():
                        if isinstance(value, dict) and "$in" in value:
                            # Handle $in filter (e.g., entity_type in [list])
                            values_str = ", ".join([f'"{v}"' for v in value["$in"]])
                            filter_conditions.append(f"{key} in [{values_str}]")
                        else:
                            filter_conditions.append(f'{key} == "{value}"')

                    if filter_conditions:
                        filter_expr = " and ".join(filter_conditions)

                # Perform search
                results = self.collection.search(
                    data=[query_embedding],
                    anns_field="embedding",
                    param=search_params,
                    limit=k,
                    expr=filter_expr,
                    output_fields=[
                        "unit_id",
                        "doc_uri",
                        "doc_type",
                        "entity_type",
                        "title",
                        "text",
                        "created_at",
                        "tags",
                    ],
                )

                # Convert Milvus results to EmbeddedUnit objects
                for hit in results[0]:
                    # Find the embedded unit or create from hit data
                    unit = next(
                        (
                            u
                            for u in self.embedded_units
                            if u.unit_id == hit.entity.get("unit_id")
                        ),
                        None,
                    )

                    if not unit:
                        # Create EmbeddedUnit from search result
                        unit = EmbeddedUnit(
                            unit_id=hit.entity.get("unit_id", ""),
                            doc_uri=hit.entity.get("doc_uri", ""),
                            doc_type=hit.entity.get("doc_type", ""),
                            entity_type=hit.entity.get("entity_type", ""),
                            title=hit.entity.get("title", ""),
                            text=hit.entity.get("text", ""),
                            embedding=[],  # Don't need full embedding for search results
                            created_at=hit.entity.get("created_at"),
                            tags=(
                                hit.entity.get("tags", "").split(",")
                                if hit.entity.get("tags")
                                else []
                            ),
                            similarity_hash="",
                        )

                    similarity = (
                        1.0 - hit.distance
                    )  # Milvus returns distance, convert to similarity
                    similar_units.append((unit, similarity))

            else:
                # ChromaDB search (fallback)
                where_clause = {}
                if filters:
                    for key, value in filters.items():
                        where_clause[key] = value

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,  # Use 8-15 range as per playbook
                    where=where_clause if where_clause else None,
                )

                # Convert ChromaDB results to EmbeddedUnit objects
                if results["ids"] and results["ids"][0]:
                    for i, unit_id in enumerate(results["ids"][0]):
                        # Find the embedded unit
                        unit = next(
                            (u for u in self.embedded_units if u.unit_id == unit_id),
                            None,
                        )
                        if unit:
                            distance = (
                                results["distances"][0][i]
                                if results["distances"]
                                else 0
                            )
                            similarity = (
                                1.0 - distance
                            )  # Convert distance to similarity
                            similar_units.append((unit, similarity))

            return similar_units

        except Exception as e:
            print(f"⚠️ Error querying similar units: {e}")
            return []

    def save_embeddings(self, output_path: str = "build/embeddings.jsonl") -> None:
        """Save embedded units to file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for unit in self.embedded_units:
                unit_dict = {
                    "unit_id": unit.unit_id,
                    "doc_uri": unit.doc_uri,
                    "doc_type": unit.doc_type,
                    "entity_type": unit.entity_type,
                    "title": unit.title,
                    "text": unit.text,
                    "embedding": unit.embedding,
                    "created_at": unit.created_at,
                    "tags": unit.tags,
                    "similarity_hash": unit.similarity_hash,
                }
                f.write(json.dumps(unit_dict, ensure_ascii=False) + "\\n")

        print(f"💾 Saved {len(self.embedded_units)} embeddings to {output_path}")

    def save_duplicate_clusters(
        self, output_path: str = "build/reports/duplicate_clusters.json"
    ) -> None:
        """Save duplicate clusters to file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        clusters_data = []
        for cluster in self.duplicate_clusters:
            clusters_data.append(
                {
                    "cluster_id": cluster.cluster_id,
                    "primary_unit_id": cluster.primary_unit_id,
                    "duplicate_unit_ids": cluster.duplicate_unit_ids,
                    "similarity_scores": cluster.similarity_scores,
                    "resolution": cluster.resolution,
                }
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(clusters_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(clusters_data)} duplicate clusters to {output_path}")

    def get_embedding_stats(self) -> Dict[str, any]:
        """Get statistics about embeddings and duplicates."""
        stats = {
            "total_embedded_units": len(self.embedded_units),
            "duplicate_clusters": len(self.duplicate_clusters),
            "total_duplicates": sum(
                len(cluster.duplicate_unit_ids) for cluster in self.duplicate_clusters
            ),
            "resolution_breakdown": {},
            "doc_type_distribution": {},
            "entity_type_distribution": {},
            "embedding_model": self.model_name,
            "similarity_threshold": self.similarity_threshold,
            "jaccard_threshold": self.jaccard_threshold,
        }

        # Resolution breakdown
        for cluster in self.duplicate_clusters:
            resolution = cluster.resolution
            stats["resolution_breakdown"][resolution] = (
                stats["resolution_breakdown"].get(resolution, 0) + 1
            )

        # Type distributions
        for unit in self.embedded_units:
            doc_type = unit.doc_type
            entity_type = unit.entity_type

            stats["doc_type_distribution"][doc_type] = (
                stats["doc_type_distribution"].get(doc_type, 0) + 1
            )
            stats["entity_type_distribution"][entity_type] = (
                stats["entity_type_distribution"].get(entity_type, 0) + 1
            )

        return stats
