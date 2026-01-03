"""
Agent Orchestrator - coordinates multi-agent execution
"""
import json
import asyncio
from typing import AsyncIterator, Union, List, Dict, Any
from datetime import datetime
from app.schemas.agent import (
    AgentRequest, AgentResponse, AgentContext,
    ExecutionPlan, StreamChunk, Message
)
from app.services.agents.agent_registry import AgentRegistry
from app.services.agents.llm_service import LLMService
from app.services.agents.context_manager import ContextManager


class AgentOrchestrator:
    """Orchestrates multi-agent collaboration"""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        llm_service: LLMService,
        context_manager: ContextManager
    ):
        self.agent_registry = agent_registry
        self.llm_service = llm_service
        self.context_manager = context_manager

    async def process_query(
        self,
        query: str,
        dataset_id: str,
        session_id: str,
        user_id: str = None,
        stream: bool = False
    ) -> Union[AgentResponse, AsyncIterator[StreamChunk]]:
        """
        Process user query with intelligent agent selection

        Steps:
        1. Get or create session context
        2. Analyze intent and select agent(s)
        3. Create execution plan
        4. Execute (single or multi-agent)
        5. Return/stream results

        Args:
            query: User query
            dataset_id: Dataset ID
            session_id: Session ID
            user_id: User ID (optional)
            stream: Whether to stream response

        Returns:
            AgentResponse or async iterator of StreamChunks
        """
        # Get or create session context
        context = await self.context_manager.get_context(session_id, dataset_id, user_id)

        # Add user message to history
        await self.context_manager.add_message(session_id, Message(
            role="user",
            content=query,
            timestamp=datetime.utcnow()
        ))

        # Detect intent and select agents
        plan = await self.create_execution_plan(query, context)

        if stream:
            return self.execute_plan_streaming(plan, context)
        else:
            return await self.execute_plan(plan, context)

    async def create_execution_plan(self, query: str, context: AgentContext) -> ExecutionPlan:
        """
        Create execution plan by analyzing query and selecting agents

        Uses a hybrid approach:
        1. Try quick keyword matching first (fast path)
        2. Fall back to LLM for complex queries

        Args:
            query: User query
            context: Agent context

        Returns:
            ExecutionPlan
        """
        # Fast path: Try keyword-based agent selection
        candidates = self.agent_registry.find_agents_for_task(query, context.dataset_id)

        if candidates and candidates[0][1] > 0.7:
            # High confidence match - use fast path
            agent, confidence = candidates[0]
            return ExecutionPlan(
                query=query,
                agents=[agent.config.name],
                execution_mode='single',
                dependencies={},
                estimated_duration=30,
                reasoning=f"High confidence match ({confidence:.2f}) with {agent.config.display_name}"
            )

        # Slow path: Use LLM for plan generation
        return await self.create_llm_execution_plan(query, context)

    async def create_llm_execution_plan(self, query: str, context: AgentContext) -> ExecutionPlan:
        """
        Create execution plan using LLM

        Args:
            query: User query
            context: Agent context

        Returns:
            ExecutionPlan
        """
        # Get available agents
        agents_info = {
            agent.config.name: {
                'display_name': agent.config.display_name,
                'capabilities': agent.get_capabilities(),
                'description': agent.config.description
            }
            for agent in self.agent_registry.get_enabled_agents()
        }

        # Format recent conversation for context
        recent_messages = context.conversation_history[-3:] if context.conversation_history else []
        conversation_context = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in recent_messages
        ])

        # Build planning prompt
        prompt = f"""Analyze the following data analysis query and create an execution plan.

Query: {query}

Available agents:
{json.dumps(agents_info, indent=2)}

Recent conversation context:
{conversation_context if conversation_context else "No previous conversation"}

Create a JSON execution plan with this structure:
{{
  "query": "original query",
  "agents": ["agent_name1", "agent_name2"],
  "execution_mode": "single|sequential|parallel",
  "dependencies": {{"agent2": ["agent1"]}},
  "estimated_duration": 30,
  "reasoning": "Why these agents were selected"
}}

Rules:
1. Use 'single' mode if only one agent is needed
2. Use 'sequential' if agents must run in order (one depends on another's output)
3. Use 'parallel' if agents can run independently
4. Select the minimum number of agents needed
5. Consider conversation context for better agent selection
6. For simple queries, prefer single agent execution

Execution Plan (JSON only):"""

        try:
            # Call LLM
            response = await self.llm_service.generate(
                prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=500
            )

            # Parse response
            plan_data = json.loads(response)
            return ExecutionPlan.from_json(plan_data)

        except Exception as e:
            # Fallback: Use best keyword match
            candidates = self.agent_registry.find_agents_for_task(query, context.dataset_id)

            if candidates:
                agent, _ = candidates[0]
                return ExecutionPlan(
                    query=query,
                    agents=[agent.config.name],
                    execution_mode='single',
                    dependencies={},
                    estimated_duration=30,
                    reasoning=f"Fallback to keyword matching (LLM failed: {str(e)})"
                )
            else:
                # No agents found - return empty plan
                return ExecutionPlan(
                    query=query,
                    agents=[],
                    execution_mode='single',
                    dependencies={},
                    estimated_duration=0,
                    reasoning="No suitable agents found"
                )

    async def execute_plan(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """
        Execute plan (non-streaming)

        Args:
            plan: Execution plan
            context: Agent context

        Returns:
            AgentResponse
        """
        if not plan.agents:
            return AgentResponse(
                agent_name="orchestrator",
                success=False,
                data={},
                error="No agents available to handle this query"
            )

        if plan.execution_mode == 'single':
            return await self.execute_single_agent(plan, context)
        elif plan.execution_mode == 'sequential':
            return await self.execute_sequential(plan, context)
        else:  # parallel
            return await self.execute_parallel(plan, context)

    async def execute_single_agent(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute single agent"""
        agent_name = plan.agents[0]
        agent = self.agent_registry.get_agent(agent_name)

        if not agent:
            return AgentResponse(
                agent_name="orchestrator",
                success=False,
                data={},
                error=f"Agent '{agent_name}' not found"
            )

        request = AgentRequest(
            query=plan.query,
            dataset_id=context.dataset_id,
            task_type="analysis"
        )

        try:
            response = await agent.process(request, context)

            # Save to context
            await self.context_manager.update_intermediate_results(
                context.session_id,
                agent_name,
                response.data
            )

            return response

        except Exception as e:
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                data={},
                error=f"Agent execution failed: {str(e)}"
            )

    async def execute_sequential(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute agents sequentially, passing outputs"""
        results = []
        combined_data = {}

        for agent_name in plan.agents:
            agent = self.agent_registry.get_agent(agent_name)

            if not agent:
                continue

            # Build request
            request = AgentRequest(
                query=plan.query,
                dataset_id=context.dataset_id,
                task_type="analysis"
            )

            try:
                # Execute agent
                response = await agent.process(request, context)
                results.append(response)

                # Store result in context for next agent
                await self.context_manager.update_intermediate_results(
                    context.session_id,
                    agent_name,
                    response.data
                )

                # Combine data
                combined_data[agent_name] = response.data

            except Exception as e:
                # Log error but continue
                results.append(AgentResponse(
                    agent_name=agent_name,
                    success=False,
                    data={},
                    error=str(e)
                ))

        # Combine results
        return self.combine_results(results, plan.query, combined_data)

    async def execute_parallel(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute agents in parallel"""
        tasks = []

        for agent_name in plan.agents:
            agent = self.agent_registry.get_agent(agent_name)

            if agent:
                request = AgentRequest(
                    query=plan.query,
                    dataset_id=context.dataset_id,
                    task_type="analysis"
                )
                tasks.append(agent.process(request, context))

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error responses
        processed_results = []
        combined_data = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResponse(
                    agent_name=plan.agents[i],
                    success=False,
                    data={},
                    error=str(result)
                ))
            else:
                processed_results.append(result)
                combined_data[plan.agents[i]] = result.data

        # Combine results
        return self.combine_results(processed_results, plan.query, combined_data)

    async def execute_plan_streaming(
        self,
        plan: ExecutionPlan,
        context: AgentContext
    ) -> AsyncIterator[StreamChunk]:
        """
        Execute plan with streaming progress updates

        Args:
            plan: Execution plan
            context: Agent context

        Yields:
            StreamChunks
        """
        # Yield initial plan
        yield StreamChunk(
            type="plan",
            data={
                "agents": plan.agents,
                "execution_mode": plan.execution_mode,
                "estimated_duration": plan.estimated_duration,
                "reasoning": plan.reasoning
            }
        )

        if not plan.agents:
            yield StreamChunk(
                type="error",
                data={
                    "error": "No agents available to handle this query"
                }
            )
            return

        # Execute agents and stream progress
        for i, agent_name in enumerate(plan.agents):
            # Agent start
            yield StreamChunk(
                type="agent_start",
                data={
                    "agent": agent_name,
                    "step": i + 1,
                    "total_steps": len(plan.agents)
                }
            )

            # Execute agent
            agent = self.agent_registry.get_agent(agent_name)

            if not agent:
                yield StreamChunk(
                    type="agent_error",
                    data={
                        "agent": agent_name,
                        "error": f"Agent '{agent_name}' not found"
                    }
                )
                continue

            request = AgentRequest(
                query=plan.query,
                dataset_id=context.dataset_id,
                task_type="analysis"
            )

            try:
                response = await agent.process(request, context)

                # Agent success
                yield StreamChunk(
                    type="agent_result",
                    data={
                        "agent": agent_name,
                        "success": True,
                        "result": response.data,
                        "code": response.code
                    }
                )

                # Store in context
                await self.context_manager.update_intermediate_results(
                    context.session_id,
                    agent_name,
                    response.data
                )

            except Exception as e:
                # Agent error
                yield StreamChunk(
                    type="agent_error",
                    data={
                        "agent": agent_name,
                        "error": str(e)
                    }
                )

        # Final summary
        final_context = await self.context_manager.get_context(context.session_id, context.dataset_id)

        yield StreamChunk(
            type="complete",
            data={
                "summary": self.generate_summary(final_context.intermediate_results),
                "results": final_context.intermediate_results
            }
        )

    def combine_results(
        self,
        results: List[AgentResponse],
        query: str,
        combined_data: Dict[str, Any]
    ) -> AgentResponse:
        """
        Combine multiple agent results into single response

        Args:
            results: List of agent responses
            query: Original query
            combined_data: Combined data from all agents

        Returns:
            Combined AgentResponse
        """
        success = all(r.success for r in results)
        errors = [r.error for r in results if r.error]

        # Generate summary
        agent_names = [r.agent_name for r in results]
        summary = f"Executed {len(results)} agents: {', '.join(agent_names)}"

        if errors:
            summary += f". Errors: {'; '.join(errors)}"

        return AgentResponse(
            agent_name="multi_agent",
            success=success,
            data={
                "summary": summary,
                "query": query,
                "agent_results": combined_data,
                "agents_executed": agent_names
            },
            metadata={
                "execution_mode": "multi_agent",
                "agent_count": len(results),
                "success_count": sum(1 for r in results if r.success),
                "error_count": len(errors)
            },
            error="; ".join(errors) if errors else None
        )

    def generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate summary from intermediate results"""
        if not results:
            return "No results available"

        summaries = []
        for agent_name, data in results.items():
            if isinstance(data, dict) and 'summary' in data:
                summaries.append(f"{agent_name}: {data['summary']}")
            else:
                summaries.append(f"{agent_name}: Completed")

        return "\n".join(summaries)
