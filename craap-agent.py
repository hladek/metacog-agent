from openai_agents import Agent, Task, Tool, Observation
"""
Generated using Copilot:

Use openai-agents sdk. Write an agent that will automatically asses a given text using CRAAP (credibility, relevance, authority, accuracy, purpose) information assessment methodology.

TODO - test

"""

class CRAAPAssessmentAgent(Agent):
    """
    An agent that assesses a given text using the CRAAP methodology:
    Credibility, Relevance, Authority, Accuracy, Purpose.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tools = [self.craap_tool()]

    def craap_tool(self):
        """
        Defines a tool for CRAAP assessment.
        """
        def assess(text: str) -> dict:
            """
            Given a text, returns a CRAAP assessment.
            """
            # Use LLM or rules to assess each criterion
            def basic_check(criterion, prompt):
                # This could call LLM or use heuristics
                response = self.llm(prompt.format(text=text))
                return response

            return {
                "Credibility": basic_check(
                    "Credibility",
                    "Assess the credibility of the following text: {text}\nIs the author trustworthy? Is the evidence reliable?"
                ),
                "Relevance": basic_check(
                    "Relevance",
                    "Assess the relevance of the following text for a research context: {text}\nIs the information directly related to the topic?"
                ),
                "Authority": basic_check(
                    "Authority",
                    "Assess the authority of the source in the following text: {text}\nIs the author or publisher an expert on the topic?"
                ),
                "Accuracy": basic_check(
                    "Accuracy",
                    "Assess the accuracy of the following text: {text}\nIs the information supported by evidence and free of errors?"
                ),
                "Purpose": basic_check(
                    "Purpose",
                    "Assess the purpose of the following text: {text}\nIs the intent to inform, to persuade, to sell, or something else? Is there bias?"
                ),
            }

        return Tool(
            name="craap_assessment",
            description="Assess text using CRAAP methodology",
            func=assess,
            input_schema={"text": "string"},
            output_schema={
                "Credibility": "string",
                "Relevance": "string",
                "Authority": "string",
                "Accuracy": "string",
                "Purpose": "string",
            }
        )

    def run(self, text: str) -> Observation:
        """
        Run CRAAP assessment on input text.
        """
        result = self.tools[0](text=text)
        return Observation(
            content="CRAAP Assessment",
            data=result
        )

# Usage Example:
# agent = CRAAPAssessmentAgent()
# assessment = agent.run("Sample text to assess...")
# print(assessment.data)
