import asyncio
from pathlib import Path
import sys

import gradio as gr
from loguru import logger


sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.paper_survey_agent.agent import PaperSurveyAgent
from src.paper_survey_agent.llm.client import llm_client


LLM_PROVIDERS = {
    "OpenRouter": {
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "amazon/nova-2-lite-v1:free",
            "qwen/qwen3-235b-a22b:free",
            "openai/gpt-oss-120b:free",
        ],
        "default": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "Groq": {
        "models": [
            "groq/llama-3.1-8b-instant",
            "groq/openai/gpt-oss-120b",
            "groq/qwen/qwen3-32b",
        ],
        "default": "groq/llama-3.1-8b-instant",
    },
}


MAIN_HEADER = """
<div style="text-align: center; margin-bottom: 40px;">

# 📑 Paper Survey Agent

**Automated Literature Reviews Using LLM Agent**

Generate comprehensive surveys on any research topic. The agent searches academic databases,
downloads papers, and synthesizes findings into a structured literature review.

</div>
"""


def format_paper_summaries(papers) -> str:
    if not papers:
        return "No papers were processed."

    output = []
    for i, paper in enumerate(papers, 1):
        authors_str = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors_str += " et al."

        output.append(f"### {i}. {paper.title}")
        pub = getattr(paper, "published_date", None)
        if hasattr(pub, "isoformat"):
            pub_str = pub.isoformat()
        else:
            pub_str = str(pub) if pub else "n.d."

        output.append(f"**{authors_str}** • {pub_str}")
        if paper.pdf_url:
            output.append(f"[📄 PDF]({paper.pdf_url})")
        output.append(f"\n{paper.summary}\n")

        if paper.key_findings:
            output.append("**Key Findings:**")
            for finding in paper.key_findings[:3]:
                output.append(f"• {finding}")

        output.append("\n---\n")

    return "\n".join(output)


async def run_survey_agent(
    topic: str,
    api_key: str,
    provider: str,
    model: str,
    progress=gr.Progress(),
) -> tuple[str, str, gr.update, gr.update]:
    if not topic or not topic.strip():
        error_msg = "⚠️ **Input Required**: Please enter a research topic to begin."
        return "", "", gr.update(visible=False), gr.update(value=error_msg, visible=True)

    if not api_key or not api_key.strip():
        error_msg = "⚠️ **API Key Required**: Please enter your API key."
        return "", "", gr.update(visible=False), gr.update(value=error_msg, visible=True)

    # Configure LLM client with user-provided settings
    llm_client.api_key = api_key
    llm_client.provider = provider.lower()
    llm_client.model = model

    log_lines = []

    def progress_callback(step, message):
        progress(step, desc=message)
        log_lines.append(f"- {message}")

    try:
        agent = PaperSurveyAgent()
        result = await agent.run(topic, progress_callback=progress_callback)

        if result is None:
            error_msg = "❌ **No Results**: No papers found or survey generation failed. Try a different topic."
            return (
                "",
                "",
                gr.update(visible=False),
                gr.update(value=error_msg + "\n" + "\n".join(log_lines), visible=True),
            )

        summarized_papers, survey_report = result
        papers_details = format_paper_summaries(summarized_papers)

        survey_formatted = f"# ⬇️ Survey\n\n{survey_report}"
        return survey_formatted, papers_details, gr.update(visible=True), gr.update(value="", visible=False)

    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        error_msg = f"❌ **Error**: {str(e)}"
        return "", "", gr.update(visible=False), gr.update(value=error_msg, visible=True)


def run_survey_sync(
    topic: str,
    api_key: str,
    provider: str,
    model: str,
    progress=gr.Progress(),
) -> tuple[str, str, gr.update, gr.update]:
    return asyncio.run(run_survey_agent(topic, api_key, provider, model, progress))


def update_models(provider: str) -> gr.Dropdown:
    """Update model dropdown when provider changes."""
    if provider in LLM_PROVIDERS:
        models = LLM_PROVIDERS[provider]["models"]
        default = LLM_PROVIDERS[provider]["default"]
        return gr.Dropdown(choices=models, value=default, interactive=True)
    return gr.Dropdown(choices=[], value=None, interactive=True)


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="Paper Survey Agent") as demo:
        gr.Markdown(MAIN_HEADER)

        with gr.Accordion("⚙️ API Configuration", open=True):
            with gr.Row():
                api_key = gr.Textbox(
                    label="API Key",
                    placeholder="Enter your API key here...",
                    type="password",
                    value="",
                    info="Your API key is not stored and only used for this session",
                )

            with gr.Row():
                provider = gr.Dropdown(
                    label="LLM Provider",
                    choices=list(LLM_PROVIDERS.keys()),
                    value="OpenRouter",
                    info="Select your LLM provider",
                )

                model = gr.Dropdown(
                    label="Model",
                    choices=LLM_PROVIDERS["OpenRouter"]["models"],
                    value=LLM_PROVIDERS["OpenRouter"]["default"],
                    info="Select the model to use",
                )

        gr.Markdown("## 💬 Enter Your Research Topic")

        topic_input = gr.Textbox(
            label="Research Topic",
            placeholder="e.g., 'quantum error correction in topological qubits'",
            lines=3,
            info="Describe the research area you want to explore",
        )

        gr.Examples(
            examples=[
                "Transformer models for natural language processing",
                "Graph neural networks for drug discovery",
                "Federated learning in healthcare applications",
                "Reinforcement learning for robotics",
            ],
            inputs=topic_input,
            label="📝 Example Topics",
        )

        with gr.Row():
            submit_btn = gr.Button(
                "🚀 Generate Literature Review",
                variant="primary",
                size="lg",
                elem_id="submit-btn",
            )
            clear_btn = gr.Button("🗑️ Clear", variant="secondary", elem_id="clear-btn")

        loading_status = gr.Markdown(value="", visible=False)

        with gr.Group(visible=False) as results_section:
            survey_output = gr.Markdown(
                value="",
                show_label=False,
                elem_id="survey-content",
            )

            gr.Markdown("<br>")

            with gr.Accordion("📑 Individual Paper Summaries", open=True):
                papers_output = gr.Markdown(
                    value="",
                    show_label=False,
                )

        provider.change(
            fn=update_models,
            inputs=[provider],
            outputs=[model],
        )

        submit_btn.click(
            fn=lambda: (
                "",
                "",
                gr.update(visible=False),
                gr.update(
                    value="⏳ **Processing...**",
                    visible=True,
                ),
            ),
            inputs=[],
            outputs=[survey_output, papers_output, results_section, loading_status],
        ).then(
            fn=run_survey_sync,
            inputs=[topic_input, api_key, provider, model],
            outputs=[survey_output, papers_output, results_section, loading_status],
        )

        clear_btn.click(
            fn=lambda: (
                "",
                "",
                "",
                gr.update(visible=False),
                gr.update(value="", visible=False),
            ),
            inputs=[],
            outputs=[topic_input, survey_output, papers_output, results_section, loading_status],
        )

    return demo


custom_css = """
#survey-content {
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 8px;
}

#submit-btn, #clear-btn {
    padding: 14px 28px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

#submit-btn {
    background: linear-gradient(90deg, #ff7a18 0%, #ff4e00 100%) !important;
    color: white !important;
}
"""


def main():
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=custom_css,
    )


if __name__ == "__main__":
    main()
