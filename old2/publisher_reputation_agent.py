import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace, WebSearchTool, ModelSettings

# https://libguides.lmu.edu/aboutRADAR

# Is the publisher of the information source reputable? 

# TODO - How to evaluate social network channels?


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
- **Summary**: Balanced 2-3 paragraph overall assessment with credibility rating (High/Medium/Low) and key considerations for readers
"""

class AuthorityVerdict(BaseModel):
    ownership_and_funding: str
    editorial_standards: str
    political_bias: str
    factual_reliability: str
    public_perception: str
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
        return bio_result.final_output

async def main():
    input_prompt = input("PLease insert a name of a publisher")
    result = await analyze_publisher(input_prompt)
    print("=======")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
