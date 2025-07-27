import gradio as gr
from fastapi import FastAPI
from src.company_mca.crew import CompanyMcaCrew

app = FastAPI(
    title="Company Name MCA API",
    description="An API for checking company name availability using CrewAI.",
    version="1.0.0"
)

def run_crew_analysis(company_name, user_preference):
    if not company_name or not user_preference:
        return "Error: Company name and user preference cannot be empty."
    
    inputs = {
        'company_name': company_name,
        'user_preference': user_preference
    }
    result = CompanyMcaCrew().crew().kickoff(inputs=inputs)
    return result

gradio_interface = gr.Interface(
    fn=run_crew_analysis,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter Company Name here...", label="Company Name"),
        gr.Textbox(lines=5, placeholder="Enter your preferences for the name (e.g., industry, style, keywords)...", label="User Preference")
    ],
    outputs=gr.Markdown(label="Analysis Result"),
    title="Company Name MCA Check",
    description="Enter a company name and your preferences to check its availability and get suggestions using AI agents."
)

app = gr.mount_gradio_app(app, gradio_interface, path="/")