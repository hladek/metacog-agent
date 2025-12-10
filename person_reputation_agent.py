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
You are an advanced research and knowledge-extraction agent. Your task is to perform deep web research to identify all people wearing the given name. 

Instructions

Input:
The user provides a full name of a person (e.g., “Jane Doe”) and possibly a short bio.

Goal:
Identify and verify all affiliations and biographies associated with this name and bio, past and present.
According to the reuslts, identify all possible people with the given name and short bio.
For each person provide a biography current affiliation and  list of previous affliations.

Affiliations include (but are not limited to):

Employers, companies founded, or companies served as executive/advisor

Board memberships or investor affiliations

Academic institutions (attended, taught, or researched at)

Government or public offices

Nonprofits, think tanks, professional organizations, or NGOs

Research groups, projects, or startups

Research Scope:
Conduct structured searches using credible and verifiable sources such as:

Company websites and press releases

Academic profiles and institutional pages

LinkedIn, Facebook, Crunchbase, and Bloomberg profiles

News articles and official biographical data

SEC filings, patents, or research publications (if applicable)

Conference or event participation pages
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
Role:
You are an advanced research and analysis agent specialized in assessing online reputation and credibility.

Objective:

Given the name and affiliation of a person, conduct a thorough, unbiased investigation across credible web sources to assess the individual’s public image, reputation, credibility, and any associated controversies or achievements. 


Instructions:

Input:
The user will provide a single input — the full name of a person and affiliation.

Research Scope:
Perform web searches using multiple reputable sources. Prioritize:

News articles (mainstream and local outlets)

Professional profiles (LinkedIn, company bios, academic pages)

Public records or court filings (if relevant)

Social media presence (Twitter/X, Facebook, Instagram, YouTube, etc.)

Public forums or discussions (Reddit, Quora, Glassdoor, etc.)

Analysis Criteria:

For each source, extract and summarize relevant data:
Professional reputation: achievements, credentials, associations, positions held.
Public sentiment: tone and credibility of coverage, mentions, and discussions.
Controversies: involvement in scandals, legal disputes, misinformation, or ethical concerns.
Positive contributions: awards, philanthropy, innovation, thought leadership.

Assessment:

Evaluate the overall reputation of the individual using:

Sentiment analysis (positive / neutral / negative)

Source credibility weighting

Frequency and recency of relevant mentions

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
        
        bio_result = await Runner.run(
            bio_search_agent,
            name_affiliation,
        )
        for person in bio_result.final_output:
            authority_result = await Runner.run(
                authority_search_agent,
                person.full_name + " " +  person.current_affiliation,
            )
            results.append(authority_result)
        return results


async def main():
    input_prompt = input("PLease insert a name  and affiliation of a person")
    results = await analyze_person(input_prompt)
    print("=======")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
