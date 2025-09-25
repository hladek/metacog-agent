# Work In Progress Fact verification agent
# Based on Claime ai and openai sdk agents examples.

# https://raw.githubusercontent.com/openai/openai-agents-python/refs/heads/main/examples/agent_patterns/deterministic.py
import asyncio

from pydantic import BaseModel

from agents import Agent, Runner, trace, WebSearchTool, ModelSettings

from datetime import datetime
import prompts


def get_current_timestamp() -> str:
    """Get current timestamp for temporal context in prompts."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")


class ClaimOutput(BaseModel):
    claims: list[str]

# https://github.com/BharathxD/ClaimeAI/tree/main/apps/agent/claim_extractor

fact_identification_agent = Agent(
    name="fact_identification_agent",
    instructions=prompts.GET_DEEP_FACTS,
    #instructions=prompts.get_facts,
    #output_type=ClaimOutput,
)


# TODO - verify and regenerate query

fact_search_agent = Agent(
    name = "fact_search_agent",
    tools=[WebSearchTool()],
    instructions=prompts.QUERY_GENERATION_INITIAL_SYSTEM_PROMPT,
    model_settings=ModelSettings(tool_choice="required"),
)


class EvaluationFeedback(BaseModel):
    feedback: str
    decision: str
    #score: Literal["Supported", "Insufficient informationn", "Refuted","Conflicting Evidence"]

search_evaluator_agent = Agent(
    name="search_evaluator_agent",
    instructions=prompts.EVIDENCE_EVALUATION_SYSTEM_PROMPT,
    output_type=EvaluationFeedback,
)

final_verdict_agent = Agent(
    name="final_verdict_agent",
    instructions=prompts.FINAL_VERDICT,
)

# https://github.com/openai/openai-agents-python/blob/main/examples/agent_patterns/llm_as_a_judge.py    

# TODO

# summrize the results of fact verification


async def main():
    input_prompt = input("What kind of story do you want? ")

    # Ensure the entire workflow is a single trace
    with trace("Deterministic story flow"):
        # 1. identify facts. 
        facts_result = await Runner.run(
            fact_identification_agent,
            input_prompt,
        )
        print("Outline generated")
        print(facts_result)
        
        #  for each fact
        for claim in facts_result.final_output.claims:
            # 2. Check the facts
            # https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent
            fact_search_result = await Runner.run(
                fact_search_agent,
                claim,
            )
            print(fact_search_result)

            fact_search_evaluation_result = await Runner.run(
                search_evaluator_agent,
                fact_search_result.final_output,
            )

            print(fact_search_evaluation_result)

        # 3. Add a gate to stop if the outline is not good quality or not a scifi story
        #assert isinstance(outline_checker_result.final_output, OutlineCheckerOutput)
        #if not outline_checker_result.final_output.good_quality:
        #    print("Outline is not good quality, so we stop here.")
        #    exit(0)

        #if not outline_checker_result.final_output.is_scifi:
        #    print("Outline is not a scifi story, so we stop here.")
        #    exit(0)
#
        #print("Outline is good quality and a scifi story, so we continue to write the story.")

        # 4. Write the story
        #story_result = await Runner.run(
        #    final_verdict_agent,
        #    outline_result.final_output,
        #)
        print(f"Story: {story_result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
