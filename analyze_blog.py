"""Blog analysis module for evaluating content accuracy, currency, and intent."""

import asyncio
import sys
from typing import Optional, Tuple

import trafilatura
from pydantic import BaseModel, Field

from agents import Agent, Runner, ModelSettings

class AccuracyInfo(BaseModel):
    """Information about the accuracy and credibility of blog content."""
    
    has_sources: bool = Field(description="Whether the blog provides sources, citations, or evidence")
    verifiable: bool = Field(description="Whether the content can be verified through other sources")
    error_free: bool = Field(description="Whether the writing is free of obvious errors")
    facts_vs_opinions: str = Field(description="Analysis of how facts and opinions are distinguished")

class CurrencyInfo(BaseModel):
    """Information about the currency and timeliness of blog content."""
    
    requires_current_info: bool = Field(description="Whether the topic requires up-to-date information")
    is_maintained: bool = Field(description="Whether the blog shows signs of being maintained")
    published_date: str = Field(description="When the blog post was published")
    last_updated: str = Field(description="When the blog post was last updated")
    has_recent_references: bool = Field(description="Whether the blog has recent references")

async def analyze_currency(text: str) -> CurrencyInfo:
    """Use a language model to identify currency of the text.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        CurrencyInfo: Contains currency analysis
    """
    prompt = f"""
Analyze the following blog content to identify:

* Is the topic one where up-to-date information matters (e.g., technology, health, current events)?
* Does the blog show signs of being maintained?

What to look for:

* When was the blog post published or last updated?
* Visible publication/update dates
* Other dates
* Recent references

Content preview:
{text[:1000] if text else "No content available"}
"""

    extraction_agent = Agent(
        name="currency_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=CurrencyInfo,
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

async def analyze_accuracy(text: str) -> AccuracyInfo:
    """Use a language model to identify factual accuracy of the text.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        AccuracyInfo: Contains accuracy analysis
    """
    prompt = f"""
Analyze the following blog content to identify:

* Does the blog provide sources, data, citations, or evidence?
* Can the content be verified through other trustworthy sources?
* Is the writing free of obvious errors or contradictions?
* Does the author distinguish between facts and opinions?

What to look for:

* Citations or references
* External links to credible sources
* Balanced, evidence-supported statements

Content preview:
{text[:1000] if text else "No content available"}
"""
    
    extraction_agent = Agent(
        name="accuracy_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=AccuracyInfo,
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

class IntentInfo(BaseModel):
    """Information about the intent and tone of blog content."""
    
    tone: str = Field(description="Tone of the text (objective or opinion-driven)")
    style: str = Field(description="Writing style of the text")
    bias: str = Field(description="Bias towards social and political groups")
    sentiment: str = Field(description="Overall sentiment of the text")
    hate: str = Field(description="Analysis of hate speech or politically incorrect speech")

async def analyze_intent(text: str) -> IntentInfo:
    """Use a language model to identify intent of the author.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        IntentInfo: Contains intent analysis
    """
    prompt = f"""
Analyze the following blog content to identify:
- Tone and style of the text. Is it objective or opinion-driven?
- Intent of the author. Is the blog trying to inform, persuade, entertain, or sell something? Are there disclosure statements?
- Bias towards social and political groups. Are ads, affiliate links, or sponsored content influencing the information?
- Hate speech: identify possible vulgar, hate speech or politically incorrect speech

If any information is not available, use "Unknown".

Content preview:
{text[:1000] if text else "No content available"}
"""
    
    extraction_agent = Agent(
        name="intent_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=IntentInfo,
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

class BlogMetadata(BaseModel):
    """Metadata information about the blog post."""
    
    author_name: str = Field(description="Name of the author")
    is_anonymous: bool = Field(description="Whether the author is anonymous or using a pseudonym")
    author_affiliation: str = Field(description="Affiliation of the author")
    blog_name: str = Field(description="Name of the blog")
    publisher_name: str = Field(description="Name of the publisher")
    publishing_date: str = Field(description="Date of publication")
    summary: str = Field(description="Short summary of the blog content")


async def extract_blog_info_with_llm(text: str) -> BlogMetadata:
    """Use a language model to extract blog metadata.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        BlogMetadata: Contains blog metadata fields
    """
    prompt = f"""
Analyze the following blog content to identify:
1. The name of the author (person who wrote the article)
2. If person name is real or pseudonym
3. Affiliation of the author (employee and professional position of the author)
4. The name of the blog (title of the blog site or section)
5. The name of the publisher (organization/company publishing the blog)
6. Date of the publishing
7. Short summary of the blog.

If any information is not available, use "Unknown".

Content preview:
{text[:1000] if text else "No content available"}
"""
    
    extraction_agent = Agent(
        name="blog_info_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=BlogMetadata,
    )
    
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

def download_blog(url: str) -> Tuple[Optional[str], dict]:
    """Download a blog page and extract text and hyperlinks using trafilatura.
    
    Args:
        url: The URL of the blog to download
    
    Returns:
        Tuple of extracted text (or None) and metadata dict
    """
    downloaded = trafilatura.fetch_url(url)
    
    if not downloaded:
        return None, {"error": "Failed to download the page"}
    
    metadata = trafilatura.extract_metadata(downloaded)
    metadata_dict = metadata.as_dict() if metadata else {}
    
    text = trafilatura.extract(
        downloaded,
        include_comments=True,
        include_tables=True,
        include_links=True,
        output_format="xml"
    )
    return text, metadata_dict
    


async def analyze_blog(url: str) -> None:
    """Analyze a blog post for accuracy, currency, intent, and reputation.
    
    Args:
        url: URL of the blog post to analyze
    """
    blog_text, metadata = download_blog(url)
    
    if blog_text is None:
        print(f"Error: {metadata.get('error', 'Unknown error')}")
        return
    
    print("Metadata:", metadata)
    
    print("\n" + "=" * 50)
    print("Extracting blog information using LLM...")
    blog_info = await extract_blog_info_with_llm(
        f"URL: {metadata}\n\n{blog_text or ''}"
    )
    print("\nAuthor Name:", blog_info.author_name)
    print("\nAuthor Affiliation:", blog_info.author_affiliation)
    print("Blog Name:", blog_info.blog_name)
    print("Is anonymous:", blog_info.is_anonymous)
    print("Publishing date:", blog_info.publishing_date)
    print("Publisher Name:", blog_info.publisher_name)
    print("Summary:", blog_info.summary)

    from person_reputation_agent import analyze_person
    from publisher_reputation_agent import analyze_publisher
    
    print("\n" + "=" * 50)
    print("Analyzing publisher reputation...")
    publisher_reputation = await analyze_publisher(blog_info.publisher_name)
    print("Publisher Reputation:", publisher_reputation)
    
    person_reputation = "Unknown"
    if not blog_info.is_anonymous:
        print("\n" + "=" * 50)
        print("Analyzing author reputation...")
        person_reputation = await analyze_person(
            f"{blog_info.author_name} {blog_info.author_affiliation} {blog_info.publisher_name}"
        )
        print("Person Reputation:", person_reputation)
    
    print("\n" + "=" * 50)
    print("Analyzing intent...")
    intent_info = await analyze_intent(blog_text)
    print("Intent Info:")
    print(f"  Tone: {intent_info.tone}")
    print(f"  Style: {intent_info.style}")
    print(f"  Bias: {intent_info.bias}")
    print(f"  Sentiment: {intent_info.sentiment}")
    print(f"  Hate: {intent_info.hate}")

    print("\n" + "=" * 50)
    print("Analyzing accuracy...")
    accuracy_info = await analyze_accuracy(blog_text)
    print("Accuracy Info:")
    print(f"  Has sources: {accuracy_info.has_sources}")
    print(f"  Verifiable: {accuracy_info.verifiable}")
    print(f"  Error free: {accuracy_info.error_free}")
    print(f"  Facts vs opinions: {accuracy_info.facts_vs_opinions}")

    print("\n" + "=" * 50)
    print("Analyzing currency...")
    currency_info = await analyze_currency(blog_text)
    print("Currency Info:")
    print(f"  Requires current info: {currency_info.requires_current_info}")
    print(f"  Is maintained: {currency_info.is_maintained}")
    print(f"  Published date: {currency_info.published_date}")
    print(f"  Last updated: {currency_info.last_updated}")
    print(f"  Has recent references: {currency_info.has_recent_references}")

async def main() -> None:
    """Main entry point for the blog analysis script."""
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/blog"
    await analyze_blog(url)


if __name__ == "__main__":
    asyncio.run(main())
