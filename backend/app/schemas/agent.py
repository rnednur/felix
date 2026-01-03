"""
Agent schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    name: str
    display_name: str
    description: str
    tier: str = "free"
    enabled: bool = True
    capabilities: List[str]
    libraries: List[str]
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    prompts: Dict[str, str] = Field(default_factory=dict)
    intent_keywords: List[str] = Field(default_factory=list)
    service_integration: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentConfig':
        """Create AgentConfig from dictionary"""
        return cls(**data)


class AgentRequest(BaseModel):
    """Request to an agent"""
    query: str
    dataset_id: str
    task_type: str = "analysis"
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response from an agent"""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request"""
    query: str
    dataset_id: str
    agent_name: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response"""
    session_id: str
    agent: str
    response: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeepAnalysisRequest(BaseModel):
    """Deep analysis request"""
    dataset_id: str
    goal: str
    include_ml: bool = True
    include_visualizations: bool = True


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str  # 'plan', 'agent_start', 'agent_result', 'agent_error', 'complete'
    data: Dict[str, Any]


class ExecutionPlan(BaseModel):
    """Execution plan for agents"""
    query: str
    agents: List[str]  # Agent names
    execution_mode: str  # 'single', 'sequential', 'parallel'
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    estimated_duration: int = 60  # seconds
    reasoning: Optional[str] = None

    @classmethod
    def from_json(cls, data: dict) -> 'ExecutionPlan':
        """Parse execution plan from LLM JSON response"""
        return cls(
            query=data.get('query', ''),
            agents=data.get('agents', []),
            execution_mode=data.get('execution_mode', 'single'),
            dependencies=data.get('dependencies', {}),
            estimated_duration=data.get('estimated_duration', 60),
            reasoning=data.get('reasoning')
        )


class AgentListResponse(BaseModel):
    """List of available agents"""
    agents: List[Dict[str, Any]]


class Message(BaseModel):
    """Chat message"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class AgentContext(BaseModel):
    """Context for agent execution"""
    session_id: str
    dataset_id: str
    user_id: Optional[str] = None
    conversation_history: List[Message] = Field(default_factory=list)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> 'AgentContext':
        """Create from JSON string"""
        return cls.model_validate_json(data)


class ChatNameRequest(BaseModel):
    """Request to generate chat name"""
    session_id: str


class ChatNameResponse(BaseModel):
    """Response with chat name"""
    name: str
