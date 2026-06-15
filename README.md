## Domain
<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] -- useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This system covers student reviews and grade data for Organic Chemistry professors at the University of Houston (CHEM 2323 and CHEM 2325). Pre-med and pre-pharmacy students really need to pick the right professor for OChem because it can make or break their GPA and their path to med school. The problem is that there is no single place to get a complete picture. Rate My Professors has reviews but they can be outdated, CougarGrades has grade data but no context about teaching style, and Reddit discussions are scattered across threads. This system pulls all of those sources together so a student can ask a plain question and get a grounded answer.

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety -- sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors -- Olafs Daugulis | Student reviews (OChem 1) | https://www.ratemyprofessors.com/professor/528047 |
| 2 | Rate My Professors -- Crystal Young | Student reviews (OChem 1) | https://www.ratemyprofessors.com/professor/2880547 |
| 3 | Rate My Professors -- Mary Bean | Student reviews (OChem 1 and 2) | https://www.ratemyprofessors.com/professor/1156106 |
| 4 | Rate My Professors -- Robert Comito | Student reviews (OChem 2) | https://www.ratemyprofessors.com/professor/2593590 |
| 5 | Rate My Professors -- Bradley Carrow | Student reviews (OChem 2) | https://www.ratemyprofessors.com/professor/2691934 |
| 6 | Rate My Professors -- Loi Do | Student reviews (OChem 1 and 2) | https://www.ratemyprofessors.com/professor/1916567 |
| 7 | CougarGrades.io | Grade distribution data for CHEM 2323 and CHEM 2325 | https://cougargrades.io/ |
| 8 | Reddit -- r/UniversityOfHouston | Student discussions about OChem professors | https://www.reddit.com/r/UniversityOfHouston/ |
| 9 | UH Chemistry Department | Official faculty list to verify who is still teaching | https://www.uh.edu/nsm/chemistry/people/faculty/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 1200 characters, which is roughly 300 tokens at the standard 4 chars per token estimate.

**Overlap:** 200 characters (roughly 50 tokens) so that a review that gets cut near the end does not lose its context completely in the next chunk.

**Why these choices fit your documents:** Most Rate My Professors reviews are only a few sentences long. A 300-token chunk is big enough to fit one full review plus a little surrounding context, but small enough that retrieval stays precise and does not pull in reviews from different professors at once. Reddit posts and comments are also short, so the same size works there. The CougarGrades data is structured line by line (one row per semester), so the chunk boundaries naturally fall between different professors and semesters without splitting a single data record. The splitter uses paragraph breaks first, then sentence breaks, then word breaks so it tries not to cut mid-sentence.

**Final chunk count:** 383 chunks across 9 documents.
## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** all-MiniLM-L6-v2 via sentence-transformers, running locally.

**Production tradeoff reflection:** The main reason I picked all-MiniLM-L6-v2 is that it runs entirely on my machine with no API cost or rate limits. It is also fast and well-tested for semantic similarity tasks. The tradeoff is that it is a general-purpose model trained on broad web text, not on academic or chemistry-specific language, so it sometimes struggles with domain-specific phrasing. If I were deploying this for real users and cost was not a concern, I would look at OpenAI's models with a longer context window so that full multi-review comparisons could be embedded as one unit rather than as separate chunks. 

## Grounded Generation

<!-- Explain how your system enforces grounding -- how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" -- show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The model is given a strict system prompt that tells it to answer only using the context documents provided in the prompt. As a result, it responds with "I don't have enough information in my documents to answer that" if the context does not cover the question. The relevant lines from the prompt are:

Answer ONLY using information from the context documents provided below.
Do NOT draw on training knowledge about professors, grades, or UH even if you believe you know the answer.
If the context does not contain enough information to answer, respond with exactly: "I don't have enough information in my documents to answer that."

The LLM is Llama 3.3 70B running on Groq with temperature set to 0.1 to keep answers factual and reduce hallucination risk.

**How source attribution is surfaced in the response:** The retrieved chunks are passed to the model with their filename labeled at the top of each chunk, like [rmp_olaf_daugulis.txt]. The model is instructed to cite the filename in its answer. The app also shows a separate sources panel next to the answer that lists every document the retriever pulled from for that query, so the user can see exactly where the answer came from.

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest -- a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | How difficult are Olafs Daugulis's exams in OChem 1? | Very difficult, supported by multiple RMP reviews | System returned a summary of reviews describing very difficult exams, low class averages, and no dropped tests | Relevant | Accurate |
| 2 | What was the average GPA for CHEM 2323 under Crystal Young? | 1.687 (Spring 2025 section from CougarGrades) | System quoted the Spring 2025 average GPA of 1.687 and referenced the CougarGrades data file | Relevant | Accurate |
| 3 | Is Robert Comito or Bradley Carrow better for OChem 2? | Carrow, based on higher GPA (2.77 vs 1.79) and better RMP rating (2.3 vs 1.7) | "I don't have enough information in my documents to answer that." | Off-target | Inaccurate |
| 4 | Is Mary Bean still teaching Organic Chemistry at UH? | No, she is not listed on the current faculty page | System correctly noted that Mary Bean does not appear on the UH Chemistry faculty list as of the scrape date | Relevant | Accurate |
| 5 | Is attendance required for Olaf Daugulis's OChem lectures? | Yes, based on RMP reviews | System cited multiple reviews confirming attendance is mandatory and quizzes are given each lecture | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context -- the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Is Robert Comito or Bradley Carrow better for OChem 2?

**What the system returned:** "I don't have enough information in my documents to answer that."

**Root cause (tied to a specific pipeline stage):** The failure happens at two stages. At retrieval, the query has both professor names in it so the single embedding vector has to split its attention between both. With k=8, the retriever fills most of the slots with RMP review chunks from one professor and does not pull in the CougarGrades data that has the actual side by side GPA numbers (Carrow 2.72 vs Comito 1.79 for CHEM 2325). Those grade distribution chunks are dense with numbers and labels so they score low on semantic similarity compared to the narrative review chunks. At generation, even when chunks from both professors do make it into the context, no single review ever says one is better than the other. The grounding prompt tells the model to only report what the documents say directly, and since no document makes that comparison explicitly, it refuses to answer.

**What you would change to fix it:** Run two separate retrieval queries, one for Comito and one for Carrow, then combine those results before sending them to the model. That way both professors are guaranteed to have chunks in the context. You could also loosen the prompt a bit for comparison questions so the model is allowed to reason across the data points it cited rather than needing a document to spell out the answer directly.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2-3 sentences each. -->

**One way the spec helped you during implementation:** Writing out the chunking strategy in planning.md before writing any code made the implementation straightforward. Because I had already decided on 300 tokens and 50 overlap and justified why those fit short reviews, I did not have to make those decisions mid-implementation. I just passed those numbers directly to RecursiveCharacterTextSplitter and they worked on the first run without needing to go back and tune. Overall it also made me understand the pipeline overall as I spent so much time drafting and writing out a very detailed plan that was very helpful.

**One way your implementation diverged from the spec, and why:** The spec set top-k to 5, but after testing during Milestone 4 I increased it to 8. During retrieval tests, Crystal Young's GPA chunk was showing up at position 6 or 7, meaning it was getting cut off with k=5 and the system could not answer GPA questions about her correctly. Increasing k to 8 fixed that. The spec was a good starting point but the actual retrieval behavior made it clear that 5 was too conservative for a corpus spread across 9 different files.

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* My Documents table and Chunking Strategy section from planning.md and asked Claude to generate the ingestion and chunking pipeline.
- *What it produced:* A complete ingest.py with load_documents, clean_text, and chunk_documents functions using RecursiveCharacterTextSplitter with the chunk size and overlap from my spec.
- *What I changed or overrode:* The initial version used character counts directly (1200 chars, 200 overlap) as estimates of the token targets in my spec. I kept those numbers but added the separators list so the splitter would prefer paragraph and sentence breaks rather than splitting mid-word.

**Instance 2**

- *What I gave the AI:* My system prompt draft along with the embed.py retrieval function and asked Claude to build the full RAG pipeline in query.py including grounding enforcement and source attribution.
- *What it produced:* The ask() function with the strict system prompt, context builder, Groq API call, and deduplicated source list returned alongside the answer.
- *What I changed or overrode:* The original system prompt did not include the instruction to respond with an exact phrase when information was missing. I added the specific fallback phrase ("I don't have enough information in my documents to answer that") so I could test grounding behavior consistently and identify failure cases more clearly. There was a brief period of time where I thought my web app did not or had crashed due to the resulting answer box just being blank. 
