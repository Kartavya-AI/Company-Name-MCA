# MCA Company Name Checker 🏢
An AI-powered company name availability checker that validates names against the Indian Ministry of Corporate Affairs (MCA) database using the Finanvo API and CrewAI framework.

## Features
- **Real-time MCA Database Check**: Validates company names against live MCA records
- **AI-Powered Analysis**: Uses CrewAI agents for intelligent name research and validation
- **Batch Processing**: Check multiple names simultaneously with progress tracking
- **Smart Alternatives**: Generates 20+ compliant alternative names automatically
- **Compliance Scoring**: Assigns scores (0-100) based on MCA naming conventions
- **Interactive Dashboard**: Streamlit UI with charts and analytics
- **Export Functionality**: Download results as CSV or JSON
- **Search History**: Track and review previous searches

## Architecture

### Core Components
1. **Streamlit App** (`app.py`): Web interface with interactive dashboard
2. **FastAPI Service** (`api.py`): RESTful API with Gradio interface
3. **CrewAI Framework** (`crew.py`): Multi-agent system for name processing
4. **MCA Tool** (`custom_tool.py`): Finanvo API integration and validation logic
5. **Main Script** (`main.py`): Command-line interface

### Agent System
- **Name Researcher**: Analyzes original name availability
- **Name Generator**: Creates intelligent alternatives
- **Name Validator**: Ensures compliance with MCA guidelines

## Installation

### Prerequisites
- Python 3.9+
- Docker (for containerized deployment)
- Google Cloud CLI (for GCP deployment)

### Local Setup

```bash
# Clone repository
git clone https://github.com/Kartavya-AI/Company-Name-MCA.git
cd Company-Name-MCA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration files
# Create config/agents.yaml and config/tasks.yaml
```

### Required Dependencies

```
streamlit
crewai
crewai[tools]
fastapi
gunicorn
uvicorn
gradio
python-dotenv
pandas
plotly
requests
pysqlite3
fuzzywuzzy
pyyaml
```

## Docker Deployment

### Building the Docker Image

The project includes a production-ready Dockerfile optimized for containerized deployment:

```bash
# Build the Docker image
docker build -t mca-name-checker .

# Run locally with Docker
docker run -p 8080:8080 mca-name-checker
```

### Docker Configuration

The Dockerfile includes:
- Python 3.11 slim base image
- Optimized pip installation with caching
- Gunicorn with Uvicorn workers for production
- Proper environment variables for Python optimization
- Exposed port 8080 for cloud deployment

### Environment Variables

Create a `.env` file for local development:
```bash
# API Configuration
FINANVO_API_KEY=your_api_key
FINANVO_SECRET_KEY=your_secret_key

# Application Settings
PORT=8080
WORKERS=2
```

## Google Cloud Platform Deployment

### Prerequisites Setup

```bash
# Authenticate with Google Cloud
gcloud auth login

# List available projects
gcloud projects list

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com
```

### Artifact Registry Setup

```bash
# Set deployment variables
$REPO_NAME = "mca-name-checker"
$REGION = "us-central1"  # or your preferred region

# Create Artifact Registry repository
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="MCA Company Name Checker Docker Repository"
```

### Build and Push Image

```bash
# Get project ID and create image tag
$PROJECT_ID = $(gcloud config get-value project)
$IMAGE_TAG = "$($REGION)-docker.pkg.dev/$($PROJECT_ID)/$($REPO_NAME)/mca-app:latest"

# Build and push to Artifact Registry
gcloud builds submit --tag $IMAGE_TAG
```

### Deploy to Cloud Run

```bash
# Set service name
$SERVICE_NAME = "mca-name-checker"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --port=8080 `
    --memory=2Gi `
    --cpu=2 `
    --max-instances=10 `
    --set-env-vars="PORT=8080"
```

### Advanced Cloud Run Configuration

For production deployments, consider these additional settings:

```bash
# Deploy with advanced configuration
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --port=8080 `
    --memory=2Gi `
    --cpu=2 `
    --min-instances=1 `
    --max-instances=20 `
    --concurrency=100 `
    --timeout=300 `
    --set-env-vars="PORT=8080,WORKERS=2" `
    --set-secrets="FINANVO_API_KEY=finanvo-api-key:latest,FINANVO_SECRET_KEY=finanvo-secret:latest"
```

### Custom Domain Setup

```bash
# Map custom domain (optional)
gcloud run domain-mappings create --service=$SERVICE_NAME --domain=your-domain.com --region=$REGION
```

## Configuration

### Agent Configuration

Create `config/agents.yaml`:

```yaml
name_researcher:
  role: "Company Name Research Specialist"
  goal: "Research and analyze company name availability"
  backstory: "Expert in MCA database research"
  verbose: true
  allow_delegation: false
  max_iter: 3

name_generator:
  role: "Company Name Generator"
  goal: "Generate compliant alternative names"
  backstory: "Creative naming specialist"
  verbose: true
  allow_delegation: false
  max_iter: 3

name_validator:
  role: "MCA Compliance Validator"
  goal: "Validate names against MCA guidelines"
  backstory: "Legal compliance expert"
  verbose: true
  allow_delegation: false
  max_iter: 3
```

### Task Configuration

Create `config/tasks.yaml`:

```yaml
research_original_name:
  description: "Research the availability of {original_name}"
  expected_output: "Detailed availability report"

generate_alternative_names:
  description: "Generate 20 alternative names based on research"
  expected_output: "List of compliant alternatives"

validate_name_availability:
  description: "Validate all names for MCA compliance"
  expected_output: "Comprehensive validation report"
```

## Usage

### Web Interface (Streamlit)

```bash
# Run Streamlit app locally
streamlit run app.py

# Access at http://localhost:8501
```

### API Interface (FastAPI + Gradio)

```bash
# Run API server locally
uvicorn api:app --host 0.0.0.0 --port 8080

# Access Gradio interface at http://localhost:8080
# API docs at http://localhost:8080/docs
```

### Production Deployment

```bash
# Run with Gunicorn (production)
gunicorn --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 api:app
```

### Command Line Interface

```bash
python main.py "Your Company Name Pvt Ltd"
```

### API Integration

```python
from src.company_mca.tools.custom_tool import mca_name_checker

result = mca_name_checker._run("Tech Solutions Pvt Ltd")
print(result)
```

## Key Features Explained

### Name Validation

The system checks for:

- **Length**: 3-120 characters
- **Prohibited Words**: Bank, Government, Ministry, etc.
- **Valid Suffixes**: Pvt Ltd, Private Limited, Limited
- **Character Restrictions**: No special characters except dots, hyphens
- **Number Restrictions**: Cannot start with numbers

### Scoring System

- **90-100**: Excellent compliance
- **70-89**: Good with minor issues  
- **50-69**: Moderate issues
- **Below 50**: Significant problems

### Alternative Generation

Creates 20 diverse alternatives using:
- Technology terms (Systems, Digital, Tech)
- Service words (Solutions, Consulting, Services)
- Business terms (Enterprises, Industries, Group)
- Modern prefixes (Global, Smart, Neo, Pro)

### Similarity Detection

Uses fuzzy matching to identify:
- Exact matches (>95% similarity)
- Similar companies (>70% similarity)
- Potential conflicts

## API Integration

### Finanvo API

The system integrates with Finanvo's company search API:

```python
# Search endpoint
GET https://api.finanvo.in/company/search
Parameters: name, limit
Headers: x-api-key, x-api-secret-key
```

### Fallback System

If API fails, the system uses intelligent mocking:
- Generates realistic company conflicts
- Maintains similarity scoring
- Provides consistent validation

## Dashboard Features

### Results Analysis

- **Summary Metrics**: Total checked, available count, average score
- **Score Distribution**: Visual charts showing compliance levels
- **Issues Summary**: Common errors and warnings
- **Export Options**: CSV and JSON download

### Search History

- Tracks recent searches
- Shows timestamps and results
- Provides quick access to previous analyses

### Real-time Updates

- Progress bars for batch processing
- Live status indicators
- Instant feedback on selections

## Deployment Monitoring

### Cloud Run Monitoring

```bash
# View service details
gcloud run services describe $SERVICE_NAME --region=$REGION

# View logs
gcloud logs read --filter="resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" --limit=50

# Set up monitoring
gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars="ENABLE_MONITORING=true"
```

### Scaling Configuration

The application automatically scales based on traffic:
- **Min instances**: 1 (keeps service warm)
- **Max instances**: 20 (handles high traffic)
- **Concurrency**: 100 requests per instance
- **Memory**: 2GB per instance
- **CPU**: 2 vCPUs per instance

## Troubleshooting

### Common Deployment Issues

1. **Build Failures**: Ensure all dependencies are in requirements.txt
2. **Port Issues**: Cloud Run expects port 8080, verify Dockerfile EXPOSE
3. **Memory Limits**: Increase memory allocation if processing large batches
4. **API Timeouts**: Adjust timeout settings for external API calls

### Local Development Issues

1. **SQLite Compatibility**: The app uses pysqlite3 for Streamlit Cloud compatibility
2. **Import Errors**: Ensure all config files are present in config/ directory
3. **API Keys**: Set up proper environment variables for Finanvo API

## API Response Format

```json
{
  "name": "Tech Solutions Pvt Ltd",
  "cleaned_name": "tech solutions",
  "is_available": true,
  "existing_companies": [],
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "score": 95
  },
  "recommendation": "✅ Name appears available and compliant"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Test Docker build: `docker build -t test-image .`
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: GitHub Issues
- **Documentation**: This README
- **API Reference**: FastAPI docs at `/docs` endpoint

---

**Deployed on Google Cloud Run** | **Powered by CrewAI & Finanvo API** | **Real-time MCA Database Access**
