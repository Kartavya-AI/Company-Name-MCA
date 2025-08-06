import os
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from src.company_mca.tools.custom_tool import mca_name_checker
import yaml
from langchain_openai import ChatOpenAI

@CrewBase
class CompanyMcaCrew():
    def __init__(self):
        base_path = os.path.dirname(__file__)
        self.agents_config = self._load_config(os.path.join(base_path, 'config/agents.yaml'))
        self.tasks_config = self._load_config(os.path.join(base_path, 'config/tasks.yaml'))
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0,
            openai_api_key=openai_api_key
        )
    
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
    def research_original_name_task(self) -> Task:
        config = self.tasks_config['research_original_name']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_researcher()
        )
    
    @task
    def generate_alternative_names_task(self) -> Task:
        config = self.tasks_config['generate_alternative_names']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_generator(),
            context=[self.research_original_name_task()]
        )
    
    @task
    def validate_name_availability_task(self) -> Task:
        config = self.tasks_config['validate_name_availability']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=self.name_validator(),
            context=[self.research_original_name_task(), self.generate_alternative_names_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.name_researcher(), self.name_generator(), self.name_validator()],
            tasks=[self.research_original_name_task(), self.generate_alternative_names_task(), self.validate_name_availability_task()],
            process=Process.sequential,
            verbose=True
        )
    
    def run_crew(self, company_name: str, user_preference: str = "") -> str:
        inputs = {
            "original_name": company_name,
            "company_name": company_name,
            "user_preference": user_preference or "Professional and brandable"
        }
        result = self.crew().kickoff(inputs=inputs)
        return str(result)