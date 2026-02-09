"""
Streamlit application for CRAAP blog analysis.
"""

import streamlit as st
import asyncio
from datetime import datetime
import re
import json
from pathlib import Path
from craap_api import analyze_blog, download_blog, CRAAPAnalysisResult, assess_user_relevance, assess_user_purpose_analysis, save_analysis_to_json, load_analysis_from_json, OUTPUT_DIR

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
st.sidebar.markdown("""
### About CRAAP
**C**urrency - Timeliness  
**R**elevance - Usefulness  
**A**uthority - Source credibility  
**A**ccuracy - Reliability  
**P**urpose - Intent  
""")

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
    Enter a blog URL below to download and analyze it. Once analyzed, use the navigation 
    menu to explore each CRAAP dimension.
    """)
    
    st.markdown("---")
    
    # URL input
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
                # Download blog
                content, metadata = download_blog(url)
                if content is None:
                    st.error("Failed to download blog content. Please check the URL.")
                else:
                    st.session_state.blog_content = content
                    st.session_state.blog_url = url
                    
                    # Analyze blog
                    result = asyncio.run(analyze_blog(url, analyze_author=True, analyze_publisher=True))
                    st.session_state.analysis_result = result
                    
                    st.success("✅ Analysis complete! Use the navigation menu to explore results.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
    
    # Load saved analysis section
    st.markdown("---")
    st.subheader("📂 Load Saved Analysis")
    
    # Get list of saved analysis files
    output_dir = Path(OUTPUT_DIR)
    if output_dir.exists():
        json_files = sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if json_files:
            # Create a selectbox with file names
            file_options = ["Select a file..."] + [f.name for f in json_files]
            selected_file = st.selectbox("Choose a saved analysis:", file_options)
            
            col_load1, col_load2 = st.columns([1, 4])
            with col_load1:
                if st.button("📥 Load Analysis") and selected_file != "Select a file...":
                    try:
                        with st.spinner("Loading analysis..."):
                            filepath = output_dir / selected_file
                            result = load_analysis_from_json(str(filepath))
                            
                            st.session_state.analysis_result = result
                            st.session_state.blog_url = result.url
                            # Note: blog_content is not saved in JSON, set to None
                            st.session_state.blog_content = None
                            
                            st.success(f"✅ Analysis loaded from {selected_file}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading analysis: {str(e)}")
        else:
            st.info("No saved analyses found. Analyze a blog to create one.")
    else:
        st.info(f"No saved analyses directory found. Directory will be created at: {OUTPUT_DIR}")
    
    # Show current analysis info if available
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        st.markdown("---")
        st.info(f"**Currently analyzing:** {st.session_state.blog_url}")
        
        st.markdown("---")
        st.subheader("📋 Blog Metainformation")
        
        # URL Section
        st.markdown("**🔗 Source URL**")
        st.code(result.url, language=None)
        
        # Author Information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Author**")
            author_name = result.metadata.author_name or "Unknown"
            if result.metadata.is_anonymous:
                st.markdown(f"🕶️ Anonymous or unidentified author")
            else:
                st.markdown(f"✓ **{author_name}**")
            
            affiliation = result.metadata.author_affiliation
            if affiliation and affiliation not in ["Unknown", "None"]:
                st.markdown(f"_Affiliation:_ {affiliation}")
        
        with col2:
            st.markdown("**🏢 Publisher**")
            publisher = result.metadata.publisher_name or "Not specified"
            st.markdown(f"**{publisher}**")
            
            if result.metadata.blog_name and result.metadata.blog_name != publisher:
                st.markdown(f"_Blog:_ {result.metadata.blog_name}")
        
        # Publication Date
        st.markdown("**📅 Publication Date**")
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
                    
                    st.markdown(f"**{pub_date[:10]}** — _{time_ago}_")
                else:
                    st.markdown(f"**{pub_date}**")
            except:
                st.markdown(f"**{pub_date}**")
        else:
            st.markdown("**Not specified**")
        
        # Content Information
        st.markdown("**📝 Content**")
        if st.session_state.blog_content:
            word_count = len(st.session_state.blog_content.split())
            read_time = max(1, word_count // 200)
            st.markdown(f"Word count: {word_count:,} words · Reading time: ~{read_time} minute{'s' if read_time > 1 else ''}")
        
        # Content summary
        st.markdown("**📋 Summary**")
        if result.metadata.summary:
            st.write(result.metadata.summary)
        else:
            st.info("_No summary available_")

# Currency page (includes metadata and timeliness)
elif page == "Currency":
    st.title("📅 Currency - Timeliness & Metadata")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Currency examines the timeliness of information and key metadata about the source.
    Understanding when and by whom content was published is crucial for evaluating credibility.
    """)
    
    # Quick tutorial
    st.markdown("### 💡 How to Evaluate Currency")
    st.markdown("""
    
    1. **When was the information published or last updated?**
       - Look for publication and update dates on the page
       - Is there a clear timestamp visible on the content?
       - If the topic requires current information, is the content recent enough?
    
    2. **Is the information current enough for your topic?**
       - For rapidly changing fields (technology, medicine, current events), recent content is critical
       - For historical or stable topics, older content may still be valuable
       - Consider: Does this topic require the latest information?
    
    3. **Are the links and references still working?**
       - Broken links may indicate outdated or unmaintained content
       - Check if cited sources are still accessible
       - Dead links suggest the information may be stale
    
    4. **Has the information been revised or updated?**
       - Does the author maintain and update the content?
       - Are there update notes or revision histories?
       - Is there evidence of ongoing maintenance?
    
    5. **Is the information outdated for your purpose?**
       - Even if published recently, is the content itself outdated?
       - Does it reference old standards, deprecated technologies, or superseded research?
       - Compare with other current sources on the same topic
    """)
    
    st.markdown("---")

    st.subheader("Do it yourself")
    
    st.info("💡 **Important:** When verifying information, use reputable sources such as:\n- Government websites (.gov)\n- Established news agencies (AP, Reuters, BBC, etc.)\n- Wikipedia for general information\n- Peer-reviewed research papers (Google Scholar, PubMed)\n- Fact-checking sites (Snopes, FactCheck.org)\n- Use trusted search engines and cross-reference multiple sources.")

    st.markdown("Search for the following parts in the text. Use the context to asses the currency of the text")

    
    

    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    # Currency assessment
    if result.currency.requires_current_info and not result.currency.is_maintained:
        st.markdown("⚠️ This topic requires current information, but the blog doesn't appear to be regularly maintained.")
    elif result.currency.is_maintained and result.currency.has_recent_references:
        st.markdown("✅ The blog appears to be well-maintained with recent references.")
    else:
        st.markdown("ℹ️ Consider the publication date when evaluating this content.")

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
        except:
            st.markdown(f"**{pub_date}**")
    else:
        st.markdown("**Not specified**")
    if result.currency.justifications:
        examples_list = result.currency.justifications
        if examples_list:
            for example in examples_list:
                st.markdown(f"- {example}")
    
    if result.currency.examples:
        examples_list = result.currency.examples
        if examples_list:
            for example in examples_list:
                st.markdown(f"- {example}")

    
    
    st.markdown("---")
    

# Relevance page
elif page == "Relevance":
    st.title("🎯 Relevance - Content Usefulness")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Relevance assesses how useful and appropriate the content is for your needs.
    """)
    
    # Quick tutorial
    st.markdown("### 💡 How to Evaluate Relevance")
    st.markdown("""
    
    1. **Does it relate to your topic?**
       - Is the content directly relevant to your research question or information need?
       - Does it cover the specific aspects you're investigating?
    
    2. **Who is the intended audience?**
       - Is it written for experts, students, or general public?
       - Does the level of complexity match your needs?
    
    3. **Is it at the right level?**
       - Too basic: Oversimplified or lacks depth?
       - Too advanced: Technical jargon you don't understand?
       - Just right: Matches your knowledge level and purpose
    
    4. **Have you looked at other sources?**
       - Did you compare multiple sources before choosing this one?
       - Is this the best available source for your needs?
    
    5. **Would you cite this in your work?**
       - Is the information substantial enough to support your argument?
       - Does it add value to your research or project?
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
            with st.spinner("Analyzing relevance of your answers to the blog content..."):
                try:
                    assessment = asyncio.run(
                        assess_user_relevance(st.session_state.blog_content, user_answers)
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
    
    st.markdown("""
    Authority evaluates the credibility and expertise of the author and publisher.
    """)
    
    # Quick tutorial
    st.markdown("### 💡 How to Evaluate Authority")
    st.markdown("""
    
    1. **Who is the author?**
       - Is the author clearly identified?
       - What are their credentials, qualifications, or expertise?
       - Can you find information about them elsewhere?
    
    2. **What are their credentials?**
       - Do they have relevant education or professional experience?
       - Are they affiliated with a reputable institution or organization?
       - Have they published other work on this topic?
    
    3. **Who is the publisher or sponsor?**
       - What organization published or hosts this content?
       - Is the publisher reputable in this field?
       - What is their mission and purpose?
    
    4. **What is the domain/URL?**
       - .edu (educational), .gov (government), .org (organization), .com (commercial)
       - Does the domain match what you'd expect for this content?
       - Is it a well-known, established site?
    
    5. **Can you verify their expertise?**
       - Search for the author's name online
       - Check for reviews, citations, or professional profiles
       - Look for bias, conflicts of interest, or controversial reputation
    """)
    
    st.markdown("---")


    st.subheader("Do it yourself")
    
    st.info("💡 **Important:** When verifying information, use reputable sources such as:\n- Government websites (.gov)\n- Established news agencies (AP, Reuters, BBC, etc.)\n- Wikipedia for general information\n- Peer-reviewed research papers (Google Scholar, PubMed)\n- Fact-checking sites (Snopes, FactCheck.org)\n- Use trusted search engines and cross-reference multiple sources.")
    
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

    st.subheader("What AI Agent Analysis Shows")
    
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
    
    st.markdown("""
    Accuracy assesses the reliability, correctness, and verifiability of the content.
    """)
    
    # Quick tutorial
    st.markdown("### 💡 How to Evaluate Accuracy")
    st.markdown("""
    
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

    if result.accuracy.verifiable_facts and len(result.accuracy.verifiable_facts) > 0:
        st.markdown("As a starting poinnt, use the provided links. You can also modify the search query to search evidence against the claim. ")
        for i, fact in enumerate(result.accuracy.verifiable_facts, 1):
            st.markdown(f"**{i}.** {fact}")
            if result.accuracy.search_urls and i <= len(result.accuracy.search_urls):
                st.markdown(f"🔍 [Verify this fact]({result.accuracy.search_urls[i-1]})")
    
    st.markdown("Pick some facts by yourself and try to verify them from reputable sources, such as Wikipedia, Google Scholar or established media agencies. ")
    st.markdown("---")
    
    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    score = sum([
        result.accuracy.has_sources,
        result.accuracy.verifiable,
        result.accuracy.error_free
    ])
    
    if score == 3:
        st.success("✅ High accuracy: Content has sources, is verifiable, and appears error-free.")
    elif score == 2:
        st.warning("⚠️ Moderate accuracy: Some concerns identified. Review carefully.")
    else:
        st.error("❌ Low accuracy: Multiple concerns identified. Use with caution.")
    
    st.markdown("---")
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        has_sources = result.accuracy.has_sources
        st.metric("Has Sources", "Yes" if has_sources else "No", 
                 delta="Good" if has_sources else "Concerning",
                 delta_color="normal" if has_sources else "inverse")
    
    with col2:
        verifiable = result.accuracy.verifiable
        st.metric("Verifiable", "Yes" if verifiable else "No",
                 delta="Good" if verifiable else "Concerning",
                 delta_color="normal" if verifiable else "inverse")
    
    with col3:
        error_free = result.accuracy.error_free
        st.metric("Error Free", "Yes" if error_free else "No",
                 delta="Good" if error_free else "Concerning",
                 delta_color="normal" if error_free else "inverse")
    
    st.markdown("---")
    
    st.subheader("🔍 Facts vs. Opinions")
    st.markdown(result.accuracy.facts_vs_opinions)
    
    st.markdown("---")
    

# Purpose page
elif page == "Purpose":
    st.title("🎯 Purpose - Intent & Bias Analysis")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Purpose examines why the content exists and identifies potential biases or agendas.
    """)
    
    # Quick tutorial
    st.markdown("### 💡 How to Evaluate Purpose")
    st.markdown("""
    
    1. **What is the purpose of the information?**
       - To inform, teach, or educate?
       - To persuade, sell, or advocate?
       - To entertain or express opinions?
    
    2. **Do the authors make their intentions clear?**
       - Is the purpose explicitly stated?
       - Is it an advertisement, opinion piece, or factual report?
       - Are there hidden agendas or conflicts of interest?
    
    3. **Is the information fact, opinion, or propaganda?**
       - Are claims presented as facts backed by evidence?
       - Is the content primarily opinion or commentary?
       - Does it use emotional language or manipulation?
    
    4. **Does the point of view appear objective and impartial?**
       - Is more than one perspective presented?
       - Does the author acknowledge limitations or counterarguments?
       - Is the language neutral or emotionally charged?
    
    5. **Are there political, ideological, or commercial biases?**
       - Who benefits from this information?
       - Is there advertising or sponsored content?
       - Does the author or publisher have a known bias?
    """)
    
    st.markdown("---")
    
    st.subheader("Do it yourself")
    st.markdown("Write down answers to the questions above.")
    
    # User answer input section
    st.markdown("---")
    st.subheader("📝 Your Answers")
    
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
            with st.spinner("Analyzing your purpose assessment against the blog content..."):
                try:
                    assessment = asyncio.run(
                        assess_user_purpose_analysis(st.session_state.blog_content, user_purpose_answers)
                    )
                    
                    st.markdown("---")
                    st.subheader("🤖 AI Purpose Assessment")
                    st.info(assessment)
                    
                except Exception as e:
                    st.error(f"Error during AI assessment: {str(e)}")
    
    st.markdown("---")
    st.subheader("What AI Agent Analysis Shows")
    
    st.warning("⚠️ **Note:** AI analysis has inherent biases and limitations. The outputs can be difficult to justify and explain. Use this as a supplementary tool, not the sole basis for evaluation.")
    
    if result.purpose.justifications:
        st.subheader("📝 Justification")
        justification_list = result.purpose.justifications
        if justification_list:
            for item in justification_list:
                st.markdown(f"- {item}")
        else:
            st.markdown(result.purpose.justifications)
        st.markdown("---")
    
    st.subheader("✍️ Writing Style")
    st.markdown(f"**Tone:** {result.purpose.tone}")
    st.markdown(f"**Style:** {result.purpose.style}")
    st.markdown(f"**Sentiment:** {result.purpose.sentiment}")

    st.subheader("⚖️ Bias Analysis")
    st.markdown(f"**Bias:** {result.purpose.bias}")
    st.markdown(f"**Hate Speech Analysis:** {result.purpose.hate}")
    
    
