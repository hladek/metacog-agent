import streamlit as st
import asyncio
from analyze_blog import (
    analyze_blog,
    download_blog,
    extract_blog_info_with_llm,
    analyze_intent,
    analyze_accuracy,
    analyze_currency
)
from person_reputation_agent import analyze_person
from publisher_reputation_agent import analyze_publisher

st.set_page_config(page_title="Blog Analyzer", page_icon="📝", layout="wide")

st.title("📝 Blog Content Analyzer")
st.markdown("Analyze blog posts for credibility, accuracy, currency, and intent using the CRAAP framework.")

# Input section
url = st.text_input("Enter Blog URL:", placeholder="https://example.com/blog-post")

if st.button("Analyze", type="primary"):
    if not url:
        st.error("Please enter a URL")
    else:
        with st.spinner("Downloading and analyzing blog..."):
            # Download blog
            blog_text, metadata = download_blog(url)
            
            if blog_text is None:
                st.error(f"Failed to download blog: {metadata.get('error', 'Unknown error')}")
            else:
                # Extract blog info first
                blog_info = asyncio.run(
                    extract_blog_info_with_llm("URL: " + str(metadata) + "\n\n" + (blog_text or ""))
                )
                
                # Display summary, image, and content preview prominently at top
                st.markdown("---")
                
                # Summary and Metadata side by side
                col_sum, col_meta = st.columns([2, 1])
                
                with col_sum:
                    if blog_info.summary and blog_info.summary.lower() != "unknown":
                        st.subheader("📝 Summary")
                        st.info(blog_info.summary)
                
                with col_meta:
                    st.subheader("📋 Metadata")
                    if metadata:
                        if metadata.get('title'):
                            st.write(f"**Title:** {metadata['title']}")
                        if metadata.get('author'):
                            st.write(f"**Author:** {metadata['author']}")
                        if metadata.get('date'):
                            st.write(f"**Published:** {metadata['date']}")
                        if metadata.get('sitename'):
                            st.write(f"**Site:** {metadata['sitename']}")
                        if metadata.get('url'):
                            st.write(f"**URL:** {metadata['url']}")
                
                # Image and Content Preview side by side
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if metadata.get('image'):
                        st.subheader("🖼️ Featured Image")
                        st.image(metadata['image'], use_container_width=True)
                
                with col2:
                    st.subheader("📄 Content Preview")
                    st.text_area("First 2000 characters", 
                                blog_text[:2000] if blog_text else "No content available", 
                                height=300, label_visibility="collapsed")
                
                st.markdown("---")
                
                # Create tabs for detailed analysis
                tab1, tab2, tab3, tab4 = st.tabs([
                    "👤 Author & Publisher", 
                    "🎯 Intent", 
                    "✅ Accuracy", 
                    "📅 Currency"
                ])
                
                # Tab 1: Author & Publisher
                with tab1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("👤 Author Information")
                        st.write(f"**Name:** {blog_info.author_name}")
                        st.write(f"**Affiliation:** {blog_info.author_affiliation}")
                        st.write(f"**Anonymous:** {blog_info.is_anonymous}")
                        st.write(f"**Publishing Date:** {blog_info.publishing_date}")
                        
                        if not blog_info.is_anonymous:
                            with st.spinner("Analyzing author reputation..."):
                                person_reputation = asyncio.run(
                                    analyze_person(f"{blog_info.author_name} {blog_info.author_affiliation} {blog_info.publisher_name}")
                                )
                                st.write("**Reputation:**")
                                st.info(person_reputation)
                    
                    with col2:
                        st.subheader("🏢 Publisher Information")
                        st.write(f"**Blog Name:** {blog_info.blog_name}")
                        st.write(f"**Publisher:** {blog_info.publisher_name}")
                        
                        with st.spinner("Analyzing publisher reputation..."):
                            publisher_reputation = asyncio.run(
                                analyze_publisher(blog_info.publisher_name)
                            )
                            st.write("**Reputation:**")
                            st.info(publisher_reputation)
                
                # Tab 2: Intent
                with tab2:
                    st.subheader("🎯 Intent Analysis")
                    st.markdown("Understanding the author's purpose, tone, and potential biases helps evaluate credibility.")
                    
                    with st.spinner("Analyzing intent..."):
                        intent_info = asyncio.run(analyze_intent(blog_text))
                        
                        # Primary Intent Assessment
                        st.markdown("### 📝 Writing Characteristics")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🎭 Tone**")
                            st.info(intent_info.tone)
                            st.caption("How the author approaches the subject (objective, emotional, promotional, etc.)")
                            
                            st.markdown("**✍️ Style**")
                            st.info(intent_info.style)
                            st.caption("The writing format and approach used")
                        
                        with col2:
                            st.markdown("**💭 Sentiment**")
                            st.info(intent_info.sentiment)
                            st.caption("The overall emotional tone of the content")
                            
                            st.markdown("**⚖️ Bias**")
                            st.info(intent_info.bias)
                            st.caption("Tendency toward or against specific groups or viewpoints")
                        
                        # Hate Speech / Offensive Content
                        st.markdown("### 🚨 Content Safety")
                        if intent_info.hate and intent_info.hate.lower() not in ["none", "none detected", "not present", "not detected"]:
                            st.error(f"**⚠️ Concerns Detected:** {intent_info.hate}")
                        else:
                            st.success("✅ No hate speech, vulgar, or offensive language detected")
                        
                        # Interpretation Guide
                        with st.expander("📖 How to Interpret Intent Analysis"):
                            st.markdown("""
                            **Tone**: Objective writing is more trustworthy for factual content. Opinion-driven or promotional tones suggest persuasion rather than information.
                            
                            **Style**: Academic and journalistic styles typically follow stricter standards. Marketing or conversational styles may prioritize engagement over accuracy.
                            
                            **Sentiment**: Extreme sentiment (very positive or negative) may indicate bias. Neutral sentiment suggests balanced reporting.
                            
                            **Bias**: All content has some perspective, but explicit bias toward/against groups raises credibility concerns. Look for balanced presentation of multiple viewpoints.
                            
                            **Content Safety**: Hateful, discriminatory, or offensive language indicates poor editorial standards and unreliable content.
                            """)
                
                # Tab 3: Accuracy
                with tab3:
                    st.subheader("✅ Accuracy Analysis")
                    st.markdown("Evaluating the reliability, verifiability, and quality of the content.")
                    
                    with st.spinner("Analyzing accuracy..."):
                        accuracy_info = asyncio.run(analyze_accuracy(blog_text))
                        
                        # Credibility Indicators
                        st.markdown("### 🔍 Credibility Indicators")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**📚 Sources Provided**")
                            if accuracy_info.has_sources:
                                st.success("✅ Yes")
                                st.caption("Content includes citations, references, or links to sources")
                            else:
                                st.error("❌ No")
                                st.caption("No clear sources or citations found")
                        
                        with col2:
                            st.markdown("**🔎 Verifiable Claims**")
                            if accuracy_info.verifiable:
                                st.success("✅ Yes")
                                st.caption("Claims can be checked against external sources")
                            else:
                                st.error("❌ No")
                                st.caption("Difficult to verify claims independently")
                        
                        with col3:
                            st.markdown("**✏️ Error-Free Writing**")
                            if accuracy_info.error_free:
                                st.success("✅ Yes")
                                st.caption("No obvious errors or contradictions detected")
                            else:
                                st.warning("⚠️ Issues Found")
                                st.caption("Contains errors, inconsistencies, or contradictions")
                        
                        # Facts vs Opinions Analysis
                        st.markdown("### 📊 Facts vs Opinions")
                        st.info(accuracy_info.facts_vs_opinions)
                        st.caption("How the author distinguishes factual claims from personal opinions")
                        
                        # Overall Credibility Score
                        st.markdown("### 🎯 Credibility Summary")
                        credibility_score = sum([
                            accuracy_info.has_sources,
                            accuracy_info.verifiable,
                            accuracy_info.error_free
                        ])
                        
                        if credibility_score == 3:
                            st.success("🌟 **High Credibility** - All accuracy indicators are positive")
                        elif credibility_score == 2:
                            st.info("⚖️ **Moderate Credibility** - Most accuracy indicators are positive")
                        elif credibility_score == 1:
                            st.warning("⚠️ **Low Credibility** - Few accuracy indicators are positive")
                        else:
                            st.error("🚫 **Very Low Credibility** - No accuracy indicators are positive")
                        
                        # Interpretation Guide
                        with st.expander("📖 How to Interpret Accuracy Analysis"):
                            st.markdown("""
                            **Sources Provided**: Credible content cites sources—academic papers, official documents, reputable publications, or expert quotes. Absence of sources is a red flag for factual claims.
                            
                            **Verifiable Claims**: Good content makes claims that can be independently verified through external trustworthy sources. Vague or unverifiable statements reduce credibility.
                            
                            **Error-Free Writing**: While minor typos are forgivable, factual errors, logical contradictions, or inconsistent information indicate poor editorial standards.
                            
                            **Facts vs Opinions**: Trustworthy content clearly distinguishes between objective facts and subjective opinions. Look for hedging language like "research suggests" for facts and clear opinion markers like "I believe" or "in my view."
                            
                            **Credibility Score**: This combines all accuracy indicators. High credibility doesn't guarantee truth, but suggests the content follows journalistic or academic standards.
                            """)
                
                # Tab 4: Currency
                with tab4:
                    st.subheader("📅 Currency Analysis")
                    st.markdown("Assessing whether the content is up-to-date and relevant for its topic.")
                    
                    with st.spinner("Analyzing currency..."):
                        currency_info = asyncio.run(analyze_currency(blog_text))
                        
                        # Timeline Information
                        st.markdown("### 🕒 Publication Timeline")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📅 Published Date**")
                            if currency_info.published_date and currency_info.published_date.lower() not in ["unknown", "not found", "not available"]:
                                st.info(currency_info.published_date)
                            else:
                                st.warning("Not found")
                            st.caption("When the content was originally published")
                        
                        with col2:
                            st.markdown("**🔄 Last Updated**")
                            if currency_info.last_updated and currency_info.last_updated.lower() not in ["unknown", "not found", "not available"]:
                                st.info(currency_info.last_updated)
                            else:
                                st.warning("Not found")
                            st.caption("When the content was most recently revised")
                        
                        # Timeliness Indicators
                        st.markdown("### ⏰ Timeliness Indicators")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**🔴 Requires Current Info**")
                            if currency_info.requires_current_info:
                                st.warning("⚠️ Yes")
                                st.caption("Topic needs up-to-date information (tech, health, news, regulations)")
                            else:
                                st.success("✅ No")
                                st.caption("Topic is evergreen or historical")
                        
                        with col2:
                            st.markdown("**🔧 Actively Maintained**")
                            if currency_info.is_maintained:
                                st.success("✅ Yes")
                                st.caption("Shows signs of ongoing updates and maintenance")
                            else:
                                st.error("❌ No")
                                st.caption("No evidence of recent maintenance")
                        
                        with col3:
                            st.markdown("**📚 Recent References**")
                            if currency_info.has_recent_references:
                                st.success("✅ Yes")
                                st.caption("Contains recent citations or sources")
                            else:
                                st.error("❌ No")
                                st.caption("References appear outdated or absent")
                        
                        # Currency Assessment
                        st.markdown("### 🎯 Currency Summary")
                        
                        # Calculate currency score based on context
                        if currency_info.requires_current_info:
                            # For topics requiring current info, maintenance and recent refs are critical
                            currency_concerns = []
                            if not currency_info.is_maintained:
                                currency_concerns.append("not actively maintained")
                            if not currency_info.has_recent_references:
                                currency_concerns.append("lacks recent references")
                            
                            if len(currency_concerns) == 0:
                                st.success("🌟 **Excellent Currency** - Content is well-maintained with recent information")
                            elif len(currency_concerns) == 1:
                                st.warning(f"⚠️ **Moderate Currency** - Content is {currency_concerns[0]}")
                            else:
                                st.error(f"🚫 **Poor Currency** - Content is {' and '.join(currency_concerns)}")
                                st.warning("⚠️ For time-sensitive topics, outdated information can be misleading or dangerous.")
                        else:
                            # For evergreen content, currency is less critical
                            st.info("ℹ️ **Evergreen Content** - Topic doesn't require frequent updates")
                            st.caption("Currency is less critical for historical, philosophical, or timeless topics.")
                        
                        # Interpretation Guide
                        with st.expander("📖 How to Interpret Currency Analysis"):
                            st.markdown("""
                            **Requires Current Info**: Some topics like technology, medical advice, current events, legal regulations, and scientific research require up-to-date information. Historical topics, classic literature analysis, or philosophical discussions are more evergreen.
                            
                            **Actively Maintained**: Look for "Updated on" notices, recent revision dates, or evidence the author revisits content. Well-maintained content suggests ongoing commitment to accuracy.
                            
                            **Recent References**: Citations and sources should be recent for time-sensitive topics. A 2020 article citing only 2010 sources about rapidly-evolving fields is a red flag.
                            
                            **Publication Dates**: Missing dates make it impossible to assess currency. Credible sources always include publication and update timestamps.
                            
                            **Context Matters**: A 5-year-old article about ancient history is fine; a 5-year-old article about COVID-19 treatments or AI technology is dangerously outdated.
                            
                            **Currency Risk**: For time-sensitive topics, outdated information can be misleading, ineffective, or harmful. Always verify if the content reflects current understanding.
                            """)
                

