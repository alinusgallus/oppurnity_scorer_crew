import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class HiringAnalyticsCrew:
    def __init__(self, anthropic_api_key: str, serper_api_key: str, test_mode: bool = False):
        self.test_mode = test_mode
        if not test_mode:
            self.llm = LLM(api_key=anthropic_api_key, model="anthropic/claude-3-sonnet-20240229")
            self.tools = self._create_tools(serper_api_key)
            self.agents = self._create_agents()
        
    def _create_tools(self, serper_api_key: str) -> Dict[str, Any]:
        return {
            "search": SerperDevTool(serper_api_key=serper_api_key, retry_on_fail=True)
        }
        
    def _create_agents(self) -> List[Agent]:
        # Financial Health Tracker
        financial_agent = Agent(
            role="Financial Analyst",
            goal="Track company financial health and stability indicators",
            backstory="""Expert financial analyst specializing in company health assessment
            through public financial data and market indicators.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            verbose=True
        )
        
        # Job Posts Monitor
        jobs_agent = Agent(
            role="Hiring Trends Analyst",
            goal="Monitor and analyze company hiring patterns and job postings",
            backstory="""Recruitment analytics specialist focused on identifying hiring trends,
            growth areas, and organizational priorities through job posting analysis.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            verbose=True
        )
        
        # Growth Indicators Analyzer
        growth_agent = Agent(
            role="Growth Metrics Analyst",
            goal="Analyze company growth through employee trends and expansions",
            backstory="""Business intelligence expert specializing in company growth analysis
            through employee metrics, geographical expansion, and product development.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            verbose=True
        )
        
        # Updated Market Position Researcher
        market_agent = Agent(
            role="Market Intelligence Specialist",
            goal="Assess company's market position and competitive landscape",
            backstory="""Expert market researcher with deep experience in competitive analysis 
            and industry trends. Specializes in analyzing market positions, identifying key 
            competitors, and evaluating industry dynamics through public data sources.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            allow_delegation=True,  # Allow agent to delegate tasks if needed
            max_iterations=3,  # Limit iterations to prevent infinite loops
            verbose=True,
            max_rpm=10  # Rate limit for API calls
        )
        
        return [financial_agent, jobs_agent, growth_agent, market_agent]
    
    def create_tasks(self, company_name: str) -> List[Task]:
        """Create more concise tasks to reduce token usage"""
        financial_task = Task(
            description=f"""Research {company_name}'s financial metrics:
            - Revenue
            - Profit margins
            - Funding/cash position
            Format: Financial Metrics: revenue, margins, funding""",
            agent=self.agents[0],
            expected_output="Financial metrics analysis"
        )
        
        jobs_task = Task(
            description=f"""Analyze {company_name}'s hiring:
            - Current openings
            - Key departments
            - Growth areas
            Format: Hiring Metrics: openings, departments, growth""",
            agent=self.agents[1],
            expected_output="Hiring patterns analysis"
        )
        
        growth_task = Task(
            description=f"""Check {company_name}'s growth:
            - Employee growth
            - Locations
            - New products
            Format: Growth Indicators: employees, locations, products""",
            agent=self.agents[2],
            expected_output="Growth indicators analysis"
        )
        
        # Updated market analysis task
        market_task = Task(
            description=f"""Research and analyze {company_name}'s market position:
            1. Identify and analyze top 3-5 direct competitors
            2. Estimate market share and relative position
            3. List key industry trends affecting the company
            4. Highlight major market challenges and opportunities
            
            Format output EXACTLY as follows:
            Market Position:
            - Competitors: [List with market share if available]
            - Market Share: [Company's estimated share]
            - Industry Trends: [Key trends]
            - Challenges: [Main challenges]""",
            agent=self.agents[3],
            expected_output="Structured market analysis with competitors, share, trends, and challenges",
            context=[financial_task, jobs_task, growth_task]
        )
        
        return [financial_task, jobs_task, growth_task, market_task]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def analyze_company(self, company_name: str) -> Dict[str, Any]:
        """Run full company analysis with the AI crew."""
        if self.test_mode:
            return self._get_mock_results(company_name)
        
        try:
            crew = Crew(
                agents=self.agents,
                tasks=self.create_tasks(company_name),
                process=Process.hierarchical,
                verbose=True,
                manager_llm=self.llm
            )
            
            # Add delay between API calls to avoid rate limits
            time.sleep(2)
            result = crew.kickoff()
            return self._parse_results(result)
            
        except Exception as e:
            error_message = str(e)
            if "credit balance is too low" in error_message:
                raise Exception("API credits depleted. Please check your Anthropic API account.")
            elif "rate limit" in error_message.lower():
                time.sleep(5)
                raise  # Retry through decorator
            else:
                raise Exception(f"Error analyzing company: {error_message}")
    
    def _parse_results(self, crew_output: Any) -> Dict[str, Any]:
        """Parse and structure the crew's output for Streamlit compatibility."""
        try:
            research_data = []
            market_data = []
            
            # Handle different output formats
            if isinstance(crew_output, list):
                task_outputs = crew_output
            elif isinstance(crew_output, dict) and 'tasks_output' in crew_output:
                task_outputs = crew_output['tasks_output']
            else:
                task_outputs = [crew_output]
            
            for task_output in task_outputs:
                # Extract the output content
                if hasattr(task_output, 'output'):
                    content = task_output.output
                elif hasattr(task_output, 'raw'):
                    content = task_output.raw
                elif isinstance(task_output, dict):
                    content = task_output.get('output', task_output.get('raw', ''))
                else:
                    content = str(task_output)
                
                # Skip metadata and empty content
                if not content or any(skip in content.lower() for skip in ['pydantic', 'json_dict', 'token_usage']):
                    continue
                
                # Categorize the content
                if any(market_term in content for market_term in ['Market Position', 'Competitors', 'Market Share']):
                    market_data.append(content)
                elif any(metric in content for metric in ['Financial Metrics', 'Hiring Metrics', 'Growth Indicators']):
                    research_data.append(content)
            
            # Clean up the data
            def clean_text(text_list):
                cleaned = []
                for text in text_list:
                    # Remove metadata-like lines
                    lines = [line.strip() for line in text.split('\n') 
                            if line.strip() and not line.strip().startswith(('(', 'Task', 'pydantic'))]
                    cleaned.extend(lines)
                return '\n'.join(cleaned)
            
            return {
                'tasks_output': [
                    {
                        'task': 'Research',
                        'raw': clean_text(research_data)
                    },
                    {
                        'task': 'Market Analysis',
                        'raw': clean_text(market_data)
                    }
                ]
            }
        except Exception as e:
            raise Exception(f"Error parsing results: {str(e)}")

    def _get_mock_results(self, company_name: str) -> Dict[str, Any]:
        """Return mock data for testing."""
        return {
            'tasks_output': [
                {
                    'task': 'Research',
                    'raw': f"""Financial Metrics:
- Revenue: $500M annual (estimated)
- Profit Margins: 15-20%
- Recent Funding: Series C, $100M (2023)
- Cash Position: Strong, with significant reserves

Hiring Metrics:
- Active Openings: 45 positions
- Key Departments: Engineering, Sales, Operations
- Growth Areas: Data Science, Cloud Infrastructure
- Hiring Velocity: Steady increase

Growth Indicators:
- Employee Growth: 25% YoY
- Locations: 5 global offices
- Products: 3 new launches in 2023
- Expansion: APAC market entry planned"""
                },
                {
                    'task': 'Market Analysis',
                    'raw': f"""Market Position:
- Competitors: 
  - Major Player A (30% market share)
  - Challenger B (15% market share)
  - {company_name} (10% market share)

- Industry Trends:
  - Digital transformation acceleration
  - AI/ML integration
  - Sustainability focus

- Market Share: 10% in primary market
- Growth Rate: 15% annually

- Challenges:
  - Intense competition
  - Talent acquisition
  - Technology adaptation"""
                }
            ]
        }
