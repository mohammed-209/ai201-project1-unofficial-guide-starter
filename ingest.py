"""
Milestone 3 — Ingestion and chunking for The Unofficial Guide.

Loads the semi-structured professor-review files in docs/, parses their
header metadata, and splits each file into chunks following the strategy in
planning.md:

  - one Summary chunk
  - one chunk per Review block
  - one Common Themes chunk
  - one Useful Student Advice chunk

The professor name (which only appears in the file header, never inside the
individual Review blocks) and the source filename are prepended to every chunk's
text so each chunk is self-anchoring once embedded. Rich metadata is attached to
every chunk for later filtering and citation.

This milestone does NOT embed, retrieve, or call any LLM — it only builds and
inspects chunks.
"""
import re
from pathlib import Path

DOCS_PATH = Path(__file__).parent / "docs"

# The four top-level section markers in every review file. Each appears on its
# own line. "Review:" appears many times (one per student review); the others
# appear once.
SECTION_MARKERS = ("Summary:", "Review:", "Common Themes:", "Useful Student Advice:")

# chunk_type label for each non-Review marker.
SECTION_TYPE = {
    "Summary:": "summary",
    "Common Themes:": "common_themes",
    "Useful Student Advice:": "useful_advice",
}

# Header fields we extract (label in file -> metadata key).
HEADER_FIELDS = {
    "Source": "source_url",
    "Professor": "professor",
    "Department": "department",
    "School": "school",
    "Overall Rating": "overall_rating",
    "Difficulty": "difficulty",
    "Would Take Again": "would_take_again",
}


def clean_text(text):
    """Light cleanup: normalize newlines, trim trailing spaces, collapse blank runs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace on each line.
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Collapse 3+ consecutive newlines down to a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(docs_path=DOCS_PATH):
    """Read every .txt file in docs/ and return a list of {filename, raw_text}."""
    documents = []
    for path in sorted(Path(docs_path).glob("*.txt")):
        documents.append(
            {
                "filename": path.name,
                "raw_text": clean_text(path.read_text(encoding="utf-8")),
            }
        )
    return documents


def parse_header(text):
    """
    Pull the header key/value lines that appear before the first 'Summary:'.

    Numeric fields ('4.1 / 5', '82%') are converted to floats/ints where
    possible; everything else is kept as a trimmed string. Missing fields are
    simply omitted.
    """
    summary_idx = text.find("\nSummary:")
    header_region = text if summary_idx == -1 else text[:summary_idx]

    meta = {}
    for label, key in HEADER_FIELDS.items():
        match = re.search(rf"^{re.escape(label)}:\s*(.+)$", header_region, re.MULTILINE)
        if not match:
            continue
        raw = match.group(1).strip()
        if key in ("overall_rating", "difficulty"):
            num = re.search(r"[\d.]+", raw)
            meta[key] = float(num.group()) if num else raw
        elif key == "would_take_again":
            num = re.search(r"\d+", raw)
            meta[key] = int(num.group()) if num else raw
        else:
            meta[key] = raw
    return meta


def split_sections(text):
    """
    Split the document body into ordered (marker, block_text) pairs.

    A new section begins on any line that is exactly one of SECTION_MARKERS.
    Everything before the first marker (the header) is discarded here — header
    parsing is handled separately by parse_header().
    """
    sections = []
    current_marker = None
    buffer = []

    for line in text.split("\n"):
        if line.strip() in SECTION_MARKERS:
            if current_marker is not None:
                sections.append((current_marker, "\n".join(buffer).strip()))
            current_marker = line.strip()
            buffer = []
        elif current_marker is not None:
            buffer.append(line)

    if current_marker is not None:
        sections.append((current_marker, "\n".join(buffer).strip()))

    return sections


def _extract_course(review_block):
    """Return the 'Course:' value from a Review block, or None if absent."""
    match = re.search(r"^Course:\s*(.+)$", review_block, re.MULTILINE)
    return match.group(1).strip() if match else None


def _slug(filename):
    """afsoon_zowj_reviews.txt -> afsoon_zowj_reviews"""
    return Path(filename).stem


def chunk_document(doc):
    """
    Turn one loaded document into a list of chunk dicts.

    Each chunk: {"chunk_id", "text", "metadata"}.
    The professor name + source filename are prepended to every chunk's text.
    """
    header = parse_header(doc["raw_text"])
    professor = header.get("professor", "Unknown Professor")
    filename = doc["filename"]
    slug = _slug(filename)

    # Header-level metadata shared by every chunk from this file.
    base_meta = {
        "professor": professor,
        "source_file": filename,
        "source_url": header.get("source_url", ""),
        "department": header.get("department", ""),
        "school": header.get("school", ""),
        "overall_rating": header.get("overall_rating", ""),
        "difficulty": header.get("difficulty", ""),
        "would_take_again": header.get("would_take_again", ""),
    }
    # Drop empty values so we don't carry blank metadata forward.
    base_meta = {k: v for k, v in base_meta.items() if v != ""}

    chunks = []
    review_index = 0

    for marker, block in split_sections(doc["raw_text"]):
        if not block:
            continue

        if marker == "Review:":
            review_index += 1
            chunk_type = "review"
            course = _extract_course(block)
            chunk_id = f"{slug}__review__{review_index:02d}"
            label = f"[Review — {course}]" if course else "[Review]"
        else:
            chunk_type = SECTION_TYPE[marker]
            course = None
            chunk_id = f"{slug}__{chunk_type}"
            label = f"[{marker.rstrip(':')}]"

        # Prepend professor + source so the chunk is self-anchoring once embedded.
        text = (
            f"Professor: {professor} | Source: {filename}\n"
            f"{label}\n"
            f"{block}"
        )

        metadata = dict(base_meta)
        metadata["chunk_type"] = chunk_type
        metadata["chunk_id"] = chunk_id
        if course:
            metadata["course"] = course

        chunks.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})

    return chunks


def build_all_chunks(docs_path=DOCS_PATH):
    """Load every document and return one flat list of chunks."""
    all_chunks = []
    for doc in load_documents(docs_path):
        all_chunks.extend(chunk_document(doc))
    return all_chunks


def _print_chunk(chunk, max_chars=400):
    print(f"  chunk_id : {chunk['chunk_id']}")
    print(f"  metadata : {chunk['metadata']}")
    body = chunk["text"]
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + " ..."
    indented = "\n".join("    " + line for line in body.split("\n"))
    print("  text:")
    print(indented)
    print()


def _representative_sample(chunks):
    """Pick up to 5 chunks covering different types (and files) for inspection."""
    sample = []
    seen_types = set()
    # One of each chunk_type first, to show variety.
    for chunk in chunks:
        ctype = chunk["metadata"]["chunk_type"]
        if ctype not in seen_types:
            sample.append(chunk)
            seen_types.add(ctype)
    # Fill any remaining slots with reviews from files not yet shown.
    shown_files = {c["metadata"]["source_file"] for c in sample}
    for chunk in chunks:
        if len(sample) >= 5:
            break
        if chunk["metadata"]["chunk_type"] == "review" and \
                chunk["metadata"]["source_file"] not in shown_files:
            sample.append(chunk)
            shown_files.add(chunk["metadata"]["source_file"])
    return sample[:5]


def main():
    chunks = build_all_chunks()

    print("=" * 70)
    print(f"Loaded docs from: {DOCS_PATH}")
    print(f"Total chunks created: {len(chunks)}")

    # Quick breakdown by chunk_type so the split is easy to sanity-check.
    counts = {}
    for c in chunks:
        counts[c["metadata"]["chunk_type"]] = counts.get(c["metadata"]["chunk_type"], 0) + 1
    print(f"By type: {counts}")
    print("=" * 70)
    print()

    print("5 representative chunks:\n")
    for i, chunk in enumerate(_representative_sample(chunks), start=1):
        print(f"--- Sample {i} ---")
        _print_chunk(chunk)


if __name__ == "__main__":
    main()
