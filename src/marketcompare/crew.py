from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import json
from pydantic import BaseModel, Field

# Import the enhanced models for task outputs
from .enhanced_models import (
    InitTaskOutput,
    InternalDataOutput,
    MarketResearchOutput,
    CompetitorAnalysisOutput,
    DataSynthesisOutput,
    RecommendationOutput,
    FinalReportOutput,
    MarkdownReportOutput
)

# Import tools
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    SerperDevTool,
    WebsiteSearchTool
)

# Initialize tools
docs_tool = DirectoryReadTool(directory='./company_docs')
file_tool = FileReadTool()
search_tool = SerperDevTool(api_key=os.environ.get("SERPER_API_KEY"))
web_rag_tool = WebsiteSearchTool()


@CrewBase
class Marketcompare():
    """Market comparison analysis crew for comprehensive competitive intelligence"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Manager agent that orchestrates the entire process
    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'], # type: ignore[index]
            verbose=True
        )

    # Internal Data Agent for company document analysis
    @agent
    def internal_data_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['internal_data_agent'], # type: ignore[index]
            verbose=True
        )

    # Market Research Agent for external market trends and data
    @agent
    def market_research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['market_research_agent'], # type: ignore[index]
            tools=[search_tool, web_rag_tool],
            verbose=True
        )

    # Competitor Agent for analyzing competitors
    @agent
    def competitor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['competitor_agent'], # type: ignore[index]
            tools=[search_tool, web_rag_tool],
            verbose=True
        )

    # Data Synthesizer for combining all research data
    @agent
    def data_synthesizer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_synthesizer'], # type: ignore[index]
            verbose=True
        )

    # Recommendation Agent for generating strategic recommendations
    @agent
    def recommendation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['recommendation_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def markdown_report_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['markdown_report_agent'],  # type: ignore[index]
            verbose=True
        )

    # Initial task for the Manager to set up the analysis
    @task
    def init_task(self) -> Task:
        return Task(
            config=self.tasks_config['init_task'], # type: ignore[index]
            output_pydantic=InitTaskOutput
        )

    # Task for Internal Data Agent to analyze company documents
    @task
    def internal_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['internal_data_task'], # type: ignore[index]
            context=[self.init_task()],
            output_pydantic=InternalDataOutput
        )

    # Task for Market Research Agent to gather market trends and data
    @task
    def market_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_research_task'], # type: ignore[index]
            context=[self.init_task()],
            output_pydantic=MarketResearchOutput
        )

    # Task for Competitor Agent to analyze competitors
    @task
    def competitor_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['competitor_analysis_task'], # type: ignore[index]
            context=[self.init_task()],
            output_pydantic=CompetitorAnalysisOutput
        )

    # Task for Data Synthesizer to combine all research data
    @task
    def data_synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_synthesis_task'], # type: ignore[index]
            context=[self.internal_data_task(), self.market_research_task(), self.competitor_analysis_task()],
            output_pydantic=DataSynthesisOutput
        )

    # Task for Recommendation Agent to generate recommendations
    @task
    def recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['recommendation_task'], # type: ignore[index]
            context=[self.data_synthesis_task()],
            output_pydantic=RecommendationOutput
        )

    # Final task for Manager to assemble the complete report
    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_report_task'], # type: ignore[index]
            context=[self.data_synthesis_task(), self.recommendation_task()],
            output_file='market_comparison_report.json',
            output_pydantic=FinalReportOutput
        )

    # @task
    # def markdown_report_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['markdown_report_task'], # type: ignore[index]
    #         context=[self.final_report_task()],
    #         output_file='market_comparison_report.html',
    #         output_pydantic=MarkdownReportOutput
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the MarketCompare crew with hierarchical process"""

        # Load environment variables if using dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        # Configure LLM
        openai_llm = LLM(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm=openai_llm,
            verbose=True,
        )

    def before_kickoff(self, inputs):
        """Prepare environment before crew execution"""
        global docs_tool, file_tool

        # Initialize using directory path string if provided
        if 'company_docs_dir' in inputs and inputs['company_docs_dir']:
            try:
                directory_path = str(inputs['company_docs_dir'])
                docs_tool = DirectoryReadTool(directory=directory_path)
                print(f"DirectoryReadTool initialized with: {directory_path}")
            except Exception as e:
                print(f"Error initializing DirectoryReadTool: {e}")
                raise

        # Validate user preferences file exists
        if 'user_preferences_file' in inputs and inputs['user_preferences_file']:
            user_prefs_file = str(inputs['user_preferences_file'])
            if not os.path.exists(user_prefs_file):
                print(f"Warning: User preferences file not found at {user_prefs_file}")

        return inputs

    def after_kickoff(self, result):
        """Process results after crew execution"""
        # Validate final report format
        if isinstance(result, dict) and 'market_comparison_report.json' in result:
            report_path = result['market_comparison_report.json']
            try:
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                # Validate against FinalReportOutput model
                FinalReportOutput(**report_data)
                print("Final report validation successful!")
            except Exception as e:
                print(f"Error validating final report: {e}")

        return result
