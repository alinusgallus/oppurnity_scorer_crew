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
    
    # Add test mode toggle in sidebar
    with st.sidebar:
        test_mode = st.toggle("Test Mode (No API calls)", value=False)
        if test_mode:
            st.info("🧪 Running in test mode - using mock data")
    
    # Company input
    company_name = st.text_input("Enter Company Name", placeholder="e.g., Microsoft")
    
    if st.button("Analyze", type="primary"):
        if not company_name:
            st.error("Please enter a company name")
            return
            
        try:
            # Initialize crew with test mode
            crew = HiringAnalyticsCrew(
                anthropic_api_key=st.secrets["ANTHROPIC_API_KEY"],
                serper_api_key=st.secrets["SERPER_API_KEY"],
                test_mode=test_mode
            )
            
            with st.spinner("Analyzing company data..."):
                results = crew.analyze_company(company_name)
                
                if results and 'tasks_output' in results:
                    col1, col2 = st.columns(2)
                    
                    # Research data
                    with col1:
                        st.subheader("Company Analysis")
                        research_data = next((task for task in results['tasks_output'] 
                                           if task['task'] == 'Research'), None)
                        if research_data and research_data.get('raw'):
                            sections = research_data['raw'].split('\n')
                            current_section = None
                            for section in sections:
                                if section.strip():
                                    if any(header in section for header in ['Metrics:', 'Indicators:']):
                                        current_section = section.strip()
                                        st.markdown(f"**{current_section}**")
                                    elif section.startswith('-'):
                                        st.markdown(section)
                                    else:
                                        st.markdown(f"• {section}")
                    
                    # Market analysis
                    with col2:
                        st.subheader("Market Position")
                        market_data = next((task for task in results['tasks_output'] 
                                         if task['task'] == 'Market Analysis'), None)
                        if market_data and market_data.get('raw'):
                            sections = market_data['raw'].split('\n')
                            current_section = None
                            for section in sections:
                                if section.strip():
                                    if 'Market Position:' in section:
                                        current_section = section.strip()
                                        st.markdown(f"**{current_section}**")
                                    elif section.startswith('-'):
                                        st.markdown(section)
                                    else:
                                        st.markdown(f"• {section}")
                    
                    # Hiring score
                    st.subheader("Hiring Potential Score")
                    # Analyze the content to determine hiring potential
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