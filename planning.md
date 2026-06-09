# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

My domain is student-generated reviews of University of the Pacific Computer Science professors and courses. This knowledge is useful because students often want honest information about teaching style, workload, exams, grading, and whether a professor is helpful before choosing classes. It is hard to find through official university pages because course catalogs describe the class content, but not what students actually experience.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Afsoon Zowj Reviews | Student reviews discussing COMP 025, COMP 047, COMP 051, and COMP 053, including workload, exams, teaching style, and grading. | docs/afsoon_zowj_reviews.txt |
| 2 | Leili Javadpour Reviews | Student reviews discussing BUSI and engineering courses, focusing on teaching quality, accessibility, and course difficulty. | docs/leili_javadpour_reviews.txt |
| 3 | Cathryn Carlson Reviews | Student reviews discussing COMP 025 and COMP 041, focusing on beginner-friendly instruction, assignments, and practical skills. | docs/cathryn_carlson_reviews.txt |
| 4 | Jinzhu Gao Reviews | Student reviews discussing COMP 053, COMP 101, COMP 173, and other CS courses, covering lecture quality, exams, and course difficulty. | docs/jinzhu_gao_reviews.txt |
| 5 | Dana Nehoran Reviews | Student reviews discussing programming, analytics, and data science courses, including Python, R, workload, and teaching effectiveness. | docs/dana_nehoran_reviews.txt |
| 6 | Daniel Cliburn Reviews | Student reviews discussing COMP 051 and COMP 053, focusing on projects, exams, coding assignments, and concept mastery. | docs/daniel_cliburn_reviews.txt |
| 7 | Sehtab Hossain Reviews | Student reviews discussing ECPE 071, focusing on grading, feedback, workload, and lecture quality. | docs/sehtab_hossain_reviews.txt |
| 8 | Michael Lanners Reviews | Student reviews discussing COMP 053 and COMP 061, focusing on self-learning, Zybooks, labs, and teaching style. | docs/michael_lanners_reviews.txt |
| 9 | William Ford Reviews | Student reviews discussing Java, algorithms, and data structures courses, focusing on teaching style, homework, and exams. | docs/william_ford_reviews.txt |
| 10 | Kathy Schuler Reviews | Student reviews discussing COMP 025, focusing on Excel, HTML, labs, projects, and beginner computer skills. | docs/kathy_schuler_reviews.txt |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
I will use one structured block per chunk instead of a fixed character size. Each `Review:` block will become one chunk. The `Summary`, `Common Themes`, and `Useful Student Advice` sections will also become their own chunks.

**Overlap:**
I will use no overlap. Since each review is already a complete block, overlap would mostly duplicate content instead of preserving meaning.

**Reasoning:**
The documents are semi-structured professor review files, not long essays. Each review already contains one student opinion with course, date, rating, difficulty, comment, and tags. Splitting by `Review:` keeps each opinion together. Fixed-size chunking could split a long review in half or merge parts of two short reviews together. Because the professor name appears in the header, I will prepend the professor name and source filename to each chunk so retrieval and citations stay clear.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
I will use `all-MiniLM-L6-v2` through sentence-transformers (it ships with ChromaDB's default embedding function and is already in requirements.txt). It is small, fast, runs locally with no API cost, and works well on short English text like student reviews.

**Top-k:**
I will retrieve the top 5 chunks per query. Because each chunk is a single short review, many of my questions ("what do students generally think of professor X?") need several opinions to answer fairly, so one or two chunks would be too few and could cherry-pick a single outlier. Too many (e.g. 15) would pull in weakly related reviews and dilute the context the LLM sees, making the answer vaguer. Five is enough to capture a representative sample without much noise. I may filter by the `professor` metadata so the 5 chunks come from the right professor.

Semantic search works even when the query words don't match the document because the embedding model maps text to vectors by *meaning*, not exact words. A query like "is she an easy grader?" lands near a review that says "she rounds grades and drops the lowest midterm," because those phrases occupy similar regions of the vector space even though they share no keywords.

**Production tradeoff reflection:**
If I were deploying this for real and cost didn't matter, I'd weigh:
- **Domain accuracy:** a larger or instruction-tuned embedding model (e.g. OpenAI `text-embedding-3-large` or a bge/e5 model) would distinguish fine-grained opinions ("hard exams" vs "hard grader") better than MiniLM.
- **Context length:** MiniLM truncates at ~256 tokens. That's fine for one review, but a model with a longer context window would let me embed whole multi-review sections without truncation.
- **Multilingual support:** not important here since all reviews are in English; I'd only pay for it if students reviewed in other languages.
- **Latency / cost:** MiniLM is local and instant; a hosted model adds an API round-trip and per-call cost. For a small class-facing tool, the local model's speed and zero cost likely outweigh the accuracy gain.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Michael Lanners' teaching style and his use of Zybooks? | Reviews are mostly negative. He lectures only about 10–15 minutes, relies heavily on Zybooks, and expects students to self-teach the material. Classes are fast-paced with lots of labs/homework and little support; 0% would take him again. |
| 2 | According to reviews, why are Daniel Cliburn's COMP 53 midterms considered difficult? | A recent review says the midterms are extremely difficult and that coding is done with pen and paper, which makes them harder. Even with strong project grades, a bad midterm can tank the course grade. |
| 3 | What grading leniency does Afsoon Zowj offer students? | Students say grading can be lenient: she may round grades, drop the lower of two midterms if the second is better, and offer extra credit on exams. |
| 4 | Is attendance important in Afsoon Zowj's classes? | Yes. Attendance is listed as mandatory in nearly all reviews, and several students warn that missing class can hurt your grade. |
| 5 | What do students recommend for succeeding in Afsoon Zowj's COMP 053? | Attend lectures regularly, keep up with the daily quizzes and labs, review before midterms, choose a reliable lab partner early, and use office hours when confused. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Wrong-professor retrieval (missing attribution in chunks).** The professor's name only appears in each file's header, not inside the individual `Review:` blocks. If I embed a review chunk on its own, it has no idea which professor it's about, so a question about a professor could retrieve a similar-sounding review about another professor. Mitigation: store `professor`/`course` as metadata and prepend the professor name to every chunk before embedding, and optionally filter retrieval by the professor metadata.

2. **Conflicting/inconsistent reviews leading to a one-sided answer.** Reviews for the same professor genuinely disagree (e.g. Cliburn has years of 5.0 reviews plus one recent 1.0 "midterms are brutal" review). With a small top-k, retrieval might surface only the positive or only the negative ones, so the LLM gives a lopsided answer that hides the disagreement. Mitigation: use top-k around 5 to sample multiple opinions, and instruct the generator to acknowledge when reviews disagree rather than picking one side.

Other risks I'm watching: off-topic retrieval when a question isn't covered by any document (the system should say it doesn't know rather than guess), and inconsistent course numbering across reviews (e.g. "COMP 53" vs "COMP 053") that could fragment results for the same course.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│ 1. Document          │     │ 2. Chunking          │     │ 3. Embedding + Vector    │
│    Ingestion         │     │                      │     │    Store                 │
│                      │     │ Split on `Review:` / │     │                          │
│ Read .txt files from │──▶  │ section delimiters;  │ ──▶│ all-MiniLM-L6-v2         │
│ docs/  (Python file  │     │ 1 review = 1 chunk;  │     │ (sentence-transformers)  │
│ I/O, python-dotenv   │     │ prepend professor    │     │ embeds chunks → stored   │
│ for the API key)     │     │ name + metadata      │     │ in ChromaDB (persistent) │
└──────────────────────┘     └──────────────────────┘     └──────────────────────────┘
                                                                       │
                                                                       ▼
┌───────────────────────────────────────┐     ┌───────────────────────────────────────┐
│ 5. Generation                         │     │ 4. Retrieval                          │
│                                       │     │                                       │
│ Groq LLM (llama-3.x) builds a         │ ◀── │ Embed the user query with the same    │
│ grounded answer from retrieved        │     │ model; ChromaDB cosine search returns │
│ reviews + cites professor/course.     │     │ top-k = 5 chunks (optionally filtered │
│ UI: Gradio or Streamlit.              │     │ by professor metadata).               │
└───────────────────────────────────────┘     └───────────────────────────────────────┘
        ▲                                                       ▲
        └──────────────  user question ────────────────────────┘
```

**Stage → tool/library:**
1. Document Ingestion — Python file I/O over `docs/*.txt`, `python-dotenv` for secrets
2. Chunking — custom `chunk_text()` (delimiter-based, metadata injection)
3. Embedding + Vector Store — `all-MiniLM-L6-v2` via `sentence-transformers`, stored in `ChromaDB`
4. Retrieval — ChromaDB cosine similarity query, top-k = 5
5. Generation — `groq` LLM with a grounding prompt; `Gradio`/`Streamlit` front end

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I'll use Claude. I'll give it my **Chunking Strategy** section plus one real sample file (`docs/afsoon_zowj_reviews.txt`) so it sees the actual `Review:` / `Summary` / `Common Themes` structure, and ask it to implement `load_documents()` and `chunk_text()` that split on the `Review:` delimiter, treat each section as its own chunk, and attach `professor`/`course`/`source` metadata while prepending the professor name to each chunk's text. I'll verify by printing the chunks for one file and checking that no review is split, no two reviews are merged, and every chunk's metadata names the right professor.

**Milestone 4 — Embedding and retrieval:**
I'll use Claude. I'll give it my **Retrieval Approach** section and ask it to implement embedding with `all-MiniLM-L6-v2` via ChromaDB's embedding function, store chunks with their metadata, and write a `retrieve(query, n_results=5)` that returns each chunk's text, professor/course, and distance. I'll verify by running my 5 evaluation questions and checking that the top results come from the correct professor and that distances are low for clear matches — exactly the "right topic but wrong professor" failure I flagged in Anticipated Challenges.

**Milestone 5 — Generation and interface:**
I'll use Claude. I'll give it my contract for `generate_response(query, retrieved_chunks)` and ask it to call the Groq LLM with a **grounding** system prompt (answer only from the retrieved reviews, cite the professor/course, say "I don't know" when the reviews don't cover it, and note when reviews disagree), then wrap it in a simple Gradio or Streamlit interface. I'll verify by asking a question that's in the docs (checking it cites the right professor) and one that isn't (checking it refuses instead of inventing an answer).
