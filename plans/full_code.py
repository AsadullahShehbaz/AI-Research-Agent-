"""
Research Assistant Agent - Complete Production Setup
From LangGraph Development to Production API

Project Structure:
research_assistant/
├── agent/
│   ├── __init__.py
│   ├── graph.py          # LangGraph workflow
│   ├── nodes.py          # Agent nodes
│   └── tools.py          # Agent tools
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # Pydantic models
│   └── middleware.py     # Auth, CORS, etc.
├── tests/
│   ├── test_agent.py
│   └── test_api.py
├── config/
│   ├── settings.py       # Configuration
│   └── .env              # Environment variables
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
"""

# ============================================================================
# FILE 1: agent/tools.py - Define Agent Tools
# ============================================================================

from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import requests

class ResearchTools:
    """Collection of tools for research assistant"""
    
    def __init__(self):
        self.search = DuckDuckGoSearchRun()
    
    def web_search(self, query: str) -> str:
        """Search the web for information"""
        try:
            results = self.search.run(query)
            return results
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def fetch_webpage(self, url: str) -> str:
        """Fetch and extract content from webpage"""
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            chunks = splitter.split_documents(docs)
            return "\n\n".join([chunk.page_content for chunk in chunks[:3]])
        except Exception as e:
            return f"Fetch error: {str(e)}"
    
    def summarize_findings(self, findings: List[str]) -> str:
        """Combine and deduplicate research findings"""
        unique_findings = list(set(findings))
        return "\n---\n".join(unique_findings)
    
    def get_tools(self) -> List[Tool]:
        """Return list of LangChain tools"""
        return [
            Tool(
                name="web_search",
                func=self.web_search,
                description="Search the web for current information. Input should be a search query string."
            ),
            Tool(
                name="fetch_webpage",
                func=self.fetch_webpage,
                description="Fetch content from a specific webpage URL. Input should be a valid URL."
            ),
            Tool(
                name="summarize_findings",
                func=self.summarize_findings,
                description="Summarize and deduplicate research findings. Input should be a list of findings."
            )
        ]


# ============================================================================
# FILE 2: agent/nodes.py - Define Agent Nodes
# ============================================================================

from typing import TypedDict, List, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode

class ResearchState(TypedDict):
    """State for research assistant workflow"""
    messages: List
    research_query: str
    findings: List[str]
    iteration: int
    max_iterations: int

class ResearchNodes:
    """Node functions for research workflow"""
    
    def __init__(self, llm_with_tools, tools):
        self.llm = llm_with_tools
        self.tool_node = ToolNode(tools)
    
    def planner(self, state: ResearchState) -> dict:
        """
        Planning node - Create research strategy
        """
        messages = state["messages"]
        iteration = state.get("iteration", 0)
        
        system_msg = SystemMessage(content="""You are a research planning expert.
        Break down the research query into specific sub-queries.
        Create a research plan with 2-3 focused search queries.""")
        
        response = self.llm.invoke([system_msg] + messages)
        
        return {
            "messages": [response],
            "iteration": iteration + 1
        }
    
    def researcher(self, state: ResearchState) -> dict:
        """
        Research node - Execute searches and gather information
        """
        messages = state["messages"]
        
        system_msg = SystemMessage(content="""You are a thorough researcher.
        Use the available tools to search for information.
        Be specific and comprehensive in your searches.""")
        
        response = self.llm.invoke([system_msg] + messages)
        
        return {"messages": [response]}
    
    def synthesizer(self, state: ResearchState) -> dict:
        """
        Synthesis node - Combine and format final report
        """
        messages = state["messages"]
        findings = state.get("findings", [])
        
        system_msg = SystemMessage(content="""You are a research synthesizer.
        Create a comprehensive, well-structured report from the research findings.
        Include:
        1. Executive Summary
        2. Key Findings (with sources)
        3. Detailed Analysis
        4. Conclusion
        
        Format in markdown.""")
        
        synthesis_prompt = f"""
        Based on the research conducted, create a final report.
        
        Findings gathered:
        {chr(10).join(findings) if findings else "Research in progress"}
        
        Create a comprehensive report now.
        """
        
        response = self.llm.invoke([
            system_msg,
            HumanMessage(content=synthesis_prompt)
        ])
        
        return {
            "messages": [response],
            "findings": findings + [response.content]
        }


# ============================================================================
# FILE 3: agent/graph.py - Build LangGraph Workflow
# ============================================================================

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
import os

class ResearchAssistant:
    """Main Research Assistant Agent using LangGraph"""
    
    def __init__(self, api_key: str = None):
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Initialize tools
        self.tools_manager = ResearchTools()
        self.tools = self.tools_manager.get_tools()
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Initialize nodes
        self.nodes = ResearchNodes(self.llm_with_tools, self.tools)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        
        # Create graph
        builder = StateGraph(ResearchState)
        
        # Add nodes
        builder.add_node("planner", self.nodes.planner)
        builder.add_node("researcher", self.nodes.researcher)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_node("synthesizer", self.nodes.synthesizer)
        
        # Define workflow
        builder.add_edge("__start__", "planner")
        builder.add_edge("planner", "researcher")
        
        # Conditional: researcher decides if tools needed
        builder.add_conditional_edges(
            "researcher",
            tools_condition,
            {
                "tools": "tools",
                "__end__": "synthesizer"
            }
        )
        
        # After tools, back to researcher or synthesize
        builder.add_conditional_edges(
            "tools",
            self._should_continue_research,
            {
                "researcher": "researcher",
                "synthesizer": "synthesizer"
            }
        )
        
        builder.add_edge("synthesizer", END)
        
        return builder.compile()
    
    def _should_continue_research(self, state: ResearchState) -> str:
        """Decide if more research needed"""
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)
        
        if iteration >= max_iterations:
            return "synthesizer"
        return "researcher"
    
    def research(self, query: str, max_iterations: int = 3) -> dict:
        """
        Execute research workflow
        
        Args:
            query: Research question
            max_iterations: Maximum research iterations
        
        Returns:
            Final research report
        """
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "research_query": query,
            "findings": [],
            "iteration": 0,
            "max_iterations": max_iterations
        }
        
        result = self.graph.invoke(initial_state)
        
        # Extract final report
        final_message = result["messages"][-1]
        
        return {
            "query": query,
            "report": final_message.content,
            "iterations": result.get("iteration", 0),
            "findings_count": len(result.get("findings", []))
        }


# ============================================================================
# FILE 4: api/models.py - Pydantic Models for API
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List

class ResearchRequest(BaseModel):
    """Request model for research endpoint"""
    query: str = Field(..., description="Research question or topic", min_length=5)
    max_iterations: Optional[int] = Field(3, ge=1, le=10, description="Maximum research iterations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest developments in quantum computing?",
                "max_iterations": 3
            }
        }

class ResearchResponse(BaseModel):
    """Response model for research results"""
    success: bool
    query: str
    report: str
    iterations: int
    findings_count: int
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "What are the latest developments in quantum computing?",
                "report": "# Quantum Computing Research Report\n\n...",
                "iterations": 3,
                "findings_count": 5,
                "processing_time": 12.34
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agent_status: str


# ============================================================================
# FILE 5: api/main.py - FastAPI Application
# ============================================================================

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import time
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
research_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global research_agent
    
    # Startup
    logger.info("Initializing Research Assistant Agent...")
    research_agent = ResearchAssistant()
    logger.info("Agent initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research Assistant Agent...")

# Create FastAPI app
app = FastAPI(
    title="Research Assistant API",
    description="AI-powered research assistant using LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Authentication (Simple version)
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    expected_key = os.getenv("API_KEY", "your-secret-key")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agent_status": "ready" if research_agent else "initializing"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agent_status": "ready" if research_agent else "initializing"
    }

@app.post("/research", response_model=ResearchResponse)
async def conduct_research(
    request: ResearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Conduct research on given query
    
    - **query**: Research question or topic (required)
    - **max_iterations**: Maximum research iterations (1-10, default: 3)
    """
    if not research_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        start_time = time.time()
        logger.info(f"Research request: {request.query}")
        
        # Execute research
        result = research_agent.research(
            query=request.query,
            max_iterations=request.max_iterations
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Research completed in {processing_time:.2f}s")
        
        return ResearchResponse(
            success=True,
            query=result["query"],
            report=result["report"],
            iterations=result["iterations"],
            findings_count=result["findings_count"],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/research/stream")
async def conduct_research_streaming(
    request: ResearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Stream research results in real-time
    """
    async def generate():
        try:
            # In production, implement streaming with graph.astream()
            yield f"data: Starting research for: {request.query}\n\n"
            
            result = research_agent.research(
                query=request.query,
                max_iterations=request.max_iterations
            )
            
            yield f"data: {result['report']}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# ============================================================================
# FILE 6: requirements.txt
# ============================================================================

"""
# Core dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
python-dotenv==1.0.0

# LangChain & LangGraph
langchain==0.1.0
langgraph==0.0.20
langchain-google-genai==0.0.6
langchain-community==0.0.13

# Tools & Utilities
duckduckgo-search==4.1.0
requests==2.31.0
python-multipart==0.0.6

# Testing
pytest==7.4.3
httpx==0.26.0

# Production
gunicorn==21.2.0
"""


# ============================================================================
# FILE 7: Dockerfile
# ============================================================================

"""
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


# ============================================================================
# FILE 8: docker-compose.yml
# ============================================================================

"""
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - API_KEY=${API_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  # Optional: Add Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
"""


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
STEP 1: Local Development
--------------------------
1. Install dependencies:
   pip install -r requirements.txt

2. Create .env file:
   GOOGLE_API_KEY=your_google_api_key
   API_KEY=your_secret_api_key

3. Run locally:
   uvicorn api.main:app --reload

4. Test at: http://localhost:8000/docs


STEP 2: Docker Deployment
--------------------------
1. Build image:
   docker build -t research-assistant .

2. Run container:
   docker run -p 8000:8000 --env-file .env research-assistant

3. Or use docker-compose:
   docker-compose up -d


STEP 3: API Usage
-----------------
# Using curl
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secret_api_key" \
  -d '{"query": "What is quantum computing?", "max_iterations": 3}'

# Using Python requests
import requests

response = requests.post(
    "http://localhost:8000/research",
    headers={"X-API-Key": "your_secret_api_key"},
    json={
        "query": "What is quantum computing?",
        "max_iterations": 3
    }
)

result = response.json()
print(result["report"])


STEP 4: Cloud Deployment Options
---------------------------------
A. AWS (EC2 + Load Balancer):
   - Launch EC2 instance
   - Install Docker
   - Deploy container
   - Configure ALB

B. Google Cloud Run:
   - Build image: gcloud builds submit --tag gcr.io/PROJECT/research-agent
   - Deploy: gcloud run deploy --image gcr.io/PROJECT/research-agent

C. Railway / Render (Easiest):
   - Connect GitHub repo
   - Auto-deploy on push
   - Configure environment variables

D. Azure Container Instances:
   - Push to ACR
   - Deploy to ACI
   - Configure networking


STEP 5: Production Considerations
----------------------------------
1. Rate Limiting:
   from slowapi import Limiter
   limiter = Limiter(key_func=lambda: request.headers.get("X-API-Key"))

2. Caching:
   Use Redis for caching research results

3. Monitoring:
   - Add Prometheus metrics
   - Use Sentry for error tracking
   - CloudWatch/Datadog for logs

4. Authentication:
   - Implement JWT tokens
   - Add user management
   - Role-based access control

5. Database:
   - Store research history
   - User preferences
   - Usage analytics

6. Queue System:
   - Use Celery for async tasks
   - RabbitMQ/Redis as message broker
"""