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
    
    # Show current analysis info if available
    if st.session_state.analysis_result:
        st.markdown("---")
        st.info(f"**Currently analyzing:** {st.session_state.blog_url}")

# Currency page (includes metadata and timeliness)
elif page == "Currency":
    st.title("📅 Currency - Timeliness & Metadata")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Currency examines the timeliness of information and key metadata about the source.
    Understanding when and by whom content was published is crucial for evaluating credibility.
    """)
    
    # Quick tutorial
    with st.expander("💡 How to Evaluate Currency"):
        st.markdown("""
        
        1. **Author Identity**
           - Is the author identified or anonymous?
           - What institution or organization is the author associated with?
        2. **Publisher/Platform** 
           - Where is this content published?
           - Is the publisher reputable?
        3. **Publication Date** 
           - When was the content published?
           - How current is the information for this topic?
           - Is the blog regularly maintained?
        4. **Content Overview**
           - Understand the scope and main points of the text
        """)
    
    st.markdown("---")
    
    # URL Section
    st.subheader("🔗 Source URL")
    st.code(result.url, language=None)
    
    st.markdown("---")
    
    # Author Information
    st.subheader("👤 Author")
    author_name = result.metadata.author_name or "Unknown"
    if result.metadata.is_anonymous:
        st.warning(f"🕶️ Anonymous or unidentified author")
    else:
        st.success(f"✓ **{author_name}**")
    
    affiliation = result.metadata.author_affiliation
    if affiliation and affiliation not in ["Unknown", "None"]:
        st.markdown(f"**Affiliation:** {affiliation}")
    
    st.markdown("---")
    
    # Publisher Information
    st.subheader("🏢 Publisher")
    publisher = result.metadata.publisher_name or "Not specified"
    st.markdown(f"**{publisher}**")
    
    if result.metadata.blog_name and result.metadata.blog_name != publisher:
        st.markdown(f"**Blog:** {result.metadata.blog_name}")
    
    st.markdown("---")
    
    # Publication Date & Timeliness
    st.subheader("📅 Publication Date & Timeliness")
    pub_date = result.metadata.publishing_date or "Not specified"
    
    if pub_date != "Not specified":
        try:
            from datetime import datetime
            import re
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
    
    # Currency analysis
    st.markdown(f"**Last Updated:** {result.currency.last_updated}")
    st.markdown(f"**Requires Current Info:** {'Yes' if result.currency.requires_current_info else 'No'}")
    st.markdown(f"**Is Maintained:** {'Yes' if result.currency.is_maintained else 'No'}")
    st.markdown(f"**Has Recent References:** {'Yes' if result.currency.has_recent_references else 'No'}")
    
    # Currency assessment
    if result.currency.requires_current_info and not result.currency.is_maintained:
        st.warning("⚠️ This topic requires current information, but the blog doesn't appear to be regularly maintained.")
    elif result.currency.is_maintained and result.currency.has_recent_references:
        st.success("✅ The blog appears to be well-maintained with recent references.")
    else:
        st.info("ℹ️ Consider the publication date when evaluating this content.")
    
    st.markdown("---")
    
    # Content Information
    st.subheader("📝 Content")
    if st.session_state.blog_content:
        word_count = len(st.session_state.blog_content.split())
        read_time = max(1, word_count // 200)
        st.markdown(f"**Word count:** {word_count:,} words")
        st.markdown(f"**Reading time:** ~{read_time} minute{'s' if read_time > 1 else ''}")
    
    st.markdown("---")
    
    # Content summary
    st.subheader("📋 Summary")
    if result.metadata.summary:
        st.write(result.metadata.summary)
    else:
        st.info("_No summary available_")
    
    # Important technical details
    if result.raw_metadata:
        st.markdown("---")
        with st.expander("🔍 Additional Technical Details"):
            # Extract only important technical details
            important_fields = {
                'title': 'Title',
                'description': 'Description',
                'keywords': 'Keywords',
                'language': 'Language',
                'content_type': 'Content Type',
                'charset': 'Character Encoding',
                'canonical_url': 'Canonical URL'
            }
            
            details_found = False
            for key, label in important_fields.items():
                if key in result.raw_metadata and result.raw_metadata[key]:
                    value = result.raw_metadata[key]
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    st.markdown(f"**{label}:** {value}")
                    details_found = True
            
            if not details_found:
                st.info("No additional technical details available")

# Relevance page
elif page == "Relevance":
    st.title("🎯 Relevance - Content Usefulness")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Relevance assesses how useful and appropriate the content is for your needs.
    """)
    
    # Quick tutorial
    with st.expander("💡 How to Evaluate Relevance"):
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
    
    st.subheader("📋 Content Summary")
    st.markdown(result.metadata.summary)
    
    st.markdown("---")
    
    st.subheader("🎓 Target Audience & Scope")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Tone:** {result.purpose.tone}")
        st.markdown(f"**Style:** {result.purpose.style}")
    
    with col2:
        st.markdown(f"**Publisher Type:** {result.metadata.publisher_name}")
        st.markdown(f"**Author Affiliation:** {result.metadata.author_affiliation}")
    
    st.markdown("---")
    
    st.subheader("📊 Assessment")
    st.info("💡 Consider whether this content matches your research needs and expertise level.")
    st.subheader("📊 Assessment")
    st.info("💡 Consider whether this content matches your research needs and expertise level.")

# Authority page
elif page == "Authority":
    st.title("👤 Authority - Source Credibility")
    result = st.session_state.analysis_result
    
    st.markdown("""
    Authority evaluates the credibility and expertise of the author and publisher.
    """)
    
    # Quick tutorial
    with st.expander("💡 How to Evaluate Authority"):
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
        st.info(result.author_authority.summary)
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
        st.info(result.publisher_authority.summary)
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
    with st.expander("💡 How to Evaluate Accuracy"):
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
    
    st.subheader("📊 Overall Assessment")
    
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
    
    # Quick tutorial
    with st.expander("💡 How to Evaluate Purpose"):
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✍️ Writing Style")
        st.markdown(f"**Tone:** {result.purpose.tone}")
        st.markdown(f"**Style:** {result.purpose.style}")
        st.markdown(f"**Sentiment:** {result.purpose.sentiment}")
    
    with col2:
        st.subheader("⚖️ Bias Analysis")
        st.markdown(f"**Bias:** {result.purpose.bias}")
        st.markdown(f"**Hate Speech Analysis:** {result.purpose.hate}")
    
    st.markdown("---")
    
    st.subheader("📊 Interpretation")
    
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
