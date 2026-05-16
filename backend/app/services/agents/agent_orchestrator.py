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
        import logging
        logger = logging.getLogger("orchestrator")

        logger.info(f"🎯 ORCHESTRATOR.process_query: query='{query}', dataset_id={dataset_id}, session_id={session_id}")

        # Get or create session context
        logger.info(f"📦 Getting context for session {session_id}...")
        context = await self.context_manager.get_context(session_id, dataset_id, user_id)
        logger.info(f"✅ Got context with {len(context.conversation_history)} history messages")

        # Add user message to history
        await self.context_manager.add_message(session_id, Message(
            role="user",
            content=query,
            timestamp=datetime.utcnow()
        ))
        logger.info(f"💬 Added user message to history")

        # Detect intent and select agents
        logger.info(f"🧠 Creating execution plan...")
        plan = await self.create_execution_plan(query, context)
        logger.info(f"📋 Plan created: mode={plan.execution_mode}, agents={plan.agents}, reasoning='{plan.reasoning}'")

        if stream:
            logger.info(f"📡 Executing plan with streaming")
            return self.execute_plan_streaming(plan, context)
        else:
            logger.info(f"⚡ Executing plan without streaming")
            result = await self.execute_plan(plan, context)
            logger.info(f"✅ Plan execution complete: success={result.success}, agent={result.agent_name}")
            return result

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
        import logging
        logger = logging.getLogger("orchestrator.plan")

        # Fast path: Try keyword-based agent selection
        logger.info(f"🔍 Finding agents for task: '{query}'")
        candidates = self.agent_registry.find_agents_for_task(query, context.dataset_id)
        logger.info(f"📊 Found {len(candidates)} candidate agents")

        for agent, confidence in candidates[:3]:
            logger.info(f"  - {agent.config.name} ({agent.config.display_name}): {confidence:.2f}")

        if candidates and candidates[0][1] > 0.7:
            # High confidence match - use fast path
            agent, confidence = candidates[0]
            logger.info(f"✅ Fast path: Using {agent.config.name} with confidence {confidence:.2f}")
            return ExecutionPlan(
                query=query,
                agents=[agent.config.name],
                execution_mode='single',
                dependencies={},
                estimated_duration=30,
                reasoning=f"High confidence match ({confidence:.2f}) with {agent.config.display_name}"
            )

        # Slow path: Use LLM for plan generation
        logger.info(f"🤔 Low confidence, using LLM for plan generation")
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
        import logging
        logger = logging.getLogger("orchestrator.llm_plan")

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
7. For queries asking to "analyze" or "summarize" data, use query_agent to retrieve data first

Execution Plan (JSON only):"""

        try:
            logger.info("🤖 Calling LLM for plan generation...")
            # Call LLM
            response = await self.llm_service.generate(
                prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=500
            )
            logger.info(f"✅ LLM response received: {response[:200]}...")

            # Parse response
            plan_data = json.loads(response)
            logger.info(f"📋 Parsed plan: agents={plan_data.get('agents')}, mode={plan_data.get('execution_mode')}")

            plan = ExecutionPlan.from_json(plan_data)

            # If LLM returns empty agents list, try fallback
            if not plan.agents:
                logger.warning("⚠️  LLM returned empty agents list, trying fallback")
                raise ValueError("LLM returned empty agents list")

            return plan

        except Exception as e:
            logger.error(f"❌ LLM plan generation failed: {str(e)}")

            # Fallback: Use best keyword match
            candidates = self.agent_registry.find_agents_for_task(query, context.dataset_id)
            logger.info(f"🔄 Fallback to keyword matching: found {len(candidates)} candidates")

            if candidates:
                agent, confidence = candidates[0]
                logger.info(f"✅ Using fallback agent: {agent.config.name} (confidence: {confidence:.2f})")
                return ExecutionPlan(
                    query=query,
                    agents=[agent.config.name],
                    execution_mode='single',
                    dependencies={},
                    estimated_duration=30,
                    reasoning=f"Fallback to keyword matching (LLM failed: {str(e)})"
                )
            else:
                # Last resort: Use query_agent as default for any data analysis task
                logger.warning("⚠️  No keyword matches found, defaulting to query_agent")
                return ExecutionPlan(
                    query=query,
                    agents=['query_agent'],
                    execution_mode='single',
                    dependencies={},
                    estimated_duration=30,
                    reasoning="Default fallback to query_agent for data analysis"
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
        import logging
        logger = logging.getLogger("orchestrator.execute")

        agent_name = plan.agents[0]
        logger.info(f"🎯 Executing single agent: {agent_name}")

        agent = self.agent_registry.get_agent(agent_name)

        if not agent:
            logger.error(f"❌ Agent not found in registry: {agent_name}")
            logger.info(f"Available agents: {list(self.agent_registry.agents.keys())}")
            return AgentResponse(
                agent_name="orchestrator",
                success=False,
                data={},
                error=f"Agent '{agent_name}' not found"
            )

        logger.info(f"✅ Found agent: {agent.config.display_name}")

        request = AgentRequest(
            query=plan.query,
            dataset_id=context.dataset_id,
            task_type="analysis"
        )

        logger.info(f"📦 Request: query='{request.query}', dataset_id={request.dataset_id}")

        try:
            logger.info(f"🚀 Calling agent.process()...")
            response = await agent.process(request, context)
            logger.info(f"✅ Agent completed: success={response.success}, has_code={response.code is not None}")

            # Save to context
            await self.context_manager.update_intermediate_results(
                context.session_id,
                agent_name,
                response.data
            )
            logger.info(f"💾 Saved results to context")

            return response

        except Exception as e:
            logger.error(f"❌ Agent execution failed: {str(e)}", exc_info=True)
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

        # Build detailed summaries from each agent
        agent_summaries = []
        for agent_name, data in combined_data.items():
            if isinstance(data, dict) and 'summary' in data:
                agent_summaries.append(f"**{agent_name}**: {data['summary']}")

        summary_text = "\n".join(agent_summaries) if agent_summaries else f"Executed {len(results)} agents: {', '.join(agent_names)}"

        if errors:
            summary_text += f"\n\n**Errors**: {'; '.join(errors)}"

        # Flatten agent results for easier frontend display
        flattened_results = []
        for agent_name, data in combined_data.items():
            flattened_results.append({
                "agent": agent_name,
                "success": any(r.agent_name == agent_name and r.success for r in results),
                "data": data
            })

        return AgentResponse(
            agent_name="multi_agent",
            success=success,
            data={
                "summary": summary_text,
                "query": query,
                "results": flattened_results,  # Flattened for easier access
                "agent_results": combined_data,  # Keep original for backwards compatibility
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
