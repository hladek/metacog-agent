import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace, WebSearchTool, ModelSettings

# https://libguides.lmu.edu/aboutRADAR

# Is the publisher of the information source reputable? 

# TODO - How to evaluate social network channels?


authority_prompt = """
You are an advanced research and analysis agent specializing in media credibility evaluation. Your goal is to assess the trustworthiness, reliability, and reputation of a given publisher based on evidence from credible sources.

Instructions

Input:
The user provides the name or domain of a publisher (e.g., The Guardian or breitbart.com).

Objective:
Conduct deep web research to evaluate the publisher’s credibility, transparency, and factual reliability, using multiple perspectives and reputable references.

Research Scope:
Search across trusted and verifiable sources, prioritizing:

Media credibility databases (e.g., Media Bias/Fact Check, Ad Fontes Media, NewsGuard, AllSides)

Wikipedia and academic analyses on media bias or reliability

Fact-checking organizations (PolitiFact, Snopes, Poynter Institute)

News coverage or journalistic watchdog reports

Publisher’s own About/Editorial Policy/Corrections pages

Evaluation Criteria:
For each publisher, assess:

Ownership and Funding: Transparency about owners, investors, and sponsors.

Editorial Standards: Existence of fact-checking, correction policies, or journalistic codes.

Reputation and Recognition: Awards, citations, or partnerships with credible institutions.

Bias and Political Leaning: Neutral, left-leaning, right-leaning, or extremist tendencies.

Factual Reliability: Frequency of false/misleading claims, if documented.

Public and Expert Perception: How journalists, academics, and readers view the outlet.

"""

class AuthorityVerdict(BaseModel):
    ownership_and_funding: str
    editorial_standards: str
    political_bias: str
    factual_reliability: str
    public_percpetion: str
    summary: str

authority_search_agent = Agent(
    name = "authority_search_agent",
    tools=[WebSearchTool()],
    instructions=authority_prompt,
    model_settings=ModelSettings(tool_choice="required"),
#    output_type=AuthorityVerdict,
)

async def analyze_publisher(name:str):
    # Ensure the entire workflow is a single trace
    out = []
    with trace("Deterministic flow"):
        
        bio_result = await Runner.run(
            authority_search_agent,
            name,
        )
        return bio_result

async def main():
    input_prompt = input("PLease insert a name of a publisher")
    result = await analyze_publisher(input_prompt)
    print("=======")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
