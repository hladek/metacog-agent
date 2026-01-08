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
    The CRAAP test is a method to evaluate sources based on five criteria:
    - **Currency**: How timely is the information?
    - **Relevance**: How useful is this information for your needs?
    - **Authority**: Who is behind the content?
    - **Accuracy**: How correct and reliable is the content?
    - **Purpose**: Why does this content exist?
    
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic Information")
        st.write(f"**URL:** {result.url}")
        st.write(f"**Author:** {result.metadata.author_name}")
        st.write(f"**Blog Name:** {result.metadata.blog_name}")
        st.write(f"**Publisher:** {result.metadata.publisher_name}")
        st.write(f"**Published:** {result.metadata.publishing_date}")
    
    with col2:
        st.subheader("Author Details")
        st.write(f"**Anonymous:** {result.metadata.is_anonymous}")
        st.write(f"**Affiliation:** {result.metadata.author_affiliation}")
    
    st.markdown("---")
    st.subheader("Summary")
    st.write(result.metadata.summary)
    
    if result.raw_metadata:
        with st.expander("Raw Metadata"):
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
