# Paper Survey Agent - Task List

## Project Structure

```
paper-survey-agent/
├── .github/
│   └── copilot-instructions.md     # Copilot instructions
├── app.py                          # Gradio web interface entry point
├── docs/
│   ├── assignment.md               # Assignment description
│   ├── tasks.md                    # This task file
│   └── team-roles.md               # Team roles and responsibilities
├── notebooks/
│   └── test_agent.ipynb            # Testing notebook
├── src/
│   └── paper_survey_agent/
│       ├── __init__.py
│       ├── agent.py                # Main LLM agent orchestration
│       ├── settings.py             # Configuration and settings (Pydantic)
│       ├── models/
│       │   ├── __init__.py
│       │   └── paper.py            # Paper, ProcessedPaper, SummarizedPaper models
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── generate_search_query/
│       │   │   └── generate_search_query.py    # LLM-based query refinement
│       │   ├── search_and_load_papers_txt/
│       │   │   ├── search_and_load_papers_txt.py  # Main search orchestration
│       │   │   └── utils/
│       │   │       ├── downloader.py           # PDF download utilities
│       │   │       ├── maintenance.py          # Cache and file management
│       │   │       ├── ranking.py              # Paper ranking and deduplication
│       │   │       ├── retrieval.py            # API retrieval orchestration
│       │   │       └── text_extractor.py       # PDF to text conversion
│       │   ├── summarize_papers/
│       │   │   └── summarize_papers.py         # LLM paper summarization
│       │   └── synthesize_survey/
│       │       └── synthesize_survey.py        # LLM survey synthesis
│       ├── apis/
│       │   ├── __init__.py
│       │   ├── base.py             # Base API class
│       │   ├── arxiv.py            # arXiv API client
│       │   └── semantic_scholar.py # Semantic Scholar API client
│       └── llm/
│           ├── __init__.py
│           ├── client.py           # LLM client (LiteLLM-based)
│           └── prompts.py          # Prompt templates
├── .env.dist                       # Environment variables template
├── .gitignore
├── LICENSE
├── Makefile                        # Development commands
├── pyproject.toml                  # Project configuration and dependencies
├── README.md                       # Project documentation
└── requirements.txt                # Dependencies for deployment
```

---

## 1. Project Setup

### 1.1 Directory Structure Initialization
- [X] Create directory `src/paper_survey_agent/`
- [X] Create directory `src/paper_survey_agent/models/`
- [X] Create directory `src/paper_survey_agent/tools/`
- [X] Create directory `src/paper_survey_agent/apis/`
- [X] Create directory `src/paper_survey_agent/llm/`
- [X] Create directory `notebooks/` (Jupyter testing)
- [X] Create all necessary `__init__.py` files

### 1.2 Project Configuration
- [X] Update `pyproject.toml` with required dependencies:
  - `litellm` - for multi-provider LLM support
  - `arxiv` - for arXiv API
  - `httpx` - for HTTP requests
  - `pydantic` and `pydantic-settings` - for data models and configuration
  - `gradio` - for web interface
  - `rapidfuzz` - for fuzzy string matching
  - `loguru` - for logging
  - `aiofiles` - for async file operations
  - `pdfplumber` - for PDF text extraction
  - `tenacity` - for retry logic
- [X] Create `.env.dist` with environment variable examples
- [X] Update `.gitignore` for Python project
- [X] Setup virtual environment

### 1.3 Documentation
- [X] Update `README.md` with:
  - Project description
  - Installation instructions
  - Usage examples
  - API key requirements
  - HuggingFace Spaces metadata for deployment

---

## 2. Core Infrastructure

### 2.1 Configuration (`src/paper_survey_agent/settings.py`)
- [X] Create `Settings` class using Pydantic BaseSettings
- [X] Add fields for LLM configuration:
  - `LLM_PROVIDER` - provider name (openrouter, groq)
  - `LLM_MODEL` - model identifier
  - `LLM_API_KEY` - API key
  - `LLM_TEMPERATURE` - generation temperature
  - `LLM_MAX_TOKENS` - max tokens for generation
- [X] Add fields for search configuration:
  - `MAX_PAPERS_TO_RETURN` - final paper limit
  - `MAX_RESULTS_PER_SOURCE` - per-API limit
  - `SEARCH_TIMEOUT` - timeout for searches
- [X] Add ranking weights configuration:
  - `WEIGHT_RELEVANCE` - relevance score weight
  - `WEIGHT_CITATIONS` - citations weight
  - `WEIGHT_RECENCY` - recency weight
  - `WEIGHT_PDF_BONUS` - PDF availability bonus
- [X] Add API-specific settings (arXiv, Semantic Scholar)
- [X] Implement loading from `.env` file

### 2.2 Data Structures (`src/paper_survey_agent/models/`)

#### `paper.py`
- [X] Create Pydantic model `Paper`:
  ```python
  class Paper(BaseModel):
      id: str
      title: str
      authors: list[str]
      abstract: str
      published_date: date | None
      source: str  # arxiv, semantic_scholar
      url: str
      pdf_url: str | None
      citations_count: int | None
      categories: list[str]
  ```

- [X] Create Pydantic model `ProcessedPaper` (extends Paper):
  ```python
  class ProcessedPaper(Paper):
      txt_path: Path | None  # Path to extracted text file
  ```

- [X] Create Pydantic model `SummarizedPaper` (extends ProcessedPaper):
  ```python
  class SummarizedPaper(ProcessedPaper):
      summary: str
      key_findings: list[str]
  ```

### 2.3 Logging
- [X] Configure logging with `loguru`
- [X] Add logging for each pipeline stage
- [X] Structured log output

### 2.4 Error Handling
- [X] Implement retry logic with `tenacity` (exponential backoff)
- [X] Graceful handling of API failures
- [X] Continue processing when individual papers fail

---

## 3. Scientific API Integration

### 3.1 Base API Class (`src/paper_survey_agent/apis/base.py`)
- [X] Create abstract base class `BaseScientificAPI`:
  ```python
  class BaseScientificAPI(ABC):
      @abstractmethod
      async def search(self, query: str, max_results: int) -> list[Paper]: ...
  ```
- [X] Add common retry and rate limiting logic

### 3.2 arXiv API (`src/paper_survey_agent/apis/arxiv.py`)
- [X] Install `arxiv` library
- [X] Implement class `ArxivAPI(BaseScientificAPI)`:
  - [X] Method `search()` - search publications by query
  - [X] Convert results to `Paper` model
- [X] Configure search parameters:
  - `sort_by` - sorting (relevance, date)
  - `max_results` - maximum results
- [X] Handle arXiv categories

### 3.3 Semantic Scholar API (`src/paper_survey_agent/apis/semantic_scholar.py`)
- [X] Implement class `SemanticScholarAPI(BaseScientificAPI)`:
  - [X] HTTP client setup (httpx)
  - [X] Method `search()` via `/paper/search` endpoint
  - [X] Convert JSON to `Paper` model
- [X] API configuration:
  - Base URL: `https://api.semanticscholar.org/graph/v1`
  - Fields: `title,authors,abstract,year,citationCount,url,openAccessPdf`
- [X] Handle rate limits

---

## 4. Agent Tools

### 4.1 Query Generation (`src/paper_survey_agent/tools/generate_search_query/`)
- [X] Implement `generate_search_query(topic: str) -> str`:
  - [X] Use LLM to refine user topic into optimized search query
  - [X] Extract key concepts and technical terms
  - [X] Return refined query string

### 4.2 Paper Search and Processing (`src/paper_survey_agent/tools/search_and_load_papers_txt/`)
- [X] Implement main function `search_and_load_papers_txt(query: str) -> list[ProcessedPaper]`:
  - [X] Call both arXiv and Semantic Scholar APIs
  - [X] Rank and deduplicate results
  - [X] Download PDFs
  - [X] Extract text from PDFs
  - [X] Return processed papers with text paths

#### Utility modules in `utils/`:
- [X] `retrieval.py` - API orchestration:
  - [X] Parallel calls to multiple APIs
  - [X] Error handling per source
  - [X] Result aggregation
- [X] `ranking.py` - Ranking and deduplication:
  - [X] Fuzzy title matching for deduplication
  - [X] Combined scoring (relevance + citations + recency + PDF bonus)
  - [X] Top-K selection
- [X] `downloader.py` - PDF downloading:
  - [X] Async PDF downloads
  - [X] Concurrent download limiting
  - [X] Cache management
- [X] `text_extractor.py` - PDF to text:
  - [X] PDF parsing with pdfplumber
  - [X] Text cleaning and formatting
- [X] `maintenance.py` - File management:
  - [X] Cache directory management
  - [X] Cleanup utilities

### 4.3 Paper Summarization (`src/paper_survey_agent/tools/summarize_papers/`)
- [X] Implement `summarize_papers(papers: list[ProcessedPaper]) -> list[SummarizedPaper]`:
  - [X] Read extracted text for each paper
  - [X] Call LLM with summarization prompt
  - [X] Parse structured JSON response
  - [X] Return papers with summaries and key findings
- [X] Handle large texts (truncation if needed)
- [X] Concurrent summarization with semaphore

### 4.4 Survey Synthesis (`src/paper_survey_agent/tools/synthesize_survey/`)
- [X] Implement `synthesize_survey(topic: str, summaries: list[SummarizedPaper]) -> str`:
  - [X] Aggregate all paper summaries
  - [X] Call LLM with synthesis prompt
  - [X] Generate cohesive literature review
  - [X] Include trends, methodologies, conclusions

---

## 5. LLM Integration

### 5.1 LLM Client (`src/paper_survey_agent/llm/client.py`)
- [X] Create `LLMClient` class:
  - [X] Initialize with API key and model settings
  - [X] Use `litellm` for multi-provider support
  - [X] Method `generate(prompt, system_prompt)` for text generation
- [X] Implement retry logic with `tenacity`:
  - [X] 3 retry attempts
  - [X] Exponential backoff
- [X] Support multiple providers (OpenRouter, Groq)
- [X] Create singleton instance `llm_client`

### 5.2 Prompts (`src/paper_survey_agent/llm/prompts.py`)
- [X] Create `QUERY_GENERATION_SYSTEM_PROMPT` - for search query refinement
- [X] Create `PAPER_SUMMARIZATION_SYSTEM_PROMPT` - for paper summarization
- [X] Create `SURVEY_SYNTHESIS_SYSTEM_PROMPT` - for literature review synthesis
- [X] Structured output format instructions (JSON)

---

## 6. Agent System (`src/paper_survey_agent/agent.py`)

### 6.1 Main Agent Class
- [X] Create `PaperSurveyAgent` class:
  ```python
  class PaperSurveyAgent:
      async def run(self, topic: str, progress_callback=None) -> tuple[list[SummarizedPaper], str] | None
  ```

### 6.2 Pipeline Stages
- [X] Stage 1: Query Refinement
  - [X] Call `generate_search_query()` tool
  - [X] Report progress
- [X] Stage 2: Paper Retrieval
  - [X] Call `search_and_load_papers_txt()` tool
  - [X] Handle empty results
  - [X] Report progress
- [X] Stage 3: Summarization
  - [X] Call `summarize_papers()` tool
  - [X] Handle failures
  - [X] Report progress
- [X] Stage 4: Synthesis
  - [X] Call `synthesize_survey()` tool
  - [X] Generate final report
  - [X] Report progress

### 6.3 Progress Tracking
- [X] Implement progress callback system
- [X] Report step completion with percentage
- [X] Integrate with Gradio progress bar

---

## 7. Web Interface (`app.py`)

### 7.1 Gradio Interface
- [X] Create main Gradio Blocks interface:
  - [X] Title and description header
  - [X] API configuration section:
    - [X] API key input (password field)
    - [X] Provider dropdown (OpenRouter, Groq)
    - [X] Model dropdown (updates based on provider)
  - [X] Research topic input field
  - [X] Example topics
  - [X] Submit and Clear buttons
  - [X] Progress/status display
  - [X] Results section:
    - [X] Survey output (Markdown)
    - [X] Individual paper summaries (Accordion)

### 7.2 Event Handlers
- [X] Provider change updates model dropdown
- [X] Submit button triggers agent pipeline
- [X] Clear button resets all fields
- [X] Progress callback updates status

### 7.3 Styling
- [X] Custom CSS for buttons and layout
- [X] Responsive design

---

## 8. Deployment

### 8.1 HuggingFace Spaces Preparation
- [X] Add Spaces metadata to `README.md`:
  ```yaml
  ---
  title: Paper Survey Agent
  emoji: 📑
  sdk: gradio
  sdk_version: 6.0.0
  app_file: app.py
  python_version: 3.11
  ---
  ```
- [X] Ensure `app.py` is at root level
- [X] Update `requirements.txt` for deployment

### 8.2 Deployment Steps
- [X] Create HuggingFace Space
- [X] Connect GitHub repository
- [X] Configure automatic deployment

---

## 9. Testing

### 9.1 Testing Environment
- [X] Create `notebooks/test_agent.ipynb` for interactive testing
- [X] Manual testing of full pipeline

### 9.2 Test Scenarios
- [X] Test with various research topics
- [X] Test error handling (invalid API key, no results)
- [X] Test progress reporting

---

## ✅ Completion Checklist

### Core Functionality
- [X] arXiv API integration works
- [X] Semantic Scholar API integration works
- [X] Paper search returns results
- [X] PDF download works
- [X] Text extraction works
- [X] Paper summarization works
- [X] Survey synthesis works
- [X] Full pipeline completes successfully

### Web Interface
- [X] UI displays input form
- [X] API key input works
- [X] Provider/model selection works
- [X] Progress indicator shows updates
- [X] Results display correctly
- [X] Clear button works

### Deployment
- [X] README has HuggingFace metadata
- [X] App deploys to Spaces
- [X] Public URL accessible
