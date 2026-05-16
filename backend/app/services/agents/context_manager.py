"""
Context Manager - manages agent execution context and conversation history
"""
import json
from typing import Optional
from datetime import datetime
from redis import Redis
from app.schemas.agent import AgentContext, Message


class ContextManager:
    """Manages agent execution context"""

    def __init__(self, redis_client: Redis, ttl: int = 3600):
        """
        Initialize context manager

        Args:
            redis_client: Redis client instance
            ttl: Time to live for context (seconds), default 1 hour
        """
        self.redis = redis_client
        self.ttl = ttl

    async def get_context(self, session_id: str, dataset_id: str, user_id: Optional[str] = None) -> AgentContext:
        """
        Get or create context

        Args:
            session_id: Session ID
            dataset_id: Dataset ID
            user_id: User ID (optional)

        Returns:
            AgentContext instance
        """
        key = f"agent_context:{session_id}"
        data = self.redis.get(key)

        if data:
            # Decode bytes to string
            data_str = data.decode('utf-8') if isinstance(data, bytes) else data
            return AgentContext.from_json(data_str)

        # Create new context
        context = AgentContext(
            session_id=session_id,
            dataset_id=dataset_id,
            user_id=user_id,
            conversation_history=[],
            intermediate_results={},
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await self.save_context(context)
        return context

    async def save_context(self, context: AgentContext):
        """
        Save context to Redis

        Args:
            context: AgentContext to save
        """
        context.updated_at = datetime.utcnow()
        key = f"agent_context:{context.session_id}"
        self.redis.setex(key, self.ttl, context.to_json())

    async def add_message(self, session_id: str, message: Message):
        """
        Add message to conversation history

        Args:
            session_id: Session ID
            message: Message to add
        """
        # Get context (will use empty dataset_id since we just need session)
        context = await self.get_context(session_id, "")
        context.conversation_history.append(message)
        context.updated_at = datetime.utcnow()
        await self.save_context(context)

    async def update_intermediate_results(self, session_id: str, agent_name: str, results: dict):
        """
        Update intermediate results from an agent

        Args:
            session_id: Session ID
            agent_name: Name of agent that produced results
            results: Results dictionary
        """
        context = await self.get_context(session_id, "")
        context.intermediate_results[agent_name] = results
        context.updated_at = datetime.utcnow()
        await self.save_context(context)

    async def clear_context(self, session_id: str):
        """
        Clear/delete context

        Args:
            session_id: Session ID to clear
        """
        key = f"agent_context:{session_id}"
        self.redis.delete(key)

    async def extend_ttl(self, session_id: str, additional_seconds: int = 3600):
        """
        Extend TTL for a session

        Args:
            session_id: Session ID
            additional_seconds: Additional seconds to add to TTL
        """
        key = f"agent_context:{session_id}"
        self.redis.expire(key, additional_seconds)

    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> list:
        """
        Get conversation history for a session

        Args:
            session_id: Session ID
            limit: Optional limit on number of messages (most recent)

        Returns:
            List of messages
        """
        key = f"agent_context:{session_id}"
        data = self.redis.get(key)

        if not data:
            return []

        data_str = data.decode('utf-8') if isinstance(data, bytes) else data
        context = AgentContext.from_json(data_str)

        history = context.conversation_history

        if limit:
            return history[-limit:]

        return history
