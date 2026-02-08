# CRAAP Analysis API

A reusable Python API for comprehensive blog credibility evaluation using the CRAAP test framework.

## What is CRAAP?

CRAAP stands for:
- **Currency**: How timely is the information?
- **Relevance**: How useful is this information?
- **Authority**: Who is behind the content?
- **Accuracy**: How correct and reliable is the content?
- **Purpose**: Why does this blog exist?

## Features

- 🔍 **Automated Content Analysis**: Download and extract blog content automatically
- 📊 **Comprehensive Evaluation**: Analyze all five CRAAP dimensions
- 🤖 **AI-Powered Insights**: Uses LLM agents for intelligent content assessment
- 🔎 **Authority Verification**: Web search-based reputation analysis for authors and publishers
- 📦 **Batch Processing**: Analyze multiple blogs in parallel
- 🎯 **Flexible API**: Async and sync interfaces available

## Installation

```bash
pip install trafilatura pydantic
# Also requires the 'agents' library (assumed to be available in your environment)
```

## Quick Start

### Basic Usage

```python
from craap_api import analyze_blog_sync, print_analysis_report

# Analyze a blog post
result = analyze_blog_sync("https://example.com/blog-post")

# Print formatted report
print_analysis_report(result)
```

### Async Usage

```python
import asyncio
from craap_api import analyze_blog, print_analysis_report

async def main():
    result = await analyze_blog("https://example.com/blog-post")
    print_analysis_report(result)

asyncio.run(main())
```

### Without Authority Analysis (Faster)

```python
# Skip web search for author/publisher reputation
result = analyze_blog_sync(
    "https://example.com/blog-post",
    analyze_author=False,
    analyze_publisher=False
)
```

### Batch Analysis

```python
from craap_api import analyze_blog_batch

urls = [
    "https://blog1.com/post",
    "https://blog2.com/article",
    "https://blog3.com/story"
]

results = await analyze_blog_batch(urls)
```

## API Reference

### Main Functions

#### `analyze_blog(url, analyze_author=True, analyze_publisher=True)`
Perform comprehensive CRAAP analysis on a blog post.

**Parameters:**
- `url` (str): URL of the blog post to analyze
- `analyze_author` (bool): Whether to perform author authority analysis (requires web search)
- `analyze_publisher` (bool): Whether to perform publisher authority analysis (requires web search)

**Returns:** `CRAAPAnalysisResult` object

**Raises:** `ValueError` if blog cannot be downloaded

#### `analyze_blog_sync(url, analyze_author=True, analyze_publisher=True)`
Synchronous wrapper for `analyze_blog()`.

#### `analyze_blog_batch(urls, analyze_author=True, analyze_publisher=True)`
Analyze multiple blog posts in parallel.

**Parameters:**
- `urls` (List[str]): List of blog URLs to analyze
- `analyze_author` (bool): Whether to perform author authority analysis
- `analyze_publisher` (bool): Whether to perform publisher authority analysis

**Returns:** List of `CRAAPAnalysisResult` objects

### Data Models

#### `CRAAPAnalysisResult`
Complete analysis result containing:
- `url`: Original blog URL
- `metadata`: BlogMetadata object
- `currency`: CurrencyInfo object
- `accuracy`: AccuracyInfo object
- `purpose`: IntentInfo object
- `author_authority`: Optional AuthorityVerdict object
- `publisher_authority`: Optional PublisherVerdict object
- `raw_metadata`: Dictionary with trafilatura metadata

**Methods:**
- `to_dict()`: Convert result to dictionary format

#### `BlogMetadata`
- `author_name`: Name of the author
- `is_anonymous`: Whether author is anonymous/pseudonymous
- `author_affiliation`: Professional affiliation
- `blog_name`: Name of the blog
- `publisher_name`: Name of the publisher
- `publishing_date`: Publication date
- `summary`: Content summary

#### `CurrencyInfo`
- `requires_current_info`: Whether topic needs up-to-date info
- `is_maintained`: Whether blog is actively maintained
- `published_date`: Publication date from content
- `last_updated`: Last update date
- `has_recent_references`: Whether references are recent

#### `AccuracyInfo`
- `has_sources`: Whether sources/citations provided
- `verifiable`: Whether content can be verified
- `error_free`: Whether writing is error-free
- `facts_vs_opinions`: Analysis of fact/opinion distinction

#### `IntentInfo`
- `tone`: Tone of the text
- `style`: Writing style
- `bias`: Bias analysis
- `sentiment`: Overall sentiment
- `hate`: Hate speech analysis

#### `AuthorityVerdict`
- `public_sentiment`: Overall public sentiment
- `positive_mentions`: Positive coverage
- `negative_mentions`: Controversies/concerns
- `sources`: Source list
- `summary`: Overall assessment

#### `PublisherVerdict`
- `ownership_and_funding`: Ownership structure
- `editorial_standards`: Editorial practices
- `political_bias`: Political leaning
- `factual_reliability`: Accuracy track record
- `public_perception`: Expert/public reputation
- `summary`: Overall assessment

### Utility Functions

#### `download_blog(url)`
Download and extract blog content.

**Returns:** Tuple of (text, metadata_dict)

#### `print_analysis_report(result)`
Print formatted CRAAP analysis report to console.

## Advanced Usage

### Custom Analysis Workflow

```python
from craap_api import (
    download_blog,
    extract_blog_metadata,
    analyze_currency,
    analyze_accuracy,
    analyze_purpose,
    analyze_author_authority,
    analyze_publisher_authority
)

async def custom_analysis(url):
    # Download content
    text, raw_metadata = download_blog(url)
    
    # Extract metadata
    metadata = await extract_blog_metadata(text, raw_metadata)
    
    # Run only specific analyses
    currency = await analyze_currency(text)
    accuracy = await analyze_accuracy(text)
    
    # Custom processing
    return {
        "metadata": metadata,
        "currency": currency,
        "accuracy": accuracy
    }
```

### Export to JSON

```python
import json

result = analyze_blog_sync("https://example.com/blog")
json_data = json.dumps(result.to_dict(), indent=2)
print(json_data)
```

### Integration Example

```python
from craap_api import analyze_blog_sync

def evaluate_source(url, min_credibility="medium"):
    """Evaluate if a source meets credibility requirements."""
    try:
        result = analyze_blog_sync(url)
        
        # Custom credibility scoring logic
        score = 0
        if result.accuracy.has_sources:
            score += 1
        if result.accuracy.verifiable:
            score += 1
        if not result.metadata.is_anonymous:
            score += 1
        
        credible = score >= 2
        return {
            "url": url,
            "credible": credible,
            "score": score,
            "result": result
        }
    except Exception as e:
        return {"url": url, "error": str(e)}
```

## Performance Considerations

- **Authority analysis** (author/publisher) requires web searches and is slower
- **Batch processing** runs analyses in parallel for better performance
- **Text truncation**: Only first 2000 characters analyzed for efficiency
- Consider caching results for frequently analyzed sources

## Error Handling

```python
from craap_api import analyze_blog_sync

try:
    result = analyze_blog_sync("https://example.com/blog")
except ValueError as e:
    print(f"Failed to analyze blog: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## CLI Usage

```bash
# Run analysis from command line
python craap_api.py "https://example.com/blog-post"
```

## Contributing

The API is built on top of:
- `trafilatura`: Web scraping and content extraction
- `pydantic`: Data validation
- `agents`: LLM agent framework with web search capabilities

## License

See LICENSE file in the repository.

## Related Files

- `analyze_blog.py`: Original implementation
- `person_reputation_agent.py`: Author reputation analysis
- `publisher_reputation_agent.py`: Publisher reputation analysis
- `CRAAP.md`: CRAAP methodology documentation
