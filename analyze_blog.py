import trafilatura
import sys
from pydantic import BaseModel
from agents import Agent, Runner, ModelSettings
import asyncio

class AccuracyInfo(BaseModel):
    pass

async def analyze_currency(text: str) -> str:
    """
        Use a language model to identify currency of the text
    
    Args:
        text: Extracted text from the blog
    
    """
    prompt=f"""
    Analyze the following blog content  to identify:

* Is the topic one where up-to-date information matters (e.g., technology, health, current events)?
* Does the blog show signs of being maintained?

What to look for:

* When was the blog post published or last updated?
* Visible publication/update dates
* Other dates
* Recent references
"""

    extraction_agent = Agent(
        name="currency_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

async def analyze_accuracy(text: str) -> str:
    """
    Use a language model to identify factual accuracy of the text
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        IntentInfo
    """
    prompt = f"""
    Analyze the following blog content  to identify:

* Does the blog provide sources, data, citations, or evidence?
* Can the content be verified through other trustworthy sources?
* Is the writing free of obvious errors or contradictions?
* Does the author distinguish between facts and opinions?

What to look for:

* Citations or references
* External links to credible sources
* Balanced, evidence-supported statements

    {text[:1000] if text else "No content available"}
"""
    
    
    extraction_agent = Agent(
        name="accuracy_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

class IntentInfo(BaseModel):
    tone: str
    style: str
    bias: str
    sentiment: str
    hate: str

async def analyze_intent(text: str) -> IntentInfo:
    """
    Use a language model to identify intent of the author.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        IntentInfo
    """
    prompt = f"""

Analyze the following blog content  to identify:
    - Tone and style of the text. Is it objective or opinion-driven?
    - Intent of the author. Is the blog trying to inform, persuade, entertain, or sell something?. Are there disclosure statements?
    - Bias towards social and political groups. Are ads, affiliate links, or sponsored content influencing the information?
    - Hate speech: identify possible vulgar, hate  speech or  politically incorrect speech
    If any information is not available, use "Unknown".

    Content preview:
    {text[:1000] if text else "No content available"}
    
    """
    
    extraction_agent = Agent(
        name="intent_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=IntentInfo,
    )
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

class BlogMetadata(BaseModel):
    author_name: str
    is_anonymous: bool
    blog_name: str
    publisher_name: str
    publishing_date: str


async def extract_blog_info_with_llm(text: str) -> BlogMetadata:
    """
    Use a language model to extract author name, blog name, and publisher name.
    
    Args:
        text: Extracted text from the blog
    
    Returns:
        BlogMetadata: Contains author_name, blog_name, and publisher_name
    """
    prompt = f"""
    Analyze the following blog content  to identify:
    1. The name of the author (person who wrote the article)
    2. If person name is real or pseudonym
    2. The name of the blog (title of the blog site or section)
    3. The name of the publisher (organization/company publishing the blog)
    4. Date of the publishing
    5. Tone and style of the text
    6. Intent of the author
    7. Bias towards social and political groups
    8. Hate speech: identify possible vulgar, hate  speech or  politically incorrect speech
    If any information is not available, use "Unknown".

    Content preview:
    {text[:1000] if text else "No content available"}
    
    """
    
    extraction_agent = Agent(
        name="blog_info_extractor",
        instructions=prompt,
        model_settings=ModelSettings(),
        output_type=BlogMetadata,
    )
    
    result = await Runner.run(extraction_agent, prompt)
    return result.final_output

def download_blog(url: str):
    """
    Download a blog page and extract text and hyperlinks using trafilatura.
    
    Args:
        url: The URL of the blog to download
    
    Returns:
        dict: Contains extracted text and hyperlinks
    """
    downloaded = trafilatura.fetch_url(url)
    
    if not downloaded:
        return {"error": "Failed to download the page"}
    
    metadata = trafilatura.extract_metadata(downloaded).as_dict()
    
    text = trafilatura.extract(
        downloaded,
        include_comments=True,
        include_tables=True,
        include_links=True,
        output_format='xml'
    )
    return text, metadata
    


async def analyze_blog(url):
    blog_text,metadata = download_blog(url)
    
    print("Metadata:", blog_text)
    
    # Extract blog information using LLM
    print("\n" + "="*50)
    print("Extracting blog information using LLM...")
    blog_info = await extract_blog_info_with_llm("URL:" +  str(metadata)  + " " + blog_text)
    print("\nAuthor Name:", blog_info.author_name)
    print("Blog Name:", blog_info.blog_name)
    print("Is real person:", blog_info.is_anonymous)
    print("Publishing date:", blog_info.publishing_date)
    print("Publisher Name:", blog_info.publisher_name)


    from person_reputation_agent import analyze_person 
    from publisher_reputation_agent import analyze_publisher 
    publisher_reputation = await analyze_publisher(blog_info.publisher_name)
    person_repuation = "Unknown"
    if blog_info.is_anonymous:
        person_repuation = await analyze_person(blog_info.author_name + " " + blog_info.publisher_name )
    intent_info = await analyze_intent(blog_text)
    print("Intent info:------")
    print(intent_info)

    accuracy_info = await analyze_accuracy(blog_text)
    print("Accuracy Info")
    print(accuracy_info)

    currency_info = await analyze_accuracy(blog_text)
    print("Currency Info")
    print(currency_info)

async def main():
    # Example usage
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com/blog'
    await analyze_blog(url)

if __name__ == "__main__":
    asyncio.run(main())

