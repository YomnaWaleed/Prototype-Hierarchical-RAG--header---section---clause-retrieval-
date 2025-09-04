# hierarchical Retrieval
## headers -> sections -> clauses
import faiss, json
from sentence_transformers import SentenceTransformer
from pathlib import Path

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class HierarchicalRetriever:
    def __init__(self, indices_meta, emb_model=EMB_MODEL):
        self.indices = []
        self.metas = []
        for idx_path, meta_path in indices_meta:
            self.indices.append(faiss.read_index(idx_path))
            self.metas.append(json.loads(Path(meta_path).read_text(encoding="utf-8")))
        self.model = SentenceTransformer(emb_model)

    def _embed(self, query):
        v = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(v)
        return v

    def search_topk(self, query, k=5):
        v = self._embed(query)
        results = []
        for index, meta in zip(self.indices, self.metas):
            D, I = index.search(v, k)
            for idx, score in zip(I[0], D[0]):
                if idx == -1:
                    continue
                info = meta[str(idx)] if str(idx) in meta else meta[idx]
                results.append({"idx": idx, "score": float(score), **info})
        results = sorted(results, key=lambda x: -x["score"])
        return results[:k]

    def hierarchical_retrieve(self, query, k_header=3, k_section=3, k_clause=3):
        top = self.search_topk(query, k=max(k_header, k_section, k_clause))
        headers = [r for r in top if r["level"] == 1][:k_header]
        if not headers:
            headers = top[:k_header]

        final_clauses = []
        for h in headers:
            q_section = f"{query} context: {h.get('title')}"
            sections = self.search_topk(q_section, k=k_section)
            if sections:
                top_section = sections[0]
                q_clause = (
                    f"{query} context: {h.get('title')} > {top_section.get('title')}"
                )
                clauses = self.search_topk(q_clause, k=k_clause)
                final_clauses.extend(clauses)

        # deduplicate & sort
        seen = set()
        deduped = []
        for c in sorted(final_clauses, key=lambda x: -x["score"]):
            if c["idx"] in seen:
                continue
            seen.add(c["idx"])
            deduped.append(c)
        return {"headers": headers, "clauses": deduped[:k_clause]}


# usage
if __name__ == "__main__":
    indices_meta = [
        (
            "../outputs/indices/automotivespice_clauses.index",
            "../outputs/indices/automotivespice_clauses_meta.json",
        ),
        (
            "../outputs/indices/autosar_ecum_clauses.index",
            "../outputs/indices/autosar_ecum_clauses_meta.json",
        ),
    ]
    hr = HierarchicalRetriever(
        [
            (
                "../outputs/indices/automotivespice_clauses.index",
                "../outputs/indices/automotivespice_clauses_meta.json",
            ),
            (
                "../outputs/indices/autosar_ecum_clauses.index",
                "../outputs/indices/autosar_ecum_clauses_meta.json",
            ),
        ]
    )

res = hr.hierarchical_retrieve(
    "What does SYS.2 require?", k_header=2, k_section=2, k_clause=3
)

retrieved_texts = []
for clause in res["clauses"]:
    retrieved_texts.append(f"{clause['title']}\n{clause['content']}")

context = "\n\n".join(retrieved_texts)
print(context)
