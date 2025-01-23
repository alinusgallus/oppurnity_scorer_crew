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
    
    # Company input
    company_name = st.text_input("Enter Company Name", placeholder="e.g., Microsoft")
    
    if st.button("Analyze", type="primary"):
        if not company_name:
            st.error("Please enter a company name")
            return
            
        try:
            # Initialize crew
            crew = HiringAnalyticsCrew(
                anthropic_api_key=st.secrets["ANTHROPIC_API_KEY"],
                serper_api_key=st.secrets["SERPER_API_KEY"]
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
                        if research_data:
                            metrics = research_data['raw'].split('\n')
                            for metric in metrics:
                                if metric.strip():
                                    st.markdown(f"• {metric.strip()}")
                    
                    # Market analysis
                    with col2:
                        st.subheader("Market Position")
                        market_data = next((task for task in results['tasks_output'] 
                                         if task['task'] == 'Market Analysis'), None)
                        if market_data:
                            metrics = market_data['raw'].split('\n')
                            for metric in metrics:
                                if metric.strip():
                                    st.markdown(f"• {metric.strip()}")
                    
                    # Hiring score
                    st.subheader("Hiring Potential Score")
                    score_text = "High hiring potential" if "hiring" in results['tasks_output'][0]['raw'].lower() else "Moderate hiring potential"
                    st.info(score_text)
                    
        except Exception as e:
            st.error(f"Error analyzing company: {str(e)}")

if __name__ == "__main__":
    main()