"""
Milestone 5 — Grounded generation + Gradio interface for The Unofficial Guide.

Ties the pipeline together: retrieve() pulls the most relevant student-review
chunks, the Groq LLM answers using ONLY those chunks, and a Sources section is
appended programmatically so citations are always present and accurate.

Run:
    python app.py
"""
import os

from dotenv import load_dotenv
from groq import Groq

from retriever import retrieve

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
N_RESULTS = 5

# Exact sentence the model must use when the reviews don't answer the question.
REFUSAL = "I don't have enough information from the reviews to answer that"

# Cosine distance above which even the best match is too weak to trust. Used as
# a safety net so clearly off-topic questions refuse without relying solely on
# the model's judgment. (Milestone 4 guidance: >0.6–0.7 = weak match.)
RELEVANCE_CUTOFF = 0.75

_client = Groq(api_key=GROQ_API_KEY)


def _source_label(chunk):
    """One-line citation for a chunk: 'Professor — Course (chunk_type) — file'."""
    parts = [chunk["professor"]]
    if chunk.get("course"):
        parts.append(chunk["course"])
    label = " — ".join(parts)
    return f"{label} ({chunk['chunk_type']}) — {chunk['source_file']}"


def _build_context(chunks):
    """Format retrieved chunks into a numbered, attributed CONTEXT block."""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        header = f"[Source {i}] {_source_label(c)}"
        blocks.append(f"{header}\n{c['text']}")
    return "\n\n".join(blocks)


def _sources_section(chunks):
    """Programmatic, de-duplicated Sources list appended to every grounded answer."""
    seen = []
    for c in chunks:
        label = _source_label(c)
        if label not in seen:
            seen.append(label)
    lines = "\n".join(f"- {label}" for label in seen)
    return f"**Sources**\n{lines}"


def _sources_view(chunks):
    """
    Detailed retrieved-sources panel for the UI.

    Shows, per chunk: professor, course (if available), source_file, chunk_type,
    and distance score (plus a short preview for context).
    """
    if not chunks:
        return "_No chunks retrieved._"
    rows = []
    for i, c in enumerate(chunks, start=1):
        course = c.get("course", "n/a")
        preview = c["text"][:300].replace("\n", " ")
        rows.append(
            f"**[{i}] professor:** {c['professor']}  \n"
            f"**course:** {course}  \n"
            f"**source_file:** {c['source_file']}  \n"
            f"**chunk_type:** {c['chunk_type']}  \n"
            f"**distance:** {c['distance']:.3f}  \n"
            f"{preview}..."
        )
    return "\n\n---\n\n".join(rows)


def generate_response(query):
    """
    Answer a question using only retrieved review chunks.

    Returns (answer_markdown, sources_markdown):
      - answer_markdown: the grounded answer with a programmatic Sources section
        appended (or the refusal sentence with no sources).
      - sources_markdown: a detailed view of the retrieved chunks for the UI.
    """
    if not query or not query.strip():
        return "Please enter a question.", ""

    chunks = retrieve(query, n_results=N_RESULTS)

    # No data at all, or the best match is too far away to be relevant -> refuse.
    if not chunks or chunks[0]["distance"] > RELEVANCE_CUTOFF:
        return REFUSAL + ".", _sources_view(chunks)

    context = _build_context(chunks)

    system_prompt = (
        "You are The Unofficial Guide, an assistant that answers questions about "
        "University of the Pacific Computer Science professors and courses using "
        "ONLY the student reviews in the CONTEXT below. Follow these rules:\n"
        "- Answer using only the provided CONTEXT. Do not use outside knowledge "
        "and do not rely on anything you may already know about these professors.\n"
        f"- If the CONTEXT does not contain the answer, reply with exactly this "
        f"sentence and nothing else: \"{REFUSAL}.\"\n"
        "- Do not guess, do not invent professors, courses, or policies.\n"
        "- Name the professor your answer is about. If reviews disagree, say so "
        "instead of picking one side.\n"
        "- Refer to the sources you used by their [Source N] number."
    )

    user_message = f"CONTEXT:\n{context}\n\nQUESTION: {query}"

    completion = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # If the model refused, don't attach sources (they'd be misleading).
    if answer.startswith(REFUSAL):
        return answer, _sources_view(chunks)

    # Guarantee citations regardless of what the model wrote.
    answer_with_sources = f"{answer}\n\n{_sources_section(chunks)}"
    return answer_with_sources, _sources_view(chunks)


def handle_query(question):
    """
    UI entry point. Wraps generate_response() and returns two separate outputs:
      - answer text (grounded answer + appended Sources, or the refusal)
      - sources text (detailed retrieved-source list for the sources panel)
    """
    answer, sources = generate_response(question)
    return answer, sources


# ---------------------------------------------------------------------------
# Gradio interface
# ---------------------------------------------------------------------------
import gradio as gr

SAMPLE_QUESTIONS = [
    "What do students say about Michael Lanners' teaching style and his use of Zybooks?",
    "According to reviews, why are Daniel Cliburn's COMP 53 midterms considered difficult?",
    "What grading leniency does Afsoon Zowj offer students?",
]

with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# 🎓 The Unofficial Guide\n"
        "Ask about University of the Pacific CS professors — answers come **only** "
        "from student reviews, with sources cited."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. What grading leniency does Afsoon Zowj offer students?",
        lines=2,
    )
    ask_btn = gr.Button("Ask", variant="primary")

    answer_out = gr.Markdown(label="Answer")
    with gr.Accordion("Retrieved sources", open=False):
        sources_out = gr.Markdown()

    gr.Examples(examples=SAMPLE_QUESTIONS, inputs=question)

    ask_btn.click(handle_query, inputs=question, outputs=[answer_out, sources_out])
    question.submit(handle_query, inputs=question, outputs=[answer_out, sources_out])


if __name__ == "__main__":
    demo.launch()
