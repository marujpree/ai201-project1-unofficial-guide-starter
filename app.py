"""
Milestone 5: Gradio web interface for the UH OChem Unofficial Guide.

Run:  venv/bin/python app.py
Open: http://localhost:7860
"""

import gradio as gr

from query import ask

TITLE = "UH Organic Chemistry — Unofficial Guide"
DESCRIPTION = """\
Ask questions about UH Organic Chemistry professors (CHEM 2323 / CHEM 2325).
Answers are grounded in Rate My Professors reviews, CougarGrades grade data,
Reddit discussions, and the official UH Chemistry faculty page.
The system will say **"I don't have enough information"** rather than guess.
"""

EXAMPLES = [
    "How difficult are Olafs Daugulis's exams in OChem 1?",
    "What was the average GPA for CHEM 2323 under Crystal Young?",
    "Is Robert Comito or Bradley Carrow better for OChem 2?",
    "Is Mary Bean still teaching Organic Chemistry at UH?",
    "Is attendance required for Olaf Daugulis's OChem lectures?",
]


def handle_query(question: str):
    if not question.strip():
        return "", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


CSS = """
footer,
.built-with,
.show-api,
.settings-gear,
#settings,
[id^="settings"] {
    display: none !important;
}
.gr-prose p { margin: 0; }
#answer-box textarea,
#sources-box textarea {
    overflow-y: auto !important;
    resize: none;
}
"""

with gr.Blocks(title=TITLE) as demo:
    gr.Markdown(f"# {TITLE}")
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        question_box = gr.Textbox(
            label="Your question",
            placeholder="e.g. Is attendance required for Daugulis?",
            lines=2,
            scale=4,
        )
        ask_btn = gr.Button("Ask", variant="primary", scale=1, min_width=80)

    with gr.Row():
        answer_box = gr.Textbox(
            label="Answer",
            lines=12,
            interactive=False,
            scale=3,
            elem_id="answer-box",
        )
        sources_box = gr.Textbox(
            label="Retrieved from",
            lines=12,
            interactive=False,
            scale=1,
            elem_id="sources-box",
        )

    gr.Examples(examples=EXAMPLES, inputs=question_box, label="Try one of these")

    ask_btn.click(handle_query, inputs=question_box, outputs=[answer_box, sources_box])
    question_box.submit(handle_query, inputs=question_box, outputs=[answer_box, sources_box])

demo.launch(theme=gr.themes.Soft(), css=CSS)
