# Team Roles and Responsibilities

## Team

| Role | Primary Responsibility | Team Member |
|------|------------------------|-------------|
| **Developer 1** | Backend: API integration & tools | Veronika |
| **Developer 2** | LLM: Agent, prompts, summarization | Daryna |
| **Developer 3** | UI, Deployment, Documentation | Denys |

---

## 👤 Developer 1: Backend & API

**Focus:** Scientific API integration and paper retrieval/processing tools

### Completed Tasks

#### 1.1 Project Structure
- [X] Create directory `src/paper_survey_agent/apis/`
- [X] Create directory `src/paper_survey_agent/tools/`
- [X] Create all `__init__.py` files

#### 1.2 Data Models (`src/paper_survey_agent/models/`)
- [X] `paper.py` - Models: `Paper`, `ProcessedPaper`, `SummarizedPaper`

#### 1.3 arXiv API (`src/paper_survey_agent/apis/arxiv.py`)
- [X] Install `arxiv` library
- [X] Implement `ArxivAPI` class:
  - [X] Method `search(query: str, max_results: int) -> list[Paper]`
  - [X] Convert results to `Paper` model
- [X] Error handling and timeout
- [X] Request logging

#### 1.4 Semantic Scholar API (`src/paper_survey_agent/apis/semantic_scholar.py`)
- [X] Implement `SemanticScholarAPI` class:
  - [X] HTTP client (httpx)
  - [X] Method `search(query: str, max_results: int) -> list[Paper]`
  - [X] JSON to `Paper` conversion
- [X] Rate limit handling
- [X] Retry logic with exponential backoff

#### 1.5 Base API Class (`src/paper_survey_agent/apis/base.py`)
- [X] Abstract class `BaseScientificAPI`

#### 1.6 Search and Processing Tool (`src/paper_survey_agent/tools/search_and_load_papers_txt/`)
- [X] Main function `search_and_load_papers_txt()`:
  - [X] Parallel API calls to arXiv and Semantic Scholar
  - [X] Result aggregation
  - [X] Error handling per API

#### 1.7 Utility Modules (`utils/`)
- [X] `retrieval.py` - API orchestration
- [X] `ranking.py` - Deduplication and ranking:
  - [X] Fuzzy title matching
  - [X] Combined scoring (relevance + citations + recency + PDF bonus)
  - [X] Top-K selection
- [X] `downloader.py` - PDF downloading:
  - [X] Async downloads
  - [X] Concurrent limiting
  - [X] Caching
- [X] `text_extractor.py` - PDF to text conversion
- [X] `maintenance.py` - File management

### Deliverables
- ✅ Working paper search from two sources
- ✅ Deduplication and ranking
- ✅ PDF download and text extraction

---

## 👤 Developer 2: LLM & Agent

**Focus:** LLM integration, agent logic, prompts, summarization and synthesis

### Completed Tasks

#### 2.1 Project Structure
- [X] Create directory `src/paper_survey_agent/llm/`
- [X] Create `src/paper_survey_agent/agent.py`
- [X] Create `src/paper_survey_agent/settings.py`

#### 2.2 Configuration (`src/paper_survey_agent/settings.py`)
- [X] `Settings` class with Pydantic BaseSettings:
  - LLM settings (provider, model, API key, temperature, max_tokens)
  - Search settings (max papers, timeout)
  - Ranking weights
  - API-specific settings
- [X] Create `.env.dist`

#### 2.3 LLM Client (`src/paper_survey_agent/llm/client.py`)
- [X] `LLMClient` class:
  - [X] Initialization with API key
  - [X] `generate(prompt, system_prompt)` method
  - [X] Multi-provider support via LiteLLM
  - [X] Retry logic with tenacity

#### 2.4 Prompts (`src/paper_survey_agent/llm/prompts.py`)
- [X] `QUERY_GENERATION_SYSTEM_PROMPT` - search query refinement
- [X] `PAPER_SUMMARIZATION_SYSTEM_PROMPT` - paper summarization
- [X] `SURVEY_SYNTHESIS_SYSTEM_PROMPT` - literature review synthesis

#### 2.5 Query Generation Tool (`src/paper_survey_agent/tools/generate_search_query/`)
- [X] Function `generate_search_query(topic: str) -> str`:
  - [X] LLM-based query optimization
  - [X] Key concept extraction

#### 2.6 Summarization Tool (`src/paper_survey_agent/tools/summarize_papers/`)
- [X] Function `summarize_papers(papers: list[ProcessedPaper]) -> list[SummarizedPaper]`:
  - [X] Read extracted text
  - [X] LLM summarization with structured output
  - [X] JSON parsing

#### 2.7 Synthesis Tool (`src/paper_survey_agent/tools/synthesize_survey/`)
- [X] Function `synthesize_survey(topic, summaries) -> str`:
  - [X] Aggregate all summaries
  - [X] Generate cohesive literature review

#### 2.8 Agent (`src/paper_survey_agent/agent.py`)
- [X] `PaperSurveyAgent` class:
  ```python
  async def run(self, topic: str, progress_callback=None) -> tuple[list[SummarizedPaper], str] | None
  ```
- [X] Pipeline stages:
  1. Query refinement
  2. Paper retrieval
  3. Summarization
  4. Synthesis
- [X] Progress callback integration

### Deliverables
- ✅ Working LLM client
- ✅ All prompts
- ✅ Complete agent pipeline
- ✅ Summarization and synthesis

---

## 👤 Developer 3: UI & Deployment

**Focus:** Web interface, deployment, documentation

### Completed Tasks

#### 3.1 Project Configuration
- [X] Update `pyproject.toml` with all dependencies
- [X] Create `.gitignore`
- [X] Create `requirements.txt` for deployment

#### 3.2 Web Interface (`app.py`)
- [X] Gradio Blocks interface:
  - [X] Header with title and description
  - [X] API configuration section:
    - [X] API key input (password)
    - [X] Provider dropdown
    - [X] Model dropdown (dynamic)
  - [X] Research topic input
  - [X] Example topics
  - [X] Submit/Clear buttons
  - [X] Progress display
  - [X] Results (survey + paper summaries)
- [X] Custom CSS styling

#### 3.3 Entry Point (`app.py`)
- [X] Main application entry point
- [X] Gradio launch configuration

#### 3.4 HuggingFace Spaces Deployment
- [X] Add Spaces metadata to README
- [X] Create HuggingFace Space
- [X] Connect GitHub repository
- [X] Test deployment

#### 3.5 Documentation
- [X] Complete README.md:
  - Project description
  - Features list
  - Architecture diagram
  - Installation instructions
  - Usage guide
  - API key instructions
  - Deployment guide

### Deliverables
- ✅ Working web interface
- ✅ Deployed service on HuggingFace Spaces
- ✅ Complete documentation

---

## 📅 Timeline

### Day 1 (December 17)

| Time | Developer 1 | Developer 2 | Developer 3 |
|------|-------------|-------------|-------------|
| Morning | Project structure + `Paper` model | Structure + config | `pyproject.toml` + `.gitignore` |
| Day | arXiv API | LLM client + prompts | Basic UI |
| Evening | Semantic Scholar API | Summarization | README draft |

### Day 2 (December 18 - DEADLINE)

| Time | Developer 1 | Developer 2 | Developer 3 |
|------|-------------|-------------|-------------|
| Morning | Retrieval tool | Survey synthesis | Connect UI to agent |
| Day | Ranking + deduplication | Agent orchestration | HuggingFace deployment |
| Evening | Testing + fixes | Testing + fixes | Testing + documentation |

---

## 🔗 Integration Points

### Component APIs

```
Developer 1                    Developer 2                    Developer 3
─────────────                  ─────────────                  ─────────────
    │                              │                              │
    │  Paper models                │                              │
    ├─────────────────────────────►│                              │
    │                              │                              │
    │  search_and_load_papers_txt()│                              │
    ├─────────────────────────────►│                              │
    │                              │                              │
    │                              │  PaperSurveyAgent           │
    │                              ├─────────────────────────────►│
    │                              │                              │
    │                              │  run() -> (summaries, survey)│
    │                              ├─────────────────────────────►│
```

### Contracts

**1. Paper Model (Developer 1 → Developer 2):**
```python
class Paper(BaseModel):
    id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: date | None
    source: str
    url: str
    pdf_url: str | None
    citations_count: int | None
    categories: list[str]
```

**2. Search Function (Developer 1 → Developer 2):**
```python
async def search_and_load_papers_txt(query: str) -> list[ProcessedPaper]
```

**3. Agent (Developer 2 → Developer 3):**
```python
class PaperSurveyAgent:
    async def run(self, topic: str, progress_callback=None) -> tuple[list[SummarizedPaper], str] | None
```

---

## ✅ Completion Checklist

### Developer 1
- [X] arXiv API works
- [X] Semantic Scholar API works
- [X] `search_and_load_papers_txt()` returns papers
- [X] Ranking and deduplication works
- [X] PDF download and text extraction works
- [X] Code pushed to repository

### Developer 2
- [X] LLM client works
- [X] All prompts created
- [X] Agent executes full pipeline
- [X] Summarization works
- [X] Survey synthesis works
- [X] Code pushed to repository

### Developer 3
- [X] UI displays input form
- [X] UI shows progress
- [X] UI displays results
- [X] Service deployed to HuggingFace
- [X] README updated
- [X] Documentation complete

### Joint
- [X] Local testing passes
- [X] HuggingFace testing passes
- [X] Project registered
- [X] Submission ready
