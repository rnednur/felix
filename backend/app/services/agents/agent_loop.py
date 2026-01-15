"""
Agent Loop - explicit reasoning cycle implementation

Implements the Observe → Think → Act → Reflect loop for transparent agent behavior.
"""
import asyncio
from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime
import logging

from app.schemas.loop import (
    LoopState,
    LoopIteration,
    Observation,
    Thought,
    Action,
    Reflection,
    LoopStreamChunk,
    LoopConfig
)
from app.schemas.tool import ToolInvocation
from app.services.agents.llm_service import LLMService
from app.tools.tool_router import ToolRouter
from app.tools.catalog import ToolCatalog
from app.skills.catalog import get_skill_catalog
from app.skills.context_builder import get_context_builder
from app.schemas.skill import SkillDiscoveryRequest, SkillScope
import json


class AgentLoop:
    """
    Explicit agent reasoning loop

    This implements a transparent, observable agent loop:
    1. Observe: What's the current state?
    2. Think: What should I do next?
    3. Act: Execute the action
    4. Reflect: Did it work? What did I learn?

    The loop continues until:
    - Goal is achieved
    - Max iterations reached
    - Agent decides to stop
    - Error occurs
    """

    def __init__(
        self,
        llm_service: LLMService,
        tool_router: ToolRouter,
        tool_catalog: ToolCatalog,
        config: Optional[LoopConfig] = None,
        enable_skills: bool = True
    ):
        self.llm_service = llm_service
        self.tool_router = tool_router
        self.tool_catalog = tool_catalog
        self.config = config or LoopConfig()
        self.enable_skills = enable_skills
        self.skill_catalog = get_skill_catalog() if enable_skills else None
        self.context_builder = get_context_builder() if enable_skills else None
        self.logger = logging.getLogger("agent.loop")

    async def run(
        self,
        session_id: str,
        agent_name: str,
        goal: str,
        context: Dict[str, Any],
        stream: bool = False
    ) -> LoopState:
        """
        Run the agent loop to completion

        Args:
            session_id: Session ID
            agent_name: Name of the agent running the loop
            goal: The goal to achieve
            context: Execution context (dataset_id, previous results, etc.)
            stream: Whether to stream progress

        Returns:
            LoopState with complete execution history
        """
        # Initialize loop state
        state = LoopState(
            session_id=session_id,
            agent_name=agent_name,
            goal=goal,
            status="running",
            max_iterations=self.config.max_iterations,
            metadata=context
        )

        self.logger.info(f"Starting agent loop: {goal}")

        # Initial observation
        initial_obs = Observation(
            type="user_query",
            content=goal,
            metadata=context
        )

        # Run loop
        while state.should_continue():
            iteration_start = datetime.utcnow()

            try:
                # Create iteration
                iteration = LoopIteration(
                    iteration_number=state.current_iteration + 1,
                    observation=initial_obs if state.current_iteration == 0 else self._observe(state, context),
                    thought=await self._think(state, context),
                    action=Action(type="respond", rationale="Not set yet"),  # Will be set by think
                    started_at=iteration_start
                )

                # Get action from thought
                iteration.action = await self._plan_action(state, iteration.thought, context)

                # Execute action
                iteration.action_result = await self._act(iteration.action, context)

                # Reflect on result
                if self.config.enable_reflection:
                    iteration.reflection = await self._reflect(
                        state,
                        iteration.action,
                        iteration.action_result
                    )

                # Mark iteration complete
                iteration.completed_at = datetime.utcnow()
                iteration.duration_ms = int(
                    (iteration.completed_at - iteration.started_at).total_seconds() * 1000
                )

                # Add to state
                state.add_iteration(iteration)

                # Check if we should continue
                if iteration.reflection and not iteration.reflection.should_continue:
                    state.status = "completed"
                    break

            except Exception as e:
                self.logger.error(f"Loop iteration failed: {str(e)}", exc_info=True)
                state.status = "failed"
                state.metadata["error"] = str(e)
                break

        self.logger.info(f"Agent loop completed: {state.current_iteration} iterations")
        return state

    async def run_streaming(
        self,
        session_id: str,
        agent_name: str,
        goal: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[LoopStreamChunk]:
        """
        Run the agent loop with streaming progress updates

        Args:
            session_id: Session ID
            agent_name: Agent name
            goal: Goal to achieve
            context: Execution context

        Yields:
            LoopStreamChunk events
        """
        # Initialize state
        state = LoopState(
            session_id=session_id,
            agent_name=agent_name,
            goal=goal,
            status="running",
            max_iterations=self.config.max_iterations,
            metadata=context
        )

        # Send loop start event
        yield LoopStreamChunk(
            type="loop_start",
            session_id=session_id,
            iteration_number=0,
            data={
                "goal": goal,
                "agent": agent_name,
                "max_iterations": self.config.max_iterations
            }
        )

        # Initial observation
        initial_obs = Observation(
            type="user_query",
            content=goal,
            metadata=context
        )

        # Run loop
        while state.should_continue():
            iteration_number = state.current_iteration + 1

            # Send iteration start
            yield LoopStreamChunk(
                type="iteration_start",
                session_id=session_id,
                iteration_number=iteration_number,
                data={"iteration": iteration_number}
            )

            try:
                iteration_start = datetime.utcnow()

                # Observe
                observation = initial_obs if state.current_iteration == 0 else self._observe(state, context)
                yield LoopStreamChunk(
                    type="observation",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "observation_type": observation.type,
                        "content": observation.content
                    }
                )

                # Think
                thought = await self._think(state, context)
                yield LoopStreamChunk(
                    type="thought",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "reasoning": thought.reasoning,
                        "confidence": thought.confidence,
                        "alternatives": thought.alternatives_considered
                    }
                )

                # Plan action
                action = await self._plan_action(state, thought, context)
                yield LoopStreamChunk(
                    type="action_proposed",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "action_type": action.type,
                        "tool_name": action.tool_name,
                        "parameters": action.parameters,
                        "rationale": action.rationale,
                        "requires_approval": action.requires_approval
                    }
                )

                # Check if approval needed
                if action.requires_approval and self.config.require_approval_for_destructive_actions:
                    # In a real system, this would wait for user approval
                    # For now, we'll just send an event
                    yield LoopStreamChunk(
                        type="action_approved",
                        session_id=session_id,
                        iteration_number=iteration_number,
                        data={"approved": True}
                    )

                # Execute action
                yield LoopStreamChunk(
                    type="action_executing",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={"tool_name": action.tool_name}
                )

                action_result = await self._act(action, context)

                yield LoopStreamChunk(
                    type="action_result",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "success": action_result.get("success", False),
                        "result": action_result
                    }
                )

                # Reflect
                reflection = await self._reflect(state, action, action_result)
                yield LoopStreamChunk(
                    type="reflection",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "success": reflection.success,
                        "learned": reflection.learned,
                        "next_steps": reflection.next_steps,
                        "should_continue": reflection.should_continue
                    }
                )

                # Create iteration
                iteration = LoopIteration(
                    iteration_number=iteration_number,
                    observation=observation,
                    thought=thought,
                    action=action,
                    action_result=action_result,
                    reflection=reflection,
                    started_at=iteration_start,
                    completed_at=datetime.utcnow()
                )
                iteration.duration_ms = int(
                    (iteration.completed_at - iteration.started_at).total_seconds() * 1000
                )

                state.add_iteration(iteration)

                # Send iteration complete
                yield LoopStreamChunk(
                    type="iteration_complete",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={
                        "duration_ms": iteration.duration_ms,
                        "should_continue": reflection.should_continue
                    }
                )

                # Check if we should continue
                if not reflection.should_continue:
                    state.status = "completed"
                    break

            except Exception as e:
                self.logger.error(f"Loop iteration failed: {str(e)}", exc_info=True)
                yield LoopStreamChunk(
                    type="loop_failed",
                    session_id=session_id,
                    iteration_number=iteration_number,
                    data={"error": str(e)}
                )
                state.status = "failed"
                break

        # Send loop complete
        yield LoopStreamChunk(
            type="loop_complete",
            session_id=session_id,
            iteration_number=state.current_iteration,
            data={
                "status": state.status,
                "total_iterations": state.current_iteration,
                "goal_achieved": state.status == "completed"
            }
        )

    def _observe(self, state: LoopState, context: Dict[str, Any]) -> Observation:
        """
        Observe the current state

        Args:
            state: Current loop state
            context: Execution context

        Returns:
            Observation
        """
        # Get the last action result as our observation
        last_iteration = state.get_latest_iteration()

        if last_iteration and last_iteration.action_result:
            return Observation(
                type="tool_result",
                content=last_iteration.action_result,
                metadata={"from_tool": last_iteration.action.tool_name}
            )

        # Fallback to context observation
        return Observation(
            type="context_update",
            content=context,
            metadata={}
        )

    async def _discover_relevant_skills(self, goal: str, context: Dict[str, Any]) -> str:
        """
        Discover and format relevant skills for the current goal

        Args:
            goal: Current goal/task
            context: Execution context

        Returns:
            Formatted skill context string (empty if skills disabled or none found)
        """
        if not self.enable_skills or not self.skill_catalog:
            return ""

        try:
            # Discover skills relevant to this goal
            request = SkillDiscoveryRequest(
                task_description=goal,
                scope=SkillScope.TASK  # Task-level skills for specific goals
            )

            response = self.skill_catalog.discover_skills(request)

            if not response.skills:
                self.logger.debug(f"No relevant skills found for: {goal}")
                return ""

            # Build context from top skills (limit to avoid token overflow)
            top_skills = response.skills[:3]  # Top 3 most relevant

            skill_context = self.context_builder.build_context(
                skills=top_skills,
                include_examples=True,
                include_best_practices=True,
                include_warnings=True
            )

            self.logger.info(
                f"Discovered {len(top_skills)} relevant skills: "
                f"{[s.metadata.name for s in top_skills]}"
            )

            return skill_context

        except Exception as e:
            self.logger.warning(f"Skill discovery failed: {str(e)}")
            return ""

    async def _think(self, state: LoopState, context: Dict[str, Any]) -> Thought:
        """
        Agent reasoning step

        Args:
            state: Current loop state
            context: Execution context

        Returns:
            Thought with reasoning
        """
        # Build prompt with context
        history = "\n".join([
            f"Iteration {i.iteration_number}: {i.action.rationale} → {i.reflection.learned if i.reflection else 'N/A'}"
            for i in state.iterations
        ])

        # Discover relevant skills for this goal
        skill_context = await self._discover_relevant_skills(state.goal, context)

        # Build base prompt
        prompt = f"""You are an intelligent data analysis agent. Analyze the situation and plan your next step.

Goal: {state.goal}

Current Iteration: {state.current_iteration + 1} / {state.max_iterations}

Previous Actions:
{history if history else "None - this is the first iteration"}

Current Context:
{json.dumps(context, indent=2)}"""

        # Add skill context if available
        if skill_context:
            prompt += f"""

{skill_context}

When planning your next step, apply relevant skills from above when appropriate."""

        prompt += """

Think through:
1. What have I accomplished so far?
2. What is the next logical step?
3. Are there alternative approaches?
4. How confident am I?

Respond with JSON:
{{
  "reasoning": "Your step-by-step reasoning",
  "confidence": 0.85,
  "alternatives_considered": ["alternative 1", "alternative 2"]
}}

Response (JSON only):"""

        try:
            response = await self.llm_service.generate(
                prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=400
            )

            data = json.loads(response)

            return Thought(
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", 0.5),
                alternatives_considered=data.get("alternatives_considered", [])
            )

        except Exception as e:
            self.logger.error(f"Think step failed: {str(e)}")
            return Thought(
                reasoning=f"Error in thinking: {str(e)}",
                confidence=0.0,
                alternatives_considered=[]
            )

    async def _plan_action(
        self,
        state: LoopState,
        thought: Thought,
        context: Dict[str, Any]
    ) -> Action:
        """
        Plan the next action based on thought

        Args:
            state: Loop state
            thought: Current thought
            context: Context

        Returns:
            Action to execute
        """
        # Route to appropriate tool
        discovery = await self.tool_router.route(
            task_description=f"{state.goal}\n\nReasoning: {thought.reasoning}",
            context=context
        )

        if not discovery.tools:
            # No tools found - respond to user
            return Action(
                type="respond",
                rationale="No suitable tools found, providing explanation",
                requires_approval=False
            )

        # Select first tool
        tool_entry = discovery.tools[0]

        return Action(
            type="tool_call",
            tool_name=tool_entry.schema.name,
            parameters={},  # Will be filled by LLM or agent
            rationale=discovery.reasoning,
            requires_approval=tool_entry.schema.requires_approval
        )

    async def _act(self, action: Action, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action

        Args:
            action: Action to execute
            context: Context

        Returns:
            Action result
        """
        if action.type == "tool_call":
            # Execute tool
            tool = self.tool_catalog.get_tool(action.tool_name)

            if not tool:
                return {
                    "success": False,
                    "error": f"Tool not found: {action.tool_name}"
                }

            # Create invocation
            invocation = ToolInvocation(
                tool_name=action.tool_name,
                parameters={**action.parameters, **context},
                invoked_by="agent_loop"
            )

            # Execute
            result = await tool.invoke(invocation)

            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms
            }

        elif action.type == "respond":
            # Agent wants to respond to user
            return {
                "success": True,
                "type": "response",
                "message": action.rationale
            }

        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action.type}"
            }

    async def _reflect(
        self,
        state: LoopState,
        action: Action,
        result: Dict[str, Any]
    ) -> Reflection:
        """
        Reflect on the action result

        Args:
            state: Loop state
            action: Action that was executed
            result: Action result

        Returns:
            Reflection
        """
        success = result.get("success", False)

        # Simple reflection logic
        if success:
            # Check if goal is achieved
            if result.get("type") == "response" or state.current_iteration >= state.max_iterations - 1:
                return Reflection(
                    success=True,
                    learned="Goal appears to be achieved",
                    next_steps=[],
                    should_continue=False
                )

            return Reflection(
                success=True,
                learned=f"Successfully executed {action.tool_name}",
                next_steps=["Continue with next step"],
                should_continue=True
            )
        else:
            # Failed - might need retry or different approach
            if state.current_iteration >= state.max_iterations - 1:
                return Reflection(
                    success=False,
                    learned=f"Failed: {result.get('error', 'Unknown error')}",
                    next_steps=[],
                    should_continue=False
                )

            return Reflection(
                success=False,
                learned=f"Action failed: {result.get('error', 'Unknown')}. Need different approach.",
                next_steps=["Try alternative tool", "Adjust parameters"],
                should_continue=True
            )
