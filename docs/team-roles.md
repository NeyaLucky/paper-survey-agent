# Розподіл завдань по ролях

## Команда

| Роль | Основна відповідальність | Хто працює |
|------|--------------------------|--------------|
| **Розробник 1** | Backend: API інтеграція та інструменти |Вероніка|
| **Розробник 2** | LLM: Агент, промпти, валідація |Дарина|
| **Розробник 3** | UI, Deployment, Документація |Денис|

---

## 👤 Розробник 1: Backend & API

**Фокус:** Інтеграція з науковими API та базові інструменти пошуку/ранжування

### Завдання

#### 1.1 Структура проєкту (спільно з Розробником 2)
- [X] Створити директорію `src/paper_survey_agent/apis/`
- [X] Створити директорію `src/paper_survey_agent/tools/`
- [X] Створити `__init__.py` файли

#### 1.2 Моделі даних (`src/paper_survey_agent/models/`)
- [X] `paper.py` - модель `Paper`:
  ```python
  class Paper(BaseModel):
      id: str
      title: str
      authors: list[str]
      abstract: str
      published_date: date
      source: str  # arxiv, semantic_scholar
      url: str
      pdf_url: str | None
      citations_count: int | None
      categories: list[str]
  ```

#### 1.3 arXiv API (`src/paper_survey_agent/apis/arxiv.py`)
- [ ] Встановити бібліотеку `arxiv`
- [ ] Імплементувати клас `ArxivAPI`:
  - [ ] Метод `search(query: str, max_results: int) -> list[Paper]`
  - [ ] Метод `get_paper_details(paper_id: str) -> Paper`
  - [ ] Конвертація результатів у модель `Paper`
- [ ] Обробка помилок та timeout
- [ ] Логування запитів

#### 1.4 Semantic Scholar API (`src/paper_survey_agent/apis/semantic_scholar.py`)
- [ ] Імплементувати клас `SemanticScholarAPI`:
  - [ ] HTTP клієнт (httpx або aiohttp)
  - [ ] Метод `search(query: str, max_results: int) -> list[Paper]`
  - [ ] Конвертація JSON у модель `Paper`
- [ ] Обробка rate limits (100 req/5 min)
- [ ] Retry логіка з exponential backoff

#### 1.5 Базовий клас API (`src/paper_survey_agent/apis/base.py`)
- [ ] Абстрактний клас `BaseScientificAPI`:
  ```python
  class BaseScientificAPI(ABC):
      @abstractmethod
      async def search(self, query: str, max_results: int) -> list[Paper]: ...
  ```

#### 1.6 Інструмент: Отримання публікацій (`src/paper_survey_agent/tools/retrieval.py`)
- [ ] Функція `retrieve_papers(query: str, sources: list[str] = None) -> list[Paper]`:
  - [ ] Паралельний виклик arXiv та Semantic Scholar
  - [ ] Об'єднання результатів
  - [ ] Обробка помилок окремих API

#### 1.7 Інструмент: Ранжування (`src/paper_survey_agent/tools/ranking.py`)
- [ ] Функція `rank_and_deduplicate(papers: list[Paper], topic: str, top_k: int = 15) -> list[Paper]`:
  - [ ] Дедуплікація за ID та fuzzy matching назв
  - [ ] Ранжування за релевантністю (TF-IDF або простий keyword matching)
  - [ ] Врахування цитувань та дати
  - [ ] Повернення топ-K результатів

#### 1.8 Тести для API та інструментів
- [ ] `tests/test_apis/test_arxiv.py` - з моками
- [ ] `tests/test_apis/test_semantic_scholar.py` - з моками
- [ ] `tests/test_tools/test_retrieval.py`
- [ ] `tests/test_tools/test_ranking.py`

### Залежності від інших
- Потребує моделі `Paper` (робить сам)
- Не залежить від LLM частини

### Результат
- Працюючий пошук публікацій з двох джерел
- Дедуплікація та ранжування
- Unit тести

---

## 👤 Розробник 2: LLM & Agent

**Фокус:** LLM інтеграція, агентна логіка, промпти, резюмування та синтез

### Завдання

#### 2.1 Структура проєкту (спільно з Розробником 1)
- [ ] Створити директорію `src/paper_survey_agent/llm/`
- [ ] Створити `src/paper_survey_agent/agent.py`
- [ ] Створити `src/paper_survey_agent/config.py`

#### 2.2 Конфігурація (`src/paper_survey_agent/config.py`)
- [ ] Клас `Settings` з Pydantic BaseSettings:
  ```python
  class Settings(BaseSettings):
      openai_api_key: str
      model_name: str = "gpt-4o-mini"
      max_papers: int = 15
      timeout: int = 300
      
      model_config = SettingsConfigDict(env_file=".env")
  ```
- [X] Створити `.env.dist`

#### 2.3 Моделі даних (`src/paper_survey_agent/models/`)
- [ ] `summary.py` - модель `PaperSummary`:
  ```python
  class PaperSummary(BaseModel):
      paper_id: str
      title: str
      key_findings: list[str]  # мін. 3
      methods: list[str]
      contributions: list[str]
      limitations: list[str]
      relevance_score: float  # 0-1
      summary_text: str
  ```
- [ ] `synthesis.py` - модель `SynthesisResult`:
  ```python
  class SynthesisResult(BaseModel):
      topic: str
      total_papers: int
      general_conclusions: list[str]
      current_trends: list[str]
      common_methodologies: list[str]
      future_directions: list[str]
      synthesis_text: str
      generated_at: datetime
  ```

#### 2.4 LLM клієнт (`src/paper_survey_agent/llm/client.py`)
- [ ] Клас `OpenAIClient`:
  - [ ] Ініціалізація з API ключем
  - [ ] Метод `complete(messages: list[dict]) -> str`
  - [ ] Метод `complete_json(messages: list[dict], schema: type) -> BaseModel`
  - [ ] Обробка помилок та retry

#### 2.5 Промпти (`src/paper_survey_agent/llm/prompts.py`)
- [ ] `SYSTEM_PROMPT` - системний промпт агента
- [ ] `PLANNING_PROMPT` - генерація пошукових запитів
- [ ] `SUMMARIZATION_PROMPT` - резюме публікації
- [ ] `SYNTHESIS_PROMPT` - синтез огляду

#### 2.6 Інструмент: Планування (`src/paper_survey_agent/tools/planning.py`)
- [ ] Функція `plan_queries(topic: str, llm_client) -> list[str]`:
  - [ ] Використання LLM для генерації 5-8 запитів
  - [ ] Валідація унікальності

#### 2.7 Інструмент: Резюмування (`src/paper_survey_agent/tools/summarization.py`)
- [ ] Функція `summarize_paper(paper: Paper, llm_client) -> PaperSummary`:
  - [ ] Промпт з назвою та abstract
  - [ ] Парсинг відповіді у `PaperSummary`

#### 2.8 Інструмент: Синтез (`src/paper_survey_agent/tools/synthesis.py`)
- [ ] Функція `synthesize_review(summaries: list[PaperSummary], topic: str, llm_client) -> SynthesisResult`:
  - [ ] Об'єднання всіх резюме
  - [ ] Генерація узагальненого огляду

#### 2.9 Валідація (`src/paper_survey_agent/tools/validation.py`)
- [ ] Функція `validate_summary(summary: PaperSummary) -> tuple[bool, list[str]]`
- [ ] Функція `validate_synthesis(result: SynthesisResult) -> tuple[bool, list[str]]`

#### 2.10 Агент (`src/paper_survey_agent/agent.py`)
- [ ] Клас `PaperSurveyAgent`:
  ```python
  class PaperSurveyAgent:
      async def run(self, topic: str) -> SynthesisResult:
          # 1. Planning
          queries = await self._planning_stage(topic)
          # 2. Retrieval
          papers = await self._retrieval_stage(queries)
          # 3. Ranking
          ranked = await self._ranking_stage(papers, topic)
          # 4. Summarization
          summaries = await self._summarization_stage(ranked)
          # 5. Synthesis
          result = await self._synthesis_stage(summaries, topic)
          # 6. Validation
          return result
  ```
- [ ] Callback для прогресу (для UI)
- [ ] Обробка помилок на кожному етапі

#### 2.11 Тести
- [ ] `tests/test_tools/test_planning.py`
- [ ] `tests/test_tools/test_summarization.py`
- [ ] `tests/test_tools/test_synthesis.py`
- [ ] `tests/test_tools/test_validation.py`
- [ ] `tests/test_agent.py`

### Залежності від інших
- Використовує `Paper` модель від Розробника 1
- Викликає `retrieve_papers` та `rank_and_deduplicate` від Розробника 1

### Результат
- Працюючий LLM клієнт
- Всі промпти
- Повний агент з пайплайном
- Unit тести

---

## 👤 Розробник 3: UI & Deployment

**Фокус:** Веб-інтерфейс, деплой, документація

### Завдання

#### 3.1 Налаштування проєкту
- [ ] Оновити `pyproject.toml` з усіма залежностями:
  ```toml
  [project]
  name = "paper-survey-agent"
  version = "0.1.0"
  dependencies = [
      "openai>=1.0.0",
      "arxiv>=2.0.0",
      "pydantic>=2.0.0",
      "pydantic-settings>=2.0.0",
      "python-dotenv>=1.0.0",
      "httpx>=0.25.0",
      "gradio>=4.0.0",
      "rapidfuzz>=3.0.0",
  ]
  
  [project.optional-dependencies]
  dev = ["pytest", "pytest-cov", "pytest-asyncio"]
  ```
- [ ] Створити `.gitignore`
- [ ] Створити `requirements.txt` для deployment

#### 3.2 Веб-інтерфейс (`demo/main.py`)

- [ ] Базовий Gradio інтерфейс у `demo/main.py` (рекомендований варіант):

```python
import gradio as gr

def create_app():
  with gr.Blocks(title="Paper Survey Agent") as app:
    gr.Markdown("# 📚 Paper Survey Agent")

    with gr.Row():
      topic_input = gr.Textbox(label="Тема дослідження")
      api_key_input = gr.Textbox(label="OpenAI API Key", type="password")

    submit_btn = gr.Button("🔍 Почати огляд", variant="primary")

    progress = gr.Textbox(label="Прогрес", lines=3)
    output = gr.Markdown(label="Результат")

    submit_btn.click(fn=run_survey, inputs=[topic_input, api_key_input], outputs=[progress, output])

  return app
```
- [ ] Відображення прогресу виконання
- [ ] Форматування результату (Markdown)
- [ ] Обробка помилок з повідомленнями

#### 3.3 Точка входу (`app.py` в корені)
- [ ] Створити `app.py`:
  ```python
  from src.paper_survey_agent.ui.app import create_app
  
  if __name__ == "__main__":
      app = create_app()
      app.launch()
  ```

#### 3.4 Deployment на HuggingFace Spaces
- [ ] Створити акаунт на HuggingFace (якщо немає)
- [ ] Створити новий Space (Gradio SDK)
- [ ] Завантажити файли або підключити GitHub
- [ ] Протестувати deployment
- [ ] Отримати публічний URL

#### 3.5 Документація

**README.md:**
- [ ] Опис проєкту
- [ ] Скріншот інтерфейсу
- [ ] Інструкції встановлення
- [ ] Інструкції запуску
- [ ] Приклад використання
- [ ] Посилання на HuggingFace Space

**Лист для здачі:**
- [ ] Підготувати текст листа (шаблон в tasks.md)
- [ ] Зібрати інформацію від команди
- [ ] Відправити після 19 грудня

#### 3.6 Фінальне тестування
- [ ] Протестувати повний flow локально
- [ ] Протестувати на HuggingFace з 2-3 темами
- [ ] Задокументувати знайдені проблеми

### Залежності від інших
- Чекає на готовий агент від Розробника 2
- UI викликає `PaperSurveyAgent.run()`

### Результат
- Працюючий веб-інтерфейс
- Задеплоєний сервіс на HuggingFace
- README та документація
- Готовий лист для здачі

---

## 📅 Таймлайн та синхронізація

### День 1 (17 грудня)

| Час | Розробник 1 | Розробник 2 | Розробник 3 |
|-----|-------------|-------------|-------------|
| Ранок | Структура + моделі `Paper` | Структура + config | `pyproject.toml` + `.gitignore` |
| День | arXiv API | LLM клієнт + промпти | Базовий UI (mock) |
| Вечір | Semantic Scholar API | Моделі `Summary`, `Synthesis` | README (draft) |

### День 2 (18 грудня - ДЕДЛАЙН)

| Час | Розробник 1 | Розробник 2 | Розробник 3 |
|-----|-------------|-------------|-------------|
| Ранок | `retrieve_papers` | `summarize_paper`, `synthesize_review` | Підключення UI до агента |
| День | `rank_and_deduplicate` | Агент + валідація | Deployment на HuggingFace |
| Вечір | Тести + фікси | Тести + фікси | Тестування + документація |

---

## 🔗 Точки інтеграції

### API між компонентами

```
Розробник 1                    Розробник 2                    Розробник 3
─────────────                  ─────────────                  ─────────────
    │                              │                              │
    │  Paper модель                │                              │
    ├─────────────────────────────►│                              │
    │                              │                              │
    │  retrieve_papers()           │                              │
    ├─────────────────────────────►│                              │
    │                              │                              │
    │  rank_and_deduplicate()      │                              │
    ├─────────────────────────────►│                              │
    │                              │                              │
    │                              │  PaperSurveyAgent           │
    │                              ├─────────────────────────────►│
    │                              │                              │
    │                              │  run() -> SynthesisResult   │
    │                              ├─────────────────────────────►│
```

### Контракти (узгодити на початку)

**1. Модель Paper (Розробник 1 → Розробник 2):**
```python
class Paper(BaseModel):
    id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: date
    source: str
    url: str
    pdf_url: str | None = None
    citations_count: int | None = None
    categories: list[str] = []
```

**2. Функція retrieve_papers (Розробник 1 → Розробник 2):**
```python
async def retrieve_papers(query: str, max_results: int = 20) -> list[Paper]
```

**3. Функція rank_and_deduplicate (Розробник 1 → Розробник 2):**
```python
def rank_and_deduplicate(papers: list[Paper], topic: str, top_k: int = 15) -> list[Paper]
```

**4. Агент (Розробник 2 → Розробник 3):**
```python
class PaperSurveyAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"): ...
    
    async def run(self, topic: str, progress_callback: Callable = None) -> SynthesisResult: ...
```

---

## ✅ Чеклист готовності до здачі

### Розробник 1
- [ ] API arXiv працює
- [ ] API Semantic Scholar працює
- [ ] `retrieve_papers()` повертає публікації
- [ ] `rank_and_deduplicate()` працює
- [ ] Код запушений в репозиторій

### Розробник 2
- [ ] LLM клієнт працює
- [ ] Всі промпти написані
- [ ] Агент виконує повний пайплайн
- [ ] Валідація працює
- [ ] Код запушений в репозиторій

### Розробник 3
- [ ] UI відображає форму введення
- [ ] UI показує прогрес
- [ ] UI відображає результат
- [ ] Сервіс задеплоєний на HuggingFace
- [ ] README оновлений
- [ ] Лист підготовлений

### Спільно
- [ ] Локальний тест проходить
- [ ] HuggingFace тест проходить
- [ ] Проєкт зареєстрований (до 19.12)
- [ ] Лист відправлений (після 19.12)
