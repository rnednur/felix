# Multi-Agent Architecture Design Document

**Project:** AI Spreadsheets Platform
**Version:** 1.0
**Date:** January 3, 2026
**Status:** Design Proposal

---

## Executive Summary

This document proposes a comprehensive multi-agent architecture to enhance the AI Spreadsheets platform with specialized, collaborative agents for data analysis. Inspired by Auto-Analyst's agent-based approach but leveraging our existing strengths in geospatial visualization, collaboration, and deep research capabilities.

### Key Goals
1. **Specialized Expertise**: Each agent focuses on specific analytical domains (preprocessing, statistics, ML, visualization)
2. **Intelligent Orchestration**: Dynamic agent selection and collaboration based on user intent
3. **Conversational Interface**: Chat-based interaction for exploratory data analysis
4. **Streaming Progress**: Real-time feedback during long-running analyses
5. **LLM Agnostic**: Pluggable LLM provider architecture (OpenRouter, OpenAI, Anthropic, etc.)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Proposed Architecture](#2-proposed-architecture)
3. [Agent Registry](#3-agent-registry)
4. [Orchestration Layer](#4-orchestration-layer)
5. [API Design](#5-api-design)
6. [Data Models](#6-data-models)
7. [Implementation Phases](#7-implementation-phases)
8. [Migration Strategy](#8-migration-strategy)
9. [Security & Compliance](#9-security--compliance)
10. [Performance Considerations](#10-performance-considerations)

---

## 1. Current State Analysis

### 1.1 Existing Capabilities

Our platform already has strong foundational components:

| Component | Current Implementation | Status |
|-----------|----------------------|--------|
| **Data Profiling** | `ProfilingService` - schema generation, column stats | ✅ Production |
| **Analysis** | `AnalysisService` - dataset descriptions, insights | ✅ Production |
| **NL to SQL** | `NLToSQLService` - natural language to SQL queries | ✅ Production |
| **NL to Python** | `NLToPythonService` - code generation with modes (ML, Stats, Workflow) | ✅ Production |
| **Code Execution** | `CodeExecutorService` - safe Python execution sandbox | ✅ Production |
| **ML Models** | `MLModelService` - model training and persistence | ✅ Production |
| **Workflow Orchestration** | `WorkflowOrchestrator` - multi-step SQL + Python workflows | ✅ Production |
| **Data Scouting** | `DataScoutingService` - LLM-powered pattern detection, PII analysis | ✅ Production |
| **Visualization** | `VisualizationService` + Kepler.gl integration | ✅ Production |
| **Deep Research** | `DeepResearchService` - comprehensive analysis workflows | ✅ Production |

### 1.2 Architecture Strengths

✅ **Strong service layer**: Well-structured service classes with clear responsibilities
✅ **Async support**: FastAPI + async operations for scalability
✅ **Data storage**: DuckDB for efficient querying + PostgreSQL for persistence
✅ **Code safety**: Sandboxed Python execution with timeout controls
✅ **LLM integration**: OpenRouter for model flexibility
✅ **Geospatial capabilities**: Kepler.gl integration (unique advantage)
✅ **Collaboration features**: Dataset sharing, workspaces, permissions

### 1.3 Gaps Identified

❌ **No agent abstraction**: Services are not agent-aware
❌ **No conversational interface**: No chat/dialogue capabilities
❌ **No agent orchestration**: No planner to coordinate multiple services
❌ **No streaming responses**: Long operations block without progress updates
❌ **Limited agent memory**: No context retention across requests
❌ **No agent registry**: No declarative agent configuration
❌ **Monolithic prompts**: LLM prompts scattered across services

---

## 2. Proposed Architecture

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                       │
│  /agents/chat, /agents/list, /agents/deep-analysis-stream       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Agent Orchestration Layer                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         AgentOrchestrator (Planner + Router)             │  │
│  │  - Intent detection                                       │  │
│  │  - Agent selection                                        │  │
│  │  - Multi-agent coordination                               │  │
│  │  - Context management                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        Agent Registry                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Preprocessing│  │ Statistical  │  │  ML Agent    │          │
│  │    Agent     │  │   Agent      │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Visualization │  │  Geospatial  │  │    Query     │          │
│  │    Agent     │  │    Agent     │  │    Agent     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Execution Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   DuckDB     │  │ Code Executor│  │  LLM Service │          │
│  │   Service    │  │   Service    │  │   (OpenRouter)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Storage    │  │  Embedding   │  │ Visualization│          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

#### 2.2.1 BaseAgent (Abstract Class)

All agents inherit from `BaseAgent` which provides:

```python
class BaseAgent(ABC):
    """Base class for all analysis agents"""

    def __init__(self, config: AgentConfig, llm_service: LLMService):
        self.config = config
        self.llm_service = llm_service
        self.logger = logging.getLogger(f"agent.{config.name}")

    @abstractmethod
    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """Process a request and return response"""
        pass

    @abstractmethod
    def can_handle(self, request: AgentRequest) -> float:
        """Return confidence score (0.0-1.0) that this agent can handle the request"""
        pass

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self.config.capabilities

    def get_prompt_template(self, task: str) -> str:
        """Get prompt template for specific task"""
        return self.config.prompts.get(task, self.config.default_prompt)
```

#### 2.2.2 AgentOrchestrator (Planner)

Coordinates multiple agents to solve complex tasks:

```python
class AgentOrchestrator:
    """Orchestrates multi-agent collaboration"""

    def __init__(self, agent_registry: AgentRegistry, llm_service: LLMService):
        self.agent_registry = agent_registry
        self.llm_service = llm_service
        self.context_manager = ContextManager()

    async def process_query(
        self,
        query: str,
        dataset_id: str,
        session_id: str,
        stream: bool = False
    ) -> Union[AgentResponse, AsyncIterator[StreamChunk]]:
        """
        Process user query with intelligent agent selection

        Steps:
        1. Analyze intent
        2. Select agent(s)
        3. Execute (single or multi-agent)
        4. Return/stream results
        """

        # Get or create session context
        context = await self.context_manager.get_context(session_id, dataset_id)

        # Detect intent and select agents
        plan = await self.create_execution_plan(query, context)

        if stream:
            return self.execute_plan_streaming(plan, context)
        else:
            return await self.execute_plan(plan, context)

    async def create_execution_plan(self, query: str, context: AgentContext) -> ExecutionPlan:
        """
        Create execution plan by analyzing query and selecting agents

        Uses LLM to determine:
        - Which agent(s) to use
        - Whether agents should run sequentially or in parallel
        - Dependencies between agent outputs
        """

        # Get all available agents and their capabilities
        available_agents = self.agent_registry.get_all_agents()
        agent_capabilities = {
            agent.config.name: agent.get_capabilities()
            for agent in available_agents
        }

        # Use LLM to create plan
        plan_prompt = self.build_planning_prompt(query, agent_capabilities, context)
        plan_json = await self.llm_service.generate(plan_prompt, response_format="json")

        # Parse into ExecutionPlan
        return ExecutionPlan.from_json(plan_json)
```

#### 2.2.3 Agent Registry

Manages available agents and their configurations:

```python
class AgentRegistry:
    """Registry of available analysis agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}

    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.config.name] = agent
        self.agent_configs[agent.config.name] = agent.config

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self.agents.get(name)

    def find_agents_for_task(self, query: str) -> List[Tuple[BaseAgent, float]]:
        """Find agents that can handle query, sorted by confidence"""
        candidates = []
        request = AgentRequest(query=query, task_type="unknown")

        for agent in self.agents.values():
            confidence = agent.can_handle(request)
            if confidence > 0.3:  # Threshold
                candidates.append((agent, confidence))

        return sorted(candidates, key=lambda x: x[1], reverse=True)

    def load_from_config(self, config_path: str):
        """Load agents from JSON configuration"""
        with open(config_path) as f:
            configs = json.load(f)

        for config_dict in configs:
            config = AgentConfig.from_dict(config_dict)
            agent = self.create_agent_from_config(config)
            self.register_agent(agent)
```

---

## 3. Agent Registry

### 3.1 Core Agents

#### **Agent 1: Preprocessing Agent**

**Purpose**: Data cleaning, transformation, and preparation

**Capabilities**:
- Handle missing values (imputation, deletion, flagging)
- Detect and convert data types
- Parse dates and timestamps
- Remove duplicates
- Handle outliers
- Normalize/standardize numeric columns
- Encode categorical variables

**Technologies**: Pandas, NumPy, scikit-learn preprocessing

**Configuration**:
```json
{
  "name": "preprocessing_agent",
  "display_name": "Data Preprocessing Agent",
  "description": "Cleans and prepares data for analysis",
  "capabilities": [
    "missing_value_handling",
    "type_conversion",
    "outlier_detection",
    "normalization",
    "encoding"
  ],
  "libraries": ["pandas", "numpy", "scikit-learn"],
  "default_model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.2,
  "max_tokens": 2000,
  "prompts": {
    "default": "You are a data preprocessing expert. Clean and prepare the data...",
    "missing_values": "Analyze missing values and suggest imputation strategies...",
    "outliers": "Detect and handle outliers in numeric columns..."
  }
}
```

**Example Service Integration**:
```python
class PreprocessingAgent(BaseAgent):
    """Data preprocessing and cleaning agent"""

    def __init__(self, config: AgentConfig, llm_service: LLMService):
        super().__init__(config, llm_service)
        self.storage_service = StorageService()
        self.code_executor = CodeExecutorService()

    def can_handle(self, request: AgentRequest) -> float:
        """Calculate confidence score"""
        keywords = ['clean', 'preprocess', 'missing', 'null', 'duplicate',
                   'outlier', 'normalize', 'encode', 'transform']

        query_lower = request.query.lower()
        matches = sum(1 for kw in keywords if kw in query_lower)

        return min(1.0, matches * 0.3)

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """Process preprocessing request"""

        # Load data
        df = self.storage_service.load_dataset(request.dataset_id)
        schema = self.storage_service.load_schema(request.dataset_id)

        # Generate preprocessing code using LLM
        prompt = self.build_preprocessing_prompt(request.query, schema, df)
        code = await self.llm_service.generate(prompt)

        # Execute preprocessing code
        result = self.code_executor.execute_python(code, request.dataset_id)

        return AgentResponse(
            agent_name=self.config.name,
            success=result['status'] == 'SUCCESS',
            data=result['output'],
            code=code,
            metadata={'preprocessing_steps': self.extract_steps(code)}
        )
```

---

#### **Agent 2: Statistical Analysis Agent**

**Purpose**: Statistical testing, correlation analysis, distribution analysis

**Capabilities**:
- Descriptive statistics
- Hypothesis testing (t-test, chi-square, ANOVA)
- Correlation analysis (Pearson, Spearman)
- Distribution fitting
- Seasonal decomposition (time series)
- Regression analysis (OLS, WLS)

**Technologies**: scipy, statsmodels, pandas

**Configuration**:
```json
{
  "name": "statistical_agent",
  "display_name": "Statistical Analysis Agent",
  "description": "Performs statistical tests and analysis",
  "capabilities": [
    "hypothesis_testing",
    "correlation_analysis",
    "distribution_analysis",
    "regression_analysis",
    "time_series_decomposition"
  ],
  "libraries": ["scipy", "statsmodels", "pandas", "numpy"],
  "default_model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.2
}
```

---

#### **Agent 3: Machine Learning Agent**

**Purpose**: Predictive modeling, classification, regression, clustering

**Capabilities**:
- Regression (Linear, RandomForest, XGBoost)
- Classification (LogisticRegression, RandomForest, XGBoost)
- Clustering (KMeans, DBSCAN, Hierarchical)
- Feature selection and importance
- Model evaluation (cross-validation, metrics)
- Hyperparameter tuning

**Technologies**: scikit-learn, XGBoost, pandas

**Configuration**:
```json
{
  "name": "ml_agent",
  "display_name": "Machine Learning Agent",
  "description": "Trains and evaluates ML models",
  "capabilities": [
    "regression",
    "classification",
    "clustering",
    "feature_engineering",
    "model_evaluation"
  ],
  "libraries": ["scikit-learn", "xgboost", "pandas", "numpy"],
  "default_model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.3
}
```

---

#### **Agent 4: Visualization Agent**

**Purpose**: Create charts, plots, and interactive visualizations

**Capabilities**:
- Statistical plots (histograms, box plots, scatter plots)
- Interactive visualizations (Plotly)
- Time series plots
- Correlation heatmaps
- Distribution plots
- Geospatial visualizations (integration with existing Kepler.gl service)

**Technologies**: matplotlib, seaborn, plotly, Kepler.gl

**Configuration**:
```json
{
  "name": "visualization_agent",
  "display_name": "Data Visualization Agent",
  "description": "Creates insightful visualizations",
  "capabilities": [
    "statistical_plots",
    "interactive_charts",
    "geospatial_maps",
    "time_series_charts",
    "correlation_heatmaps"
  ],
  "libraries": ["matplotlib", "seaborn", "plotly", "pandas"],
  "default_model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.4
}
```

---

#### **Agent 5: Query Agent** (Existing: NL to SQL)

**Purpose**: Translate natural language to SQL queries

**Capabilities**:
- Natural language to SQL translation
- Query optimization
- Aggregations and grouping
- Joins and filtering
- Window functions

**Technologies**: DuckDB, existing `NLToSQLService`

---

#### **Agent 6: Geospatial Agent** (Unique to Our Platform)

**Purpose**: Geospatial analysis and mapping (leverages our Kepler.gl integration)

**Capabilities**:
- Geocoding and reverse geocoding
- Spatial joins
- Distance calculations
- Clustering by location
- Heatmaps and choropleths
- Interactive Kepler.gl maps

**Technologies**: GeoPandas, Shapely, Kepler.gl, existing `SpatialService`

**Configuration**:
```json
{
  "name": "geospatial_agent",
  "display_name": "Geospatial Analysis Agent",
  "description": "Performs spatial analysis and creates interactive maps",
  "capabilities": [
    "geocoding",
    "spatial_joins",
    "distance_calculations",
    "location_clustering",
    "interactive_maps"
  ],
  "libraries": ["geopandas", "shapely", "pandas"],
  "integration": "kepler_gl",
  "default_model": "anthropic/claude-3.5-sonnet"
}
```

---

#### **Agent 7: Data Scouting Agent** (Existing)

**Purpose**: Intelligent data profiling and quality assessment

**Capabilities**:
- Pattern detection (email, phone, URLs, business IDs)
- PII detection
- Data quality assessment
- Semantic type inference (LLM-powered)
- Metadata validation

**Technologies**: Existing `DataScoutingService`

---

### 3.2 Agent Configuration Schema

**File**: `agents_config.json`

```json
{
  "agents": [
    {
      "name": "preprocessing_agent",
      "display_name": "Data Preprocessing Agent",
      "description": "Cleans and prepares data for analysis",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "missing_value_handling",
        "type_conversion",
        "outlier_detection",
        "normalization",
        "encoding"
      ],
      "libraries": ["pandas", "numpy", "scikit-learn"],
      "llm_config": {
        "default_model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.2,
        "max_tokens": 2000
      },
      "prompts": {
        "default": "prompts/preprocessing/default.txt",
        "missing_values": "prompts/preprocessing/missing_values.txt",
        "outliers": "prompts/preprocessing/outliers.txt"
      },
      "intent_keywords": [
        "clean", "preprocess", "missing", "null", "duplicate",
        "outlier", "normalize", "encode", "transform", "impute"
      ]
    },
    {
      "name": "statistical_agent",
      "display_name": "Statistical Analysis Agent",
      "description": "Performs statistical tests and analysis",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "hypothesis_testing",
        "correlation_analysis",
        "distribution_analysis",
        "regression_analysis",
        "time_series_decomposition"
      ],
      "libraries": ["scipy", "statsmodels", "pandas", "numpy"],
      "llm_config": {
        "default_model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.2,
        "max_tokens": 2500
      },
      "intent_keywords": [
        "correlation", "test", "significance", "p-value", "hypothesis",
        "distribution", "regression", "anova", "chi-square", "t-test"
      ]
    },
    {
      "name": "ml_agent",
      "display_name": "Machine Learning Agent",
      "description": "Trains and evaluates ML models",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "regression",
        "classification",
        "clustering",
        "feature_engineering",
        "model_evaluation"
      ],
      "libraries": ["scikit-learn", "xgboost", "pandas", "numpy"],
      "llm_config": {
        "default_model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.3,
        "max_tokens": 3000
      },
      "intent_keywords": [
        "predict", "model", "forecast", "train", "machine learning",
        "classify", "cluster", "random forest", "xgboost", "accuracy"
      ]
    },
    {
      "name": "visualization_agent",
      "display_name": "Data Visualization Agent",
      "description": "Creates insightful visualizations",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "statistical_plots",
        "interactive_charts",
        "geospatial_maps",
        "time_series_charts",
        "correlation_heatmaps"
      ],
      "libraries": ["matplotlib", "seaborn", "plotly", "pandas"],
      "llm_config": {
        "default_model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.4,
        "max_tokens": 2000
      },
      "intent_keywords": [
        "plot", "chart", "visualize", "graph", "show", "display",
        "histogram", "scatter", "bar chart", "heatmap", "map"
      ]
    },
    {
      "name": "query_agent",
      "display_name": "SQL Query Agent",
      "description": "Translates natural language to SQL queries",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "sql_generation",
        "aggregations",
        "filtering",
        "joins",
        "window_functions"
      ],
      "libraries": ["duckdb"],
      "service_integration": "NLToSQLService",
      "intent_keywords": [
        "select", "filter", "group by", "count", "sum", "average",
        "join", "where", "order by", "top", "limit"
      ]
    },
    {
      "name": "geospatial_agent",
      "display_name": "Geospatial Analysis Agent",
      "description": "Performs spatial analysis and creates interactive maps",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "geocoding",
        "spatial_joins",
        "distance_calculations",
        "location_clustering",
        "interactive_maps"
      ],
      "libraries": ["geopandas", "shapely", "pandas"],
      "service_integration": "SpatialService",
      "llm_config": {
        "default_model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.3,
        "max_tokens": 2000
      },
      "intent_keywords": [
        "map", "location", "latitude", "longitude", "geocode",
        "distance", "spatial", "coordinates", "geography", "proximity"
      ]
    },
    {
      "name": "data_scouting_agent",
      "display_name": "Data Scouting Agent",
      "description": "Profiles data and detects quality issues",
      "tier": "free",
      "enabled": true,
      "capabilities": [
        "pattern_detection",
        "pii_detection",
        "quality_assessment",
        "semantic_typing",
        "metadata_validation"
      ],
      "service_integration": "DataScoutingService",
      "intent_keywords": [
        "profile", "scout", "analyze data", "quality", "pii",
        "patterns", "data types", "metadata", "describe data"
      ]
    }
  ]
}
```

---

## 4. Orchestration Layer

### 4.1 Context Management

```python
@dataclass
class AgentContext:
    """Context shared across agent executions"""
    session_id: str
    dataset_id: str
    user_id: str
    conversation_history: List[Message]
    intermediate_results: Dict[str, Any]  # Shared data between agents
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ContextManager:
    """Manages agent execution context"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    async def get_context(self, session_id: str, dataset_id: str) -> AgentContext:
        """Get or create context"""
        key = f"agent_context:{session_id}"
        data = await self.redis.get(key)

        if data:
            return AgentContext.from_json(data)

        # Create new context
        context = AgentContext(
            session_id=session_id,
            dataset_id=dataset_id,
            conversation_history=[],
            intermediate_results={},
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await self.save_context(context)
        return context

    async def save_context(self, context: AgentContext):
        """Save context to Redis"""
        key = f"agent_context:{context.session_id}"
        await self.redis.setex(key, self.ttl, context.to_json())

    async def add_message(self, session_id: str, message: Message):
        """Add message to conversation history"""
        context = await self.get_context(session_id, "")
        context.conversation_history.append(message)
        context.updated_at = datetime.utcnow()
        await self.save_context(context)
```

### 4.2 Execution Planning

```python
@dataclass
class ExecutionPlan:
    """Plan for executing agent(s)"""
    query: str
    agents: List[str]  # Agent names
    execution_mode: str  # 'single', 'sequential', 'parallel'
    dependencies: Dict[str, List[str]]  # Agent dependencies
    estimated_duration: int  # seconds

    @classmethod
    def from_json(cls, data: dict) -> 'ExecutionPlan':
        """Parse execution plan from LLM JSON response"""
        return cls(
            query=data['query'],
            agents=data['agents'],
            execution_mode=data['execution_mode'],
            dependencies=data.get('dependencies', {}),
            estimated_duration=data.get('estimated_duration', 60)
        )

class AgentOrchestrator:
    """Orchestrates multi-agent execution"""

    async def create_execution_plan(self, query: str, context: AgentContext) -> ExecutionPlan:
        """Create execution plan using LLM"""

        # Get available agents
        agents_info = {
            name: {
                'capabilities': agent.get_capabilities(),
                'description': agent.config.description
            }
            for name, agent in self.agent_registry.agents.items()
        }

        # Build planning prompt
        prompt = f"""Analyze the following data analysis query and create an execution plan.

Query: {query}

Available agents:
{json.dumps(agents_info, indent=2)}

Recent conversation context:
{self.format_conversation_history(context.conversation_history[-3:])}

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

Execution Plan (JSON only):"""

        # Call LLM
        response = await self.llm_service.generate(
            prompt,
            response_format="json",
            temperature=0.2
        )

        return ExecutionPlan.from_json(json.loads(response))

    async def execute_plan(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute plan (non-streaming)"""

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

        request = AgentRequest(
            query=plan.query,
            dataset_id=context.dataset_id,
            task_type="analysis"
        )

        return await agent.process(request, context)

    async def execute_sequential(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute agents sequentially, passing outputs"""

        results = []

        for agent_name in plan.agents:
            agent = self.agent_registry.get_agent(agent_name)

            # Build request with previous results in context
            request = AgentRequest(
                query=plan.query,
                dataset_id=context.dataset_id,
                task_type="analysis"
            )

            # Execute agent
            response = await agent.process(request, context)
            results.append(response)

            # Store result in context for next agent
            context.intermediate_results[agent_name] = response.data

        # Combine results
        return self.combine_results(results, plan.query)

    async def execute_parallel(self, plan: ExecutionPlan, context: AgentContext) -> AgentResponse:
        """Execute agents in parallel"""

        tasks = []
        for agent_name in plan.agents:
            agent = self.agent_registry.get_agent(agent_name)
            request = AgentRequest(
                query=plan.query,
                dataset_id=context.dataset_id,
                task_type="analysis"
            )
            tasks.append(agent.process(request, context))

        # Run in parallel
        results = await asyncio.gather(*tasks)

        # Combine results
        return self.combine_results(results, plan.query)
```

### 4.3 Streaming Support

```python
async def execute_plan_streaming(
    self,
    plan: ExecutionPlan,
    context: AgentContext
) -> AsyncIterator[StreamChunk]:
    """Execute plan with streaming progress updates"""

    # Yield initial plan
    yield StreamChunk(
        type="plan",
        data={
            "agents": plan.agents,
            "execution_mode": plan.execution_mode,
            "estimated_duration": plan.estimated_duration
        }
    )

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
            context.intermediate_results[agent_name] = response.data

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
    yield StreamChunk(
        type="complete",
        data={
            "summary": self.generate_summary(context.intermediate_results),
            "results": context.intermediate_results
        }
    )
```

---

## 5. API Design

### 5.1 New Endpoints

#### **5.1.1 Chat with Agent**

**Endpoint**: `POST /api/v1/agents/chat`

**Purpose**: Interactive chat with a specific agent

```python
@router.post("/agents/chat")
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat with a specific agent or let orchestrator select

    Request:
    {
        "query": "What's the correlation between price and sales?",
        "dataset_id": "uuid",
        "agent_name": "statistical_agent",  # optional
        "session_id": "uuid",  # optional, creates new if not provided
        "stream": false
    }

    Response:
    {
        "session_id": "uuid",
        "agent": "statistical_agent",
        "response": {
            "summary": "Strong positive correlation (r=0.87, p<0.001)",
            "data": {...},
            "visualizations": [...],
            "code": "import pandas as pd..."
        },
        "metadata": {
            "execution_time_ms": 1234,
            "tokens_used": 567
        }
    }
    """
    orchestrator = AgentOrchestrator(agent_registry, llm_service)

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())

    # Process query
    if request.agent_name:
        # Direct agent chat
        agent = agent_registry.get_agent(request.agent_name)
        context = await context_manager.get_context(session_id, request.dataset_id)
        agent_request = AgentRequest(
            query=request.query,
            dataset_id=request.dataset_id,
            task_type="chat"
        )
        response = await agent.process(agent_request, context)
    else:
        # Orchestrated chat (auto-select agent)
        response = await orchestrator.process_query(
            query=request.query,
            dataset_id=request.dataset_id,
            session_id=session_id
        )

    # Save to conversation history
    await context_manager.add_message(session_id, Message(
        role="user",
        content=request.query,
        timestamp=datetime.utcnow()
    ))
    await context_manager.add_message(session_id, Message(
        role="assistant",
        content=response.data['summary'],
        timestamp=datetime.utcnow(),
        metadata={"agent": response.agent_name}
    ))

    return ChatResponse(
        session_id=session_id,
        agent=response.agent_name,
        response=response.data,
        metadata=response.metadata
    )
```

#### **5.1.2 Multi-Agent Chat**

**Endpoint**: `POST /api/v1/agents/chat/multi`

**Purpose**: Collaborative chat with multiple agents

```python
@router.post("/agents/chat/multi")
async def multi_agent_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat that may involve multiple agents collaborating

    Example query: "Clean the data, then run correlation analysis and create visualizations"

    The orchestrator will:
    1. Select multiple agents (preprocessing, statistical, visualization)
    2. Execute them sequentially or in parallel
    3. Combine results
    """
    orchestrator = AgentOrchestrator(agent_registry, llm_service)

    session_id = request.session_id or str(uuid.uuid4())

    response = await orchestrator.process_query(
        query=request.query,
        dataset_id=request.dataset_id,
        session_id=session_id,
        stream=False
    )

    return ChatResponse(
        session_id=session_id,
        agent="multi_agent",
        response=response.data,
        metadata=response.metadata
    )
```

#### **5.1.3 Deep Analysis with Streaming**

**Endpoint**: `POST /api/v1/agents/deep-analysis-stream`

**Purpose**: Long-running comprehensive analysis with real-time progress

```python
@router.post("/agents/deep-analysis-stream")
async def deep_analysis_streaming(
    request: DeepAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Streaming deep analysis (similar to Auto-Analyst's /deep_analysis_streaming)

    Request:
    {
        "dataset_id": "uuid",
        "goal": "Comprehensive analysis to predict customer churn",
        "include_ml": true,
        "include_visualizations": true
    }

    Response: Server-Sent Events (SSE) stream

    Event types:
    - plan: Execution plan
    - agent_start: Agent starting
    - agent_progress: Progress update
    - agent_result: Agent completed
    - agent_error: Agent failed
    - complete: Analysis complete
    """
    orchestrator = AgentOrchestrator(agent_registry, llm_service)

    # Create comprehensive analysis plan
    session_id = str(uuid.uuid4())

    # Build analysis query from goal
    query = f"""Perform comprehensive analysis: {request.goal}

    Steps:
    1. Profile the data and assess quality
    2. Preprocess and clean as needed
    3. Perform exploratory data analysis
    4. {'Train predictive models' if request.include_ml else 'Statistical analysis'}
    5. {'Create visualizations' if request.include_visualizations else ''}
    """

    # Stream execution
    async def event_generator():
        async for chunk in orchestrator.process_query(
            query=query,
            dataset_id=request.dataset_id,
            session_id=session_id,
            stream=True
        ):
            yield {
                "event": chunk.type,
                "data": json.dumps(chunk.data)
            }

    return EventSourceResponse(event_generator())
```

#### **5.1.4 List Agents**

**Endpoint**: `GET /api/v1/agents`

**Purpose**: List available agents

```python
@router.get("/agents")
async def list_agents() -> AgentListResponse:
    """
    List all available agents

    Response:
    {
        "agents": [
            {
                "name": "preprocessing_agent",
                "display_name": "Data Preprocessing Agent",
                "description": "Cleans and prepares data",
                "capabilities": [...],
                "tier": "free",
                "enabled": true
            },
            ...
        ]
    }
    """
    agents = agent_registry.get_all_agents()

    return AgentListResponse(
        agents=[
            {
                "name": agent.config.name,
                "display_name": agent.config.display_name,
                "description": agent.config.description,
                "capabilities": agent.get_capabilities(),
                "tier": agent.config.tier,
                "enabled": agent.config.enabled
            }
            for agent in agents
        ]
    )
```

#### **5.1.5 Download Report**

**Endpoint**: `GET /api/v1/agents/reports/{session_id}`

**Purpose**: Download HTML analysis report

```python
@router.get("/agents/reports/{session_id}")
async def download_report(
    session_id: str,
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Download HTML report for a session

    Similar to Auto-Analyst's /deep_analysis/download_report
    """
    context = await context_manager.get_context(session_id, "")

    # Generate HTML report
    report_service = ReportGeneratorService()
    html = report_service.generate_html_report(
        conversation_history=context.conversation_history,
        results=context.intermediate_results,
        dataset_id=context.dataset_id
    )

    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f"attachment; filename=analysis_report_{session_id}.html"
        }
    )
```

#### **5.1.6 Generate Chat Name**

**Endpoint**: `POST /api/v1/agents/chat-history-name`

**Purpose**: Generate descriptive name for chat session

```python
@router.post("/agents/chat-history-name")
async def generate_chat_name(
    request: ChatNameRequest
) -> ChatNameResponse:
    """
    Generate descriptive name for chat session

    Request:
    {
        "session_id": "uuid"
    }

    Response:
    {
        "name": "Correlation Analysis: Price vs Sales"
    }
    """
    context = await context_manager.get_context(request.session_id, "")

    # Use LLM to generate name from conversation
    messages_text = "\n".join([
        f"{msg.role}: {msg.content}"
        for msg in context.conversation_history[:5]
    ])

    prompt = f"""Generate a short descriptive name (max 50 chars) for this data analysis conversation:

{messages_text}

Name:"""

    name = await llm_service.generate(prompt, max_tokens=20)

    return ChatNameResponse(name=name.strip())
```

---

## 6. Data Models

### 6.1 Database Models

```python
# app/models/agent_session.py

class AgentSession(Base):
    """Agent chat session"""
    __tablename__ = "agent_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    name = Column(String, nullable=True)  # User-friendly name

    # Session metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User")
    dataset = relationship("Dataset")

class AgentMessage(Base):
    """Message in agent conversation"""
    __tablename__ = "agent_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=False)

    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Agent metadata
    agent_name = Column(String, nullable=True)  # Which agent responded
    code = Column(Text, nullable=True)  # Generated code
    result_data = Column(JSON, nullable=True)  # Result data

    # Tokens and cost tracking
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("AgentSession", back_populates="messages")

class AgentExecution(Base):
    """Track agent execution metrics"""
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("agent_sessions.id"))
    agent_name = Column(String, nullable=False)

    # Execution details
    query = Column(Text, nullable=False)
    execution_mode = Column(String)  # 'single', 'sequential', 'parallel'
    status = Column(String)  # 'success', 'failed', 'partial'

    # Performance metrics
    execution_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    cost_usd = Column(Float)

    # Results
    result_summary = Column(Text)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
```

### 6.2 Pydantic Schemas

```python
# app/schemas/agent.py

class AgentRequest(BaseModel):
    query: str
    dataset_id: str
    task_type: str = "analysis"

class AgentResponse(BaseModel):
    agent_name: str
    success: bool
    data: Dict[str, Any]
    code: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    query: str
    dataset_id: str
    agent_name: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    session_id: str
    agent: str
    response: Dict[str, Any]
    metadata: Dict[str, Any]

class DeepAnalysisRequest(BaseModel):
    dataset_id: str
    goal: str
    include_ml: bool = True
    include_visualizations: bool = True

class StreamChunk(BaseModel):
    type: str  # 'plan', 'agent_start', 'agent_result', 'agent_error', 'complete'
    data: Dict[str, Any]

class AgentConfig(BaseModel):
    name: str
    display_name: str
    description: str
    tier: str = "free"
    enabled: bool = True
    capabilities: List[str]
    libraries: List[str]
    llm_config: Dict[str, Any]
    prompts: Dict[str, str] = {}
    intent_keywords: List[str] = []
    service_integration: Optional[str] = None
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals**: Set up core agent infrastructure

**Tasks**:
1. ✅ Create `BaseAgent` abstract class
2. ✅ Implement `AgentRegistry` with JSON config loading
3. ✅ Create `AgentOrchestrator` with basic intent detection
4. ✅ Implement `ContextManager` with Redis
5. ✅ Add database models (`AgentSession`, `AgentMessage`, `AgentExecution`)
6. ✅ Create Pydantic schemas
7. ✅ Write unit tests for core components

**Deliverables**:
- Working agent registry
- Context management system
- Database migrations

### Phase 2: Core Agents (Week 3-4)

**Goals**: Implement first 3 agents

**Tasks**:
1. ✅ Implement `PreprocessingAgent` (wraps existing code generation)
2. ✅ Implement `StatisticalAgent` (new statistical capabilities)
3. ✅ Implement `QueryAgent` (wraps `NLToSQLService`)
4. ✅ Create agent configuration files
5. ✅ Test each agent independently

**Deliverables**:
- 3 working agents
- Agent configuration system

### Phase 3: API & Chat (Week 5-6)

**Goals**: Build chat API endpoints

**Tasks**:
1. ✅ Implement `/agents/chat` endpoint
2. ✅ Implement `/agents/list` endpoint
3. ✅ Add conversation history persistence
4. ✅ Create frontend chat UI (basic)
5. ✅ Add session management
6. ✅ Test end-to-end chat flow

**Deliverables**:
- Working chat API
- Basic chat UI
- Session persistence

### Phase 4: Advanced Agents (Week 7-8)

**Goals**: Add remaining agents

**Tasks**:
1. ✅ Implement `MLAgent` (wraps ML service)
2. ✅ Implement `VisualizationAgent`
3. ✅ Implement `GeospatialAgent` (Kepler.gl integration)
4. ✅ Wrap existing `DataScoutingService` as agent
5. ✅ Test multi-agent collaboration

**Deliverables**:
- 7 total agents
- Multi-agent orchestration

### Phase 5: Streaming & Deep Analysis (Week 9-10)

**Goals**: Add streaming and comprehensive analysis

**Tasks**:
1. ✅ Implement streaming execution in orchestrator
2. ✅ Add `/agents/deep-analysis-stream` endpoint
3. ✅ Create `ReportGeneratorService` for HTML reports
4. ✅ Add SSE (Server-Sent Events) support
5. ✅ Build streaming UI components
6. ✅ Test long-running analyses

**Deliverables**:
- Streaming analysis
- HTML report generation
- Progress indicators in UI

### Phase 6: Optimization & Polish (Week 11-12)

**Goals**: Performance, error handling, UX

**Tasks**:
1. ✅ Optimize agent selection (caching, faster intent detection)
2. ✅ Add comprehensive error handling
3. ✅ Implement retry logic for failed LLM calls
4. ✅ Add cost tracking and limits
5. ✅ Performance testing and optimization
6. ✅ Polish UI/UX
7. ✅ Documentation

**Deliverables**:
- Production-ready system
- Performance benchmarks
- User documentation

---

## 8. Migration Strategy

### 8.1 Backward Compatibility

**Principle**: Existing APIs must continue to work

**Strategy**:
1. Keep existing endpoints (`/queries/nl-to-sql`, `/python-analysis/generate`, etc.)
2. Gradually add agent wrappers around existing services
3. New agent endpoints exist alongside old endpoints
4. Frontend can use either API
5. Deprecate old endpoints after 6 months

### 8.2 Service Wrapping

**Pattern**: Wrap existing services as agents

```python
class QueryAgent(BaseAgent):
    """Wraps NLToSQLService as an agent"""

    def __init__(self, config: AgentConfig, llm_service: LLMService):
        super().__init__(config, llm_service)
        self.nl_to_sql_service = NLToSQLService()  # Existing service

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        # Delegate to existing service
        result = await self.nl_to_sql_service.generate_sql(
            request.query,
            request.dataset_id
        )

        # Wrap in agent response format
        return AgentResponse(
            agent_name=self.config.name,
            success=True,
            data={
                'sql': result['sql'],
                'explanation': result.get('explanation'),
                'result_preview': result.get('result')
            },
            code=result['sql']
        )
```

### 8.3 Data Migration

**No breaking changes needed**:
- New tables added (`agent_sessions`, `agent_messages`, `agent_executions`)
- Existing tables unchanged
- No data migration required

---

## 9. Security & Compliance

### 9.1 Code Execution Security

**Existing**: `CodeExecutorService` already has sandboxing

**Enhancements**:
- Per-user execution limits (CPU, memory, time)
- Code review for dangerous patterns
- Audit logging of all code executions
- Ability to disable Python execution per agent

### 9.2 PII Protection

**Existing**: `DataScoutingService` detects PII

**Enhancements**:
- Auto-redaction in agent responses
- Warning messages when PII detected
- Admin controls to disable PII columns from analysis

### 9.3 Cost Controls

**New Features**:
- Token usage tracking per user/session
- Cost limits per user tier
- Automatic agent downgrade (use cheaper models)
- Usage analytics dashboard

---

## 10. Performance Considerations

### 10.1 Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Agent selection | < 200ms | Intent detection + routing |
| Single agent chat | < 5s | LLM call + code generation |
| Multi-agent sequential | < 15s | 3 agents max |
| Deep analysis streaming | 30-120s | Progress updates every 2s |

### 10.2 Optimization Strategies

1. **Agent Selection Caching**
   - Cache intent → agent mappings
   - Use keyword matching before LLM calls
   - Fallback to LLM only for ambiguous queries

2. **Parallel Execution**
   - Run independent agents in parallel
   - Use `asyncio.gather()` for concurrent tasks

3. **LLM Response Caching**
   - Cache similar queries (embeddings similarity)
   - 1-hour TTL for cached responses

4. **Code Execution Optimization**
   - Reuse Python interpreter sessions
   - Pre-import common libraries
   - Limit data loading to necessary columns

5. **Streaming for Long Operations**
   - Always use streaming for multi-agent workflows
   - Send progress updates every 2 seconds
   - Allow client-side cancellation

---

## Appendix A: Example Workflows

### Example 1: Simple Single-Agent Query

**User**: "What's the average price?"

**Flow**:
1. Orchestrator detects simple SQL query
2. Selects `QueryAgent`
3. QueryAgent calls `NLToSQLService`
4. Returns SQL + result

**Response Time**: ~2 seconds

---

### Example 2: Multi-Step Sequential Workflow

**User**: "Clean the data, then predict sales based on price and region"

**Flow**:
1. Orchestrator creates plan:
   - Agent 1: `PreprocessingAgent` (clean data)
   - Agent 2: `MLAgent` (train model)
   - Mode: Sequential
2. Execute PreprocessingAgent
   - Generates cleaning code
   - Executes and stores cleaned data in context
3. Execute MLAgent
   - Loads cleaned data from context
   - Trains regression model
   - Returns predictions + metrics

**Response Time**: ~15 seconds (with streaming updates)

---

### Example 3: Deep Analysis with All Agents

**User**: "Perform comprehensive analysis to understand customer churn"

**Flow**:
1. Orchestrator creates comprehensive plan:
   - Agent 1: `DataScoutingAgent` (profile data)
   - Agent 2: `PreprocessingAgent` (clean)
   - Agent 3: `StatisticalAgent` (correlations)
   - Agent 4: `MLAgent` (train churn model)
   - Agent 5: `VisualizationAgent` (create dashboards)
   - Mode: Sequential with streaming
2. Stream progress updates every 2 seconds
3. Generate HTML report at end

**Response Time**: ~60-90 seconds (streaming)

---

## Appendix B: Prompt Templates

### Planning Prompt Template

```
Analyze the following data analysis query and create an execution plan.

Query: {query}

Dataset schema:
{schema_summary}

Available agents:
{agents_info}

Recent conversation:
{conversation_history}

Create a JSON execution plan:
{
  "query": "original query",
  "agents": ["agent1", "agent2"],
  "execution_mode": "single|sequential|parallel",
  "dependencies": {"agent2": ["agent1"]},
  "estimated_duration": 30,
  "reasoning": "Why these agents were selected"
}

Rules:
1. Use minimum number of agents
2. Consider conversation context
3. Sequential if outputs depend on each other
4. Parallel if independent

Execution Plan (JSON only):
```

### Agent-Specific Prompt Templates

Located in: `prompts/{agent_name}/{task}.txt`

Example: `prompts/preprocessing/default.txt`

---

## Conclusion

This multi-agent architecture transforms our platform into a sophisticated, conversational data analysis system while preserving our unique strengths (geospatial, collaboration, deep research). The phased implementation ensures we can deliver value incrementally while maintaining backward compatibility.

**Next Steps**:
1. Review and approve this design
2. Set up Phase 1 infrastructure
3. Begin implementing core agents
4. Iterate based on user feedback

**Questions for Discussion**:
1. Should we use DSPy for agent orchestration or build custom?
2. What tier system for premium agents (if any)?
3. Frontend framework preferences for chat UI?
4. Prioritization of agent capabilities?
