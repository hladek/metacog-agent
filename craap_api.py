"""
CRAAP Analysis API - Reusable Python API for evaluating blog credibility.

This module provides a comprehensive framework for analyzing blogs using the CRAAP test:
- Currency: How timely is the information?
- Relevance: How useful is this information?
- Authority: Who is behind the content?
- Accuracy: How correct and reliable is the content?
- Purpose: Why does this blog exist?
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

import sys
import trafilatura
from pydantic import BaseModel, Field

from agents import Agent, Runner, ModelSettings, WebSearchTool, trace


# ============================================================================
# Data Models
# ============================================================================

class AccuracyInfo(BaseModel):
    """Information about the accuracy and credibility of blog content."""
    
    has_sources: bool = Field(description="Whether the blog provides sources, citations, or evidence")
    verifiable: bool = Field(description="Whether the content can be verified through other sources")
    error_free: bool = Field(description="Whether the writing is free of obvious errors")
    facts_vs_opinions: str = Field(description="Analysis of how facts and opinions are distinguished")
    verifiable_facts: list[str] = Field(description="list of facts that can be verified")
    search_urls: list[str] = Field(description="URL to google search with a query to verify each fact. ")


class CurrencyInfo(BaseModel):
    """Information about the currency and timeliness of blog content."""
    
    requires_current_info: bool = Field(description="Whether the topic requires up-to-date information")
    is_maintained: bool = Field(description="Whether the blog shows signs of being maintained")
    published_date: str = Field(description="When the blog post was published")
    last_updated: str = Field(description="When the blog post was last updated")
    has_recent_references: bool = Field(description="Whether the blog has recent references")
    examples: list[str] = Field(description="Notable citations that support the decision")
    justifications: list[str] = Field(description="Citations that support the decision with justifications.")


class IntentInfo(BaseModel):
    """Information about the intent and tone of blog content."""
    
    tone: str = Field(description="Tone of the text (objective or opinion-driven)")
    style: str = Field(description="Writing style of the text")
    bias: str = Field(description="Bias towards social and political groups")
    sentiment: str = Field(description="Overall sentiment of the text")
    hate: str = Field(description="Analysis of hate speech or politically incorrect speech")
    justifications: list[str] = Field(description="Justification of the decision with examples from text")



class BlogMetadata(BaseModel):
    """Metadata information about the blog post."""
    
    author_name: str = Field(description="Name of the author")
    is_anonymous: bool = Field(description="Whether the author is anonymous or using a pseudonym")
    author_affiliation: str = Field(description="Affiliation of the author")
    blog_name: str = Field(description="Name of the blog")
    publisher_name: str = Field(description="Name of the publisher")
    publishing_date: str = Field(description="Date of publication")
    summary: str = Field(description="Short summary of the blog content")


class PersonBio(BaseModel):
    """Biographical information about a person."""
    
    full_name: str
    past_affiliations: List[str]
    current_affiliation: str
    biography: str


class AuthorityVerdict(BaseModel):
    """Verdict on author or publisher authority."""
    
    public_sentiment: str
    positive_mentions: str
    negative_mentions: str
    sources: str
    summary: str
    search_url: str
    justification: str


class PublisherVerdict(BaseModel):
    """Verdict on publisher credibility."""
    
    ownership_and_funding: str
    editorial_standards: str
    political_bias: str
    factual_reliability: str
    public_perception: str
    summary: str
    search_url: str

@dataclass
class CRAAPAnalysisResult:
    """Complete CRAAP analysis result for a blog post."""
    
    url: str
    metadata: BlogMetadata
    currency: CurrencyInfo
    accuracy: AccuracyInfo
    purpose: IntentInfo
    author_authority: Optional[AuthorityVerdict]
    publisher_authority: Optional[PublisherVerdict]
    raw_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = asdict(self)
        result['metadata'] = self.metadata.model_dump()
        result['currency'] = self.currency.model_dump()
        result['accuracy'] = self.accuracy.model_dump()
        result['purpose'] = self.purpose.model_dump()
        result['author_authority'] = self.author_authority.model_dump() if self.author_authority else None
        result['publisher_authority'] = self.publisher_authority.model_dump() if self.publisher_authority else None
        return result


# ============================================================================
# Content Download
# ============================================================================

def download_blog(url: str) -> tuple[Optional[str], Dict[str, Any]]:
    """
    Download a blog page and extract text and metadata using trafilatura.
    
    Args:
        url: The URL of the blog to download
    
    Returns:
        Tuple of (extracted text or None, metadata dict)
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


# ============================================================================
# LLM-Based Analysis Functions
# ============================================================================

async def extract_blog_metadata(text: str, url_metadata: Dict[str, Any]) -> BlogMetadata:
    """
    Extract structured metadata from blog text using LLM.
    
    Args:
        text: Extracted text from the blog
        url_metadata: Metadata from trafilatura
    
    Returns:
        BlogMetadata object with extracted information
    """
    prompt = f"""
Extract structured metadata from this blog post.

Required information:
1. Author name: Full name of the person who wrote the blog
2. Author status: Determine if the name appears to be real (with credentials) or a pseudonym/anonymous
3. Author affiliation: Employment, professional title, organizational association, or credentials
4. Blog name: Title of the blog site or section (not the post title)
5. Publisher name: Organization, company, or platform publishing the blog
6. Publication date: When the post was originally published
7. Summary: A concise 2-3 sentence summary of the blog's main points

Guidelines:
- For unknown/missing fields, use "Unknown"
- For author status, consider: presence of bio, credentials, linked profiles, consistency with real identity
- Distinguish between the author (writer), blog name (site), and publisher (organization)
- Extract dates in a consistent format (YYYY-MM-DD if possible)

Content to analyze:
{text[:2000] if text else "No content available"}
"""
    
    extraction_agent = Agent(
        name="blog_metadata_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=BlogMetadata,
    )
    
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output


async def analyze_currency(text: str) -> CurrencyInfo:
    """
    Analyze the currency and timeliness of blog content.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        CurrencyInfo with timeliness analysis
    """
    prompt = f"""
Analyze the currency and timeliness of this blog content.

Your task:
1. Determine if this topic requires up-to-date information (e.g., technology, health, current events, regulations)
2. Assess if the blog appears to be actively maintained
3. Identify all dates mentioned: publication date, last update, and reference dates
4. Evaluate if references and sources are recent
5. Provide examples from text and justifications  that support your decision.

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
    """
    Analyze the factual accuracy and reliability of blog content.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        AccuracyInfo with accuracy analysis
    """
    prompt = f"""
Evaluate the accuracy and credibility of this blog content.

Your task:
1. Identify if sources, citations, data, or evidence are provided
2. Detect obvious errors, contradictions, or inconsistencies in the writing
3. Assess how the author distinguishes facts from opinions
4. Determine if claims can be verified through external trustworthy sources
5. Provide a list of three claim that can be verified from external sources. Pick non-trivial facts that can serve as evidence of author's truthfulness.
6. Provide an URL to Google search for each fact that could verify the truthfullness of the fact. 

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


async def analyze_purpose(text: str) -> IntentInfo:
    """
    Analyze the intent, tone, and potential bias of blog content.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        IntentInfo with purpose analysis
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
Provide also justification of your decision with examples.

Content to analyze:
{text[:2000] if text else "No content available"}
"""
    
    extraction_agent = Agent(
        name="purpose_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=IntentInfo,
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output


async def assess_user_relevance(blog_content: str, user_answers: str) -> str:
    """
    Assess whether the blog content is relevant to the user's stated information needs.
    
    Args:
        blog_content: The full text of the blog
        user_answers: User's answers about their information needs
    
    Returns:
        String containing the relevance assessment
    """
    prompt = f"""
You are evaluating the relevance between a user's information needs and a blog post.

Blog Content:
{blog_content[:3000]}...

User's Answers about their needs:
{user_answers}

Based on the user's stated needs and the blog content, assess:
1. Does the blog content address the user's information needs?
2. Is the blog content at an appropriate level for the user's purpose?
3. Is this blog relevant for what the user is trying to find?

Provide a clear assessment in 3-4 sentences, explaining whether this blog is relevant for the user's stated needs.
"""
    
    relevance_agent = Agent(
        name="relevance_assessor",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(relevance_agent, prompt)
    return result.final_output


async def assess_user_purpose_analysis(blog_content: str, user_answers: str) -> str:
    """
    Assess the user's understanding of the blog's purpose compared to the actual content.
    
    Args:
        blog_content: The full text of the blog
        user_answers: User's answers about the blog's purpose, bias, and intent
    
    Returns:
        String containing the purpose assessment
    """
    prompt = f"""
You are evaluating a user's analysis of a blog post's purpose, intent, and bias.

Blog Content:
{blog_content[:3000]}...

User's Answers about the blog's purpose:
{user_answers}

Based on the user's analysis and the actual blog content, assess:
1. Did the user correctly identify the primary purpose of the blog (inform, persuade, sell, entertain)?
2. Did the user accurately detect any biases (political, ideological, commercial)?
3. Did the user appropriately evaluate the objectivity and tone of the content?
4. Are there any important aspects of purpose or bias that the user missed?

Provide a clear assessment in 3-4 sentences, explaining how well the user's analysis matches the actual purpose and bias of the blog.
"""
    
    purpose_agent = Agent(
        name="purpose_assessor",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(purpose_agent, prompt)
    return result.final_output


# ============================================================================
# Authority Analysis
# ============================================================================

async def analyze_author_authority(name_affiliation: str) -> AuthorityVerdict:
    """
    Analyze the reputation and authority of a blog author.
    
    Args:
        name_affiliation: Full name and affiliation of the author
    
    Returns:
        AuthorityVerdict with reputation analysis
    """
    authority_prompt = """
You are an expert reputation analyst specializing in comprehensive credibility assessment based on publicly available information.

## Input
Full name and current affiliation of an individual.

## Objective
Conduct an objective, evidence-based investigation of the individual's public reputation, credibility, and professional standing across authoritative web sources.

## Research Sources (Priority Order)
1. **News Media**: Major outlets, trade publications, local news
2. **Professional Profiles**: LinkedIn, company bios, academic faculty pages
3. **Public Records**: Court filings, regulatory documents, legal notices
4. **Social Media**: Twitter/X, Facebook, Instagram, YouTube (verified accounts)
5. **Public Forums**: Reddit, Quora, Glassdoor, industry forums

## Analysis Framework

### Professional Reputation
- Credentials, certifications, educational background
- Career achievements and positions held
- Professional associations and industry recognition
- Publications, patents, or significant contributions

### Public Sentiment
- Tone and nature of media coverage (positive/neutral/negative)
- Volume and recency of mentions
- Context and credibility of sources

### Controversies & Concerns
- Legal disputes, regulatory actions, or ethical concerns
- Involvement in scandals or misinformation
- Professional misconduct or disciplinary actions
- Patterns of criticism from credible sources

### Positive Contributions
- Awards, honors, and recognitions
- Philanthropic activities and community service
- Innovation, thought leadership, or industry impact
- Mentorship and professional development contributions

## Output Requirements
- **Public Sentiment**: Overall sentiment classification with evidence
- **Positive Mentions**: Key achievements and favorable coverage with sources
- **Negative Mentions**: Controversies or concerns with context and sources
- **Sources**: List of primary sources consulted with credibility assessment
- **Search URL** Url to google Search with appropriate query
- ** Justification ** Justification of the decision
- **Summary**: Balanced 2-3 paragraph synthesis weighing source credibility, recency, and frequency of mentions
"""
    
    authority_search_agent = Agent(
        name="authority_search_agent",
        tools=[WebSearchTool()],
        instructions=authority_prompt,
        model_settings=ModelSettings(tool_choice="required"),
        output_type=AuthorityVerdict,
    )
    
    with trace("Author authority analysis"):
        authority_result = await Runner.run(
            authority_search_agent,
            name_affiliation
        )
        return authority_result.final_output


async def analyze_publisher_authority(publisher_name: str) -> PublisherVerdict:
    """
    Analyze the credibility and reputation of a publisher.
    
    Args:
        publisher_name: Name of the publisher or publication
    
    Returns:
        PublisherVerdict with credibility analysis
    """
    authority_prompt = """
You are an expert media analyst specializing in publisher credibility assessment and media literacy evaluation.

## Input
Name or domain of a publisher (e.g., "The Guardian", "breitbart.com", "CNN", "example-news.com").

## Objective
Conduct comprehensive research to evaluate the publisher's credibility, transparency, factual reliability, and editorial standards using evidence from authoritative media watchdog organizations and academic sources.

## Research Sources (Priority Order)
1. **Media Credibility Databases**: Media Bias/Fact Check, Ad Fontes Media, NewsGuard, AllSides, Pew Research
2. **Fact-Checking Organizations**: PolitiFact, Snopes, FactCheck.org, Poynter Institute, International Fact-Checking Network
3. **Academic Resources**: Wikipedia media entries, scholarly articles on media analysis, journalism reviews
4. **Journalism Watchdogs**: Committee to Protect Journalists, Reporters Without Borders, Columbia Journalism Review
5. **Publisher Transparency**: About page, Editorial Policy, Corrections/Retractions page, Ownership disclosure

## Evaluation Framework

### Ownership and Funding
- Parent company or owner identification
- Major investors or funding sources
- Financial transparency and disclosure practices
- Potential conflicts of interest
- Independence vs. corporate/political affiliations

### Editorial Standards
- Existence and accessibility of editorial policies
- Fact-checking procedures and verification processes
- Corrections policy and transparency about errors
- Distinction between news and opinion content
- Journalistic code of ethics adherence
- Use of anonymous sources policy

### Political Bias and Ideological Leaning
- Overall political orientation (left, center, right, or mixed)
- Degree of bias (minimal, moderate, strong)
- Balance in coverage and representation of viewpoints
- Tendency toward sensationalism or clickbait
- Use of loaded or inflammatory language

### Factual Reliability
- Track record of accuracy and truthfulness
- Frequency of corrections or retractions
- History of misinformation or false claims
- Source credibility and citation practices
- Verification standards for breaking news

### Public and Expert Perception
- Reputation among journalists and media professionals
- Academic citations and scholarly assessment
- Industry awards and recognitions (Pulitzer, Peabody, etc.)
- Reader trust and audience perception
- Controversies or credibility challenges

## Output Requirements
- **Ownership and Funding**: Clear description of ownership structure, funding sources, and transparency level
- **Editorial Standards**: Assessment of journalistic practices, fact-checking, and correction policies with specific examples
- **Political Bias**: Classification of political leaning with evidence and degree of bias
- **Factual Reliability**: Evaluation of accuracy track record with documented examples of fact-checking assessments
- **Public Perception**: Summary of reputation among experts, awards, and any significant controversies
- ** Search URL ** URL to Google search with proper query to search for the publisher.
- **Summary**: Balanced 2-3 paragraph overall assessment with credibility rating (High/Medium/Low) and key considerations for readers
"""
    
    authority_search_agent = Agent(
        name="publisher_authority_agent",
        tools=[WebSearchTool()],
        instructions=authority_prompt,
        model_settings=ModelSettings(tool_choice="required"),
        output_type=PublisherVerdict,
    )
    
    with trace("Publisher authority analysis"):
        result = await Runner.run(
            authority_search_agent,
            publisher_name,
        )
        return result.final_output


# ============================================================================
# Main API Functions
# ============================================================================

async def analyze_blog(
    url: str,
    analyze_author: bool = True,
    analyze_publisher: bool = True
) -> CRAAPAnalysisResult:
    """
    Perform a comprehensive CRAAP analysis on a blog post.
    
    Args:
        url: URL of the blog post to analyze
        analyze_author: Whether to perform author authority analysis (requires web search)
        analyze_publisher: Whether to perform publisher authority analysis (requires web search)
    
    Returns:
        CRAAPAnalysisResult containing all analysis results
    
    Raises:
        ValueError: If the blog cannot be downloaded or parsed
    """
    # Download and extract blog content
    blog_text, raw_metadata = download_blog(url)
    
    if blog_text is None:
        raise ValueError(f"Failed to download blog: {raw_metadata.get('error', 'Unknown error')}")
    
    # Extract metadata
    metadata = await extract_blog_metadata(
        f"URL: {raw_metadata}\n\n{blog_text or ''}",
        raw_metadata
    )
    
    # Run CRAAP analyses in parallel
    currency_task = analyze_currency(blog_text)
    accuracy_task = analyze_accuracy(blog_text)
    purpose_task = analyze_purpose(blog_text)
    
    currency_info, accuracy_info, purpose_info = await asyncio.gather(
        currency_task, accuracy_task, purpose_task
    )
    
    # Analyze authority if requested
    author_authority = None
    publisher_authority = None
    
    if analyze_publisher:
        publisher_authority = await analyze_publisher_authority(metadata.publisher_name)
    
    if analyze_author and not metadata.is_anonymous:
        author_authority = await analyze_author_authority(
            f"{metadata.author_name} {metadata.author_affiliation} {metadata.publisher_name}"
        )
    
    return CRAAPAnalysisResult(
        url=url,
        metadata=metadata,
        currency=currency_info,
        accuracy=accuracy_info,
        purpose=purpose_info,
        author_authority=author_authority,
        publisher_authority=publisher_authority,
        raw_metadata=raw_metadata
    )


async def analyze_blog_batch(
    urls: List[str],
    analyze_author: bool = True,
    analyze_publisher: bool = True
) -> List[CRAAPAnalysisResult]:
    """
    Analyze multiple blog posts in parallel.
    
    Args:
        urls: List of blog URLs to analyze
        analyze_author: Whether to perform author authority analysis
        analyze_publisher: Whether to perform publisher authority analysis
    
    Returns:
        List of CRAAPAnalysisResult objects
    """
    tasks = [
        analyze_blog(url, analyze_author, analyze_publisher)
        for url in urls
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================================
# Convenience Functions
# ============================================================================

def analyze_blog_sync(
    url: str,
    analyze_author: bool = True,
    analyze_publisher: bool = True
) -> CRAAPAnalysisResult:
    """
    Synchronous wrapper for analyze_blog.
    
    Args:
        url: URL of the blog post to analyze
        analyze_author: Whether to perform author authority analysis
        analyze_publisher: Whether to perform publisher authority analysis
    
    Returns:
        CRAAPAnalysisResult containing all analysis results
    """
    return asyncio.run(analyze_blog(url, analyze_author, analyze_publisher))


def print_analysis_report(result: CRAAPAnalysisResult) -> None:
    """
    Print a formatted CRAAP analysis report.
    
    Args:
        result: CRAAPAnalysisResult to format and print
    """
    print("\n" + "=" * 80)
    print(f"CRAAP ANALYSIS REPORT: {result.url}")
    print("=" * 80)
    
    print("\n📄 METADATA")
    print(f"  Author: {result.metadata.author_name}")
    print(f"  Affiliation: {result.metadata.author_affiliation}")
    print(f"  Publisher: {result.metadata.publisher_name}")
    print(f"  Blog: {result.metadata.blog_name}")
    print(f"  Published: {result.metadata.publishing_date}")
    print(f"  Anonymous: {result.metadata.is_anonymous}")
    print(f"  Summary: {result.metadata.summary}")
    
    print("\n📅 CURRENCY (Timeliness)")
    print(f"  Requires Current Info: {result.currency.requires_current_info}")
    print(f"  Is Maintained: {result.currency.is_maintained}")
    print(f"  Published Date: {result.currency.published_date}")
    print(f"  Last Updated: {result.currency.last_updated}")
    print(f"  Recent References: {result.currency.has_recent_references}")
    
    print("\n✓ ACCURACY (Reliability)")
    print(f"  Has Sources: {result.accuracy.has_sources}")
    print(f"  Verifiable: {result.accuracy.verifiable}")
    print(f"  Error Free: {result.accuracy.error_free}")
    print(f"  Facts vs Opinions: {result.accuracy.facts_vs_opinions}")
    
    print("\n🎯 PURPOSE (Intent)")
    print(f"  Tone: {result.purpose.tone}")
    print(f"  Style: {result.purpose.style}")
    print(f"  Bias: {result.purpose.bias}")
    print(f"  Sentiment: {result.purpose.sentiment}")
    print(f"  Hate Speech: {result.purpose.hate}")
    
    if result.publisher_authority:
        print("\n🏢 PUBLISHER AUTHORITY")
        print(f"  Ownership: {result.publisher_authority.ownership_and_funding[:200]}...")
        print(f"  Editorial Standards: {result.publisher_authority.editorial_standards[:200]}...")
        print(f"  Political Bias: {result.publisher_authority.political_bias}")
        print(f"  Factual Reliability: {result.publisher_authority.factual_reliability[:200]}...")
        print(f"  Summary: {result.publisher_authority.summary}")
    
    if result.author_authority:
        print("\n👤 AUTHOR AUTHORITY")
        print(f"  Public Sentiment: {result.author_authority.public_sentiment}")
        print(f"  Positive: {result.author_authority.positive_mentions[:200]}...")
        print(f"  Negative: {result.author_authority.negative_mentions[:200]}...")
        print(f"  Summary: {result.author_authority.summary}")
    
    print("\n" + "=" * 80)


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """Example usage of the CRAAP API."""
    
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/blog"
    
    print(f"Analyzing: {url}")
    result = await analyze_blog(url)
    print_analysis_report(result)


if __name__ == "__main__":
    asyncio.run(main())
