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

class Claim(BaseModel):
    text: str
    pros: str
    cons: str
    falacies: list[str]
    labels: list[str] 


# https://github.com/BharathxD/ClaimeAI/tree/main/apps/agent/claim_extractor

fact_identification_agent = Agent(
    name="fact_identification_agent",
    instructions=prompts.GET_DEEP_FACTS,
    output_type=list[Claim],
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
    input_prompt = input("PLease insert a text with factual claims")

    # Ensure the entire workflow is a single trace
    with trace("Deterministic flow"):
        # 1. identify facts. 
        # the agent can return a pre-liminary fact evaluation
        # TODO the opriginal claime approach evaluates each sentence in context for existence of a factual claim.
        # this will make the agent mode difficult and expensive.
        # TODO claims should have resolved co-references
        facts_result = await Runner.run(
            fact_identification_agent,
            input_prompt,
        )
        print("Ideintified facts")
        print(facts_result)
        
        # for each claim
        # check evidence on web
        for claim in facts_result.final_output:
            # https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent
            # generate query and search for the claim
            # TODO - generate multiple queries if necessary
            # 3. Add a gate to stop or regenerate results are not good quality
            fact_search_result = await Runner.run(
                fact_search_agent,
                claim.text,
            )
            print(fact_search_result)
            
            # this might not be necessary
            # evaluate search results. Do they support or refute the claim?
            #fact_search_evaluation_result = await Runner.run(
            #    search_evaluator_agent,
            #    fact_search_result.final_output,
            #)

            #print(fact_search_evaluation_result)

        # TODO generate overall evaluation of the text


if __name__ == "__main__":
    asyncio.run(main())
