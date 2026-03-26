"""
Streamlit application for CRAAP blog analysis.
"""

import os
import streamlit as st
import asyncio
from datetime import datetime
import re
import json
from pathlib import Path
from craap_api import analyze_blog, CRAAPAnalysisResult, assess_user_relevance, assess_user_purpose_analysis, save_analysis_to_json, load_analysis_from_json, OUTPUT_DIR

# Admin mode is enabled when CRAAP_ADMIN=true
ADMIN_MODE = os.environ.get("CRAAP_ADMIN", "").lower() == "true"

# Page configuration
st.set_page_config(
    page_title="CRAAP Blog Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'blog_content' not in st.session_state:
    st.session_state.blog_content = None
if 'blog_url' not in st.session_state:
    st.session_state.blog_url = None


# Sidebar navigation
st.sidebar.title("📰 CRAAP Analyzer")
st.sidebar.markdown("---")

# Navigation menu
if st.session_state.analysis_result is None:
    page = st.sidebar.radio("Navigation", ["Home"])
else:
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Currency", "Relevance", "Authority", "Accuracy", "Purpose"]
    )

st.sidebar.markdown("---")

# Helper to get display name from saved analysis JSON
def _blog_display_name(filepath: Path) -> str:
    """Return blog name from JSON metadata, falling back to filename stem."""
    try:
        with open(filepath) as fh:
            data = json.load(fh)
        name = (data.get("metadata") or {}).get("blog_name") or ""
        return name.strip() or filepath.stem
    except Exception:
        return filepath.stem

# Load saved analyses in sidebar
st.sidebar.subheader("📂 Load Saved Analysis")
output_dir = Path(OUTPUT_DIR)
if output_dir.exists():
    json_files = sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if json_files:
        for filepath in json_files:
            display = _blog_display_name(filepath)
            if st.sidebar.button(f"📄 {display}", key=f"sidebar_{filepath}", use_container_width=True):
                try:
                    with st.spinner("Loading analysis..."):
                        result = load_analysis_from_json(str(filepath))
                        st.session_state.analysis_result = result
                        st.session_state.blog_url = result.url
                        st.session_state.blog_content = None
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error loading: {str(e)}")
    else:
        st.sidebar.info("No saved analyses found.")
else:
    st.sidebar.info("No saved analyses directory found.")

# Blog metainformation in sidebar when analysis is loaded
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Blog Metainformation")

    st.sidebar.markdown(f"**🔗 URL**")
    st.sidebar.code(result.url, language=None)

    st.sidebar.markdown("**👤 Author**")
    author_name = result.metadata.author_name or "Unknown"
    if result.metadata.is_anonymous:
        st.sidebar.markdown("🕶️ Anonymous or unidentified author")
    else:
        st.sidebar.markdown(f"✓ **{author_name}**")
    affiliation = result.metadata.author_affiliation
    if affiliation and affiliation not in ["Unknown", "None"]:
        st.sidebar.markdown(f"_Affiliation:_ {affiliation}")

    st.sidebar.markdown("**🏢 Publisher**")
    publisher = result.metadata.publisher_name or "Not specified"
    st.sidebar.markdown(f"**{publisher}**")
    if result.metadata.blog_name and result.metadata.blog_name != publisher:
        st.sidebar.markdown(f"_Blog:_ {result.metadata.blog_name}")

    st.sidebar.markdown("**📅 Publication Date**")
    pub_date = result.metadata.publishing_date or "Not specified"
    if pub_date != "Not specified":
        try:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', pub_date)
            if date_match:
                parsed_date = datetime.strptime(date_match.group(), '%Y-%m-%d')
                days_ago = (datetime.now() - parsed_date).days
                if days_ago == 0:
                    time_ago = "Published today"
                elif days_ago == 1:
                    time_ago = "Published yesterday"
                elif days_ago < 7:
                    time_ago = f"Published {days_ago} days ago"
                elif days_ago < 30:
                    weeks = days_ago // 7
                    time_ago = f"Published {weeks} week{'s' if weeks > 1 else ''} ago"
                elif days_ago < 365:
                    months = days_ago // 30
                    time_ago = f"Published {months} month{'s' if months > 1 else ''} ago"
                else:
                    years = days_ago // 365
                    time_ago = f"Published {years} year{'s' if years > 1 else ''} ago"
                st.sidebar.markdown(f"**{pub_date[:10]}** — _{time_ago}_")
            else:
                st.sidebar.markdown(f"**{pub_date}**")
        except Exception:
            st.sidebar.markdown(f"**{pub_date}**")
    else:
        st.sidebar.markdown("**Not specified**")

    if st.session_state.blog_content:
        word_count = len(st.session_state.blog_content.split())
        read_time = max(1, word_count // 200)
        st.sidebar.markdown(f"**📝 Content:** {word_count:,} words · ~{read_time} min read")

    st.sidebar.markdown("**📋 Summary**")
    if result.metadata.summary:
        st.sidebar.write(result.metadata.summary)
    else:
        st.sidebar.info("_No summary available_")

# Home page
if page == "Home":
    st.title("🔍 CRAAP Blog Analyzer")
    st.markdown("""
    Welcome to the CRAAP Blog Analyzer! This tool helps you evaluate the credibility 
    and reliability of blog posts using the CRAAP test framework.
    
    ### What is CRAAP?
    The **CRAAP Test** is a widely-used evaluation framework developed by librarians at California State University, Chico 
    to help assess the quality and reliability of information sources. It's particularly valuable in today's digital age 
    where misinformation spreads rapidly. The acronym stands for five key criteria:
    
    - **Currency**: How timely is the information? When was it published or last updated?
    - **Relevance**: How useful is this information for your needs? Does it match your research level?
    - **Authority**: Who is behind the content? What are their credentials and qualifications?
    - **Accuracy**: How correct and reliable is the content? Can it be verified with evidence?
    - **Purpose**: Why does this content exist? What is the author's intent and potential bias?
    
    ### Learn More About Information Evaluation
    
    Explore these recommended methodologies for evaluating online sources:
    
    📚 **[CRAAP Test Guide](https://library.csuchico.edu/help/source-or-information-good)** - Comprehensive guide from CSU Chico  
    🔍 **[SIFT Method](https://www.ala.org/advocacy/intfreedom/SIFT)** - Four moves for quick fact-checking (Stop, Investigate, Find, Trace)  
    📡 **[RADAR Framework](https://www.open.edu/openlearn/ocw/mod/oucontent/view.php?id=106020)** - Evaluate sources using Relevance, Authority, Date, Appearance, and Reason
    
    ### Get Started
    """)
    if ADMIN_MODE:
        st.markdown("Enter a blog URL below to download and analyze it. Once analyzed, use the navigation menu to explore each CRAAP dimension.")
    else:
        st.markdown("Once a blog has been analyzed, use the navigation menu to explore each CRAAP dimension.")

    st.markdown("---")

    if ADMIN_MODE:
        # URL input (admin only)
        url = st.text_input("Enter blog URL:", placeholder="https://example.com/blog-post")

        col1, col2 = st.columns([1, 4])
        with col1:
            analyze_button = st.button("🚀 Analyze Blog", type="primary")
        with col2:
            if st.session_state.analysis_result:
                if st.button("🗑️ Clear Analysis"):
                    st.session_state.analysis_result = None
                    st.session_state.blog_content = None
                    st.session_state.blog_url = None
                    st.rerun()

        if analyze_button and url:
            with st.spinner("Downloading and analyzing blog..."):
                try:
                    result = asyncio.run(analyze_blog(url, analyze_author=True, analyze_publisher=True))
                    st.session_state.analysis_result = result
                    st.session_state.blog_content = result.blog_text
                    st.session_state.blog_url = url
                    st.success("✅ Analysis complete! Use the navigation menu to explore results.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
    else:
        if st.session_state.analysis_result:
            if st.button("🗑️ Clear Analysis"):
                st.session_state.analysis_result = None
                st.session_state.blog_content = None
                st.session_state.blog_url = None
                st.rerun()
    


# Currency page (includes metadata and timeliness)
elif page == "Currency":
    st.title("📅 Currency - Timeliness & Metadata")
    result = st.session_state.analysis_result
    
    # Quick tutorial
    st.markdown("""
Currency evaluates how up-to-date and timely a source is. Knowing when information was published, updated, and by whom helps determine its relevance and credibility.

Ask yourself:

* **When was it published or updated?**
  Check for clear dates on the page. Is the timing appropriate for your topic?

* **Is it current enough?**
  Fast-changing fields (e.g., tech, medicine, news) require recent sources, while stable topics may not.

* **Do links and references work?**
  Broken or outdated links can signal neglected or unreliable content.

* **Has it been maintained?**
  Look for updates, revisions, or signs the content is actively managed.

* **Is it outdated for your purpose?**
  Even recent content can be obsolete—watch for old standards, technologies, or research.
    """)
    
    st.markdown("---")

    # TODO
    #st.subheader("Do it yourself")
    #st.markdown("Search for the following parts in the text. Use the context to asses the currency of the text")
     
    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    # Publication Date & Timeliness
    pub_date = result.metadata.publishing_date or "Not specified"

    if pub_date != "Not specified":
        try:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', pub_date)
            if date_match:
                parsed_date = datetime.strptime(date_match.group(), '%Y-%m-%d')
                days_ago = (datetime.now() - parsed_date).days

                if days_ago == 0:
                    time_ago = "Published today"
                elif days_ago == 1:
                    time_ago = "Published yesterday"
                elif days_ago < 7:
                    time_ago = f"Published {days_ago} days ago"
                elif days_ago < 30:
                    weeks = days_ago // 7
                    time_ago = f"Published {weeks} week{'s' if weeks > 1 else ''} ago"
                elif days_ago < 365:
                    months = days_ago // 30
                    time_ago = f"Published {months} month{'s' if months > 1 else ''} ago"
                else:
                    years = days_ago // 365
                    time_ago = f"Published {years} year{'s' if years > 1 else ''} ago"

                st.markdown(f"**{pub_date[:10]}** — {time_ago}")
            else:
                st.markdown(f"**{pub_date}**")
        except Exception:
            st.markdown(f"**{pub_date}**")
    else:
        st.markdown("**Not specified**")

    st.markdown(result.currency)

    
    
    st.markdown("---")
    

# Relevance page
elif page == "Relevance":
    st.title("🎯 Relevance - Content Usefulness")
    
    st.markdown("""
   
    Relevance assesses how useful and appropriate the content is for your needs.
    Look at the text and try to answer the following questions. Ask yourself:

* **Does it relate to your topic?**
  Is the content directly connected to your research question or specific focus?

* **Who is the audience?**
  Is it aimed at experts, students, or the general public? Does that match your needs?

* **Is it the right level?**
  Too basic, too advanced, or appropriately detailed for your purpose?

* **Have you compared sources?**
  Is this the most suitable and useful source available?

* **Would you cite it?**
  Does it provide meaningful, relevant information that supports your work?
    """)
    
    st.markdown("---")
    
    st.subheader("Do it yourself")

    st.markdown("Write down answers to the following questions:")
    st.markdown("""
    - why do you search for this information?
    - What kind of information do you need?
    - What do you want to find in this material?

    Then asses by yoursef, if the text is appropriate for your purpose.
    """
    )
    
    # User answer input section
    st.markdown("---")
    st.subheader("📝 Your Answers")
    
    result = st.session_state.analysis_result
    user_answers = st.text_area(
        "Write your answers to the questions above:",
        placeholder="Example:\n- I'm searching for this information to learn about...\n- I need information that...\n- I want to find...",
        height=150,
        key="relevance_answers"
    )
    
    if st.button("🤖 Assess Relevance with AI", type="primary", key="assess_relevance_btn"):
        if not user_answers or user_answers.strip() == "":
            st.warning("⚠️ Please write your answers before assessing.")
        else:
            blog_content = st.session_state.blog_content or result.blog_text
            with st.spinner("Analyzing relevance of your answers to the blog content..."):
                try:
                    assessment = asyncio.run(
                        assess_user_relevance(blog_content, user_answers)
                    )
                    
                    st.markdown("---")
                    st.subheader("🤖 AI Relevance Assessment")
                    st.info(assessment)
                    
                except Exception as e:
                    st.error(f"Error during AI assessment: {str(e)}")


# Authority page
elif page == "Authority":
    st.title("👤 Authority - Source Credibility")
    result = st.session_state.analysis_result
    
    # Quick tutorial
    st.markdown("""
    Authority evaluates the credibility and expertise of the author and publisher.
Ask yourself following questions about the text:

* **Who is the author?**
  Are they clearly identified? What are their qualifications or expertise?

* **What are their credentials?**
  Do they have relevant education, experience, or publications? Are they affiliated with a reputable institution?

* **Who is the publisher?**
  Is the organization trustworthy and recognized in the field?

* **What is the domain?**
  Does the URL (.edu, .gov, .org, .com) align with the type of content and source?

* **Can you verify their expertise?**
  Find other work, profiles, or citations. Watch for bias or conflicts of interest.

    """)
    
    st.markdown("---")


    st.subheader("Do it yourself")
    
    
    if result.author_authority:
        st.markdown("Search the internet for information about the author.")
        if result.author_authority.search_url:
            st.markdown("You can use the following link as a starting point.")
            st.markdown(f"🔍 **[Search for author]({result.author_authority.search_url})**")
    if result.publisher_authority:
        st.markdown("Search the internet for information about the publisher.")
        if result.publisher_authority.search_url:
            st.markdown("You can use the following link as a starting point.")
            st.markdown(f"🔍 **[Search for publisher]({result.publisher_authority.search_url})**")

    st.info("When verifying information, use reputable sources such as:\n- Government websites (.gov)\n- Established news agencies (AP, Reuters, BBC, etc.)\n- Wikipedia for general information\n- Peer-reviewed research papers (Google Scholar, PubMed)\n- Fact-checking sites (Snopes, FactCheck.org)\n- Use trusted search engines and cross-reference multiple sources.")

    st.subheader("What AI Agent Analysis Shows")
    
    st.markdown("""
    Read the analysis consturcted automatically by an intelligent agent. Compare it with your conclustions.
    """)
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    # Author Authority
    st.subheader("👤 Author Authority")
    
    if result.author_authority:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Public Sentiment**")
            st.markdown(result.author_authority.public_sentiment)
            
            st.markdown("**Positive Mentions**")
            st.markdown(result.author_authority.positive_mentions)
        
        with col2:
            st.markdown("**Negative Mentions**")
            st.markdown(result.author_authority.negative_mentions)
            
            st.markdown("**Sources**")
            st.markdown(result.author_authority.sources)
        
        st.markdown("---")
        
        st.subheader("📊 Author Summary")
        st.markdown(result.author_authority.summary)
        
        
        if result.author_authority.justification:
            st.markdown("---")
            st.subheader("📝 Justification")
            st.markdown(result.author_authority.justification)
    else:
        st.warning("⚠️ Author authority analysis not available.")
    
    st.markdown("---")
    
    # Publisher Authority
    st.subheader("🏢 Publisher Authority")
    
    if result.publisher_authority:
        tabs = st.tabs(["Overview", "Bias & Reliability", "Public Perception"])
        
        with tabs[0]:
            st.markdown("**Ownership and Funding**")
            st.markdown(result.publisher_authority.ownership_and_funding)
            
            st.markdown("**Editorial Standards**")
            st.markdown(result.publisher_authority.editorial_standards)
        
        with tabs[1]:
            st.markdown("**Political Bias**")
            st.markdown(result.publisher_authority.political_bias)
            
            st.markdown("**Factual Reliability**")
            st.markdown(result.publisher_authority.factual_reliability)
        
        with tabs[2]:
            st.markdown("**Public Perception**")
            st.markdown(result.publisher_authority.public_perception)
        
        st.markdown("---")
        
        st.subheader("📊 Publisher Summary")
        st.markdown(result.publisher_authority.summary)
        
    else:
        st.warning("⚠️ Publisher authority analysis not available.")

# Accuracy page
elif page == "Accuracy":
    st.title("✓ Accuracy - Reliability & Correctness")
    result = st.session_state.analysis_result
    
    # Quick tutorial
    st.markdown("""
    
    Accuracy assesses the reliability, correctness, and verifiability of the content. Find answers to the following questions:

    1. **Where does the information come from?**
       - Are sources clearly cited and documented?
       - Can you verify the information in other sources?
       - Are there links to original research or data?
    
    2. **Is the information supported by evidence?**
       - Are claims backed up with facts, data, or research?
       - Can you distinguish between facts and opinions?
       - Are statistics and data presented with context?
    
    3. **Can you verify the information?**
       - Can you find the same information in other reliable sources?
       - Do the sources cited actually support the claims made?
       - Can you trace information back to the original source?
    
    4. **Has it been reviewed or refereed?**
       - Has the content been peer-reviewed or fact-checked?
       - Is there editorial oversight or quality control?
       - Are corrections or updates clearly noted?
    
    5. **Does the content appear reliable?**
       - Is the writing clear and free of errors (spelling, grammar)?
       - Does it seem objective and balanced?
       - Are there obvious signs of bias, exaggeration, or misinformation?
    """)
    
    st.markdown("---")
    
    st.subheader("Do it yourself")

    st.info("💡 **Important:** When verifying information, use reputable sources such as:\n- Government websites (.gov)\n- Established news agencies (AP, Reuters, BBC, etc.)\n- Wikipedia for general information\n- Peer-reviewed research papers (Google Scholar, PubMed)\n- Fact-checking sites (Snopes, FactCheck.org)\n- Use trusted search engines and cross-reference multiple sources.")
    
    st.markdown("Search the internet to verify the following claims from the text.")

    if result.facts_result.facts:
        st.markdown("As a starting point, use the provided links. You can also modify the search query to search for evidence against the claim.")
        for i, verified_fact in enumerate(result.facts_result.facts, 1):
            st.markdown(f"**{i}.** {verified_fact.fact}")
            if verified_fact.search_url:
                st.markdown(f"🔍 [Verify this fact]({verified_fact.search_url})")
    
    st.markdown("Pick some facts by yourself and try to verify them from reputable sources, such as Wikipedia, Google Scholar or established media agencies. ")
    st.markdown("---")
    
    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")

    st.markdown(result.accuracy_text)

    if result.facts_result.facts:
        st.markdown("---")
        st.subheader("🔎 Verified Facts")
        for verified_fact in result.facts_result.facts:
            with st.expander(verified_fact.fact):
                st.markdown(verified_fact.verification)
                if verified_fact.search_url:
                    st.markdown(f"🔍 [Search to verify]({verified_fact.search_url})")

    st.markdown("---")
    

# Purpose page
elif page == "Purpose":
    st.title("🎯 Purpose - Intent & Bias Analysis")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Purpose examines why the content exists and identifies potential biases or agendas.
Ask yourself:

* **What is the purpose?**
  Is it to inform, teach, persuade, sell, or entertain?

* **Is the intent clear?**
  Is it labeled as an ad, opinion, or factual report? Are there hidden agendas?

* **Is it fact, opinion, or propaganda?**
  Are claims supported by evidence, or driven by opinion or emotion?

* **Is it objective?**
  Does it present multiple perspectives and use neutral language?

* **Are there biases?**
  Who benefits? Is there political, ideological, or commercial influence?

    """)
    
    st.markdown("---")
    
    st.subheader("Do it yourself")
    st.markdown("Write down answers to the questions above to this text box. You can have automated feedback to your response.")
    
    
    user_purpose_answers = st.text_area(
        "Write your analysis of the blog's purpose:",
        placeholder="Example:\n- The purpose of this blog is to...\n- The author's intentions seem to be...\n- I detected bias toward/against...\n- The tone appears to be...",
        height=150,
        key="purpose_answers"
    )
    
    if st.button("🤖 Assess Purpose Analysis with AI", type="primary", key="assess_purpose_btn"):
        if not user_purpose_answers or user_purpose_answers.strip() == "":
            st.warning("⚠️ Please write your answers before assessing.")
        else:
            blog_content = st.session_state.blog_content or result.blog_text
            with st.spinner("Analyzing your purpose assessment against the blog content..."):
                try:
                    assessment = asyncio.run(
                        assess_user_purpose_analysis(blog_content, user_purpose_answers)
                    )
                    
                    st.markdown("---")
                    st.subheader("🤖 AI Purpose Assessment")
                    st.info(assessment)
                    
                except Exception as e:
                    st.error(f"Error during AI assessment: {str(e)}")
    
    st.markdown("---")
    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    
    st.subheader("✍️ Writing Style")
    st.markdown(f"**Tone:** {result.purpose.tone}")
    st.markdown(f"**Style:** {result.purpose.style}")
    st.markdown(f"**Sentiment:** {result.purpose.sentiment}")

    st.subheader("⚖️ Bias Analysis")
    st.markdown(f"**Bias:** {result.purpose.bias}")
    st.markdown(f"**Hate Speech Analysis:** {result.purpose.hate}")
    
    
    if result.purpose.justifications:
        st.subheader("📝 Justification")
        justification_list = result.purpose.justifications
        if justification_list:
            for item in justification_list:
                st.markdown(f"- {item}")
        else:
            st.markdown(result.purpose.justifications)
        st.markdown("---")
