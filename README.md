---
title: Paper Survey Agent
emoji: 📑
colorFrom: orange
colorTo: red
sdk: gradio
sdk_version: 6.1.0
app_file: app.py
pinned: false
license: mit
tags:
  - literature-review
  - paper-survey
  - arxiv
  - semantic-scholar
  - llm-agent
  - research
python_version: 3.11
---

# Paper Survey Agent

📑 **Automated Literature Reviews Using LLM Agent**

An intelligent agent that automatically generates comprehensive literature surveys on any research topic. The agent searches academic databases (arXiv & Semantic Scholar), downloads and analyzes papers, and synthesizes findings into structured literature reviews.

## 🌟 Features

- 🔍 **Multi-Source Search**: Queries both arXiv and Semantic Scholar APIs
- 📊 **Smart Ranking**: Combines relevance, citations, and recency for paper selection
- 🧹 **Deduplication**: Fuzzy matching to remove duplicate papers across sources
- 📥 **PDF Processing**: Automatic PDF download and text extraction
- 🧠 **LLM Summarization**: AI-powered paper summarization with key findings
- 📝 **Survey Synthesis**: Generates cohesive literature reviews with trends and conclusions
- 🎨 **Interactive UI**: Gradio-based web interface with progress tracking
- 🔑 **Multi-Provider LLM**: Supports OpenRouter and Groq (free models available)

## 🏗️ Architecture

```
User Topic
    ↓
┌─────────────────────────────────────┐
│ 1. Query Refinement                 │
│    - LLM optimizes search query     │
│    - Extracts key concepts          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Paper Search                     │
│    - arXiv API                      │
│    - Semantic Scholar API           │
│    - Parallel retrieval             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Ranking & Deduplication          │
│    - Fuzzy title matching           │
│    - Combined scoring               │
│    - Top-K selection                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. PDF Processing                   │
│    - Download PDFs                  │
│    - Extract text                   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Summarization                    │
│    - LLM reads full papers          │
│    - Generates structured summaries │
│    - Extracts key findings          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. Survey Synthesis                 │
│    - Aggregates all summaries       │
│    - Generates literature review    │
│    - Identifies trends & gaps       │
└─────────────────────────────────────┘
    ↓
Literature Survey Report
```

## ⚙️ Installation

### 🔧 Prerequisites

- Python 3.11+
- UV package manager (recommended) or pip

### 📦 Setup Steps

#### 1. Clone the repository

```bash
git clone https://github.com/NeyaLucky/paper-survey-agent.git
cd paper-survey-agent
```

#### 2. Install `uv` — A fast Python package manager

📖 [Installation guide](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 3. Install dependencies

```bash
make install
```

This will:
- Create virtual environment `.venv`
- Install all dependencies
- Setup pre-commit hooks

#### 4. Configure environment (optional)

Copy `.env` template for local development:

```bash
cp .env.dist .env
# Edit .env and add your API keys
```

**Note**: API keys can also be entered directly in the web interface.

## 🔑 Getting API Keys

### LLM API Key (Required)

Choose one of the following providers:

| Provider | Free Tier | Link |
|----------|-----------|------|
| **OpenRouter** | ✅ Multiple free models | [openrouter.ai](https://openrouter.ai/) |
| **Groq** | ✅ Free tier available | [console.groq.com](https://console.groq.com/) |

### Semantic Scholar API Key (Optional)

For higher rate limits (recommended for heavy usage):
1. Register at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api)
2. Request API key
3. Add to `.env` as `SEMANTIC_SCHOLAR_API_KEY`

**Note**: Semantic Scholar works without a key but with rate limits (100 requests/5 min).

## 🚀 Quick Start

### Launch Web Interface

```bash
make run-app
```

Open `http://localhost:7860` in your browser.

### Using the Interface

1. **Enter API Key**: Paste your OpenRouter or Groq API key
2. **Select Provider**: Choose your LLM provider
3. **Select Model**: Pick a model (free options available)
4. **Enter Topic**: Describe your research topic
5. **Generate**: Click "Generate Literature Review"

### Example Topics

Try these example queries:
- "Transformer models for natural language processing"
- "Graph neural networks for drug discovery"
- "Federated learning in healthcare applications"
- "Reinforcement learning for robotics"

## 📖 Usage Guide

### Web Interface Components

**API Configuration:**
- API Key (password field, not stored)
- Provider selection (OpenRouter/Groq)
- Model selection (updates based on provider)

**Input:**
- Research topic text field
- Example topics for quick testing

**Output:**
- Progress indicator with stage updates
- Survey report (Markdown formatted)
- Individual paper summaries (expandable)

### Available Models

**OpenRouter (Free):**
- `meta-llama/llama-3.3-70b-instruct:free`
- `amazon/nova-2-lite-v1:free`
- `qwen/qwen3-235b-a22b:free`
- `openai/gpt-oss-120b:free`

**Groq:**
- `groq/llama-3.1-8b-instant`
- `groq/openai/gpt-oss-120b`
- `groq/qwen/qwen3-32b`

## 🔧 Configuration

Environment variables in `.env`:

```bash
# LLM Settings
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
LLM_API_KEY=your_api_key_here
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Search Settings
MAX_PAPERS_TO_RETURN=10
MAX_RESULTS_PER_SOURCE=10
SEARCH_TIMEOUT=300

# Ranking Weights
WEIGHT_RELEVANCE=0.4
WEIGHT_CITATIONS=0.3
WEIGHT_RECENCY=0.2
WEIGHT_PDF_BONUS=0.1

# API Settings
SEMANTIC_SCHOLAR_API_KEY=optional_key_here
```

## 🚀 Deployment to Hugging Face Spaces

This repository is **ready to deploy** to Hugging Face Spaces directly from the main branch!

### Quick Deploy (3 Steps)

1. **Create Space**: Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Name: `paper-survey-agent`
   - SDK: Gradio
   - License: MIT

2. **Link Repository**: In Space settings, connect your GitHub repo or push directly:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/paper-survey-agent
   git push space main
   ```

3. **Done!** The space will build automatically using:
   - [app.py](app.py) - Main application
   - [requirements.txt](requirements.txt) - Dependencies

**Note**: Users enter their own API keys in the interface, so no secrets configuration is needed.

## 🛠️ Development

### Available Commands

```bash
make install     # Install dependencies
make run-app     # Launch Gradio app
make lint        # Run ruff linter
make format      # Format code
make help        # Show all commands
```
