# CRAAP API - Quick Start Guide

## 🚀 Installation

The API requires these dependencies (add to your project):
```bash
pip install trafilatura pydantic
# Also needs: agents library with WebSearchTool
```

## 💻 Basic Usage

```python
from craap_api import analyze_blog_sync, print_analysis_report

# Analyze a blog post
result = analyze_blog_sync("https://example.com/blog-post")

# Print formatted report
print_analysis_report(result)
```

## ⚡ Fast Mode (No Web Search)

```python
# Skip authority checks for faster analysis
result = analyze_blog_sync(
    "https://example.com/blog-post",
    analyze_author=False,
    analyze_publisher=False
)
```

## 🔄 Async Usage

```python
import asyncio
from craap_api import analyze_blog

async def main():
    result = await analyze_blog("https://example.com/blog")
    print(result.metadata.author_name)
    print(result.accuracy.has_sources)

asyncio.run(main())
```

## 📦 Batch Processing

```python
from craap_api import analyze_blog_batch

urls = ["url1", "url2", "url3"]
results = await analyze_blog_batch(urls)
```

## 📊 Access Results

```python
result = analyze_blog_sync(url)

# Metadata
print(result.metadata.author_name)
print(result.metadata.publisher_name)
print(result.metadata.is_anonymous)

# Currency
print(result.currency.published_date)
print(result.currency.is_maintained)

# Accuracy
print(result.accuracy.has_sources)
print(result.accuracy.verifiable)

# Purpose
print(result.purpose.tone)
print(result.purpose.bias)
print(result.purpose.sentiment)

# Authority (if enabled)
if result.author_authority:
    print(result.author_authority.summary)
```

## 💾 Export to JSON

```python
import json

result = analyze_blog_sync(url)
json_data = json.dumps(result.to_dict(), indent=2, default=str)
print(json_data)
```

## 🎯 Custom Scoring

```python
result = analyze_blog_sync(url)

score = 0
if result.accuracy.has_sources: score += 1
if result.accuracy.verifiable: score += 1
if not result.metadata.is_anonymous: score += 1

print(f"Credibility: {score}/3")
```

## 🔧 Selective Analysis

```python
from craap_api import download_blog, analyze_accuracy

text, metadata = download_blog(url)
if text:
    accuracy = await analyze_accuracy(text)
    print(accuracy.has_sources)
```

## ⚠️ Error Handling

```python
try:
    result = analyze_blog_sync(url)
except ValueError as e:
    print(f"Failed to download: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## 📖 More Information

- **Full API Reference**: See `CRAAP_API_README.md`
- **Examples**: See `example_craap_usage.py`
- **Implementation Details**: See `CRAAP_API_SUMMARY.md`
- **Main Module**: `craap_api.py`

## 🎓 What is CRAAP?

- **C**urrency - How timely is the information?
- **R**elevance - How useful is this information?
- **A**uthority - Who is behind the content?
- **A**ccuracy - How correct and reliable is the content?
- **P**urpose - Why does this blog exist?

## 🏃 CLI Usage

```bash
python craap_api.py "https://example.com/blog-post"
```

---

**Need help?** Check the full documentation in `CRAAP_API_README.md`
