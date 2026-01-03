"""
Agent Registry - manages available agents and their configurations
"""
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from app.schemas.agent import AgentConfig, AgentRequest
from app.services.agents.base_agent import BaseAgent


class AgentRegistry:
    """Registry of available analysis agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent

        Args:
            agent: Agent instance to register
        """
        self.agents[agent.config.name] = agent
        self.agent_configs[agent.config.name] = agent.config

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get agent by name

        Args:
            name: Agent name

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(name)

    def get_all_agents(self) -> List[BaseAgent]:
        """
        Get all registered agents

        Returns:
            List of all agents
        """
        return list(self.agents.values())

    def get_enabled_agents(self) -> List[BaseAgent]:
        """
        Get only enabled agents

        Returns:
            List of enabled agents
        """
        return [
            agent for agent in self.agents.values()
            if agent.config.enabled
        ]

    def find_agents_for_task(self, query: str, dataset_id: str = "") -> List[Tuple[BaseAgent, float]]:
        """
        Find agents that can handle query, sorted by confidence

        Args:
            query: User query
            dataset_id: Dataset ID (optional)

        Returns:
            List of (agent, confidence) tuples, sorted by confidence descending
        """
        candidates = []
        request = AgentRequest(
            query=query,
            dataset_id=dataset_id,
            task_type="analysis"
        )

        for agent in self.get_enabled_agents():
            confidence = agent.can_handle(request)
            if confidence > 0.3:  # Threshold for consideration
                candidates.append((agent, confidence))

        # Sort by confidence descending
        return sorted(candidates, key=lambda x: x[1], reverse=True)

    def load_from_config(self, config_path: str):
        """
        Load agent configurations from JSON file

        Note: This only loads the configs. Actual agent instances
        must be created and registered separately.

        Args:
            config_path: Path to agents_config.json
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Agent config file not found: {config_path}")

        with open(config_file, 'r') as f:
            data = json.load(f)

        configs = data.get('agents', [])

        for config_dict in configs:
            config = AgentConfig.from_dict(config_dict)
            self.agent_configs[config.name] = config

    def get_config(self, name: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by name

        Args:
            name: Agent name

        Returns:
            AgentConfig or None
        """
        return self.agent_configs.get(name)

    def list_agents(self) -> List[Dict]:
        """
        List all agents with their basic info

        Returns:
            List of agent info dicts
        """
        return [
            {
                'name': agent.config.name,
                'display_name': agent.config.display_name,
                'description': agent.config.description,
                'capabilities': agent.get_capabilities(),
                'tier': agent.config.tier,
                'enabled': agent.config.enabled
            }
            for agent in self.agents.values()
        ]

    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return len(self.agents)

    def get_enabled_count(self) -> int:
        """Get number of enabled agents"""
        return len(self.get_enabled_agents())
