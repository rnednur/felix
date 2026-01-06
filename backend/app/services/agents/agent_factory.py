"""
Agent Factory - creates and initializes agents from configuration
"""
from typing import Dict, Optional
from pathlib import Path
from redis import Redis
from app.schemas.agent import AgentConfig
from app.services.agents.base_agent import BaseAgent
from app.services.agents.agent_registry import AgentRegistry
from app.services.agents.llm_service import LLMService
from app.services.agents.context_manager import ContextManager
from app.services.agents.agent_orchestrator import AgentOrchestrator
from app.services.agents.query_agent import QueryAgent
from app.services.agents.data_scouting_agent import DataScoutingAgent
from app.services.agents.visualization_agent import VisualizationAgent
from app.services.agents.statistical_agent import StatisticalAgent
from app.services.agents.ml_agent import MLAgent
from app.services.agents.geospatial_agent import GeospatialAgent


class AgentFactory:
    """
    Factory for creating agent instances

    Maps agent names to their implementation classes
    """

    # Agent class registry
    AGENT_CLASSES: Dict[str, type] = {
        'query_agent': QueryAgent,
        'data_scouting_agent': DataScoutingAgent,
        'visualization_agent': VisualizationAgent,
        'statistical_agent': StatisticalAgent,
        'ml_agent': MLAgent,
        'geospatial_agent': GeospatialAgent,
    }

    @classmethod
    def create_agent(cls, config: AgentConfig) -> Optional[BaseAgent]:
        """
        Create agent instance from configuration

        Args:
            config: Agent configuration

        Returns:
            Agent instance or None if agent type not found
        """
        agent_class = cls.AGENT_CLASSES.get(config.name)

        if not agent_class:
            # Check if this is a service integration agent
            if config.service_integration:
                # For now, return None - these are created differently
                # In the future, we can dynamically create wrappers
                return None

            return None

        # Create agent instance
        return agent_class(config)

    @classmethod
    def register_agent_class(cls, name: str, agent_class: type):
        """
        Register a new agent class

        Allows adding custom agents at runtime

        Args:
            name: Agent name
            agent_class: Agent class (must inherit from BaseAgent)
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class must inherit from BaseAgent")

        cls.AGENT_CLASSES[name] = agent_class


def initialize_agent_system(
    redis_client: Redis,
    config_path: str = "backend/agents_config.json"
) -> tuple[AgentRegistry, AgentOrchestrator, ContextManager]:
    """
    Initialize the complete agent system

    Args:
        redis_client: Redis client for context management
        config_path: Path to agents configuration file

    Returns:
        Tuple of (AgentRegistry, AgentOrchestrator, ContextManager)
    """
    # Create core services
    llm_service = LLMService()
    context_manager = ContextManager(redis_client)
    agent_registry = AgentRegistry()

    # Load agent configurations
    config_file = Path(config_path)
    if config_file.exists():
        agent_registry.load_from_config(str(config_file))

        # Create and register agent instances
        for config_name, config in agent_registry.agent_configs.items():
            if not config.enabled:
                continue

            # Create agent using factory
            agent = AgentFactory.create_agent(config)

            if agent:
                agent_registry.register_agent(agent)
            else:
                print(f"Warning: Could not create agent '{config_name}'")

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agent_registry=agent_registry,
        llm_service=llm_service,
        context_manager=context_manager
    )

    return agent_registry, orchestrator, context_manager


# Global agent system instances (initialized on app startup)
_agent_registry: Optional[AgentRegistry] = None
_agent_orchestrator: Optional[AgentOrchestrator] = None
_context_manager: Optional[ContextManager] = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance"""
    if _agent_registry is None:
        raise RuntimeError("Agent system not initialized. Call setup_agent_system() first.")
    return _agent_registry


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get global agent orchestrator instance"""
    if _agent_orchestrator is None:
        raise RuntimeError("Agent system not initialized. Call setup_agent_system() first.")
    return _agent_orchestrator


def get_context_manager() -> ContextManager:
    """Get global context manager instance"""
    if _context_manager is None:
        raise RuntimeError("Agent system not initialized. Call setup_agent_system() first.")
    return _context_manager


def setup_agent_system(redis_client: Redis, config_path: str = "backend/agents_config.json"):
    """
    Setup global agent system instances

    Should be called during application startup

    Args:
        redis_client: Redis client
        config_path: Path to agent configuration file
    """
    global _agent_registry, _agent_orchestrator, _context_manager

    _agent_registry, _agent_orchestrator, _context_manager = initialize_agent_system(
        redis_client,
        config_path
    )

    print(f"✅ Agent system initialized with {_agent_registry.get_enabled_count()} agents")
