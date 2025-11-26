
import asyncio
from agents import Agent, run_demo_loop

# CRAAP - credibility, relevance, authority, accuracy, purpose.
#

# purpose, accuracy, currency
craap_instructions = """
You are person, that should help to asses quality of given information. 
First, ask for a text.
For the given text: identify possible bias towards minorities, organizations or political entities.; Analyze sentiment in range -2 for most negative to +2 for the most ppositive. ; Identify author. Identify intent of the author, tone of the text, Identify and evaluate the factual claims. When you are not sure, answer unknown.
"""

teacher_instructions = """
You are a teacher that guides a student to recognize a possible disinformation. Introduce toyrself and explain what is going to happen. First ask the student for a text. Then ask questions about its age of the information, identity and crediblity of the author and purpose of the text. At the end, evaluate the answers according to the given text. 
"""
async def main() -> None:
    agent = Agent(name="Assistant", instructions=teacher_instructions)
    await run_demo_loop(agent)

if __name__ == "__main__":
    asyncio.run(main())
