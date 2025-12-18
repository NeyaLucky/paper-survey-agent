# Здача роботи: Paper Survey Agent

## Задача

Створення LLM-based агента для автоматизованого огляду наукової літератури з пошуком в arXiv та Semantic Scholar.

## Компоненти системи

### Джерела даних
- **arXiv API** - пошук наукових статей через офіційний API
- **Semantic Scholar API** - пошук з даними про цитування

### Пошук та обробка
- **Query Refinement**: LLM оптимізує пошуковий запит користувача
- **Parallel Retrieval**: Паралельні запити до обох API
- **Deduplication**: Fuzzy matching назв для видалення дублікатів
- **Ranking**: Комбінований скоринг (relevance + citations + recency + PDF bonus)
- **PDF Processing**: Завантаження PDF та екстракція тексту (pdfplumber)

### LLM
- **Провайдер**: OpenRouter (за замовчуванням), Groq
- **Моделі**: Llama 3.3 70B, Qwen, Nova, та інші безкоштовні
- **Інтеграція**: LiteLLM для уніфікованого API
- API ключ вводиться користувачем через UI

### Summarization
- **Paper Summarization**: LLM читає повний текст кожної статті
- **Structured Output**: JSON з summary та key_findings
- **Concurrent Processing**: Асинхронна обробка з семафором

### Survey Synthesis
- **Literature Review**: LLM генерує узгоджений огляд літератури
- **Trends & Conclusions**: Виявлення трендів, методологій, висновків
- **Citations**: Посилання на джерела в огляді

### UI
**Gradio** з можливостями:
- Вибір провайдера та моделі (динамічне оновлення)
- Введення API ключа (password field)
- Progress tracking з етапами
- Відображення результатів:
  - Survey report (Markdown)
  - Individual paper summaries (Accordion)
- Example topics

### Архітектура
- **Agent Pattern**: PaperSurveyAgent з pipeline етапами
- **Tools**: Окремі інструменти для кожного етапу
- **Type Safety**: Pydantic моделі (Paper, ProcessedPaper, SummarizedPaper)
- **Logging**: Loguru
- **Retry Logic**: Tenacity для LLM та API запитів
- **Async**: Асинхронна обробка для паралелізації

## Виконання

*Backend: API integration, retrieval, ranking, PDF processing* - **Veronika Lakiza**
*LLM: Agent, prompts, summarization, synthesis* - **Daryna Vasylashko**
*UI, Deployment, Documentation, Cleaning* - **Denys Koval**

## Посилання

- **Deployed Service**: https://huggingface.co/spaces/ai-department-lpnu/paper-survey-agent
- **Source Code**: https://github.com/NeyaLucky/paper-survey-agent

## Інструкції з запуску

### Локально
```bash
# 1. Clone та встановити залежності
git clone https://github.com/NeyaLucky/paper-survey-agent.git
cd paper-survey-agent
make install

# 2. (Опційно) Налаштувати .env
cp .env.dist .env
# API ключ можна також ввести через UI

# 3. Запустити додаток
make run-app
```

### HF Spaces
Автоматичний deploy з main branch - всі необхідні файли (app.py, requirements.txt) в root директорії.
