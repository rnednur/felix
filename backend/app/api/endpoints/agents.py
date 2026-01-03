"""
Agent API endpoints
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncIterator

from app.core.database import get_db
from app.schemas.agent import (
    ChatRequest, ChatResponse, AgentListResponse,
    ChatNameRequest, ChatNameResponse, StreamChunk
)
from app.services.agents import (
    get_agent_registry,
    get_agent_orchestrator,
    get_context_manager,
)
from app.models.agent_session import AgentSession, AgentMessage

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
async def list_agents() -> AgentListResponse:
    """
    List all available agents

    Returns:
        AgentListResponse with agent information
    """
    try:
        agent_registry = get_agent_registry()
        agents_info = agent_registry.list_agents()

        return AgentListResponse(agents=agents_info)

    except RuntimeError as e:
        raise HTTPException(500, f"Agent system not initialized: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Failed to list agents: {str(e)}")


@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat with an agent

    Can either specify a specific agent or let the orchestrator select the best one.

    Request:
    {
        "query": "What's the average price?",
        "dataset_id": "uuid",
        "agent_name": "query_agent",  # optional
        "session_id": "uuid",  # optional
        "stream": false
    }

    Response:
    {
        "session_id": "uuid",
        "agent": "query_agent",
        "response": {
            "summary": "...",
            "data": {...}
        },
        "metadata": {...}
    }
    """
    try:
        orchestrator = get_agent_orchestrator()
        context_manager = get_context_manager()

        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        # Check if session exists in database
        session = db.query(AgentSession).filter(
            AgentSession.id == session_id
        ).first()

        if not session:
            # Create new session
            session = AgentSession(
                id=session_id,
                dataset_id=request.dataset_id,
                name=None,  # Will be generated later
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()

        # Process query
        if request.agent_name:
            # Direct agent chat
            agent_registry = get_agent_registry()
            agent = agent_registry.get_agent(request.agent_name)

            if not agent:
                raise HTTPException(404, f"Agent '{request.agent_name}' not found")

            from app.schemas.agent import AgentRequest, Message
            context = await context_manager.get_context(session_id, request.dataset_id)

            agent_request = AgentRequest(
                query=request.query,
                dataset_id=request.dataset_id,
                task_type="chat"
            )

            response = await agent.process(agent_request, context)
            agent_name = request.agent_name

        else:
            # Orchestrated chat (auto-select agent)
            response = await orchestrator.process_query(
                query=request.query,
                dataset_id=request.dataset_id,
                session_id=session_id,
                stream=False
            )
            agent_name = response.agent_name

        # Save message to database
        user_message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=request.query,
            timestamp=datetime.utcnow()
        )
        db.add(user_message)

        assistant_message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=response.data.get('summary', ''),
            agent_name=agent_name,
            code=response.code,
            result_data=response.data,
            timestamp=datetime.utcnow()
        )
        db.add(assistant_message)

        # Update session timestamp
        session.updated_at = datetime.utcnow()
        db.commit()

        return ChatResponse(
            session_id=session_id,
            agent=agent_name,
            response=response.data,
            metadata=response.metadata
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(500, f"Agent system not initialized: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {str(e)}")


@router.post("/chat/stream")
async def chat_with_agent_streaming(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with streaming response (Server-Sent Events)

    Returns real-time progress updates for long-running operations
    """
    try:
        orchestrator = get_agent_orchestrator()

        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        session = db.query(AgentSession).filter(
            AgentSession.id == session_id
        ).first()

        if not session:
            session = AgentSession(
                id=session_id,
                dataset_id=request.dataset_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()

        async def event_generator() -> AsyncIterator[str]:
            """Generate SSE events"""
            try:
                # Process query with streaming
                stream = await orchestrator.process_query(
                    query=request.query,
                    dataset_id=request.dataset_id,
                    session_id=session_id,
                    stream=True
                )

                # Stream chunks
                async for chunk in stream:
                    # Format as SSE
                    yield f"event: {chunk.type}\n"
                    yield f"data: {chunk.model_dump_json()}\n\n"

            except Exception as e:
                # Send error event
                error_chunk = StreamChunk(
                    type="error",
                    data={"error": str(e)}
                )
                yield f"event: error\n"
                yield f"data: {error_chunk.model_dump_json()}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(500, f"Streaming chat failed: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get session details with message history

    Returns:
    {
        "session": {...},
        "messages": [...]
    }
    """
    session = db.query(AgentSession).filter(
        AgentSession.id == session_id,
        AgentSession.deleted_at.is_(None)
    ).first()

    if not session:
        raise HTTPException(404, "Session not found")

    # Get messages
    messages = db.query(AgentMessage).filter(
        AgentMessage.session_id == session_id
    ).order_by(AgentMessage.timestamp).all()

    return {
        "session": {
            "id": session.id,
            "dataset_id": session.dataset_id,
            "name": session.name,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "agent_name": msg.agent_name,
                "code": msg.code,
                "result_data": msg.result_data,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    }


@router.post("/sessions/{session_id}/name")
async def generate_session_name(
    session_id: str,
    db: Session = Depends(get_db)
) -> ChatNameResponse:
    """
    Generate a descriptive name for a session based on conversation history

    Uses LLM to create a short, meaningful name
    """
    session = db.query(AgentSession).filter(
        AgentSession.id == session_id,
        AgentSession.deleted_at.is_(None)
    ).first()

    if not session:
        raise HTTPException(404, "Session not found")

    # Get first few messages
    messages = db.query(AgentMessage).filter(
        AgentMessage.session_id == session_id
    ).order_by(AgentMessage.timestamp).limit(5).all()

    if not messages:
        return ChatNameResponse(name="New Chat")

    try:
        from app.services.agents import LLMService

        llm_service = LLMService()

        # Format messages
        messages_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages
        ])

        prompt = f"""Generate a short descriptive name (max 50 chars) for this data analysis conversation:

{messages_text}

Name:"""

        name = await llm_service.generate(prompt, max_tokens=20)
        name = name.strip().strip('"').strip("'")

        # Update session
        session.name = name
        session.updated_at = datetime.utcnow()
        db.commit()

        return ChatNameResponse(name=name)

    except Exception as e:
        # Fallback to generic name
        return ChatNameResponse(name=f"Chat {session.created_at.strftime('%Y-%m-%d')}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Soft delete a session

    Marks session as deleted (soft delete)
    """
    session = db.query(AgentSession).filter(
        AgentSession.id == session_id,
        AgentSession.deleted_at.is_(None)
    ).first()

    if not session:
        raise HTTPException(404, "Session not found")

    session.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Session deleted successfully"}


@router.get("/sessions")
async def list_sessions(
    dataset_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List agent sessions

    Optionally filter by dataset_id
    """
    query = db.query(AgentSession).filter(
        AgentSession.deleted_at.is_(None)
    )

    if dataset_id:
        query = query.filter(AgentSession.dataset_id == dataset_id)

    sessions = query.order_by(
        AgentSession.updated_at.desc()
    ).limit(limit).all()

    return {
        "sessions": [
            {
                "id": s.id,
                "dataset_id": s.dataset_id,
                "name": s.name,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            }
            for s in sessions
        ]
    }
