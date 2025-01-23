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
    def __init__(self, anthropic_api_key: str, serper_api_key: str):
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
        
        # Market Position Researcher
        market_agent = Agent(
            role="Market Intelligence Specialist",
            goal="Assess company's market position and competitive landscape",
            backstory="""Market research expert focused on competitive analysis,
            industry trends, and market positioning strategies.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            verbose=True
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
        
        market_task = Task(
            description=f"""Assess {company_name}'s market:
            - Competitors
            - Market share
            - Industry trends
            Format: Market Position: competitors, share, trends""",
            agent=self.agents[3],
            expected_output="Market position analysis",
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
            if "rate_limit" in str(e).lower():
                # Wait longer if we hit rate limits
                time.sleep(5)
                raise  # Retry through decorator
            raise Exception(f"Error analyzing company: {str(e)}")
    
    def _parse_results(self, crew_output: Any) -> Dict[str, Any]:
        """Parse and structure the crew's output for Streamlit compatibility."""
        try:
            research_data = []
            market_data = []
            
            if isinstance(crew_output, dict) and 'tasks_output' in crew_output:
                task_outputs = crew_output['tasks_output']
            else:
                task_outputs = crew_output
            
            for task_output in task_outputs:
                # Extract the raw content from the task output
                if hasattr(task_output, 'raw'):
                    content = task_output.raw
                elif isinstance(task_output, dict):
                    content = task_output.get('raw', '')
                else:
                    content = str(task_output)
                
                # Skip empty or irrelevant content
                if not content or content.startswith(('(', 'Task')):
                    continue
                
                # Categorize the content
                if 'Market Position' in content:
                    market_data.append(content)
                else:
                    if content.startswith(('Financial Metrics', 'Hiring Metrics', 'Growth Indicators')):
                        research_data.append(content)
            
            # Clean up the data by removing empty lines and extra whitespace
            research_text = '\n'.join(line.strip() for line in research_data if line.strip())
            market_text = '\n'.join(line.strip() for line in market_data if line.strip())
            
            return {
                'tasks_output': [
                    {
                        'task': 'Research',
                        'raw': research_text
                    },
                    {
                        'task': 'Market Analysis',
                        'raw': market_text
                    }
                ]
            }
        except Exception as e:
            raise Exception(f"Error parsing results: {str(e)}")
