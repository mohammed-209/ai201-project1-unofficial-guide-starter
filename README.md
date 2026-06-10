# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

My system covers student-generated reviews of University of the Pacific Computer Science professors and courses. Students usually want honest information about teaching style, workload, exam difficulty, grading, and whether a professor is actually helpful before they sign up for a class. This is hard to find through official channels because the course catalog describes *what* a class covers, but not what it's actually like to take it — things like "he only lectures for 10–15 minutes and expects you to self-teach with Zybooks" or "she rounds grades and drops your lower midterm" only show up in student reviews. My system pulls answers straight from those reviews so a student can ask a normal question and get a grounded, cited answer instead of digging through dozens of individual reviews.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

All sources are student reviews collected from Rate My Professors and saved as plain `.txt` files in `docs/`. I chose 10 professors with a range of ratings and review sentiment so the corpus included both positive and negative student experiences., not just one perspective.

| # | Source (professor) | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Afsoon Zowj (4.1★, CS) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/2525611 — `docs/afsoon_zowj_reviews.txt` |
| 2 | Leili Javadpour (4.2★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/2059648 — `docs/leili_javadpour_reviews.txt` |
| 3 | Cathryn Carlson (4.6★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/1427020 — `docs/cathryn_carlson_reviews.txt` |
| 4 | Jinzhu Gao (3.6★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/1529263 — `docs/jinzhu_gao_reviews.txt` |
| 5 | Dana Nehoran (3.6★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/2286280 — `docs/dana_nehoran_reviews.txt` |
| 6 | Daniel Cliburn (4.0★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/1487898 — `docs/daniel_cliburn_reviews.txt` |
| 7 | Sehtab Hossain (2.0★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/2926262 — `docs/sehtab_hossain_reviews.txt` |
| 8 | Michael Lanners (2.3★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/3039384 — `docs/michael_lanners_reviews.txt` |
| 9 | William Ford (3.9★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/619643 — `docs/william_ford_reviews.txt` |
| 10 | Kathy Schuler (4.9★) | Rate My Professors reviews (.txt) | https://www.ratemyprofessors.com/professor/441473 — `docs/kathy_schuler_reviews.txt` |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One structured block per chunk, not a fixed character count. Each `Review:` block becomes one chunk, and the `Summary`, `Common Themes`, and `Useful Student Advice` sections each become their own chunk. In practice chunks range from about 174 to 907 characters (average ~440), since reviews vary in length.

**Overlap:** None. Each review is already a self-contained block, so overlap would mostly just duplicate text instead of preserving meaning that spans a boundary.

**Why these choices fit your documents:** My documents are semi-structured review files, not long essays. Each `Review:` block is one student's complete opinion with its own course, ratings, comment, and tags, so splitting on the `Review:` delimiter keeps one opinion per chunk. A fixed-size split would have been wrong here — it would cut a long review in half or merge two short reviews into one muddled chunk. The one piece of important context that *isn't* inside each review block is the professor's name (it only appears in the file header), so during ingestion I **prepend the professor name and source filename to every chunk** and also store them as metadata. Preprocessing was light: I normalized newlines and trimmed extra whitespace, but there was no HTML or boilerplate to strip because the files were collected as plain text (I verified with a search that there were no HTML tags or entities like `&amp;`/`&nbsp;`).

**Final chunk count:** 126 chunks across the 10 documents — 96 review chunks, plus 10 summary, 10 common-themes, and 10 useful-advice chunks (one of each per file). This sits comfortably inside the healthy 50–2,000 range, and a check confirmed there were 0 empty chunks and no fragments under 60 characters.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers, with vectors stored in a persistent ChromaDB collection using cosine distance. I picked it because it runs locally with no API key, no cost, and no rate limits, and it works well on short English text like student reviews. The evaluation backed this up — every test question's top result came back under 0.5 distance, which is plenty good for this corpus.

**Production tradeoff reflection:** If I were deploying this for real students and cost wasn't a constraint, I'd weigh a few things. **Domain accuracy:** a larger or instruction-tuned embedding model (like OpenAI `text-embedding-3-large` or a bge/e5 model) would draw finer distinctions between similar-sounding opinions ("hard exams" vs. "hard grader") than MiniLM. **Context length:** MiniLM truncates around 256 tokens, which is fine for one review but would clip a long multi-review section — a longer-context model would let me embed bigger blocks without losing text. **Multilingual support:** not relevant here since all reviews are in English, so I wouldn't pay for it. **Latency and cost:** MiniLM is local and basically instant, while a hosted model adds an API round-trip and per-call cost. For a small class-facing tool, MiniLM's speed and zero cost outweigh the modest accuracy gain — but for a campus-wide deployment with thousands of professors, the better accuracy of a hosted model might be worth it.

---

## Retrieval Analysis

<!-- How well did retrieval perform across the evaluation questions? -->

Retrieval uses `all-MiniLM-L6-v2` embeddings stored in a ChromaDB collection with cosine distance, returning the top 5 chunks per query. Across all five evaluation questions, retrieval was **Relevant for 5/5**: every one of the 25 retrieved chunks (5 queries × 5 results) came from the **correct professor's file**, and the top result for every question scored comfortably under the 0.5 checkpoint threshold.

Top-result distances by question:

| Question | Distance range (top 5) | Best match |
|----------|------------------------|-----------|
| Q1 — Lanners / Zybooks | 0.226 – 0.313 | 0.226 (COMP 53 review) |
| Q2 — Cliburn COMP 53 midterms | 0.336 – 0.512 | 0.336 (summary) |
| Q3 — Zowj grading leniency | 0.268 – 0.287 | 0.268 (COMP 053 review) |
| Q4 — Zowj attendance | 0.326 – 0.382 | 0.326 (COMP 025 review) |
| Q5 — Zowj COMP 053 advice | 0.339 – 0.409 | 0.339 (useful_advice) |

Two observations:

1. **No cross-professor contamination.** Even though terms like "Zybooks," "midterms," and "grading" appear across many professors' files, not a single query pulled a chunk from the wrong professor. This is a direct result of prepending the professor name to every chunk during ingestion (see Chunking Strategy) — the name anchors each embedding to its professor.

2. **Summary chunks sometimes outrank the specific review.** On Q2 the Cliburn *summary* chunk (0.336) outranked the actual pen-and-paper midterm *review* (0.415), because the summary echoes the query's wording ("COMP 53 midterms being very difficult"). Phrasing overlap can beat specificity — useful to know, since the detailed evidence may sit at rank 2–3 rather than rank 1.

There were no retrieval failures: no off-target chunks, no fragments, and no wrong-source results. As a contrast, out-of-scope queries score far higher distances (≈0.93 — see Grounded Generation), showing the signal is well separated from noise.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

Grounding is enforced with an instruction that prohibits specific behaviors rather than describing a vague goal. The system prompt tells the model:

> "You are The Unofficial Guide... Answer using only the provided CONTEXT. Do not use outside knowledge and do not rely on anything you may already know about these professors. If the CONTEXT does not contain the answer, reply with exactly this sentence and nothing else: 'I don't have enough information from the reviews to answer that.' Do not guess, do not invent professors, courses, or policies. Name the professor your answer is about. If reviews disagree, say so instead of picking one side. Refer to the sources you used by their [Source N] number."

Two structural choices reinforce the prompt:

- **Numbered, attributed context.** Each retrieved chunk is passed in as a `[Source N]` block prefixed with its professor, course, source_file, and chunk_type, so the model has explicit, labeled evidence to cite.
- **A distance-based refusal guard.** Because retrieval always returns 5 chunks even for off-topic questions, the system also refuses *before* calling the LLM when the best chunk's cosine distance exceeds `RELEVANCE_CUTOFF = 0.75`. For example, "What is the best pizza restaurant in Stockton?" and "How do I file my taxes in California?" both retrieved their nearest chunk at distance ≈0.93, so the system returned the exact refusal sentence without ever invoking the model. This makes grounding robust against both "the model ignored the context" and "the context was irrelevant" failure modes.

The grounding also produced a desirable behavior on Q2: instead of forcing one answer, the model wrote "there is disagreement among reviews..." and contrasted the recent pen-and-paper midterm review with an older review — exactly the "say so when reviews disagree" instruction working.

**How source attribution is surfaced in the response:**

Attribution is surfaced in two complementary places, and citations are **guaranteed programmatically** rather than left to the model:

- **Appended Sources section.** After the model's answer, the code appends a `**Sources**` list built directly from the retrieved chunks — each line is `professor — course (chunk_type) — source_file`, de-duplicated. Because this is generated in code from the retrieved metadata, the answer always carries citations even if the model forgets to. (When the system refuses, no sources are appended, so a refusal is never dressed up with misleading citations.)
- **Retrieved sources panel.** The Gradio UI shows a separate "Retrieved sources" output listing every retrieved chunk with its professor, course (if available), source_file, chunk_type, **and distance score**, plus a short preview — so a user can inspect exactly what evidence the answer was grounded in and how relevant each piece was.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

All five questions came from my planning.md Evaluation Plan. I ran each through the full system (`handle_query`) and recorded the answer, the retrieved sources, and how it compared to the expected answer.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Michael Lanners' teaching style and his use of Zybooks? | Mostly negative; ~10–15 min lectures, heavy Zybooks reliance, self-teaching, fast-paced, little support; 0% would take again. | Heavy Zybooks reliance, limited lecturing (~10–15 min), students self-teach; difficult, fast-paced, unsupportive. Omits the "0% would take again" stat. | Relevant (5/5 correct prof, 0.226–0.313) | Accurate |
| 2 | According to reviews, why are Daniel Cliburn's COMP 53 midterms considered difficult? | Recent review: midterms extremely difficult, pen-and-paper coding, can tank grade even with strong projects. | Pen-and-paper coding makes exams harder; notes reviews disagree on whether difficulty is the material vs. the professor. Omits "tanks grade despite strong projects." | Relevant (5/5 correct prof, 0.336–0.512) | Accurate |
| 3 | What grading leniency does Afsoon Zowj offer students? | Rounds grades, drops the lower midterm, offers extra credit. | Rounds grades, drops a lower midterm, offers extra credit. | Relevant (5/5 correct prof, 0.268–0.287) | Accurate |
| 4 | Is attendance important in Afsoon Zowj's classes? | Yes — mandatory; missing class can hurt your grade. | Yes — mandatory across reviews; missing class can hurt your grade. | Relevant (5/5 correct prof, 0.326–0.382) | Accurate |
| 5 | What do students recommend for succeeding in Afsoon Zowj's COMP 053? | Attend lectures, keep up with quizzes/labs, review before midterms, choose a reliable lab partner, use office hours. | Pay attention in lectures, choose a reliable lab partner, keep up with quizzes/labs, attendance matters. Omits "review before midterms" and "use office hours." | Relevant (5/5 correct prof, 0.339–0.409) | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target — **all 5 were Relevant.**
**Response accuracy:** Accurate / Partially accurate / Inaccurate — **4 Accurate, 1 Partially accurate.**

Honest summary: retrieval was the strong part — every query pulled all five chunks from the correct professor's file with low distances, and an out-of-scope control question ("best pizza in Stockton") was correctly refused. Generation was accurate on 4 of 5. The one weak spot (Q5) is a completeness gap, not a wrong answer — the model under-extracted from a chunk it correctly retrieved (see Failure Case Analysis below). I also noticed (Q1, Q2) that the model can't cite header-only facts like "0% would take again," because those live in chunk metadata rather than the chunk text the model reads.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

Q5 — "What do students recommend for succeeding in Afsoon Zowj's COMP 053?" (labeled *Partially Accurate* in the evaluation report).

**What the system returned:**

The answer recommended paying attention during lectures, choosing a reliable lab partner, keeping up with the frequent quizzes/labs/zyBook work, and noted that attendance matters. It **omitted two recommendations** that were part of the expected answer: "review before midterms" and "use office hours when confused."

**Root cause (tied to a specific pipeline stage):**

This is a **generation-stage** problem, not a retrieval problem. The relevant `useful_advice` chunk ranked **#1 at distance 0.339** and was cited as [Source 1] — and that chunk contains the exact text "Students should attend class regularly, review before midterms, use office hours when confused, and keep up with labs and quizzes." So the full answer was present in the retrieved context. The LLM produced a short paraphrase/synthesis and dropped two of the listed recommendations rather than enumerating all of them. In other words, retrieval did its job; generation under-extracted from a chunk it had in hand.

**What you would change to fix it:**

Adjust the system prompt for list-style questions to instruct the model to **enumerate every distinct recommendation found in the context** (e.g., "If the question asks what students recommend, list each recommendation present in the sources as a separate bullet point; do not summarize them into a single sentence"). I would also consider lowering the sampling temperature for more deterministic extraction. This is a prompt fix at the generation stage — no change to chunking or retrieval is needed, since the correct chunk was already retrieved and cited.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

The Chunking Strategy section forced me to notice — before writing any code — that the professor's name appears only in each file's header, never inside the individual `Review:` blocks. That single observation drove the decision to prepend the professor name to every chunk and store it as metadata. The payoff showed up directly in evaluation: across all five questions, every one of the 25 retrieved chunks came from the correct professor, with top distances of 0.23–0.34, despite heavy shared vocabulary like "Zybooks" and "midterms" across files. If I'd skipped the spec and chunked naively, those anonymous review chunks would almost certainly have produced cross-professor retrieval, and I'd have spent debugging time chasing a problem the spec let me design around up front.

**One way your implementation diverged from the spec, and why:**

The Retrieval Approach section described retrieval as plain semantic top-5 and said I "may filter by professor metadata." In practice I diverged in two ways. First, I added a distance-based refusal guard (`RELEVANCE_CUTOFF = 0.75`) that wasn't in the plan: since ChromaDB always returns 5 chunks even for off-topic questions, I needed a way to refuse before calling the LLM — validated by the pizza/taxes queries scoring ≈0.93. Second, I never implemented the optional professor metadata filter, because retrieval turned out clean enough without it (the correct professor was returned every time), so adding a filter would have been complexity with no measurable benefit. Both changes were driven by what the actual retrieval results showed, which is exactly the kind of mid-implementation update the planning template anticipates.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

I used Claude as a coding assistant across Milestones 3–5, always driving it from my planning.md spec rather than asking it to design things from scratch. For every piece of generated code, I inspected what it produced, ran it against my own data, and modified it where it didn't match my spec or my evaluation results. The verification was concrete: I checked the printed chunk output and counts for ingestion, the distance scores and source professors for retrieval, and the actual answers (plus an out-of-scope refusal) for generation.

**Instance 1 — Ingestion and chunking (Milestone 3)**

- *What I gave the AI:* My Chunking Strategy and Documents sections from planning.md, plus a real sample review file so it could see the actual `Source/Professor/Summary/Review/Common Themes/Useful Student Advice` structure. I asked it to load the files, clean them, and chunk by structural block (one chunk per review + one per section) with professor/course/source metadata.
- *What it produced:* `ingest.py` with `load_documents()`, a header parser, a section splitter, and `chunk_document()`. It correctly split on the `Review:` delimiter and attached metadata.
- *What I changed or overrode / how I verified:* I ran it and inspected the output — 126 chunks (96 reviews + 10 each of summary/common-themes/advice) with a per-file breakdown, and confirmed no review was split or merged. I specifically verified that the professor name was prepended to each chunk and stored as metadata, since the name only appears in the file header. I also confirmed there were 0 empty chunks and no HTML artifacts before relying on it.

**Instance 2 — Embedding, retrieval, and grounded generation (Milestones 4–5)**

- *What I gave the AI:* My Retrieval Approach section and architecture diagram, plus explicit requirements — embed with `all-MiniLM-L6-v2`, store in a persistent ChromaDB `unofficial_guide` collection, write `retrieve(query, n_results=5)`, and then a `generate_response`/`handle_query` that answers only from retrieved context with a strict grounding prompt and programmatic source citations, wrapped in a Gradio UI.
- *What it produced:* `retriever.py` (manual SentenceTransformer embedding stored in ChromaDB with a dedup check) and `app.py` (Groq `llama-3.3-70b-versatile`, grounding system prompt, appended Sources section, Gradio interface with separate answer and retrieved-sources outputs).
- *What I changed or overrode / how I verified:* I tested retrieval on my evaluation questions and confirmed top distances were under 0.5 and every result came from the correct professor. The biggest change I directed was adding a `RELEVANCE_CUTOFF = 0.75` distance guard that wasn't in my original plan — I added it after seeing that off-topic questions still returned 5 chunks, so the system now refuses before calling the LLM (the pizza/taxes test queries scored ≈0.93 and were correctly refused). I also tested the full pipeline end to end with 3 normal questions plus an out-of-scope one to confirm grounding held before considering it done.
