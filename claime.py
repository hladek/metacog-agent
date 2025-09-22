# Work In Progress Fact verification agent
# Based on Claime ai and openai sdk agents examples.

# https://raw.githubusercontent.com/openai/openai-agents-python/refs/heads/main/examples/agent_patterns/deterministic.py
import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace

from datetime import datetime


def get_current_timestamp() -> str:
    """Get current timestamp for temporal context in prompts."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

# Trivial agent to extract claims
# TODO make it more complex
facts_instructions = "For the given text, identify and list verifiable factual claims. "

class ClaimOutput(BaseModel):
    claims: list[str]

# https://github.com/BharathxD/ClaimeAI/tree/main/apps/agent/claim_extractor

fact_identification_agent = Agent(
    name="fact_identification_agent",
    instructions=facts_instructions,
    output_tyoe=ClaimOutput,
)


# https://github.com/BharathxD/ClaimeAI/blob/main/apps/agent/claim_verifier/prompts.py

# A query and search is generated for each claim

QUERY_GENERATION_INITIAL_SYSTEM_PROMPT = """You are an expert search agent for verification of fact-checking claims.

Current time: {current_time}

Your task: Perform a web search with an effective search query to find evidence that could verify or refute the given claim.

Requirements:
- Include key entities, names, dates, and specific details from the claim
- Use search-engine-friendly language (no special characters)
- Target authoritative sources (news, government, academic, fact-checking sites)
- Keep it concise (5-15 words optimal)
- Design to find both supporting AND contradictory evidence
- For time-sensitive claims, include relevant temporal constraints

Examples:
- Policy claim: "Biden student loan forgiveness program 2023 official announcement"
- Statistics: "unemployment rate March 2024 Bureau Labor Statistics"
- Events: "Taylor Swift concert cancellation official statement"
- Recent claims: Add "latest" or current year when relevant

"""

query_generation_agent = Agent(
    name = "query_generation_agent",
    tools=[WebSearchTool()],
    model_settings=ModelSettings(tool_choice="required"),
)

# https://github.com/openai/openai-agents-python/blob/main/examples/financial_research_agent/agents/search_agent.py

# Search results are evaluated for each claim

### EVIDENCE EVALUATION PROMPTS ###

EVIDENCE_EVALUATION_SYSTEM_PROMPT = """You are an expert fact-checker. Evaluate claims based ONLY on the evidence provided - do not use prior knowledge.

Current time: {current_time}

Your task: Assess the factual accuracy of the claim based solely on the provided evidence.

Verdict criteria:

SUPPORTED - Use when:
- Multiple reliable sources confirm the claim
- Evidence directly addresses the core assertion
- No credible contradictory evidence
- Sources are authoritative and credible
- Evidence is current/recent enough for time-sensitive claims

REFUTED - Use when:
- Authoritative sources explicitly contradict the claim
- Evidence provides clear counter-factual information
- Contradiction is direct and unambiguous

INSUFFICIENT INFORMATION - Use when:
- Limited evidence (too few sources)
- Evidence is indirect, vague, or incomplete
- Sources lack credibility
- Key information missing for verification
- Evidence is outdated for time-sensitive claims

CONFLICTING EVIDENCE - Use when:
- Multiple credible sources present opposing views
- No clear resolution from available evidence
- Both sides have credible support

Decision rule: Be conservative - when evidence is ambiguous or insufficient, choose "Insufficient Information."

Source reporting: Always identify which evidence sources were relevant to your decision, regardless of the verdict. For "Insufficient Information" and "Conflicting Evidence" verdicts, include sources that were considered even if they were inadequate, to maintain transparency in the fact-checking process.

Think step by step through the evidence before reaching your verdict."""

@dataclass
class EvaluationFeedback:
    feedback: str
    score: Literal["Supported", "Insufficient informationn", "Refuted","Conflicting Evidence"]

search_evaluator_agent = Agent(
    name="search_evaluator_agent",
    instructions=EVIDENCE_EVALUATION_SYSTEM_PROMPT,
    output_type=EvaluationFeedback,


# https://github.com/openai/openai-agents-python/blob/main/examples/agent_patterns/llm_as_a_judge.py    

# TODO

# summrize the results of fact verification


async def main():
    input_prompt = input("What kind of story do you want? ")

    # Ensure the entire workflow is a single trace
    with trace("Deterministic story flow"):
        # 1. Generate an outline
        outline_result = await Runner.run(
            story_outline_agent,
            input_prompt,
        )
        print("Outline generated")

        # 2. Check the outline
        outline_checker_result = await Runner.run(
            outline_checker_agent,
            outline_result.final_output,
        )

        # 3. Add a gate to stop if the outline is not good quality or not a scifi story
        assert isinstance(outline_checker_result.final_output, OutlineCheckerOutput)
        if not outline_checker_result.final_output.good_quality:
            print("Outline is not good quality, so we stop here.")
            exit(0)

        if not outline_checker_result.final_output.is_scifi:
            print("Outline is not a scifi story, so we stop here.")
            exit(0)

        print("Outline is good quality and a scifi story, so we continue to write the story.")

        # 4. Write the story
        story_result = await Runner.run(
            story_agent,
            outline_result.final_output,
        )
        print(f"Story: {story_result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
