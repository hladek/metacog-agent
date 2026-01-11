"""
Streamlit application for CRAAP blog analysis.
"""

import streamlit as st
import asyncio
from craap_api import analyze_blog, download_blog, CRAAPAnalysisResult

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
        ["Home", "Metadata", "Currency", "Relevance", "Authority", "Accuracy", "Purpose"]
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
    
    # Show current analysis info if available
    if st.session_state.analysis_result:
        st.markdown("---")
        st.info(f"**Currently analyzing:** {st.session_state.blog_url}")

# Metadata page
elif page == "Metadata":
    st.title("📄 Blog Metadata")
    result = st.session_state.analysis_result
    
    # Quick tutorial
    with st.expander("💡 How to Evaluate Blog Metadata"):
        st.markdown("""
        
        1. Identify author and affiliation author
           - Is it anonymous author?     
           - What institution or organization is the author associated with?
        2. **Publisher/Platform** 
           - Where is this content published?
        3. **Publication Date** 
           - When was the content published?
           - How current is the information?
        4. **Message**
           - Identify the genre, topic and main points of the text.
        """)
    
    # URL Section
    st.code(result.url, language=None)
    st.markdown("---")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        author_name = result.metadata.author_name or "Unknown"
        author_icon = "🕶️" if result.metadata.is_anonymous else "✓"
        st.metric("Author", f"{author_name} {author_icon}")
    
    with col2:
        st.metric("Publisher", result.metadata.publisher_name or "Not specified")
    
    with col3:
        pub_date = result.metadata.publishing_date or "Not specified"
        # Calculate time ago
        time_ago = ""
        if pub_date != "Not specified":
            try:
                from datetime import datetime
                import re
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', pub_date)
                if date_match:
                    parsed_date = datetime.strptime(date_match.group(), '%Y-%m-%d')
                    days_ago = (datetime.now() - parsed_date).days
                    if days_ago == 0:
                        time_ago = "today"
                    elif days_ago == 1:
                        time_ago = "yesterday"
                    elif days_ago < 7:
                        time_ago = f"{days_ago}d ago"
                    elif days_ago < 30:
                        time_ago = f"{days_ago // 7}w ago"
                    elif days_ago < 365:
                        time_ago = f"{days_ago // 30}mo ago"
                    else:
                        time_ago = f"{days_ago // 365}y ago"
            except:
                pass
        st.metric("Published", pub_date[:10] if len(pub_date) > 10 else pub_date, delta=time_ago)
    
    with col4:
        if st.session_state.blog_content:
            word_count = len(st.session_state.blog_content.split())
            read_time = max(1, word_count // 200)
            st.metric("Read Time", f"{read_time} min", delta=f"{word_count:,} words")
        else:
            st.metric("Read Time", "N/A")
    
    st.markdown("---")
    
    # Author transparency assessment
    author_indicators = []
    if not result.metadata.is_anonymous:
        author_indicators.append("✅ Author identified")
    else:
        author_indicators.append("⚠️ Anonymous author")
    
    affiliation = result.metadata.author_affiliation
    if affiliation and affiliation not in ["Unknown", "None"]:
        author_indicators.append(f"✅ Affiliation: {affiliation}")
    else:
        author_indicators.append("ℹ️ No affiliation listed")
    
    if result.metadata.blog_name:
        author_indicators.append(f"📰 Blog: {result.metadata.blog_name}")
    
    # Display as compact list
    st.markdown("**Authorship:** " + " • ".join(author_indicators))
    
    st.markdown("---")
    
    # Content summary
    st.subheader("Summary")
    if result.metadata.summary:
        st.write(result.metadata.summary)
    else:
        st.info("_No summary available_")
    
    # Raw metadata in expandable section
    if result.raw_metadata:
        st.markdown("---")
        with st.expander("🔍 Technical Details"):
            st.json(result.raw_metadata)

# Currency page
elif page == "Currency":
    st.title("📅 Currency - Timeliness Analysis")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Currency examines how timely and up-to-date the information is. This is particularly 
    important for topics that change rapidly.
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Requires Current Info", 
                 "Yes" if result.currency.requires_current_info else "No")
        st.metric("Is Maintained", 
                 "Yes" if result.currency.is_maintained else "No")
    
    with col2:
        st.metric("Published Date", result.currency.published_date)
        st.metric("Last Updated", result.currency.last_updated)
    
    with col3:
        st.metric("Recent References", 
                 "Yes" if result.currency.has_recent_references else "No")
    
    st.markdown("---")
    st.subheader("Analysis")
    
    if result.currency.requires_current_info and not result.currency.is_maintained:
        st.warning("⚠️ This topic requires current information, but the blog doesn't appear to be regularly maintained.")
    elif result.currency.is_maintained and result.currency.has_recent_references:
        st.success("✅ The blog appears to be well-maintained with recent references.")
    else:
        st.info("ℹ️ Consider the publication date when evaluating this content.")

# Relevance page
elif page == "Relevance":
    st.title("🎯 Relevance - Content Usefulness")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Relevance assesses how useful and appropriate the content is for your needs.
    """)
    
    st.markdown("---")
    
    st.subheader("Content Summary")
    st.write(result.metadata.summary)
    
    st.markdown("---")
    st.subheader("Target Audience & Scope")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Tone:** {result.purpose.tone}")
        st.write(f"**Style:** {result.purpose.style}")
    
    with col2:
        st.write(f"**Publisher Type:** {result.metadata.publisher_name}")
        st.write(f"**Author Affiliation:** {result.metadata.author_affiliation}")
    
    st.markdown("---")
    st.info("💡 Consider whether this content matches your research needs and expertise level.")

# Authority page
elif page == "Authority":
    st.title("👤 Authority - Source Credibility")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Authority evaluates the credibility and expertise of the author and publisher.
    """)
    
    st.markdown("---")
    
    # Author Authority
    st.subheader("👤 Author Authority")
    
    if result.author_authority:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Public Sentiment**")
            st.write(result.author_authority.public_sentiment)
            
            st.write("**Positive Mentions**")
            st.write(result.author_authority.positive_mentions)
        
        with col2:
            st.write("**Negative Mentions**")
            st.write(result.author_authority.negative_mentions)
            
            st.write("**Sources**")
            st.write(result.author_authority.sources)
        
        st.markdown("---")
        st.write("**Summary**")
        st.info(result.author_authority.summary)
    else:
        st.warning("Author authority analysis not available.")
    
    st.markdown("---")
    
    # Publisher Authority
    st.subheader("🏢 Publisher Authority")
    
    if result.publisher_authority:
        tabs = st.tabs(["Overview", "Bias & Reliability", "Public Perception"])
        
        with tabs[0]:
            st.write("**Ownership and Funding**")
            st.write(result.publisher_authority.ownership_and_funding)
            
            st.write("**Editorial Standards**")
            st.write(result.publisher_authority.editorial_standards)
        
        with tabs[1]:
            st.write("**Political Bias**")
            st.write(result.publisher_authority.political_bias)
            
            st.write("**Factual Reliability**")
            st.write(result.publisher_authority.factual_reliability)
        
        with tabs[2]:
            st.write("**Public Perception**")
            st.write(result.publisher_authority.public_perception)
        
        st.markdown("---")
        st.write("**Summary**")
        st.info(result.publisher_authority.summary)
    else:
        st.warning("Publisher authority analysis not available.")

# Accuracy page
elif page == "Accuracy":
    st.title("✓ Accuracy - Reliability & Correctness")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Accuracy assesses the reliability, correctness, and verifiability of the content.
    """)
    
    st.markdown("---")
    
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
    st.subheader("Facts vs. Opinions")
    st.write(result.accuracy.facts_vs_opinions)
    
    st.markdown("---")
    st.subheader("Overall Assessment")
    
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

# Purpose page
elif page == "Purpose":
    st.title("🎯 Purpose - Intent & Bias Analysis")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Purpose examines why the content exists and identifies potential biases or agendas.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Writing Style")
        st.write(f"**Tone:** {result.purpose.tone}")
        st.write(f"**Style:** {result.purpose.style}")
        st.write(f"**Sentiment:** {result.purpose.sentiment}")
    
    with col2:
        st.subheader("Bias Analysis")
        st.write(f"**Bias:** {result.purpose.bias}")
        st.write(f"**Hate Speech Analysis:** {result.purpose.hate}")
    
    st.markdown("---")
    st.subheader("Interpretation")
    
    if "objective" in result.purpose.tone.lower():
        st.success("✅ The content appears to maintain an objective tone.")
    elif "opinion" in result.purpose.tone.lower():
        st.info("ℹ️ The content is opinion-driven. Consider this when evaluating claims.")
    
    if "neutral" in result.purpose.bias.lower():
        st.success("✅ No significant bias detected.")
    else:
        st.warning(f"⚠️ Potential bias detected: {result.purpose.bias}")
    
    if "none" in result.purpose.hate.lower() or "no hate" in result.purpose.hate.lower():
        st.success("✅ No hate speech or inappropriate content detected.")
    else:
        st.error(f"❌ Concerning content detected: {result.purpose.hate}")
