# CRAAP Blog Analyzer

A Streamlit web application that evaluates the credibility and reliability of blog posts using the **CRAAP test** framework, powered by OpenAI-based AI agents.

## What is CRAAP?

The **CRAAP Test** is an information evaluation framework developed by librarians at California State University, Chico. It provides five criteria for assessing any information source:

| Criterion | Question |
|-----------|----------|
| **C**urrency | How timely is the information? |
| **R**elevance | How useful is it for your needs? |
| **A**uthority | Who is behind the content? |
| **A**ccuracy | How correct and reliable is it? |
| **P**urpose | Why does this content exist? |

CRAAP overlaps with similar frameworks: **RADAR** (Relevance, Authority, Date, Appearance, Reason) and **SIFT** (Stop, Investigate, Find, Trace). This tool supports all three mental models.

---

## Features

- **Automatic blog download** — fetches and parses any public blog URL using [trafilatura](https://trafilatura.readthedocs.io/)
- **Currency analysis** — evaluates publication date, maintenance, and link freshness
- **Relevance assessment** — user answers questions about their needs, then AI evaluates fit
- **Authority analysis** — web-searches the author and publisher to assess reputation and credibility
- **Accuracy analysis** — extracts verifiable facts, searches the web to fact-check each one
- **Purpose analysis** — detects tone, writing style, political/ideological bias, and hate speech
- **Save & load analyses** — results are automatically saved as JSON for later review

---

## Architecture

```
metacog-agent/
├── app.py            # Streamlit web UI
├── craap_api.py      # Reusable Python API (can be used independently)
├── craap_results/    # Auto-generated JSON analysis output files
├── pyproject.toml
└── CRAAP.md          # CRAAP framework reference notes
```

### `craap_api.py` — Core API

The API module can be used independently of the Streamlit UI:

| Function | Description |
|----------|-------------|
| `analyze_blog(url)` | Full CRAAP analysis, returns `CRAAPAnalysisResult` |
| `analyze_blog_batch(urls)` | Analyze multiple URLs in parallel |
| `analyze_blog_sync(url)` | Synchronous wrapper for `analyze_blog` |
| `download_blog(url)` | Download and extract text + metadata from a URL |
| `save_analysis_to_json(result)` | Save result to a timestamped JSON file |
| `load_analysis_from_json(path)` | Load a previously saved result |
| `assess_user_relevance(content, answers)` | AI assessment of user relevance answers |
| `assess_user_purpose_analysis(content, answers)` | AI assessment of user purpose answers |

### Key data models

- `CRAAPAnalysisResult` — top-level result dataclass containing all analysis fields
- `BlogMetadata` — author, publisher, date, summary
- `VerifiedFactsResult` / `VerifiedFact` — facts with web-verified verdicts
- `AuthorityVerdict` — author reputation from web search
- `PublisherVerdict` — publisher credibility from web search
- `IntentInfo` — tone, style, bias, sentiment, hate speech

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An **OpenAI API key** with access to a model that supports tool use (e.g. `gpt-4o`)

---

## Installation

```bash
git clone <repo-url>
cd metacog-agent
uv sync
```

Or with pip:

```bash
pip install -e .
```

---

## Configuration

Export your OpenAI API key before running:

```bash
export OPENAI_API_KEY=your-key-here
```

Optionally, set a custom output directory for saved analyses (default: `craap_results/`):

```bash
export CRAAP_OUTPUT_DIR=/path/to/output
```

---

## Running the app

```bash
uv run streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Using the API directly

```python
import asyncio
from craap_api import analyze_blog, analyze_blog_sync

# Synchronous
result = analyze_blog_sync("https://example.com/some-blog-post")
print(result.metadata.author_name)
print(result.currency)
print(result.accuracy_text)

# Async
result = asyncio.run(analyze_blog("https://example.com/some-blog-post"))

# Batch
from craap_api import analyze_blog_batch
results = asyncio.run(analyze_blog_batch([
    "https://example.com/post-1",
    "https://example.com/post-2",
]))

# Save / load
from craap_api import save_analysis_to_json, load_analysis_from_json
path = save_analysis_to_json(result)
result = load_analysis_from_json(path)
```

### Disable authority analysis (faster, no web search)

```python
result = analyze_blog_sync(url, analyze_author=False, analyze_publisher=False)
```

---

## How it works

1. **Download** — `trafilatura` fetches the page and extracts clean text, links, and metadata (author, date, publisher).
2. **Metadata extraction** — an LLM agent structures the raw metadata into `BlogMetadata`.
3. **Parallel analysis** — four agents run concurrently:
   - Currency agent → Markdown report on timeliness
   - Accuracy agent → Markdown report on reliability
   - Facts agent → list of verifiable claims with Google search URLs
   - Purpose agent → tone, bias, sentiment, hate speech
4. **Fact verification** — each extracted fact is independently web-searched and fact-checked in parallel.
5. **Authority analysis** — two web-search agents investigate the author and publisher (optional).
6. **Auto-save** — the complete result is saved as a JSON file in `craap_results/`.

---

## Limitations

- AI analysis reflects the biases and limitations of the underlying language model. Use results as a supplementary tool, not the sole basis for evaluation.
- Authority and fact-verification steps require web search and consume more API calls and time.
- Blog download depends on `trafilatura` being able to extract content; paywalled or JavaScript-heavy pages may not parse correctly.
- The accuracy of fact-checking depends on what the web search returns at the time of analysis.
