
import asyncio
from agents import Agent, run_demo_loop

bias_instructions = "For the given text: identify possible bias towards minorities, organizations or political entities"
sentiment_instructions = "Analyze sentiment in range -2 for most negative to +2 for the most ppositive."
abuse_instructions = "For the given text, identify possible hate speech, politically incorrect speech, illegal activities, personal information"
facts_instructions = "For the given text, identify and list verifiable factual claims."
purpose_instructions = "Assess the tone and possible intent of author"

bias_agent = Agent(name="bias_agent",instructions=bias_instructions)

sentiment_agent = Agent(name="sentiment_agent",instructions=sentiment_instructions)
abuse_agent = Agent(name="abuse_agent",instructions=abuse_instructions)
facts_agent = Agent(name="facts_agent",instructions=facts_instructions)
purpose_agent = Agent(name="purpose_agent",instructions=purpose_instructions)


content_agent = "Evaluate the given text with all given tools. Write a report from the gathered information."

content_agent = Agent(name="content_agemt",instructions=content_agent,tools=[
    bias_agent.as_tool(tool_name="bias_agent",tool_description="Evaluates possible bias in text"),
    sentiment_agent.as_tool(tool_name="sentimen_agent",tool_description="Evaluates sentiment in text"),
    abuse_agent.as_tool(tool_name="abuse_agent",tool_description="Evaluates possible abuse in text"),
    facts_agent.as_tool(tool_name="facts_agent",tool_description="Identifies factual claims in text"),
    purpose_agent.as_tool(tool_name="purpose_agent",tool_description="Identifies intent of the author"),
    ])

async def main() -> None:
    await run_demo_loop(content_agent)

if __name__ == "__main__":
    asyncio.run(main())
