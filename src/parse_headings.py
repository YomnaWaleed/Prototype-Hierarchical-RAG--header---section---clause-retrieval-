import re, uuid
from typing import List, Dict
from pathlib import Path

numbered_header_re = re.compile(
    r"^\s*(\d+(?:\.\d+){0,3})\s*\.?\s+(?P<title>[A-Z][^\n]{3,200})$", re.M
)

code_header_re = re.compile(r"^(?P<code>[A-Z]{2,5}\.\d+)\s+(?P<title>.+)$", re.M)


def parse_numbered_headings(text: str) -> List[Dict]:
    """
    Parse text into hierarchical chunks with full content under each header.
    """
    matches = list(numbered_header_re.finditer(text))
    if not matches:
        matches = list(code_header_re.finditer(text))

    if not matches:
        return [
            {
                "id": str(uuid.uuid4()),
                "level": 1,
                "title": "Document",
                "parent_id": None,
                "content": text.strip(),
            }
        ]

    chunks = []
    boundaries = [
        (m.start(), m.end(), m.group(0), m.groupdict().get("title") or m.group(0))
        for m in matches
    ]
    boundaries.append((len(text), len(text), "", ""))

    for i in range(len(boundaries) - 1):
        header_line = boundaries[i][2]
        title = boundaries[i][3].strip()
        content = text[boundaries[i][1] : boundaries[i + 1][0]].strip()
        num_match = re.match(r"^\s*(\d+(?:\.\d+)*)", header_line)
        level = num_match.group(1).count(".") + 1 if num_match else 2
        chunks.append(
            {
                "id": str(uuid.uuid4()),
                "level": level,
                "title": title,
                "parent_num": num_match.group(1) if num_match else None,
                "content": content,
            }
        )

    for c in chunks:
        if c.get("parent_num"):
            parts = c["parent_num"].split(".")
            found_parent = None
            for candidate in reversed(chunks):
                pnum = candidate.get("parent_num")
                if pnum and pnum == ".".join(parts[:-1]):
                    found_parent = candidate["id"]
                    break
            c["parent_id"] = found_parent
        else:
            c["parent_id"] = None

    return chunks


def save_markdown(chunks: List[Dict], out_md_path: Path):
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for c in chunks:
        header_prefix = "#" * c["level"]
        lines.append(f"{header_prefix} {c['title']}\n")
        lines.append(c["content"] + "\n")
    out_md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved Markdown: {out_md_path}")


txt_files = Path("../data/txt").glob("*.txt")
for txt_file in txt_files:
    text = txt_file.read_text(encoding="utf-8")
    chunks = parse_numbered_headings(text)
    md_path = Path("../data/md") / txt_file.with_suffix(".md").name
    save_markdown(chunks, md_path)
