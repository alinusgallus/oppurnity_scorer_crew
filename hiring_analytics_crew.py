import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

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
        financial_task = Task(
            description=f"""Analyze {company_name}'s financial health:
            1. Find latest quarterly revenue and profits
            2. Calculate burn rate if available
            3. Identify recent funding events
            4. Assess cash reserves
            
            Format output as:
            Financial Metrics:
            - Revenue: [Latest quarterly]
            - Profit Margins: [%]
            - Burn Rate: [If applicable]
            - Recent Funding: [Date, Amount]
            - Cash Position: [Latest figure]""",
            agent=self.agents[0],
            expected_output="A structured analysis of the company's financial metrics including revenue, profits, burn rate, funding, and cash position."
        )
        
        jobs_task = Task(
            description=f"""Analyze {company_name}'s hiring patterns:
            1. Count current job openings
            2. Identify most frequent roles
            3. Track department growth
            4. Note any hiring freezes/slowdowns
            
            Format output as:
            Hiring Metrics:
            - Active Openings: [Number]
            - Key Departments: [List]
            - Growth Areas: [Departments]
            - Hiring Velocity: [Trend]""",
            agent=self.agents[1],
            expected_output="A detailed analysis of the company's hiring patterns including job openings, key departments, and hiring trends."
        )
        
        growth_task = Task(
            description=f"""Analyze {company_name}'s growth indicators:
            1. Track LinkedIn employee growth
            2. Monitor office locations
            3. Identify new products/services
            4. Note expansion plans
            
            Format output as:
            Growth Indicators:
            - Employee Growth: [Rate]
            - Locations: [Changes]
            - Products: [New launches]
            - Expansion: [Plans]""",
            agent=self.agents[2],
            expected_output="A comprehensive analysis of company growth indicators including employee growth, locations, products, and expansion plans."
        )
        
        market_task = Task(
            description=f"""Analyze {company_name}'s market position:
            1. Compare with competitors
            2. Assess market share
            3. Track industry trends
            4. Identify market challenges
            
            Format output as:
            Market Position:
            - Competitors: [Key rivals]
            - Market Share: [Estimate]
            - Industry Trends: [Key movements]
            - Challenges: [Main obstacles]""",
            agent=self.agents[3],
            expected_output="A detailed analysis of the company's market position including competitors, market share, trends, and challenges.",
            context=[financial_task, jobs_task, growth_task]
        )
        
        return [financial_task, jobs_task, growth_task, market_task]
    
    def analyze_company(self, company_name: str) -> Dict[str, Any]:
        """Run full company analysis with the AI crew."""
        try:
            crew = Crew(
                agents=self.agents,
                tasks=self.create_tasks(company_name),
                process=Process.hierarchical,
                verbose=True
            )
            
            result = crew.kickoff()
            return self._parse_results(result)
            
        except Exception as e:
            raise Exception(f"Error analyzing company: {str(e)}")
    
    def _parse_results(self, crew_output: Any) -> Dict[str, Any]:
        """Parse and structure the crew's output for Streamlit compatibility."""
        try:
            if hasattr(crew_output, 'model_dump'):
                return crew_output.model_dump()
            return {
                'tasks_output': [
                    {
                        'task': 'Research',
                        'raw': crew_output.get('Financial Metrics', '') + '\n' + 
                              crew_output.get('Hiring Metrics', '') + '\n' +
                              crew_output.get('Growth Indicators', '')
                    },
                    {
                        'task': 'Market Analysis',
                        'raw': crew_output.get('Market Position', '')
                    }
                ]
            }
        except Exception as e:
            raise Exception(f"Error parsing results: {str(e)}")
