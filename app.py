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
    
    # Sidebar configuration
    with st.sidebar:
        test_mode = st.toggle("Test Mode (No API calls)", value=False)
        if test_mode:
            st.info("🧪 Running in test mode - using mock data")
    
    # Company input with validation
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter Company Name", placeholder="e.g., Microsoft")
    with col2:
        analyze_button = st.button("Analyze", type="primary", disabled=not company_name)
    
    if analyze_button:
        try:
            crew = HiringAnalyticsCrew(
                anthropic_api_key=st.secrets["ANTHROPIC_API_KEY"],
                serper_api_key=st.secrets["SERPER_API_KEY"],
                test_mode=test_mode
            )
            
            with st.spinner("🔍 " + ("Loading test data..." if test_mode else "Analyzing company data...")):
                results = crew.analyze_company(company_name)
                
                if results and 'tasks_output' in results:
                    # Create three main tabs
                    market_tab, company_tab, hiring_tab = st.tabs([
                        "Market Overview", 
                        "Company Analysis", 
                        "Hiring Analysis"
                    ])
                    
                    # Market Overview Tab
                    with market_tab:
                        market_data = next((task for task in results['tasks_output'] 
                                         if task['task'] == 'Market Analysis'), None)
                        if market_data and market_data.get('raw'):
                            # Split into two columns
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("Market Position")
                                # Display competitors and market share
                                sections = market_data['raw'].split('\n')
                                for section in sections:
                                    if section.strip():
                                        if 'Competitors:' in section:
                                            st.markdown("#### Key Competitors")
                                        elif 'Market Share:' in section:
                                            st.markdown("#### Market Share")
                                        if section.startswith('-'):
                                            st.markdown(section)
                            
                            with col2:
                                st.subheader("Industry Insights")
                                # Display trends and challenges
                                for section in sections:
                                    if section.strip():
                                        if 'Industry Trends:' in section:
                                            st.markdown("#### Trends")
                                        elif 'Challenges:' in section:
                                            st.markdown("#### Challenges")
                                        if section.startswith('-'):
                                            st.markdown(section)
                    
                    # Company Analysis Tab
                    with company_tab:
                        research_data = next((task for task in results['tasks_output'] 
                                           if task['task'] == 'Research'), None)
                        if research_data and research_data.get('raw'):
                            sections = research_data['raw'].split('\n')
                            
                            # Create metrics cards for financial and growth data
                            st.subheader("Company Performance")
                            metrics_cols = st.columns(2)
                            
                            with metrics_cols[0]:
                                st.markdown("#### Financial Metrics")
                                for section in sections:
                                    if section.strip() and ('Revenue:' in section or 
                                                          'Profit Margins:' in section or 
                                                          'Cash Position:' in section):
                                        st.markdown(section)
                            
                            with metrics_cols[1]:
                                st.markdown("#### Growth Indicators")
                                for section in sections:
                                    if section.strip() and ('Employee Growth:' in section or 
                                                          'Locations:' in section or 
                                                          'Products:' in section):
                                        st.markdown(section)
                    
                    # Hiring Analysis Tab
                    with hiring_tab:
                        if research_data and research_data.get('raw'):
                            st.subheader("Hiring Overview")
                            
                            # Create columns for hiring metrics
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown("#### Current Hiring Status")
                                for section in sections:
                                    if section.strip() and ('Active Openings:' in section or 
                                                          'Key Departments:' in section or 
                                                          'Growth Areas:' in section):
                                        st.markdown(section)
                            
                            with col2:
                                st.markdown("#### Hiring Potential")
                                # Determine hiring potential
                                content = research_data['raw'].lower()
                                if 'hiring freeze' in content or 'layoff' in content:
                                    potential = "Low"
                                    color = "🔴"
                                elif 'moderate' in content or 'stable' in content:
                                    potential = "Moderate"
                                    color = "🟡"
                                else:
                                    potential = "High"
                                    color = "🟢"
                                
                                st.markdown(f"### {color} {potential}")
                                st.markdown("#### Key Factors")
                                factors = {
                                    "High": "Active hiring across departments with strong growth indicators",
                                    "Moderate": "Stable hiring with selective growth",
                                    "Low": "Limited hiring with potential challenges"
                                }
                                st.markdown(f"• {factors[potential]}")
                    
        except Exception as e:
            error_message = str(e)
            if "credit balance is too low" in error_message:
                st.error("⚠️ API credits depleted. Please check your Anthropic API account.")
            elif "rate limit" in error_message.lower():
                st.error("⚠️ Too many requests. Please wait a few minutes and try again.")
            else:
                st.error(f"Error analyzing company: {error_message}")

if __name__ == "__main__":
    main()