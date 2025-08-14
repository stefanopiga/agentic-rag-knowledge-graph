"""
FastAPI endpoints for the agentic RAG system.
"""

import os
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from dotenv import load_dotenv
# Optional Prometheus import
try:
    from prometheus_client import generate_latest
except Exception:
    generate_latest = None  # type: ignore

from .agent import rag_agent, AgentDependencies
from .db_utils import (
    initialize_database,
    close_database,
    create_session,
    get_session,
    add_message,
    get_session_messages,
    test_connection,
    get_database_status
)
from .cache_manager import initialize_cache, close_cache, cache_manager
from .graph_utils import initialize_graph, close_graph, test_graph_connection
from .models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    StreamDelta,
    ErrorResponse,
    HealthStatus,
    ToolCall
)
# Monitoring is optional in test/dev to avoid hard deps
MONITORING_AVAILABLE = True
try:
    from .monitoring import (
        setup_monitoring,
        MonitoringMiddleware,
        track_rag_query,
        track_vector_search,
        track_graph_query,
        get_detailed_health_status,
        update_connection_metrics
    )
except Exception:
    MONITORING_AVAILABLE = False

    def setup_monitoring(app: FastAPI, enable_metrics: bool = True):  # type: ignore
        return None

    class MonitoringMiddleware:  # type: ignore
        pass

    def track_rag_query(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

    def track_vector_search(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

    def track_graph_query(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

    async def get_detailed_health_status():  # type: ignore
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "healthy",
                "database": "unknown",
                "graph_database": "unknown",
                "cache": "unknown",
                "llm_provider": "unknown",
            },
            "version": "0.1.0",
            "uptime_seconds": "n/a",
        }

    def update_connection_metrics():  # type: ignore
        return None
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    list_documents_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentListInput
)

from uuid import UUID

# Load environment variables
# 1) Load base .env (does not override already-set env vars)
load_dotenv()
# 2) If running in production, optionally load .env.production (without overriding process env)
if os.getenv("APP_ENV", "development").lower() == "production":
    try:
        load_dotenv(".env.production", override=False)
    except Exception:
        # Non-blocking: proceed even if file not present
        pass

logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", 9090))
DISABLE_DB_PERSISTENCE = os.getenv("DISABLE_DB_PERSISTENCE", "false").lower() == "true"
"""
Production CORS configuration
 - CORS_ALLOWED_ORIGINS: comma-separated list of origins (e.g. "https://app.example.com,https://www.example.com")
   If not set, defaults to "*" in non-production, and empty in production (which implies deny-all unless explicitly set)
"""
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "" if APP_ENV == "production" else "*")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up agentic RAG API...")
    
    try:
        # Initialize database connections
        await initialize_database()
        logger.info("Database initialized")
        
        # Initialize graph database
        await initialize_graph()
        logger.info("Graph database initialized")
        
        # Initialize cache
        await initialize_cache()
        logger.info("Cache manager initialized")
        
        # Test connections
        db_ok = await test_connection()
        graph_ok = await test_graph_connection()
        cache_ok = (await cache_manager.health_check()).get("status") == "healthy"
        
        if not db_ok:
            logger.error("Database connection failed")
        if not graph_ok:
            logger.error("Graph database connection failed")
        if not cache_ok:
            logger.error("Cache connection failed")
        
        logger.info("Agentic RAG API startup complete")
        
        # Expose metrics endpoint if enabled
        if ENABLE_METRICS and instrumentator:
            instrumentator.expose(app, endpoint="/metrics")
            logger.info(f"Metrics endpoint exposed at /metrics")
        elif ENABLE_METRICS and not instrumentator:
            logger.warning("ENABLE_METRICS is true but monitoring is not available; skipping /metrics exposure")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # In non-production environments, continue startup to allow health endpoints/tests to run
        if APP_ENV.lower() == "production":
            raise
        logger.warning("Continuing startup despite initialization errors (non-production environment)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down agentic RAG API...")
    
    try:
        await close_database()
        await close_graph()
        await close_cache()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG with Knowledge Graph",
    description="AI agent combining vector search and knowledge graph for tech company analysis",
    version="0.1.0",
    lifespan=lifespan
)

def _parse_allowed_origins(origins_str: str) -> list[str]:
    if not origins_str:
        return []
    if origins_str.strip() == "*":
        return ["*"]
    return [o.strip() for o in origins_str.split(",") if o.strip()]


# Add middleware with flexible, env-driven CORS
_allowed_origins = _parse_allowed_origins(CORS_ALLOWED_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins if _allowed_origins else ([] if APP_ENV == "production" else ["*"] ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add monitoring middleware if available
if MONITORING_AVAILABLE:
    app.add_middleware(MonitoringMiddleware)

# Setup monitoring and metrics (optional)
instrumentator = setup_monitoring(app, enable_metrics=ENABLE_METRICS) if MONITORING_AVAILABLE else None


# ------------------------------------
# Minimal Auth (development placeholder)
# ------------------------------------
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: str
    email: str
    name: str
    role: str = "admin"


class AuthTenant(BaseModel):
    id: str
    name: str
    slug: str
    created_at: str


class AuthResponseModel(BaseModel):
    user: AuthUser
    tenant: AuthTenant
    token: str
    refreshToken: str


_DEV_TOKEN = os.getenv("DEV_AUTH_TOKEN", "dev-token")


@app.post("/auth/login", response_model=AuthResponseModel)
async def auth_login(payload: LoginRequest):
    # Minimal stub: accept any credentials and return a fixed token and tenant
    user = AuthUser(id="u-1", email=payload.email, name="Dev User")
    tenant = AuthTenant(id="t-1", name="Dev Tenant", slug="dev", created_at=datetime.now().isoformat())
    return AuthResponseModel(user=user, tenant=tenant, token=_DEV_TOKEN, refreshToken=_DEV_TOKEN)


@app.get("/auth/me", response_model=AuthUser)
async def auth_me():
    # Minimal stub: return the same dev user
    return AuthUser(id="u-1", email="dev@example.com", name="Dev User")


# Helper functions for agent execution
async def get_or_create_session(request: ChatRequest) -> str:
    """Get existing session or create new one."""
    # Normalize tenant_id to UUID in development to handle stub IDs like "t-1"
    try:
        tenant_uuid: UUID = UUID(str(request.tenant_id))
    except Exception:
        # Fallback dev UUID (stable)
        tenant_uuid = UUID(os.getenv("DEV_TENANT_UUID", "00000000-0000-0000-0000-000000000001"))

    if DISABLE_DB_PERSISTENCE:
        # Return a deterministic UUID in dev mode without DB persistence
        return os.getenv("DEV_SESSION_UUID", "11111111-1111-1111-1111-111111111111")

    if request.session_id:
        session = await get_session(request.session_id, tenant_id=tenant_uuid)
        if session:
            return request.session_id
    
    # Create new session
    return await create_session(
        tenant_id=tenant_uuid,
        user_id=request.user_id,
        metadata=request.metadata
    )


async def get_conversation_context(
    session_id: str,
    tenant_id: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Get recent conversation context.
    
    Args:
        session_id: Session ID
        max_messages: Maximum number of messages to retrieve
    
    Returns:
        List of messages
    """
    # Ensure tenant_id is UUID
    try:
        tenant_uuid_ctx: UUID = UUID(str(tenant_id))
    except Exception:
        tenant_uuid_ctx = UUID(os.getenv("DEV_TENANT_UUID", "00000000-0000-0000-0000-000000000001"))
    if DISABLE_DB_PERSISTENCE:
        return []
    messages = await get_session_messages(session_id, tenant_id=tenant_uuid_ctx, limit=max_messages)
    
    return [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in messages
    ]


def extract_tool_calls(result) -> List[ToolCall]:
    """
    Extract tool calls from Pydantic AI result.
    
    Args:
        result: Pydantic AI result object
    
    Returns:
        List of ToolCall objects
    """
    tools_used = []
    
    try:
        # Get all messages from the result
        messages = result.all_messages()
        
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if this is a tool call part
                    if part.__class__.__name__ == 'ToolCallPart':
                        try:
                            # Debug logging to understand structure
                            logger.debug(f"ToolCallPart attributes: {dir(part)}")
                            logger.debug(f"ToolCallPart content: tool_name={getattr(part, 'tool_name', None)}")
                            
                            # Extract tool information safely
                            tool_name = str(part.tool_name) if hasattr(part, 'tool_name') else 'unknown'
                            
                            # Get args - the args field is a JSON string in Pydantic AI
                            tool_args = {}
                            if hasattr(part, 'args') and part.args is not None:
                                if isinstance(part.args, str):
                                    # Args is a JSON string, parse it
                                    try:
                                        import json
                                        tool_args = json.loads(part.args)
                                        logger.debug(f"Parsed args from JSON string: {tool_args}")
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"Failed to parse args JSON: {e}")
                                        tool_args = {}
                                elif isinstance(part.args, dict):
                                    tool_args = part.args
                                    logger.debug(f"Args already a dict: {tool_args}")
                            
                            # Alternative: use args_as_dict method if available
                            if hasattr(part, 'args_as_dict'):
                                try:
                                    tool_args = part.args_as_dict()
                                    logger.debug(f"Got args from args_as_dict(): {tool_args}")
                                except:
                                    pass
                            
                            # Get tool call ID
                            tool_call_id = None
                            if hasattr(part, 'tool_call_id'):
                                tool_call_id = str(part.tool_call_id) if part.tool_call_id else None
                            
                            # Create ToolCall with explicit field mapping
                            tool_call_data = {
                                "tool_name": tool_name,
                                "args": tool_args,
                                "tool_call_id": tool_call_id
                            }
                            logger.debug(f"Creating ToolCall with data: {tool_call_data}")
                            tools_used.append(ToolCall(**tool_call_data))
                        except Exception as e:
                            logger.debug(f"Failed to parse tool call part: {e}")
                            continue
    except Exception as e:
        logger.warning(f"Failed to extract tool calls: {e}")
    
    return tools_used


async def save_conversation_turn(
    session_id: str,
    tenant_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Save a conversation turn to the database.
    
    Args:
        session_id: Session ID
        user_message: User's message
        assistant_message: Assistant's response
        metadata: Optional metadata
    """
    # Save user message
    # Ensure tenant_id is UUID
    try:
        tenant_uuid_save: UUID = UUID(str(tenant_id))
    except Exception:
        tenant_uuid_save = UUID(os.getenv("DEV_TENANT_UUID", "00000000-0000-0000-0000-000000000001"))

    if DISABLE_DB_PERSISTENCE:
        return

    await add_message(
        session_id=session_id,
        tenant_id=tenant_uuid_save,
        role="user",
        content=user_message,
        metadata=metadata or {}
    )
    
    # Save assistant message
    await add_message(
        session_id=session_id,
        tenant_id=tenant_uuid_save,
        role="assistant",
        content=assistant_message,
        metadata=metadata or {}
    )


async def execute_agent(
    message: str,
    session_id: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    save_conversation: bool = True
) -> tuple[str, List[ToolCall]]:
    """
    Execute the agent with a message.
    
    Args:
        message: User message
        session_id: Session ID
        user_id: Optional user ID
        save_conversation: Whether to save the conversation
    
    Returns:
        Tuple of (agent response, tools used)
    """
    try:
        # Create dependencies
        deps = AgentDependencies(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        # Get conversation context
        context = await get_conversation_context(session_id, tenant_id=tenant_id)
        
        # Build prompt with context
        full_prompt = message
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context[-6:]  # Last 3 turns
            ])
            full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {message}"
        
        # Run the agent
        result = await rag_agent.run(full_prompt, deps=deps)
        
        response = result.data
        tools_used = extract_tool_calls(result)
        
        # Save conversation if requested
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                tenant_id=tenant_id,
                user_message=message,
                assistant_message=response,
                metadata={
                    "user_id": user_id,
                    "tool_calls": len(tools_used)
                }
            )
        
        return response, tools_used
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        error_response = f"I encountered an error while processing your request: {str(e)}"
        
        if save_conversation:
            await save_conversation_turn(
                session_id=session_id,
                tenant_id=tenant_id,
                user_message=message,
                assistant_message=error_response,
                metadata={"error": str(e)}
            )
        
        return error_response, []


# API Endpoints
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        db_status = await test_connection()
        graph_status = await test_graph_connection()
        cache_health = await cache_manager.health_check()
        cache_status = cache_health.get("status") == "healthy"
        
        # Update connection metrics
        update_connection_metrics()
        
        # Determine overall status
        if db_status and graph_status and cache_status:
            status = "healthy"
        elif (db_status and graph_status) or (db_status and cache_status) or (graph_status and cache_status):
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            database=db_status,
            graph_database=graph_status,
            llm_connection=True,  # Assume OK if we can respond
            version="0.1.0",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics information."""
    try:
        return await get_detailed_health_status()
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not ENABLE_METRICS or generate_latest is None:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/status/database")
async def database_status():
    """Get detailed database status and metrics."""
    try:
        status = await get_database_status()
        cache_health = await cache_manager.health_check()
        
        return {
            "database": status,
            "cache": cache_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        raise HTTPException(status_code=500, detail="Database status check failed")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        # Execute agent
        response, tools_used = await execute_agent(
            message=request.message,
            session_id=session_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id
        )
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            tools_used=tools_used,
            metadata={"search_type": str(request.search_type)}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        async def generate_stream():
            """Generate streaming response using agent.iter() pattern."""
            try:
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Create dependencies
                deps = AgentDependencies(
                    session_id=session_id,
                    tenant_id=request.tenant_id,
                    user_id=request.user_id
                )
                
                # Get conversation context
                context = await get_conversation_context(session_id, tenant_id=request.tenant_id)
                
                # Build input with context
                full_prompt = request.message
                if context:
                    context_str = "\n".join([
                        f"{msg['role']}: {msg['content']}"
                        for msg in context[-6:]
                    ])
                    full_prompt = f"Previous conversation:\n{context_str}\n\nCurrent question: {request.message}"
                
                # Save user message immediately (skip when persistence disabled)
                if not DISABLE_DB_PERSISTENCE:
                    await add_message(
                        session_id=session_id,
                        tenant_id=request.tenant_id,
                        role="user",
                        content=request.message,
                        metadata={"user_id": request.user_id}
                    )
                
                full_response = ""
                
                # Stream using agent.iter() pattern
                async with rag_agent.iter(full_prompt, deps=deps) as run:
                    async for node in run:
                        if rag_agent.is_model_request_node(node):
                            # Stream tokens from the model
                            async with node.stream(run.ctx) as request_stream:
                                async for event in request_stream:
                                    from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta
                                    
                                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        delta_content = event.part.content
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                                        
                                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        delta_content = event.delta.content_delta
                                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
                                        full_response += delta_content
                
                # Extract tools used from the final result
                result = run.result
                tools_used = extract_tool_calls(result)
                
                # Send tools used information
                if tools_used:
                    tools_data = [
                        {
                            "tool_name": tool.tool_name,
                            "args": tool.args,
                            "tool_call_id": tool.tool_call_id
                        }
                        for tool in tools_used
                    ]
                    yield f"data: {json.dumps({'type': 'tools', 'tools': tools_data})}\n\n"
                
                # Save assistant response (skip when persistence disabled)
                if not DISABLE_DB_PERSISTENCE:
                    await add_message(
                        session_id=session_id,
                        tenant_id=request.tenant_id,
                        role="assistant",
                        content=full_response,
                        metadata={
                            "streamed": True,
                            "tool_calls": len(tools_used)
                        }
                    )
                
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Stream error: {str(e)}"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector")
@track_vector_search()
async def search_vector(request: SearchRequest):
    """Vector search endpoint."""
    try:
        input_data = VectorSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await vector_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="vector",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/graph")
@track_graph_query()
async def search_graph(request: SearchRequest):
    """Knowledge graph search endpoint."""
    try:
        input_data = GraphSearchInput(
            query=request.query
        )
        
        start_time = datetime.now()
        results = await graph_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            graph_results=results,
            total_results=len(results),
            search_type="graph",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
@track_rag_query(query_type="hybrid")
async def search_hybrid(request: SearchRequest):
    """Hybrid search endpoint."""
    try:
        input_data = HybridSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await hybrid_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="hybrid",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents_endpoint(
    limit: int = 20,
    offset: int = 0
):
    """List documents endpoint."""
    try:
        input_data = DocumentListInput(limit=limit, offset=offset)
        documents = await list_documents_tool(input_data)
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "agent.api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_ENV == "development",
        log_level=LOG_LEVEL.lower()
    )