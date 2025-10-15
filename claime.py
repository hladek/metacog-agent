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
    verdict: str
    justification: str

class Verdict(BaseModel):
    query: str
    source: str
    url: str
    verdict: str
    justification: str


class SearchVerdict(BaseModel):
    searches: list[Verdict]
    final_verdict: str
    final_justification: str

class FactQuery(BaseModel):
    query: str
    source: str

class FactVerdict(BaseModel):
    verdict: str
    justification: str

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
    instructions=prompts.QUERY_GENERATE_AND_SEARCH,
    model_settings=ModelSettings(tool_choice="required"),
    output_type=SearchVerdict,
)

fact_query_agent = Agent(
    name = "fact_search_agent",
    instructions=prompts.QUERY_SEARCH,
    output_type=list[FactQuery],
)

fact_retrieve_agent = Agent(
    name = "fact_retrieve_agent",
    tools=[WebSearchTool()],
    instructions=prompts.QUERY_SEARCH,
    model_settings=ModelSettings(tool_choice="required"),
    output_type=FactVerdict,
)

final_verdict_agent = Agent(
    name="final_verdict_agent",
    instructions=prompts.FINAL_VERDICT,
)

# https://github.com/openai/openai-agents-python/blob/main/examples/agent_patterns/llm_as_a_judge.py    


# https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api_agents
def print_final_output_citations(stream, preceding_chars=50):
    citations = []
    # Iterate over new_items in reverse to find the last message_output_item(s)
    for item in reversed(stream.new_items):
        if item.type == "message_output_item":
            for content in getattr(item.raw_item, 'content', []):
                if not hasattr(content, 'annotations') or not hasattr(content, 'text'):
                    continue
                text = content.text
                for ann in content.annotations:
                    if getattr(ann, 'type', None) == 'url_citation':
                        title = getattr(ann, 'title', '<no title>')
                        url = getattr(ann, 'url', '<no url>')
                        start = getattr(ann, 'start_index', None)
                        end = getattr(ann, 'end_index', None)

                        if start is not None and end is not None and isinstance(text, str):
                            citations.append((title,url))
                            # Calculate preceding snippet start index safely
                            #pre_start = max(0, start - preceding_chars)
                            #preceding_text = text[pre_start:start].replace('\n', ' ').strip()
                            #excerpt = text[start:end].replace('\n', ' ').strip()
                        #else:
                            # fallback if no indices available
                            #print(f"- {title}: {url}")
            break
    return citations

async def main():
    input_prompt = input("PLease insert a text with factual claims")

    # Ensure the entire workflow is a single trace
    out = []
    with trace("Deterministic flow"):
        # 1. identify facts. 
        # the agent can return a pre-liminary fact evaluation
        # TODO the opriginal claime approach evaluates each sentence in context for existence of a factual claim.
        # this will make the agent mode difficult and expensive.
        facts_result = await Runner.run(
            fact_identification_agent,
            input_prompt,
        )
        print("Ideintified facts")
        #print(facts_result)
        
        # for each claim
        # check evidence on web
        for claim in facts_result.final_output:
            print("-------------")
            print(claim.text)
            # https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent
            # generate query and search for the claim
            # TODO - generate multiple queries if necessary Add a gate to stop or regenerate results are not good quality
            #fact_search_result = await Runner.run(
            #    fact_search_agent,
            #    claim.text,
            #)
            #print(fact_search_result)

            fact_query_result = await Runner.run(
                fact_query_agent,
                claim.text,
            )
            print(fact_query_result)
            queries = fact_query_result.final_output
            print(queries)
            #q = "source:" + query.source + "query:" + query.query
            zz = []
            for q in queries:
                zz.append(q.source)
                zz.append(":")
                zz.append(q.query)
            fact_retrieve_result = await Runner.run(
                fact_retrieve_agent,
                " ".join(zz),
            )
            print(fact_retrieve_result)
            citations = print_final_output_citations(fact_retrieve_result)
            result = fact_retrieve_result.final_output
            out.append(claim.text  + result.verdict + " " + result.justification)

            
        
        final_verdict_result = await Runner.run(
                final_verdict_agent,
                input_prompt + " ".join(out),
        )
        print("<<<<<<<<<<")
        print(final_verdict_result)


if __name__ == "__main__":
    asyncio.run(main())
