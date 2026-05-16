"""
Base Agent class - all agents inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext


class BaseAgent(ABC):
    """Base class for all analysis agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"agent.{config.name}")

    @abstractmethod
    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process a request and return response

        Args:
            request: Agent request with query and dataset info
            context: Execution context with conversation history and intermediate results

        Returns:
            AgentResponse with results
        """
        pass

    @abstractmethod
    def can_handle(self, request: AgentRequest) -> float:
        """
        Return confidence score (0.0-1.0) that this agent can handle the request

        Uses keyword matching and query analysis to determine if this agent
        is suitable for the given request.

        Args:
            request: Agent request

        Returns:
            Confidence score (0.0 = cannot handle, 1.0 = perfect match)
        """
        pass

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self.config.capabilities

    def get_prompt_template(self, task: str) -> str:
        """
        Get prompt template for specific task

        Args:
            task: Task type (e.g., 'default', 'missing_values', 'outliers')

        Returns:
            Prompt template string
        """
        return self.config.prompts.get(task, self.config.prompts.get('default', ''))

    def calculate_confidence(self, query: str, keywords: List[str]) -> float:
        """
        Calculate confidence score based on keyword matching

        Args:
            query: User query
            keywords: List of keywords for this agent

        Returns:
            Confidence score between 0.0 and 1.0
        """
        query_lower = query.lower()
        matches = sum(1 for kw in keywords if kw in query_lower)

        if matches == 0:
            return 0.0

        # More matches = higher confidence, but cap at 1.0
        return min(1.0, matches * 0.25)

    def log_execution(self, request: AgentRequest, response: AgentResponse):
        """Log agent execution details"""
        self.logger.info(
            f"Agent executed: {self.config.name}",
            extra={
                'query': request.query,
                'dataset_id': request.dataset_id,
                'success': response.success,
                'error': response.error
            }
        )
