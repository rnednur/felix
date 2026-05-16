# Full Agentation Integration Plan for Felix

## 🎯 Vision
Transform Felix's Canvas mode into an **AI-powered dashboard editor** where users can click any element and request changes in natural language, processed by your multi-agent system.

---

## 📋 Phase 1: Foundation (Week 1-2)

### 1.1 Install & Configure Agentation

**Frontend (React/TypeScript)**
```bash
npm install agentation
```

**Integration in Canvas Mode:**
```typescript
// src/components/Canvas/CanvasMode.tsx
import { AgentationProvider, useAgentation } from 'agentation';

export const CanvasMode = () => {
  const [annotations, setAnnotations] = useState([]);
  
  return (
    <AgentationProvider
      enabled={true}
      onAnnotationAdd={(annotation) => {
        setAnnotations([...annotations, annotation]);
        sendToFelixAgent(annotation);
      }}
    >
      <DashboardCanvas />
    </AgentationProvider>
  );
};
```

### 1.2 Create Dashboard Element Registry

**Map UI components to data models:**
```typescript
// src/types/dashboard.ts
interface DashboardElement {
  id: string;
  type: 'metric' | 'chart' | 'insight' | 'layout';
  selector: string;
  config: {
    chartType?: 'line' | 'bar' | 'pie' | 'scatter';
    dataSource?: string;
    filters?: any;
    styling?: any;
  };
}

// src/utils/elementRegistry.ts
export class ElementRegistry {
  // Maps CSS selectors to dashboard config
  private registry: Map<string, DashboardElement>;
  
  register(selector: string, element: DashboardElement) {
    this.registry.set(selector, element);
  }
  
  getBySelector(selector: string): DashboardElement | null {
    return this.registry.get(selector);
  }
}
```

### 1.3 Add Component Metadata

**Tag each dashboard component:**
```typescript
// src/components/Dashboard/MetricCard.tsx
export const MetricCard = ({ id, title, value, trend }) => {
  return (
    <div 
      className="metric-card"
      data-felix-id={id}
      data-felix-type="metric"
      data-felix-config={JSON.stringify({ title, value, trend })}
    >
      {/* ... */}
    </div>
  );
};
```

---

## 📋 Phase 2: Backend Integration (Week 2-3)

### 2.1 Create Annotation API Endpoint

**FastAPI Backend:**
```python
# backend/api/v1/annotations.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class Annotation(BaseModel):
    element_selector: str
    element_type: str
    element_config: dict
    user_feedback: str
    screenshot_url: Optional[str]
    timestamp: datetime

@router.post("/annotations")
async def process_annotation(
    annotation: Annotation,
    user: User = Depends(get_current_user)
):
    # Send to agent orchestrator
    result = await agent_orchestrator.process_edit_request(
        annotation=annotation,
        user_id=user.id
    )
    return result
```

### 2.2 Create DashboardEditorAgent

**New agent in multi-agent architecture:**
```python
# backend/agents/dashboard_editor_agent.py
from backend.agents.base_agent import BaseAgent

class DashboardEditorAgent(BaseAgent):
    """
    Interprets user annotations and generates dashboard modifications
    """
    
    async def process(self, annotation: Annotation) -> DashboardEdit:
        # 1. Parse user intent
        intent = await self._parse_intent(annotation.user_feedback)
        
        # 2. Identify element type
        element = self._identify_element(
            annotation.element_selector,
            annotation.element_config
        )
        
        # 3. Generate modification plan
        if intent.type == "change_chart_type":
            return await self._change_chart_type(element, intent)
        elif intent.type == "modify_data":
            return await self._modify_data_source(element, intent)
        elif intent.type == "update_styling":
            return await self._update_styling(element, intent)
        elif intent.type == "add_element":
            return await self._add_new_element(intent)
        elif intent.type == "remove_element":
            return await self._remove_element(element)
        
        # 4. Validate changes
        validation = await self._validate_edit(edit)
        
        return DashboardEdit(
            element_id=element.id,
            changes=changes,
            validation=validation
        )
    
    async def _parse_intent(self, feedback: str) -> Intent:
        """Use LLM to parse user intent"""
        prompt = f"""
        Parse this dashboard edit request:
        "{feedback}"
        
        Identify:
        1. Action type (change_chart_type, modify_data, update_styling, add_element, remove_element)
        2. Target element
        3. Specific changes requested
        4. Any constraints or preferences
        
        Return structured JSON.
        """
        
        response = await self.llm.generate(prompt)
        return Intent.parse_obj(response)
```

### 2.3 Update Agent Orchestrator

**Add DashboardEditorAgent to orchestration:**
```python
# backend/agents/orchestrator.py
class AgentOrchestrator:
    def __init__(self):
        self.agents = {
            'query': QueryAgent(),
            'visualization': VisualizationAgent(),
            'insight': InsightAgent(),
            'dashboard_editor': DashboardEditorAgent(),  # NEW
        }
    
    async def process_edit_request(
        self, 
        annotation: Annotation,
        user_id: str
    ) -> DashboardUpdate:
        # 1. DashboardEditorAgent interprets the request
        edit_plan = await self.agents['dashboard_editor'].process(annotation)
        
        # 2. Route to appropriate agents based on edit type
        if edit_plan.requires_new_data:
            data = await self.agents['query'].execute(edit_plan.query)
        
        if edit_plan.requires_new_visualization:
            viz = await self.agents['visualization'].generate(
                data=data,
                chart_type=edit_plan.chart_type
            )
        
        if edit_plan.requires_new_insights:
            insights = await self.agents['insight'].analyze(data)
        
        # 3. Generate updated dashboard config
        updated_config = self._merge_changes(
            current_config=annotation.element_config,
            edit_plan=edit_plan,
            new_data=data,
            new_viz=viz
        )
        
        return DashboardUpdate(
            element_id=edit_plan.element_id,
            config=updated_config,
            preview_url=self._generate_preview(updated_config)
        )
```

---

## 📋 Phase 3: Real-time Updates (Week 3-4)

### 3.1 WebSocket Connection

**Real-time dashboard updates:**
```python
# backend/api/v1/websockets.py
from fastapi import WebSocket

@app.websocket("/ws/dashboard/{dashboard_id}")
async def dashboard_websocket(
    websocket: WebSocket,
    dashboard_id: str
):
    await websocket.accept()
    
    try:
        while True:
            # Listen for annotation events
            data = await websocket.receive_json()
            
            if data['type'] == 'annotation':
                # Process through agents
                result = await agent_orchestrator.process_edit_request(
                    annotation=Annotation(**data['annotation']),
                    user_id=data['user_id']
                )
                
                # Send back updated config
                await websocket.send_json({
                    'type': 'dashboard_update',
                    'element_id': result.element_id,
                    'config': result.config,
                    'status': 'success'
                })
    except WebSocketDisconnect:
        pass
```

**Frontend WebSocket handler:**
```typescript
// src/hooks/useDashboardWebSocket.ts
export const useDashboardWebSocket = (dashboardId: string) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    const socket = new WebSocket(
      `ws://localhost:8000/ws/dashboard/${dashboardId}`
    );
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'dashboard_update') {
        // Update dashboard element
        updateDashboardElement(data.element_id, data.config);
      }
    };
    
    setWs(socket);
    
    return () => socket.close();
  }, [dashboardId]);
  
  const sendAnnotation = (annotation: Annotation) => {
    ws?.send(JSON.stringify({
      type: 'annotation',
      annotation,
      user_id: currentUser.id
    }));
  };
  
  return { sendAnnotation };
};
```

### 3.2 Optimistic UI Updates

**Show loading states while agents process:**
```typescript
// src/components/Canvas/AnnotationHandler.tsx
export const AnnotationHandler = () => {
  const [pendingEdits, setPendingEdits] = useState<Map<string, boolean>>();
  const { sendAnnotation } = useDashboardWebSocket(dashboardId);
  
  const handleAnnotation = async (annotation: Annotation) => {
    const elementId = annotation.element_selector;
    
    // Show loading state
    setPendingEdits(prev => new Map(prev).set(elementId, true));
    
    // Send to backend
    sendAnnotation(annotation);
    
    // Wait for response (handled by WebSocket)
  };
  
  return (
    <AgentationProvider onAnnotationAdd={handleAnnotation}>
      {/* Dashboard components with loading overlays */}
    </AgentationProvider>
  );
};
```

---

## 📋 Phase 4: Advanced Features (Week 4-6)

### 4.1 Edit History & Undo/Redo

**Track all changes:**
```python
# backend/models/dashboard_history.py
class DashboardEdit(BaseModel):
    id: str
    dashboard_id: str
    user_id: str
    timestamp: datetime
    annotation: Annotation
    previous_config: dict
    new_config: dict
    agent_reasoning: str

class DashboardHistory:
    def __init__(self, dashboard_id: str):
        self.dashboard_id = dashboard_id
        self.edits: List[DashboardEdit] = []
        self.current_index = -1
    
    def add_edit(self, edit: DashboardEdit):
        # Remove any edits after current index (for redo)
        self.edits = self.edits[:self.current_index + 1]
        self.edits.append(edit)
        self.current_index += 1
    
    def undo(self) -> Optional[dict]:
        if self.current_index >= 0:
            edit = self.edits[self.current_index]
            self.current_index -= 1
            return edit.previous_config
        return None
    
    def redo(self) -> Optional[dict]:
        if self.current_index < len(self.edits) - 1:
            self.current_index += 1
            edit = self.edits[self.current_index]
            return edit.new_config
        return None
```

### 4.2 Batch Edits

**Allow multiple annotations before applying:**
```typescript
// src/components/Canvas/BatchEditMode.tsx
export const BatchEditMode = () => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isBatchMode, setIsBatchMode] = useState(false);
  
  const applyBatchEdits = async () => {
    // Send all annotations together
    const result = await fetch('/api/v1/annotations/batch', {
      method: 'POST',
      body: JSON.stringify({ annotations })
    });
    
    // Apply all changes at once
    const updates = await result.json();
    applyDashboardUpdates(updates);
    
    setAnnotations([]);
  };
  
  return (
    <div>
      <button onClick={() => setIsBatchMode(!isBatchMode)}>
        {isBatchMode ? 'Apply All Changes' : 'Batch Edit Mode'}
      </button>
      
      {isBatchMode && (
        <AnnotationQueue 
          annotations={annotations}
          onApply={applyBatchEdits}
        />
      )}
    </div>
  );
};
```

### 4.3 Smart Suggestions

**Agent proactively suggests improvements:**
```python
# backend/agents/suggestion_agent.py
class SuggestionAgent(BaseAgent):
    """
    Analyzes dashboard and suggests improvements
    """
    
    async def analyze_dashboard(
        self, 
        dashboard_config: dict
    ) -> List[Suggestion]:
        suggestions = []
        
        # Check for common issues
        if self._has_too_many_metrics(dashboard_config):
            suggestions.append(Suggestion(
                type="simplify",
                message="Consider grouping related metrics",
                target_elements=["metric-1", "metric-2", "metric-3"]
            ))
        
        if self._chart_type_mismatch(dashboard_config):
            suggestions.append(Suggestion(
                type="change_chart",
                message="A line chart would better show trends over time",
                target_element="chart-2",
                recommended_chart="line"
            ))
        
        return suggestions
```

### 4.4 Collaborative Editing

**Multiple users editing simultaneously:**
```python
# backend/services/collaboration.py
class CollaborationService:
    def __init__(self):
        self.active_sessions: Dict[str, Set[str]] = {}
        self.locks: Dict[str, str] = {}  # element_id -> user_id
    
    async def acquire_lock(
        self, 
        dashboard_id: str,
        element_id: str,
        user_id: str
    ) -> bool:
        key = f"{dashboard_id}:{element_id}"
        
        if key in self.locks and self.locks[key] != user_id:
            return False  # Element locked by another user
        
        self.locks[key] = user_id
        return True
    
    async def broadcast_edit(
        self,
        dashboard_id: str,
        edit: DashboardEdit,
        exclude_user: str
    ):
        # Notify all other users viewing this dashboard
        for user_id in self.active_sessions.get(dashboard_id, set()):
            if user_id != exclude_user:
                await self.send_to_user(user_id, {
                    'type': 'external_edit',
                    'edit': edit
                })
```

---

## 📋 Phase 5: Polish & Launch (Week 6-8)

### 5.1 Onboarding Flow

**Teach users how to use AI editing:**
```typescript
// src/components/Onboarding/CanvasTutorial.tsx
export const CanvasTutorial = () => {
  const steps = [
    {
      target: '.canvas-mode-button',
      content: 'Click here to enter Canvas mode'
    },
    {
      target: '.metric-card',
      content: 'Click any element to annotate it'
    },
    {
      target: '.agentation-toolbar',
      content: 'Describe what you want to change'
    },
    {
      target: '.apply-button',
      content: 'Felix AI will update your dashboard'
    }
  ];
  
  return <Joyride steps={steps} />;
};
```

### 5.2 Example Prompts

**Help users with suggestions:**
```typescript
const EXAMPLE_PROMPTS = {
  metric: [
    "Add a sparkline trend",
    "Change color to red if value decreases",
    "Show percentage change from last month"
  ],
  chart: [
    "Convert to pie chart",
    "Add a trend line",
    "Filter to show only top 5",
    "Change colors to match brand"
  ],
  insight: [
    "Make this more concise",
    "Add specific numbers",
    "Highlight the key takeaway"
  ],
  layout: [
    "Move this to the top",
    "Make this chart bigger",
    "Add more spacing"
  ]
};
```

### 5.3 Analytics & Monitoring

**Track usage and success:**
```python
# backend/services/analytics.py
class EditAnalytics:
    async def track_annotation(
        self,
        annotation: Annotation,
        result: DashboardUpdate,
        user_id: str
    ):
        await self.log_event({
            'event': 'annotation_processed',
            'user_id': user_id,
            'element_type': annotation.element_type,
            'intent': result.intent_type,
            'success': result.validation.passed,
            'processing_time_ms': result.processing_time,
            'agent_confidence': result.confidence_score
        })
    
    async def track_user_satisfaction(
        self,
        edit_id: str,
        user_id: str,
        accepted: bool,
        feedback: Optional[str]
    ):
        # Track if user kept the change or reverted
        await self.log_event({
            'event': 'edit_feedback',
            'edit_id': edit_id,
            'user_id': user_id,
            'accepted': accepted,
            'feedback': feedback
        })
```

---

## 🎨 UI/UX Enhancements

### Enhanced Canvas Mode UI
```typescript
// src/components/Canvas/EnhancedCanvasMode.tsx
export const EnhancedCanvasMode = () => {
  return (
    <div className="canvas-mode">
      {/* Top toolbar */}
      <CanvasToolbar>
        <button>Undo</button>
        <button>Redo</button>
        <button>Batch Mode</button>
        <button>View History</button>
        <button>AI Suggestions</button>
      </CanvasToolbar>
      
      {/* Agentation-enabled dashboard */}
      <AgentationProvider>
        <DashboardCanvas />
      </AgentationProvider>
      
      {/* Side panel for annotations */}
      <AnnotationPanel>
        <h3>Active Edits</h3>
        <AnnotationList />
        
        <h3>Suggestions</h3>
        <SuggestionList />
      </AnnotationPanel>
      
      {/* Bottom status bar */}
      <StatusBar>
        <span>Canvas Mode Active</span>
        <span>3 pending edits</span>
        <span>Last saved: 2 min ago</span>
      </StatusBar>
    </div>
  );
};
```

---

## 📊 Success Metrics

Track these KPIs:
- **Adoption**: % of users who try Canvas mode
- **Engagement**: Avg annotations per session
- **Success Rate**: % of annotations successfully applied
- **User Satisfaction**: % of edits kept vs reverted
- **Time Saved**: Comparison to manual dashboard editing

---

## 🚀 Deployment Strategy

### Week 1-2: Internal Alpha
- Test with your team
- Fix critical bugs
- Refine agent prompts

### Week 3-4: Private Beta
- Invite 10-20 power users
- Gather feedback
- Iterate on UX

### Week 5-6: Public Beta
- Roll out to all users with feature flag
- Monitor performance
- Scale infrastructure

### Week 7-8: General Availability
- Full launch
- Marketing push
- Documentation & tutorials

---

## 💰 Cost Considerations

**LLM API Costs:**
- ~$0.01-0.05 per annotation (depending on model)
- Budget for 1000 annotations/day = $10-50/day

**Infrastructure:**
- WebSocket server for real-time updates
- Redis for session management
- PostgreSQL for edit history

---

## 🎯 Competitive Advantage

This makes Felix **unique** in the analytics space:
- **Tableau/PowerBI**: No AI-powered editing
- **Looker**: No natural language dashboard modification
- **Metabase**: No intelligent element annotation

**Your pitch:** *"Edit dashboards by talking to them"*

Want me to dive deeper into any specific phase or component?