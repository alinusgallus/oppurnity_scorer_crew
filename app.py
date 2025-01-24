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

def format_section(section_text: str) -> str:
    """Helper function to format section text with proper indentation and bullets"""
    if section_text.startswith('-'):
        return f"• {section_text[1:].strip()}"
    return section_text.strip()

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
                            col1, col2 = st.columns(2)
                            
                            sections = market_data['raw'].split('\n')
                            market_sections = {'competitors': [], 'share': [], 'trends': [], 'challenges': []}
                            current_section = None
                            
                            # Categorize market data
                            for section in sections:
                                if not section.strip():
                                    continue
                                if 'Competitors:' in section:
                                    current_section = 'competitors'
                                elif 'Market Share:' in section:
                                    current_section = 'share'
                                elif 'Industry Trends:' in section:
                                    current_section = 'trends'
                                elif 'Challenges:' in section:
                                    current_section = 'challenges'
                                elif current_section and section.strip():
                                    market_sections[current_section].append(format_section(section))
                            
                            # Display market data
                            with col1:
                                st.markdown("### 🎯 Market Position")
                                if market_sections['competitors']:
                                    st.markdown("#### Key Competitors")
                                    for comp in market_sections['competitors']:
                                        st.markdown(comp)
                                if market_sections['share']:
                                    st.markdown("#### 📊 Market Share")
                                    for share in market_sections['share']:
                                        st.markdown(share)
                            
                            with col2:
                                st.markdown("### 📈 Industry Insights")
                                if market_sections['trends']:
                                    st.markdown("#### Key Trends")
                                    for trend in market_sections['trends']:
                                        st.markdown(trend)
                                if market_sections['challenges']:
                                    st.markdown("#### 🚧 Challenges")
                                    for challenge in market_sections['challenges']:
                                        st.markdown(challenge)
                    
                    # Company Analysis Tab
                    with company_tab:
                        research_data = next((task for task in results['tasks_output'] 
                                           if task['task'] == 'Research'), None)
                        if research_data and research_data.get('raw'):
                            sections = research_data['raw'].split('\n')
                            company_sections = {
                                'financial': [], 'growth': [], 'hiring': []
                            }
                            current_section = None
                            
                            # Categorize company data
                            for section in sections:
                                if not section.strip():
                                    continue
                                if 'Financial Metrics:' in section:
                                    current_section = 'financial'
                                elif 'Growth Indicators:' in section:
                                    current_section = 'growth'
                                elif 'Hiring Metrics:' in section:
                                    current_section = 'hiring'
                                elif current_section and section.strip():
                                    company_sections[current_section].append(format_section(section))
                            
                            # Display company metrics
                            st.markdown("### 📊 Company Performance")
                            metrics_cols = st.columns(2)
                            
                            with metrics_cols[0]:
                                st.markdown("#### 💰 Financial Overview")
                                for metric in company_sections['financial']:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="metric-value">{metric}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with metrics_cols[1]:
                                st.markdown("#### 📈 Growth Metrics")
                                for metric in company_sections['growth']:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="metric-value">{metric}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
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