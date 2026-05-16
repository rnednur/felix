"""
Agent loop schemas for explicit reasoning cycles
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime


class Observation(BaseModel):
    """What the agent observes from the environment"""
    type: Literal["user_query", "tool_result", "context_update", "error"]
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Thought(BaseModel):
    """Agent's internal reasoning"""
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives_considered: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Action(BaseModel):
    """Agent's proposed action"""
    type: Literal["tool_call", "ask_user", "respond", "delegate"]
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: str
    requires_approval: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Reflection(BaseModel):
    """Agent's reflection on action result"""
    success: bool
    learned: str  # What the agent learned from this iteration
    next_steps: List[str] = Field(default_factory=list)
    should_continue: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LoopIteration(BaseModel):
    """A single iteration of the agent loop"""
    iteration_number: int
    observation: Observation
    thought: Thought
    action: Action
    action_result: Optional[Dict[str, Any]] = None
    reflection: Optional[Reflection] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class LoopState(BaseModel):
    """State of an agent loop"""
    session_id: str
    agent_name: str
    goal: str
    status: Literal["initializing", "running", "paused", "completed", "failed"] = "initializing"
    iterations: List[LoopIteration] = Field(default_factory=list)
    max_iterations: int = 10
    current_iteration: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_iteration(self, iteration: LoopIteration):
        """Add an iteration to the loop"""
        self.iterations.append(iteration)
        self.current_iteration = len(self.iterations)
        self.updated_at = datetime.utcnow()

    def should_continue(self) -> bool:
        """Check if the loop should continue"""
        if self.status in ["completed", "failed"]:
            return False
        if self.current_iteration >= self.max_iterations:
            return False
        if self.iterations and self.iterations[-1].reflection:
            return self.iterations[-1].reflection.should_continue
        return True

    def get_latest_iteration(self) -> Optional[LoopIteration]:
        """Get the most recent iteration"""
        return self.iterations[-1] if self.iterations else None


class LoopStreamChunk(BaseModel):
    """Streaming chunk for loop progress"""
    type: Literal[
        "loop_start",
        "iteration_start",
        "observation",
        "thought",
        "action_proposed",
        "action_approved",
        "action_executing",
        "action_result",
        "reflection",
        "iteration_complete",
        "loop_complete",
        "loop_failed"
    ]
    session_id: str
    iteration_number: int
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LoopConfig(BaseModel):
    """Configuration for agent loop behavior"""
    max_iterations: int = 10
    require_approval_for_destructive_actions: bool = True
    enable_reflection: bool = True
    verbose_reasoning: bool = True
    timeout_per_iteration_seconds: int = 60
    save_checkpoints: bool = True
