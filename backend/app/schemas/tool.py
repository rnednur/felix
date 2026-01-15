"""
Tool schemas for the agent-native tool system
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from enum import Enum


class ToolParameterType(str, Enum):
    """Types of tool parameters"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class ToolSchema(BaseModel):
    """Schema defining a tool's interface"""
    name: str
    description: str
    category: str  # e.g., "data_access", "computation", "visualization", "ml"
    parameters: List[ToolParameter]
    returns: Dict[str, Any]  # JSON schema for return value
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    is_destructive: bool = False
    estimated_duration_ms: int = 1000


class ToolInvocation(BaseModel):
    """A specific invocation of a tool"""
    tool_name: str
    parameters: Dict[str, Any]
    invoked_by: str  # agent name or user ID
    invoked_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "approved", "running", "success", "failed"] = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


class ToolResult(BaseModel):
    """Result from a tool execution"""
    tool_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int = 0


class ToolCapability(BaseModel):
    """Description of what a tool can do"""
    name: str
    description: str
    use_cases: List[str]
    limitations: List[str] = Field(default_factory=list)


class ToolCatalogEntry(BaseModel):
    """Entry in the tool catalog"""
    schema: ToolSchema
    capability: ToolCapability
    enabled: bool = True
    access_level: str = "public"  # public, premium, admin
    rate_limit_per_minute: Optional[int] = None
    cost_credits: int = 1  # Cost in credits per invocation


class ToolDiscoveryRequest(BaseModel):
    """Request for tool discovery"""
    task_description: str
    required_capabilities: List[str] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = None


class ToolDiscoveryResponse(BaseModel):
    """Response with discovered tools"""
    tools: List[ToolCatalogEntry]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
