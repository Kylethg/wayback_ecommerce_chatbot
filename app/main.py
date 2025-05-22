"""
Main Streamlit application for the Wayback Ecommerce Chatbot.
"""

import os
import sys
# Add the parent directory of the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import datetime
import time

# Try to import dotenv, but handle the case where it might not be available
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")
except Exception as e:
    print(f"Warning: Error loading .env file: {e}")
    print("Environment variables must be set manually.")

# Import components using relative imports
from .components.query_processor import QueryProcessor
from .components.wayback_client import WaybackClient
from .components.content_extractor import ContentExtractor
from .components.content_analyzer import ContentAnalyzer
from .components.response_generator import ResponseGenerator

# Set page config
st.set_page_config(
    page_title="Wayback Ecommerce Insights",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E88E5;
    font-weight: 700;
}
.sub-header {
    font-size: 1.5rem;
    color: #424242;
    font-weight: 500;
}
.insight-box {
    background-color: #1E3A8A;  /* Darker blue background */
    border-left: 5px solid #3B82F6;
    padding: 20px;
    border-radius: 5px;
    color: #FFFFFF;  /* White text color for better contrast */
}
.metadata {
    font-size: 0.8rem;
    color: #616161;
}
.highlight {
    background-color: #ffff99;
    padding: 2px 5px;
    border-radius: 3px;
}
/* Additional styles for better readability */
.insight-box h1, .insight-box h2, .insight-box h3, .insight-box h4, .insight-box h5, .insight-box h6 {
    color: #FFFFFF;
}
.insight-box ul, .insight-box ol {
    color: #FFFFFF;
    margin-left: 20px;
}
.insight-box p {
    color: #FFFFFF;
}
.insight-box li {
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Initialize components
query_processor = QueryProcessor()
wayback_client = WaybackClient()
content_extractor = ContentExtractor()
content_analyzer = ContentAnalyzer()
response_generator = ResponseGenerator()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # API key input (optional if not using environment variable)
    api_key = st.text_input("OpenAI API Key (optional)", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Advanced options
    st.markdown("### 🔧 Advanced Options")
    model_choice = st.selectbox(
        "OpenAI Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=0
    )
    
    max_retries = st.slider("Max API Retries", 1, 5, 3)
    
    # Query history
    st.markdown("### 📜 Recent Queries")
    
    # Display history items with clickable links
    for i, (query, date, domain) in enumerate(st.session_state.history):
        if st.button(f"{domain} - {date.strftime('%b %d, %Y')}", key=f"history_{i}"):
            # Restore this query
            st.session_state.query = query
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

# Main content
st.markdown('<p class="main-header">Wayback Machine Ecommerce Insights</p>', unsafe_allow_html=True)
st.markdown("""
Ask questions about what competitors were promoting in the past.
The system will retrieve historical snapshots from the Wayback Machine and analyze them.
""")

# Initialize session state for query
if "query" not in st.session_state:
    st.session_state.query = ""

# Query input with examples
query = st.text_input(
    "Ask about a competitor's past promotions:",
    value=st.session_state.query,
    placeholder="What was asos.com promoting this time last year?"
)

# Example queries
example_col1, example_col2, example_col3 = st.columns(3)
with example_col1:
    if st.button("What was lookfantastic.com promoting last Black Friday?"):
        st.session_state.query = "What was lookfantastic.com promoting last Black Friday?"
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
with example_col2:
    if st.button("How did sephora.com handle Mother's Day last year?"):
        st.session_state.query = "How did sephora.com handle Mother's Day last year?"
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
with example_col3:
    if st.button("What shipping offers did asos.com have 6 months ago?"):
        st.session_state.query = "What shipping offers did asos.com have 6 months ago?"
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

# Submit button
if st.button("🔍 Get Insights", type="primary") and query:
    # Process query - no custom date needed as we're using LLM to infer the date
    query_info = query_processor.process_query(query)
    
    if not query_info["domain"]:
        st.error("Please include a website domain in your query (e.g., asos.com)")
    else:
        # Add to history
        if len(st.session_state.history) < 10:  # Limit history to 10 items
            history_item = (query, query_info["target_date"], query_info["domain"])
            if history_item not in st.session_state.history:
                st.session_state.history.insert(0, history_item)  # Add to beginning
        
        # Display the inferred date
        st.info(f"Analyzing {query_info['domain']} from {query_info['target_date'].strftime('%B %d, %Y')}")
        
        # Process query with a nice loading animation
        with st.spinner("🔄 Searching the Wayback Machine..."):
            # Step 1: Find snapshot
            timestamp, original_url, found_date = wayback_client.find_snapshot_for_date(
                query_info["domain"], 
                query_info["target_date"]
            )
            
            if not timestamp:
                st.error(f"No snapshot found for {query_info['domain']} near {query_info['target_date'].strftime('%B %d, %Y')}")
            else:
                st.success(f"Found snapshot from {found_date.strftime('%B %d, %Y')}")
                
                # Step 2: Get HTML content
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                html_content = wayback_client.get_snapshot_content(timestamp, original_url)
                
                if not html_content:
                    st.error(f"Found a snapshot, but couldn't retrieve the content")
                else:
                    st.success("Retrieved webpage content")
                    
                    # Step 3: Extract content
                    with st.spinner("🔍 Extracting relevant content..."):
                        extracted_content = content_extractor.extract_content(html_content, query_info["domain"])
                        formatted_content = content_extractor.format_extracted_content(extracted_content)
                    
                    # Step 4: Analyze with AI
                    with st.spinner("🧠 Analyzing with AI..."):
                        insights = content_analyzer.analyze_content(
                            query_info["domain"],
                            found_date,
                            formatted_content,
                            query
                        )
                    
                    # Store wayback URL
                    wayback_url = wayback_client.get_wayback_url(timestamp, original_url)
                    
                    # Generate response
                    response = response_generator.generate_response(
                        query_info["domain"],
                        found_date,
                        insights,
                        wayback_url,
                        query
                    )
                    
                    # Display results in a nice format
                    st.markdown('<p class="sub-header">📊 Insights</p>', unsafe_allow_html=True)
                    
                    # Create tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Analysis", "Snapshot", "Raw Data"])
                    
                    with tab1:
                        st.markdown(f'<div class="insight-box">{insights}</div>', unsafe_allow_html=True)
                        
                        # Add metadata about the analysis
                        st.markdown(f"""
                        <p class="metadata">
                        Analysis generated on {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')} | 
                        Snapshot date: {found_date.strftime('%B %d, %Y')} |
                        Model: {model_choice}
                        </p>
                        """, unsafe_allow_html=True)
                    
                    with tab2:
                        # Display a link to the Wayback Machine snapshot
                        st.markdown(f"### Wayback Machine Snapshot")
                        st.markdown(f"[View original snapshot]({wayback_url})")
                        
                        # Display iframe of the snapshot
                        st.components.v1.iframe(wayback_url, height=600, scrolling=True)
                    
                    with tab3:
                        # Display the raw extracted data
                        st.markdown("### Raw Extracted Content")
                        st.code(formatted_content, language="text")

# Footer
st.markdown("---")
st.markdown("""
<p class="metadata">
Powered by Wayback Machine and OpenAI | Data retrieved from web.archive.org
</p>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    # This will only be executed when the script is run directly, not when imported
    pass