# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

I will chose to research student reviews of Organic Chemistry professors at the University of Houston.
It's very difficult for pre medical students to find out who is actually the best professor to prepare them correctly for tests and make the course fair. 

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Ratemyprofessor | Student reviews of professors |https://www.ratemyprofessors.com/
| 2 | Reddit | r/UniversityofHouston subreddit for UH students to discuss things about the school | https://www.reddit.com/r/UniversityOfHouston/
| 3 | UH Edu official | chem department faculty list | https://www.uh.edu/nsm/chemistry/people/faculty/
| 4 | CougargradesIO | grade distribution data for UH classes | https://cougargrades.io/
| 5 | ratemyprofessor | Olafs Daugulis ochem1 reviews | https://www.ratemyprofessors.com/professor/528047
| 6 | ratemyprofessor | Crystal young ochem1 reviews | https://www.ratemyprofessors.com/professor/2880547
| 7 | ratemyprofessor ? mary bean reviews ochem1 | https://www.ratemyprofessors.com/professor/1156106
| 8 | ratemyprofessor | robert comito ochem2 reviews | https://www.ratemyprofessors.com/professor/2593590
| 9 | ratemyprofessor |bradley carrow ochem 2 reviews | https://www.ratemyprofessors.com/professor/2691934
| 10 | ratemyprofessor ? Loi Do ochem2 | https://www.ratemyprofessors.com/professor/1916567

- CHEM 2323 (previously known as CHEM 3331) = Organic Chemistry I 
- Chem 2325 (previously known as CHEM 3332) = Organic Chemistry II



---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
