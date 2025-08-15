import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from src.company_mca.crew import CompanyMcaCrew
from src.company_mca.tools.custom_tool import MCANameChecker, get_name_suggestions, batch_check_names

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCA Company Name Checker API",
    description="API for checking company name availability through MCA database using AI-powered crew",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Pydantic models
class CompanyNameRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name to check")
    user_preference: Optional[str] = Field(None, max_length=500, description="User preferences for naming")
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()

class BatchNameRequest(BaseModel):
    company_names: List[str] = Field(..., min_items=1, max_items=20, description="List of company names to check")
    
    @validator('company_names')
    def validate_names(cls, v):
        if not v:
            raise ValueError('At least one company name is required')
        cleaned_names = []
        for name in v:
            if name and name.strip():
                cleaned_names.append(name.strip())
        if not cleaned_names:
            raise ValueError('No valid company names provided')
        return cleaned_names

class NameSuggestionRequest(BaseModel):
    base_name: str = Field(..., min_length=1, max_length=100, description="Base name for suggestions")
    count: int = Field(5, ge=1, le=20, description="Number of suggestions to generate")

class CompanyNameResponse(BaseModel):
    name: str
    is_available: bool
    validation: Dict[str, Any]
    existing_companies: List[Dict[str, Any]]
    recommendation: str
    timestamp: str
    processing_time_seconds: float

class CrewAnalysisResponse(BaseModel):
    original_name: str
    user_preference: str
    crew_analysis: str
    timestamp: str
    processing_time_seconds: float

class BatchResponse(BaseModel):
    results: List[CompanyNameResponse]
    total_processed: int
    timestamp: str
    processing_time_seconds: float

class SuggestionsResponse(BaseModel):
    base_name: str
    suggestions: List[str]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: Dict[str, bool]

# Global instances
mca_checker = None
company_crew = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global mca_checker, company_crew
    
    logger.info("Starting MCA Company Name Checker API...")
    
    # Validate required environment variables
    required_env_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        # Initialize MCA checker
        mca_checker = MCANameChecker()
        logger.info("MCA Checker initialized successfully")
        
        # Initialize Company Crew
        company_crew = CompanyMcaCrew()
        logger.info("Company Crew initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise RuntimeError(f"Application initialization failed: {str(e)}")
    
    logger.info("Application startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MCA Company Name Checker API...")
    executor.shutdown(wait=True)
    logger.info("Application shutdown completed")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    env_status = {
        "openai_api_key": bool(os.getenv('OPENAI_API_KEY')),
        "mca_checker_initialized": mca_checker is not None,
        "crew_initialized": company_crew is not None
    }
    
    return HealthResponse(
        status="healthy" if all(env_status.values()) else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=env_status
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MCA Company Name Checker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "check_name": "/api/v1/check-name",
            "crew_analysis": "/api/v1/crew-analysis",
            "batch_check": "/api/v1/batch-check",
            "suggestions": "/api/v1/suggestions"
        }
    }

def run_mca_check(company_name: str) -> Dict[str, Any]:
    """Run MCA check in thread pool"""
    try:
        return mca_checker.check_name(company_name)
    except Exception as e:
        logger.error(f"Error in MCA check for '{company_name}': {str(e)}")
        return {
            "error": str(e),
            "name": company_name,
            "is_available": False
        }

def run_crew_analysis(company_name: str, user_preference: str) -> str:
    """Run crew analysis in thread pool"""
    try:
        return company_crew.run_crew(company_name, user_preference)
    except Exception as e:
        logger.error(f"Error in crew analysis for '{company_name}': {str(e)}")
        return f"Error during analysis: {str(e)}"

@app.post("/api/v1/check-name", response_model=CompanyNameResponse)
async def check_company_name(request: CompanyNameRequest):
    """
    Check a single company name for availability and compliance
    """
    start_time = datetime.utcnow()
    
    if not mca_checker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCA Checker service not initialized"
        )
    
    try:
        logger.info(f"Checking company name: {request.company_name}")
        
        # Run MCA check in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            run_mca_check, 
            request.company_name
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if "error" in result:
            logger.error(f"MCA check failed for '{request.company_name}': {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCA check failed: {result['error']}"
            )
        
        return CompanyNameResponse(
            name=result.get("name", request.company_name),
            is_available=result.get("is_available", False),
            validation=result.get("validation", {}),
            existing_companies=result.get("existing_companies", []),
            recommendation=result.get("recommendation", "Unable to determine"),
            timestamp=datetime.utcnow().isoformat(),
            processing_time_seconds=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking name '{request.company_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during name check"
        )

@app.post("/api/v1/crew-analysis", response_model=CrewAnalysisResponse)
async def crew_analysis(request: CompanyNameRequest):
    """
    Get AI-powered crew analysis for company name with suggestions
    """
    start_time = datetime.utcnow()
    
    if not company_crew:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company Crew service not initialized"
        )
    
    try:
        logger.info(f"Running crew analysis for: {request.company_name}")
        
        # Run crew analysis in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_crew_analysis,
            request.company_name,
            request.user_preference or "Professional and brandable"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return CrewAnalysisResponse(
            original_name=request.company_name,
            user_preference=request.user_preference or "Professional and brandable",
            crew_analysis=result,
            timestamp=datetime.utcnow().isoformat(),
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"Crew analysis failed for '{request.company_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Crew analysis failed"
        )

@app.post("/api/v1/batch-check", response_model=BatchResponse)
async def batch_check_names(request: BatchNameRequest):
    """
    Check multiple company names in batch
    """
    start_time = datetime.utcnow()
    
    if not mca_checker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCA Checker service not initialized"
        )
    
    try:
        logger.info(f"Batch checking {len(request.company_names)} names")
        
        # Run batch check in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            executor,
            batch_check_names,
            request.company_names
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        formatted_results = []
        for result in results:
            formatted_results.append(CompanyNameResponse(
                name=result.get("name", ""),
                is_available=result.get("is_available", False),
                validation=result.get("validation", {}),
                existing_companies=result.get("existing_companies", []),
                recommendation=result.get("recommendation", "Unable to determine"),
                timestamp=datetime.utcnow().isoformat(),
                processing_time_seconds=0  # Individual processing time not tracked in batch
            ))
        
        return BatchResponse(
            results=formatted_results,
            total_processed=len(formatted_results),
            timestamp=datetime.utcnow().isoformat(),
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch check failed"
        )

@app.post("/api/v1/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(request: NameSuggestionRequest):
    """
    Generate name suggestions based on base name
    """
    try:
        logger.info(f"Generating {request.count} suggestions for: {request.base_name}")
        
        # Run suggestion generation in thread pool
        loop = asyncio.get_event_loop()
        suggestions = await loop.run_in_executor(
            executor,
            get_name_suggestions,
            request.base_name,
            request.count
        )
        
        return SuggestionsResponse(
            base_name=request.base_name,
            suggestions=suggestions,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Suggestion generation failed for '{request.base_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Suggestion generation failed"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 500
        }
    )

# For local development
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )