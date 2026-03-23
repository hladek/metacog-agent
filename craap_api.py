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
import json
from pathlib import Path
import os

import sys
import trafilatura
from pydantic import BaseModel, Field

from agents import Agent, Runner, ModelSettings, WebSearchTool, trace


# ============================================================================
# Configuration
# ============================================================================

# Output directory for analysis JSON files
OUTPUT_DIR = os.environ.get("CRAAP_OUTPUT_DIR", "craap_results")


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


class FactsResult(BaseModel):
    """Verifiable facts extracted from blog content with search URLs."""

    verifiable_facts: list[str] = Field(description="List of facts that can be verified externally")
    search_urls: list[str] = Field(description="Google search URL to verify each corresponding fact")


class VerifiedFact(BaseModel):
    """A single fact with its search URL and web-verified verdict."""

    fact: str = Field(description="The claim extracted from the blog")
    search_url: str = Field(description="Google search URL to verify the fact")
    verification: str = Field(description="Markdown fact-check verdict from verify_fact")


class VerifiedFactsResult(BaseModel):
    """Collection of facts enriched with individual verification results."""

    facts: list[VerifiedFact] = Field(description="Facts with their verification verdicts")


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
    blog_text: str
    metadata: BlogMetadata
    currency: str
    accuracy_text: str
    facts_result: "VerifiedFactsResult"
    purpose: IntentInfo
    author_authority: Optional[AuthorityVerdict]
    publisher_authority: Optional[PublisherVerdict]
    raw_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = asdict(self)
        result['metadata'] = self.metadata.model_dump()
        result['currency'] = self.currency
        result['accuracy_text'] = self.accuracy_text
        result['facts_result'] = self.facts_result.model_dump()
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


async def analyze_currency_html(text: str) -> str:
    """
    Analyze the currency (timeliness) of a blog post from its raw text.

    Uses an LLM to answer five structured currency questions and returns
    the result as formatted Markdown:
      1. Publication / last-update date and timing appropriateness
      2. Whether the content is current enough for its field
      3. Whether links and references appear functional (not broken/outdated)
      4. Whether the content shows signs of active maintenance
      5. Whether the content is outdated for its stated purpose

    Args:
        text: Raw text content of the blog page

    Returns:
        Markdown-formatted answers to the five currency questions
    """
    prompt = f"""You are a media-literacy analyst evaluating the CURRENCY (timeliness) of a blog post.

Answer each of the five questions below in 1-3 sentences. Be direct and evidence-based.
Use only information present in the text. If information is missing, say so briefly.

---
1. PUBLICATION / UPDATE DATE
   When was it published or last updated? Are those dates visible and clear?
   Is the timing appropriate for the topic?

2. CURRENCY FOR THE FIELD
   Does the topic change quickly (technology, medicine, news, law)?
   Is the content recent enough for that field?

3. LINKS AND REFERENCES
   Do referenced sources, studies, or links appear current and functional?
   Any signs of broken or outdated references?

4. MAINTENANCE
   Are there signs the content is actively maintained (update notices,
   revision history, corrections, recent comments)?

5. OBSOLESCENCE RISK
   Even if recently published, does it rely on old standards, deprecated
   technologies, superseded research, or outdated terminology?
---

Blog text (truncated):
{text[:3000] if text else "No content available."}

Respond in this exact Markdown format:
## Currency Analysis

**1. Publication/Update Date**
<answer>

**2. Currency for the Field**
<answer>

**3. Maintenance**
<answer>

**4. Obsolescence Risk**
<answer>
"""

    currency_html_agent = Agent(
        name="currency_html_analyzer",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(currency_html_agent, prompt)
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
1. Identify if sources, citations, data, or evidence are provided - always include specific references or quotes when found
2. Detect obvious errors, contradictions, or inconsistencies in the writing - reference specific examples
3. Assess how the author distinguishes facts from opinions - cite specific instances
4. Determine if claims can be verified through external trustworthy sources
5. Provide a list of three claims that can be verified from external sources. Pick non-trivial facts that can serve as evidence of author's truthfulness. Always quote or reference the exact claims from the text.
6. Provide a URL to Google search for each fact that could verify the truthfulness of the fact. 

Look for:
- Academic or journalistic citations (footnotes, references, links) - always note specific citations found
- Links to credible external sources (research papers, official sites, reputable publications)
- Data with clear provenance - reference where it appears in the text
- Use of hedging language ("studies suggest", "research shows") - cite examples
- Clear labeling of opinions vs facts - provide specific examples
- Logical consistency throughout the text
- Factual errors or misleading statements - quote specific instances

Provide clear boolean assessments and descriptive analysis for facts vs opinions.
Always include direct references, quotes, or citations from the text to support your analysis.

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


async def analyze_accuracy_text(text: str) -> str:
    """
    Analyze the factual accuracy and reliability of blog content, returning Markdown.

    Uses an LLM to answer four structured accuracy questions and returns
    the result as formatted Markdown:
      1. Sources, citations, data, or evidence provided (with specific references)
      2. Obvious errors, contradictions, or inconsistencies (with specific examples)
      3. How the author distinguishes facts from opinions (with specific instances)
      4. Whether claims can be verified through external trustworthy sources

    Args:
        text: Extracted text from the blog

    Returns:
        Markdown-formatted accuracy analysis
    """
    prompt = f"""You are a media-literacy analyst evaluating the ACCURACY of a blog post.

Answer each of the four questions below in 2-4 sentences. Be direct and evidence-based.
Use only information present in the text. Quote or reference specific passages whenever possible.
If information is missing, say so briefly.

---
1. SOURCES AND EVIDENCE
   Are sources, citations, data, or evidence provided?
   Quote or reference specific citations, links, or data points found in the text.
   If none are present, say so explicitly.

2. ERRORS, CONTRADICTIONS, AND INCONSISTENCIES
   Are there obvious factual errors, contradictions, or logical inconsistencies?
   Reference specific examples from the text. If none are detected, say so explicitly.

3. FACTS VS. OPINIONS
   How does the author distinguish facts from opinions?
   Cite specific instances where opinion language (e.g. "I believe", "in my view") or
   hedging language (e.g. "studies suggest") is used — or where facts and opinions are mixed
   without clear separation.

4. VERIFIABILITY
   Can the main claims be verified through external trustworthy sources
   (e.g. peer-reviewed research, official statistics, reputable journalism)?
   Identify the key claims and assess how checkable they are.
---

Blog text (truncated):
{text[:3000] if text else "No content available."}

Respond in this exact Markdown format:
## Accuracy Analysis

**1. Sources and Evidence**
<answer>

**2. Errors, Contradictions, and Inconsistencies**
<answer>

**3. Facts vs. Opinions**
<answer>

**4. Verifiability**
<answer>
"""

    accuracy_text_agent = Agent(
        name="accuracy_text_analyzer",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(accuracy_text_agent, prompt)
    return result.final_output


async def verify_fact(claim: str) -> str:
    """
    Verify the factual accuracy of a single claim using web search.

    Searches the web for evidence supporting or contradicting the claim and
    returns a short Markdown verdict with justification and source references.
    If a definitive verdict cannot be reached, the response says so explicitly.

    Args:
        claim: The specific claim or statement to verify

    Returns:
        Markdown-formatted fact-check result with verdict, justification, and references
    """
    instructions = """You are a rigorous fact-checker. Your job is to verify a single claim
using web search, then write a concise, honest verdict.

Steps:
1. Search the web for evidence directly related to the claim. Use multiple searches if needed.
2. Evaluate the quality and consistency of sources found.
3. Reach a verdict based solely on what the evidence supports.

Verdict options:
- **TRUE** — credible sources clearly confirm the claim
- **FALSE** — credible sources clearly contradict the claim
- **PARTIALLY TRUE** — the claim is accurate in some respects but misleading or incomplete in others
- **UNVERIFIABLE** — insufficient publicly available evidence to decide either way
- **UNCERTAIN** — sources conflict or evidence is weak; a definitive conclusion cannot be drawn

Rules:
- Always cite the specific sources you found (title + URL when available).
- Quote or paraphrase the key evidence that drove your verdict.
- If you could not find relevant sources, say so explicitly.
- Do not guess or fill gaps with background knowledge — only use what you found.
- Keep the full response under 250 words.

Respond in this exact Markdown format:

## Fact Check

**Claim:** <repeat the claim verbatim>

**Verdict:** <TRUE | FALSE | PARTIALLY TRUE | UNVERIFIABLE | UNCERTAIN>

**Justification:**
<2-4 sentences explaining the verdict, referencing specific evidence found>

**References:**
<bullet list of sources: title and URL, or "No relevant sources found" if none>
"""

    fact_check_agent = Agent(
        name="fact_check_agent",
        tools=[WebSearchTool()],
        instructions=instructions,
        model_settings=ModelSettings(tool_choice="required"),
    )

    with trace("Fact verification"):
        result = await Runner.run(fact_check_agent, claim)
    return result.final_output


async def provide_facts(text: str) -> "FactsResult":
    """
    Extract verifiable facts and corresponding Google search URLs from blog content.

    Similar to analyze_accuracy but returns only the verifiable facts and
    search URLs, without the broader accuracy assessment.

    Args:
        text: Extracted text from the blog

    Returns:
        FactsResult containing verifiable_facts and search_urls
    """
    prompt = f"""
Extract a list of specific, non-trivial, verifiable facts from this blog content.

For each fact:
1. Quote or closely paraphrase the exact claim from the text.
2. Pick claims that serve as evidence of the author's truthfulness — prefer concrete, checkable statements (statistics, named studies, events, attributions).
3. Provide a Google search URL that would help verify the fact (e.g. https://www.google.com/search?q=...).

Aim for 3–5 facts. Avoid vague or trivially true statements.

Content to analyze:
{text[:2000] if text else "No content available"}
"""

    extraction_agent = Agent(
        name="facts_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=FactsResult,
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
1. Tone: Determine if the writing is objective, opinion-driven, emotional, or promotional - cite specific examples from the text
2. Style: Identify the writing style (journalistic, academic, conversational, marketing, etc.) - reference specific passages
3. Bias: Assess bias toward or against social, political, or ideological groups - quote specific instances
4. Sentiment: Classify overall sentiment (positive, negative, neutral, mixed) - provide specific examples
5. Hate speech: Identify any vulgar, hateful, discriminatory, or offensive language - always quote exact phrases if found

Author intent to evaluate:
- Is the primary purpose to inform, persuade, entertain, or sell? - reference specific indicators
- Are there disclosure statements for sponsorships, affiliates, or conflicts of interest? - cite if found
- Are ads, affiliate links, or sponsored content present? - note specific mentions
- Is the language inflammatory or deliberately polarizing? - quote examples if present

Provide descriptive assessments. Use "None detected" or "Not present" rather than "Unknown" when elements are absent.
Always provide justification of your decision with specific examples and quotes from the text.

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
- Credentials, certifications, educational background - always cite specific sources
- Career achievements and positions held - reference where this information was found
- Professional associations and industry recognition - include specific sources
- Publications, patents, or significant contributions - provide specific references

### Public Sentiment
- Tone and nature of media coverage (positive/neutral/negative) - cite specific articles or sources
- Volume and recency of mentions - reference specific sources and dates
- Context and credibility of sources - always identify and link to sources

### Controversies & Concerns
- Legal disputes, regulatory actions, or ethical concerns - cite specific sources and documents
- Involvement in scandals or misinformation - reference specific reports and dates
- Professional misconduct or disciplinary actions - provide source references
- Patterns of criticism from credible sources - cite specific sources

### Positive Contributions
- Awards, honors, and recognitions - cite specific sources and dates
- Philanthropic activities and community service - reference where this was documented
- Innovation, thought leadership, or industry impact - provide specific examples with sources
- Mentorship and professional development contributions - cite references if available

## Output Requirements
- **Public Sentiment**: Overall sentiment classification with specific evidence and source references
- **Positive Mentions**: Key achievements and favorable coverage with specific sources and URLs when available
- **Negative Mentions**: Controversies or concerns with context, specific sources, and references
- **Sources**: List of primary sources consulted with credibility assessment - always include specific URLs or citations
- **Search URL**: URL to Google Search with appropriate query
- **Justification**: Justification of the decision with specific references to sources consulted
- **Summary**: Balanced 2-3 paragraph synthesis weighing source credibility, recency, and frequency of mentions - always reference specific sources
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
1. **Media Credibility Databases**: Media Bias/Fact Check, Ad Fontes Media, NewsGuard, AllSides, Pew Research - always cite specific sources
2. **Fact-Checking Organizations**: PolitiFact, Snopes, FactCheck.org, Poynter Institute, International Fact-Checking Network - include specific references
3. **Academic Resources**: Wikipedia media entries, scholarly articles on media analysis, journalism reviews - provide citations
4. **Journalism Watchdogs**: Committee to Protect Journalists, Reporters Without Borders, Columbia Journalism Review - cite specific reports
5. **Publisher Transparency**: About page, Editorial Policy, Corrections/Retractions page, Ownership disclosure - reference specific pages/URLs

## Evaluation Framework

### Ownership and Funding
- Parent company or owner identification - cite specific sources
- Major investors or funding sources - reference where this information was found
- Financial transparency and disclosure practices - cite specific sources
- Potential conflicts of interest - provide specific references
- Independence vs. corporate/political affiliations - cite sources

### Editorial Standards
- Existence and accessibility of editorial policies - reference specific URLs or sources
- Fact-checking procedures and verification processes - cite sources documenting these
- Corrections policy and transparency about errors - reference specific examples
- Distinction between news and opinion content - cite specific assessments
- Journalistic code of ethics adherence - reference specific sources
- Use of anonymous sources policy - cite where documented

### Political Bias and Ideological Leaning
- Overall political orientation (left, center, right, or mixed) - cite specific assessments (e.g., Media Bias/Fact Check, AllSides)
- Degree of bias (minimal, moderate, strong) - reference specific sources
- Balance in coverage and representation of viewpoints - cite specific analyses
- Tendency toward sensationalism or clickbait - reference specific assessments
- Use of loaded or inflammatory language - cite specific examples or sources

### Factual Reliability
- Track record of accuracy and truthfulness - cite specific fact-checking reports
- Frequency of corrections or retractions - reference specific sources or examples
- History of misinformation or false claims - cite specific fact-checking reports
- Source credibility and citation practices - reference specific assessments
- Verification standards for breaking news - cite sources documenting standards

### Public and Expert Perception
- Reputation among journalists and media professionals - cite specific sources
- Academic citations and scholarly assessment - provide specific references
- Industry awards and recognitions (Pulitzer, Peabody, etc.) - cite specific awards with sources
- Reader trust and audience perception - reference specific surveys or studies
- Controversies or credibility challenges - cite specific sources and reports

## Output Requirements
- **Ownership and Funding**: Clear description of ownership structure, funding sources, and transparency level - always cite specific sources
- **Editorial Standards**: Assessment of journalistic practices, fact-checking, and correction policies with specific examples and source references
- **Political Bias**: Classification of political leaning with evidence and degree of bias - cite specific assessments and sources
- **Factual Reliability**: Evaluation of accuracy track record with documented examples of fact-checking assessments - always include specific references
- **Public Perception**: Summary of reputation among experts, awards, and any significant controversies - cite specific sources and references
- **Search URL**: URL to Google search with proper query to search for the publisher
- **Summary**: Balanced 2-3 paragraph overall assessment with credibility rating (High/Medium/Low) and key considerations for readers - always reference specific sources used in the analysis
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
    currency_task = analyze_currency_html(blog_text)
    accuracy_text_task = analyze_accuracy_text(blog_text)
    facts_task = provide_facts(blog_text)
    purpose_task = analyze_purpose(blog_text)

    currency_info, accuracy_text_info, facts_result, purpose_info = await asyncio.gather(
        currency_task, accuracy_text_task, facts_task, purpose_task
    )

    # Verify each extracted fact in parallel
    facts = facts_result.verifiable_facts
    urls = facts_result.search_urls
    verifications = await asyncio.gather(*[verify_fact(f) for f in facts])
    verified_facts_result = VerifiedFactsResult(
        facts=[
            VerifiedFact(
                fact=fact,
                search_url=urls[i] if i < len(urls) else "",
                verification=verifications[i],
            )
            for i, fact in enumerate(facts)
        ]
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
    
    result = CRAAPAnalysisResult(
        url=url,
        blog_text=blog_text,
        metadata=metadata,
        currency=currency_info,
        accuracy_text=accuracy_text_info,
        facts_result=verified_facts_result,
        purpose=purpose_info,
        author_authority=author_authority,
        publisher_authority=publisher_authority,
        raw_metadata=raw_metadata
    )
    
    # Automatically save to JSON file
    try:
        save_analysis_to_json(result)
    except Exception as e:
        print(f"Warning: Failed to save analysis to JSON: {e}")
    
    return result


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
    print(result.currency)
    
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


def save_analysis_to_json(result: CRAAPAnalysisResult, filepath: str = None) -> str:
    """
    Save CRAAP analysis result to a JSON file.
    
    Args:
        result: CRAAPAnalysisResult object to save
        filepath: Optional path to save the JSON file. If None, generates filename from timestamp
                  and saves to configured output directory.
    
    Returns:
        Absolute path to the saved file
    """
    from datetime import datetime
    
    # If no filepath provided, generate from timestamp in configured directory
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"craap_analysis_{timestamp}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Convert result to dictionary
    result_dict = result.to_dict()
    
    # Clean raw_metadata to ensure JSON serializability
    if 'raw_metadata' in result_dict and result_dict['raw_metadata']:
        cleaned_metadata = {}
        for key, value in result_dict['raw_metadata'].items():
            # Skip None values and non-serializable objects
            if value is None:
                continue
            # Convert to string if not already a JSON-serializable type
            if isinstance(value, (str, int, float, bool, list, dict)):
                cleaned_metadata[key] = value
            else:
                # Convert other types to string representation
                cleaned_metadata[key] = str(value)
        result_dict['raw_metadata'] = cleaned_metadata
    
    # Convert to Path object for better path handling
    output_path = Path(filepath)
    
    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON file with pretty formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    return str(output_path.absolute())


def load_analysis_from_json(filepath: str) -> CRAAPAnalysisResult:
    """
    Load CRAAP analysis result from a JSON file.
    
    Args:
        filepath: Path to the JSON file to load
    
    Returns:
        CRAAPAnalysisResult object reconstructed from JSON
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the JSON is invalid or missing required fields
    """
    file_path = Path(filepath)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Analysis file not found: {filepath}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Reconstruct the Pydantic models from dictionaries
    metadata = BlogMetadata(**data['metadata'])
    currency = data['currency']
    accuracy_text = data.get('accuracy_text', '')
    facts_result = VerifiedFactsResult(facts=[VerifiedFact(**f) for f in data['facts_result']['facts']]) if data.get('facts_result') else VerifiedFactsResult(facts=[])
    purpose = IntentInfo(**data['purpose'])
    
    author_authority = None
    if data.get('author_authority'):
        author_authority = AuthorityVerdict(**data['author_authority'])
    
    publisher_authority = None
    if data.get('publisher_authority'):
        publisher_authority = PublisherVerdict(**data['publisher_authority'])
    
    return CRAAPAnalysisResult(
        url=data['url'],
        blog_text=data.get('blog_text', ''),
        metadata=metadata,
        currency=currency,
        accuracy_text=accuracy_text,
        facts_result=facts_result,
        purpose=purpose,
        author_authority=author_authority,
        publisher_authority=publisher_authority,
        raw_metadata=data.get('raw_metadata', {})
    )


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """Example usage of the CRAAP API."""
    
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/blog"
    
    print(f"Analyzing: {url}")
    result = await analyze_blog(url)
    print_analysis_report(result)
    
    # Note: Analysis is automatically saved to timestamped JSON file
    print(f"\n📄 Analysis automatically saved to timestamped JSON file")


if __name__ == "__main__":
    asyncio.run(main())
