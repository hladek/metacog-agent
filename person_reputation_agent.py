import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace, WebSearchTool, ModelSettings

# https://libguides.lmu.edu/aboutRADAR

# What are the author's credentials?
# How is the author related to your topic?
# Is the author affiliated with an educational institution or a reputable organization?
# Can you find information about the author in reference books or on the Internet?
# Do other books or articles on the same research topic cite the author?
# Is the publisher of the information source reputable? 

bio_prompt = """
You are an advanced research and knowledge-extraction agent specializing in comprehensive biographical verification.

## Input
A full name of a person (e.g., "Jane Doe") and optionally a short biographical hint.

## Objective
Identify and verify all individuals matching the given name. For each distinct person found, provide:
- Full name and current affiliation
- Complete biography with key professional milestones
- Chronological list of past affiliations

## Affiliation Types
Include all verifiable professional and institutional connections:
- Employment history (companies, positions, dates)
- Entrepreneurial ventures (founded, executive, advisory roles)
- Board memberships and investor relationships
- Academic institutions (attended, faculty positions, research roles)
- Government positions and public offices
- Nonprofit organizations, think tanks, professional associations, NGOs
- Research groups, collaborative projects, startups

## Research Requirements
Use only credible, verifiable sources:
- Official company websites and press releases
- Academic institutional profiles and faculty pages
- Professional networking profiles (LinkedIn, Crunchbase, Bloomberg)
- Reputable news articles and biographical databases
- Public records (SEC filings, patents, publications)
- Conference proceedings and speaker listings

## Output Standards
- Distinguish clearly between different individuals with the same name
- Provide evidence-based information with source credibility
- Focus on verifiable facts, not speculation
- Include date ranges where available
"""

class PersonBio(BaseModel):
    full_name: str
    past_affiliations: list[str]
    current_affiliation: str
    biography: str

bio_search_agent = Agent(
    name = "bio_search_agent",
    tools=[WebSearchTool()],
    instructions=bio_prompt,
    model_settings=ModelSettings(tool_choice="required"),
    #    output_type=list[str]
   output_type=list[PersonBio],
)

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
- **Summary**: Balanced 2-3 paragraph synthesis weighing source credibility, recency, and frequency of mentions
"""

class AuthorityVerdict(BaseModel):
    public_sentiment: str
    positive_mentions: str
    negative_mentions: str
    sources: str
    summary: str

authority_search_agent = Agent(
    name = "authority_search_agent",
    tools=[WebSearchTool()],
    instructions=authority_prompt,
    model_settings=ModelSettings(tool_choice="required"),
    output_type=AuthorityVerdict,
)


async def analyze_person(name_affiliation: str):

    # Ensure the entire workflow is a single trace
    out = []
    results = []
    with trace("Deterministic flow"):
        authority_result = await Runner.run(
            authority_search_agent,
            name_affiliation
        )
        results.append(authority_result.final_output)

async def analyze_person_without_affiliation(name: str):

    # Ensure the entire workflow is a single trace
    out = []
    results = []
    with trace("Deterministic flow"):
        bio_result = await Runner.run(
            bio_search_agent,
            name,
        )
        for person in bio_result.final_output:
            authority_result = await Runner.run(
                authority_search_agent,
                person.full_name + " " +  person.current_affiliation,
            )
            results.append(authority_result.final_output)
        return results


async def main():
    input_prompt = input("PLease insert a name  and affiliation of a person")
    results = await analyze_person(input_prompt)
    print("=======")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
