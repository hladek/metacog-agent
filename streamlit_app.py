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
                # Create tabs for different sections
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "📋 Metadata", 
                    "👤 Author & Publisher", 
                    "🎯 Intent", 
                    "✅ Accuracy", 
                    "📅 Currency",
                    "📄 Content Preview"
                ])
                
                # Tab 1: Metadata
                with tab1:
                    st.subheader("Blog Metadata")
                    if metadata:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📰 Article Information**")
                            if metadata.get('title'):
                                st.write(f"**Title:** {metadata['title']}")
                            if metadata.get('author'):
                                st.write(f"**Author:** {metadata['author']}")
                            if metadata.get('date'):
                                st.write(f"**Published:** {metadata['date']}")
                            if metadata.get('description'):
                                st.write(f"**Description:** {metadata['description']}")
                            if metadata.get('pagetype'):
                                st.write(f"**Page Type:** {metadata['pagetype']}")
                        
                        with col2:
                            st.write("**🌐 Source Information**")
                            if metadata.get('url'):
                                st.write(f"**URL:** {metadata['url']}")
                            if metadata.get('hostname'):
                                st.write(f"**Hostname:** {metadata['hostname']}")
                            if metadata.get('sitename'):
                                st.write(f"**Site Name:** {metadata['sitename']}")
                            if metadata.get('image'):
                                st.write(f"**Featured Image:**")
                                st.image(metadata['image'], use_container_width=True)
                            if metadata.get('filedate'):
                                st.write(f"**Retrieved:** {metadata['filedate']}")
                        
                        if metadata.get('categories') or metadata.get('tags'):
                            st.write("**🏷️ Categories & Tags**")
                            if metadata.get('categories'):
                                st.write(f"**Categories:** {', '.join(metadata['categories']) if metadata['categories'] else 'None'}")
                            if metadata.get('tags'):
                                st.write(f"**Tags:** {', '.join(metadata['tags']) if metadata['tags'] else 'None'}")
                        
                        with st.expander("View Raw Metadata"):
                            st.json(metadata)
                    else:
                        st.info("No metadata available")
                
                # Extract blog info
                blog_info = asyncio.run(
                    extract_blog_info_with_llm("URL: " + str(metadata) + "\n\n" + (blog_text or ""))
                )
                
                # Tab 2: Author & Publisher
                with tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("👤 Author Information")
                        st.write(f"**Name:** {blog_info.author_name}")
                        st.write(f"**Anonymous:** {blog_info.is_anonymous}")
                        st.write(f"**Publishing Date:** {blog_info.publishing_date}")
                        
                        if not blog_info.is_anonymous:
                            with st.spinner("Analyzing author reputation..."):
                                person_reputation = asyncio.run(
                                    analyze_person(blog_info.author_name + " " + blog_info.publisher_name)
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
                
                # Tab 3: Intent
                with tab3:
                    st.subheader("🎯 Intent Analysis")
                    with st.spinner("Analyzing intent..."):
                        intent_info = asyncio.run(analyze_intent(blog_text))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Tone", intent_info.tone)
                            st.metric("Style", intent_info.style)
                        with col2:
                            st.metric("Bias", intent_info.bias)
                            st.metric("Sentiment", intent_info.sentiment)
                        
                        if intent_info.hate and intent_info.hate.lower() != "none":
                            st.warning(f"⚠️ **Hate Speech Detection:** {intent_info.hate}")
                        else:
                            st.success("✅ No hate speech detected")
                
                # Tab 4: Accuracy
                with tab4:
                    st.subheader("✅ Accuracy Analysis")
                    with st.spinner("Analyzing accuracy..."):
                        accuracy_info = asyncio.run(analyze_accuracy(blog_text))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Has Sources", "✅" if accuracy_info.has_sources else "❌")
                            st.metric("Verifiable", "✅" if accuracy_info.verifiable else "❌")
                        with col2:
                            st.metric("Error Free", "✅" if accuracy_info.error_free else "❌")
                        
                        st.write("**Facts vs Opinions:**")
                        st.info(accuracy_info.facts_vs_opinions)
                
                # Tab 5: Currency
                with tab5:
                    st.subheader("📅 Currency Analysis")
                    with st.spinner("Analyzing currency..."):
                        currency_info = asyncio.run(analyze_currency(blog_text))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Requires Current Info", "✅" if currency_info.requires_current_info else "❌")
                            st.metric("Is Maintained", "✅" if currency_info.is_maintained else "❌")
                            st.metric("Has Recent References", "✅" if currency_info.has_recent_references else "❌")
                        with col2:
                            st.write(f"**Published Date:** {currency_info.published_date}")
                            st.write(f"**Last Updated:** {currency_info.last_updated}")
                
                # Tab 6: Content Preview
                with tab6:
                    st.subheader("📄 Content Preview")
                    st.text_area("Blog Content (first 2000 characters)", 
                                blog_text[:2000] if blog_text else "No content available", 
                                height=400)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This tool analyzes blog posts using the CRAAP framework:\n\n"
    "- **C**urrency: Timeliness of information\n\n"
    "- **R**elevance: Importance to your needs\n\n"
    "- **A**uthority: Source credibility\n\n"
    "- **A**ccuracy: Reliability and correctness\n\n"
    "- **P**urpose: Reason the information exists"
)
