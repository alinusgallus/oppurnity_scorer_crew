import streamlit as st
import os
from hiring_analytics_crew import HiringAnalyticsCrew

st.set_page_config(
    page_title="Company Hiring Analytics",
    page_icon="📊",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("Company Hiring Analytics 📊")
    
    # Add test mode toggle and info in sidebar
    with st.sidebar:
        test_mode = st.toggle("Test Mode (No API calls)", value=False)
        if test_mode:
            st.info("🧪 Running in test mode - using mock data")
            st.markdown("""
            ℹ️ **Test Mode Info**
            - No API credits used
            - Instant results
            - Standardized mock data
            - Great for UI testing
            """)
        
        # Add API usage info
        if not test_mode:
            st.markdown("### API Usage")
            st.markdown("- Each analysis uses approximately:")
            st.markdown("  - 4 agent tasks")
            st.markdown("  - ~2000-3000 tokens")
    
    # Company input with validation
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter Company Name", placeholder="e.g., Microsoft")
    with col2:
        analyze_button = st.button("Analyze", type="primary", disabled=not company_name)
    
    if analyze_button:
        try:
            # Initialize crew with test mode
            crew = HiringAnalyticsCrew(
                anthropic_api_key=st.secrets["ANTHROPIC_API_KEY"],
                serper_api_key=st.secrets["SERPER_API_KEY"],
                test_mode=test_mode
            )
            
            with st.spinner("🔍 " + ("Loading test data..." if test_mode else "Analyzing company data...")):
                results = crew.analyze_company(company_name)
                
                if results and 'tasks_output' in results:
                    # Create tabs for different sections
                    analysis_tab, market_tab = st.tabs(["Company Analysis", "Market Position"])
                    
                    # Company Analysis tab
                    with analysis_tab:
                        research_data = next((task for task in results['tasks_output'] 
                                           if task['task'] == 'Research'), None)
                        if research_data and research_data.get('raw'):
                            sections = research_data['raw'].split('\n')
                            current_section = None
                            
                            # Create columns for metrics
                            metrics_cols = st.columns(3)
                            col_idx = 0
                            
                            for section in sections:
                                if section.strip():
                                    if any(header in section for header in ['Metrics:', 'Indicators:']):
                                        current_section = section.strip()
                                        with metrics_cols[col_idx]:
                                            st.markdown(f"### {current_section}")
                                            col_idx = (col_idx + 1) % 3
                                    elif section.startswith('-'):
                                        with metrics_cols[col_idx - 1]:
                                            st.markdown(section)
                                    else:
                                        with metrics_cols[col_idx - 1]:
                                            st.markdown(f"• {section}")
                    
                    # Market Position tab
                    with market_tab:
                        market_data = next((task for task in results['tasks_output'] 
                                         if task['task'] == 'Market Analysis'), None)
                        if market_data and market_data.get('raw'):
                            sections = market_data['raw'].split('\n')
                            
                            # Create two columns for market data
                            market_col1, market_col2 = st.columns(2)
                            
                            with market_col1:
                                st.markdown("### Market Overview")
                                for section in sections:
                                    if section.strip():
                                        if 'Competitors:' in section or 'Market Share:' in section:
                                            st.markdown(f"**{section.strip()}**")
                                        elif section.startswith('-'):
                                            st.markdown(section)
                            
                            with market_col2:
                                st.markdown("### Industry Analysis")
                                for section in sections:
                                    if section.strip():
                                        if 'Industry Trends:' in section or 'Challenges:' in section:
                                            st.markdown(f"**{section.strip()}**")
                                        elif section.startswith('-'):
                                            st.markdown(section)
                    
                    # Hiring score (below tabs)
                    st.markdown("---")
                    score_col1, score_col2 = st.columns([1, 2])
                    with score_col1:
                        st.subheader("Hiring Potential Score")
                        hiring_potential = "High"
                        if research_data and research_data.get('raw'):
                            content = research_data['raw'].lower()
                            if 'hiring freeze' in content or 'layoff' in content:
                                hiring_potential = "Low"
                            elif 'moderate' in content or 'stable' in content:
                                hiring_potential = "Moderate"
                        
                        score_text = f"{hiring_potential} hiring potential"
                        if hiring_potential == "High":
                            st.success(score_text)
                        elif hiring_potential == "Moderate":
                            st.info(score_text)
                        else:
                            st.warning(score_text)
                    
                    with score_col2:
                        st.markdown("### Key Factors")
                        st.markdown("• " + ("Active hiring across multiple departments" if hiring_potential == "High" 
                                          else "Stable hiring with some growth" if hiring_potential == "Moderate"
                                          else "Limited hiring opportunities"))
                    
        except Exception as e:
            error_message = str(e)
            if "credit balance is too low" in error_message:
                st.error("⚠️ API credits have been depleted. Please check your Anthropic API account and add more credits to continue using the service.")
            elif "rate limit" in error_message.lower():
                st.error("⚠️ Too many requests. Please wait a few minutes and try again.")
            else:
                st.error(f"Error analyzing company: {error_message}")

if __name__ == "__main__":
    main()