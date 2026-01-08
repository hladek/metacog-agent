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
Analyze the currency and timeliness of this blog content.

Your task:
1. Determine if this topic requires up-to-date information (e.g., technology, health, current events, regulations)
2. Assess if the blog appears to be actively maintained
3. Identify all dates mentioned: publication date, last update, and reference dates
4. Evaluate if references and sources are recent

Look for:
- Explicit publication/update timestamps
- Date stamps in the content
- Dates in citations or references
- Signs of ongoing maintenance (e.g., "Updated on...")
- Recency of external sources mentioned

Provide clear boolean values and specific date strings when available (use "Not found" if absent).

Content to analyze:
{text[:2000] if text else "No content available"}
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
Evaluate the accuracy and credibility of this blog content.

Your task:
1. Identify if sources, citations, data, or evidence are provided
2. Determine if claims can be verified through external trustworthy sources
3. Detect obvious errors, contradictions, or inconsistencies in the writing
4. Assess how the author distinguishes facts from opinions

Look for:
- Academic or journalistic citations (footnotes, references, links)
- Links to credible external sources (research papers, official sites, reputable publications)
- Data with clear provenance
- Use of hedging language ("studies suggest", "research shows")
- Clear labeling of opinions vs facts
- Logical consistency throughout the text
- Factual errors or misleading statements

Provide clear boolean assessments and descriptive analysis for facts vs opinions.

Content to analyze:
{text[:2000] if text else "No content available"}
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
Analyze the intent, tone, and potential bias of this blog content.

Your task:
1. Tone: Determine if the writing is objective, opinion-driven, emotional, or promotional
2. Style: Identify the writing style (journalistic, academic, conversational, marketing, etc.)
3. Bias: Assess bias toward or against social, political, or ideological groups
4. Sentiment: Classify overall sentiment (positive, negative, neutral, mixed)
5. Hate speech: Identify any vulgar, hateful, discriminatory, or offensive language

Author intent to evaluate:
- Is the primary purpose to inform, persuade, entertain, or sell?
- Are there disclosure statements for sponsorships, affiliates, or conflicts of interest?
- Are ads, affiliate links, or sponsored content present?
- Is the language inflammatory or deliberately polarizing?

Provide descriptive assessments. Use "None detected" or "Not present" rather than "Unknown" when elements are absent.

Content to analyze:
{text[:2000] if text else "No content available"}
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
    author_language: str = Field(description="Primary language the author writes in")
    blog_name: str = Field(description="Name of the blog")
    publisher_name: str = Field(description="Name of the publisher")
    publisher_country: str = Field(description="Country where the publisher is based")
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
Extract structured metadata from this blog post.

Required information:
1. Author name: Full name of the person who wrote the blog
2. Author status: Determine if the name appears to be real (with credentials) or a pseudonym/anonymous
3. Author affiliation: Employment, professional title, organizational association, or credentials
4. Author language: Primary language the author writes in (e.g., "English", "Spanish", "French")
5. Blog name: Title of the blog site or section (not the post title)
6. Publisher name: Organization, company, or platform publishing the blog
7. Publisher country: Country where the publisher is based
8. Publication date: When the post was originally published
9. Summary: A concise 2-3 sentence summary of the blog's main points

Guidelines:
- For unknown/missing fields, use "Unknown"
- For author status, consider: presence of bio, credentials, linked profiles, consistency with real identity
- Distinguish between the author (writer), blog name (site), and publisher (organization)
- Extract dates in a consistent format (YYYY-MM-DD if possible)
- For author language, identify the primary language they write in based on the content
- For publisher country, look for location information, domain extensions, or contextual clues

Content to analyze:
{text[:2000] if text else "No content available"}
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
    print("Author Affiliation:", blog_info.author_affiliation)
    print("Author Language:", blog_info.author_language)
    print("Blog Name:", blog_info.blog_name)
    print("Is anonymous:", blog_info.is_anonymous)
    print("Publishing date:", blog_info.publishing_date)
    print("Publisher Name:", blog_info.publisher_name)
    print("Publisher Country:", blog_info.publisher_country)
    print("Summary:", blog_info.summary)

    from person_reputation_agent import analyze_person
    from publisher_reputation_agent import analyze_publisher
    
    print("\n" + "=" * 50)
    print("Analyzing publisher reputation...")
    publisher_reputation = await analyze_publisher(blog_info.publisher_name + " from " + blog_info.publisher_country + " in " + blog_info.author_language + " language" )
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
