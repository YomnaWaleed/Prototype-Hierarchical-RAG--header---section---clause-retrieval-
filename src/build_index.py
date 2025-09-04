from sentence_transformers import SentenceTransformer
import faiss, json
from pathlib import Path
from src.parse_headings import parse_numbered_headings

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def build_embeddings(chunks, model_name=EMB_MODEL):
    model = SentenceTransformer(model_name)
    texts = [c["content"] or c["title"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def build_faiss_index(chunks, embeddings, out_dir: str, index_name: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    d = embeddings.shape[1]
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    faiss.write_index(index, f"{out_dir}/{index_name}.index")

    # save metadata
    meta = {
        i: {
            "id": chunks[i]["id"],
            "title": chunks[i].get("title"),
            "level": chunks[i]["level"],
            "parent_id": chunks[i].get("parent_id"),
            "content": chunks[i].get("content"),  # مهم جدًا
        }
        for i in range(len(chunks))
    }
    Path(f"{out_dir}/{index_name}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved index + meta for {index_name}")
    return index


if __name__ == "__main__":
    md_dir = Path("../data/md")
    out_dir = Path("../outputs/indices")

    # process all md files
    for md_file in md_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        chunks = parse_numbered_headings(text)
        embeddings = build_embeddings(chunks)
        index_name = md_file.stem + "_clauses"
        build_faiss_index(chunks, embeddings, out_dir=out_dir, index_name=index_name)
