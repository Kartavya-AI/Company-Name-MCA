import os
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from src.company_mca.tools.custom_tool import mca_name_checker
import yaml
from langchain_openai import ChatOpenAI

@CrewBase
class CompanyMcaCrew():
    def __init__(self):
        self.agents_config = self._load_config('config/agents.yaml')
        self.tasks_config = self._load_config('config/tasks.yaml')
        self.llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)
    
    def _load_config(self, file_path: str) -> dict:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    
    @agent
    def name_researcher(self) -> Agent:
        config = self.agents_config['name_researcher']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config['verbose'],
            allow_delegation=config['allow_delegation'],
            max_iter=config['max_iter'],
            tools=[mca_name_checker],
            llm=self.llm
        )
    
    @agent
    def name_generator(self) -> Agent:
        config = self.agents_config['name_generator']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config['verbose'],
            allow_delegation=config['allow_delegation'],
            max_iter=config['max_iter'],
            tools=[mca_name_checker],
            llm=self.llm
        )
    
    @agent
    def name_validator(self) -> Agent:
        config = self.agents_config['name_validator']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config['verbose'],
            allow_delegation=config['allow_delegation'],
            max_iter=config['max_iter'],
            tools=[mca_name_checker],
            llm=self.llm
        )
    
    @task
    def research_original_name(self) -> Task:
        config = self.tasks_config['research_original_name']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_researcher()
        )
    
    @task
    def generate_alternative_names(self) -> Task:
        config = self.tasks_config['generate_alternative_names']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_generator(),
            context=[self.research_original_name()]
        )
    
    @task
    def validate_name_availability(self) -> Task:
        config = self.tasks_config['validate_name_availability']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_validator(),
            context=[self.research_original_name(), self.generate_alternative_names()]
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
    
    def run_crew(self, original_name: str) -> str:
        result = self.crew().kickoff(inputs={"original_name": original_name})
        return str(result)