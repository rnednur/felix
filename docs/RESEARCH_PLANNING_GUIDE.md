# Research Planning Feature - Implementation Guide

## Overview
Add a multi-step research planning UI that lets users review and edit the research plan before execution.

---

## What This Adds

**Current Flow:**
```
User asks question → Deep Research executes → Shows results
```

**New Flow:**
```
User asks question → Generate plan → User reviews/edits → Execute → Shows results
```

---

## Architecture

### Backend Changes

#### 1. Add Planning Endpoint

**File:** `app/api/endpoints/deep_research.py`

```python
class PlanRequest(BaseModel):
    dataset_id: str
    question: str
    max_sub_questions: int = Field(default=10, ge=1, le=20)

class PlanResponse(BaseModel):
    main_question: str
    sub_questions: List[Dict[str, Any]]
    estimated_time: str
    research_stages: List[str]

@router.post("/plan", response_model=PlanResponse)
async def create_research_plan(
    request: PlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate research plan without executing
    Returns decomposed sub-questions for user review
    """

    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Initialize service
    service = DeepResearchService()
    schema = service.storage_service.load_schema(request.dataset_id)

    # Decompose question into sub-questions
    sub_questions = await service._decompose_question(
        request.question,
        schema,
        request.max_sub_questions
    )

    # Format response
    return PlanResponse(
        main_question=request.question,
        sub_questions=[
            {
                "id": f"sq_{i}",
                "question": sq.question,
                "intent_type": sq.intent_type,
                "desired_output": sq.desired_output,
                "priority": sq.priority,
                "editable": True
            }
            for i, sq in enumerate(sub_questions)
        ],
        estimated_time=f"{len(sub_questions) * 2}s",
        research_stages=[
            "Research Websites",
            "Analyze Results",
            "Create Report"
        ]
    )
```

#### 2. Add Execute Plan Endpoint

```python
class ExecutePlanRequest(BaseModel):
    dataset_id: str
    main_question: str
    sub_questions: List[Dict[str, Any]]
    enable_python: bool = True
    enable_world_knowledge: bool = True
    generate_infographic: bool = False
    infographic_format: str = 'pdf'
    infographic_color_scheme: str = 'professional'

@router.post("/execute-plan", response_model=DeepResearchResponse)
async def execute_research_plan(
    request: ExecutePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Execute research with user-edited plan
    """

    # Verify dataset
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Initialize service
    service = DeepResearchService()

    # Convert sub_questions back to SubQuestion objects
    from app.services.deep_research_service import SubQuestion
    sub_questions = [
        SubQuestion(
            question=sq['question'],
            intent_type=sq['intent_type'],
            desired_output=sq['desired_output'],
            priority=sq.get('priority', 1)
        )
        for sq in request.sub_questions
    ]

    # Execute research starting from classification stage
    # (skip decomposition since we have user-edited plan)
    schema = service.storage_service.load_schema(request.dataset_id)

    # Stage 2: Classification
    classified = await service._classify_and_map(sub_questions, schema)

    # Stage 3: Query Execution
    results = await service._execute_queries(
        classified,
        request.dataset_id,
        schema,
        request.enable_python
    )

    # Stage 4: World Knowledge
    world_knowledge = {}
    if request.enable_world_knowledge:
        world_knowledge = await service._enrich_world_knowledge(classified, results)

    # Stage 5: Synthesis
    synthesis = await service._synthesize_insights(
        request.main_question,
        sub_questions,
        classified,
        results,
        world_knowledge,
        schema
    )

    # Stage 6: Follow-ups
    follow_ups = await service._suggest_follow_ups(
        request.main_question,
        synthesis,
        schema
    )

    # Generate infographic if requested
    infographic_data = None
    if request.generate_infographic:
        infographic_service = InfographicService(template=request.infographic_color_scheme)
        infographic_result = infographic_service.generate_infographic(
            research_result={
                'main_question': request.main_question,
                'direct_answer': synthesis.get('direct_answer', ''),
                'key_findings': synthesis.get('key_findings', []),
                # ... rest of result
            },
            format=request.infographic_format
        )
        infographic_data = {
            'data': infographic_result['data'],
            'format': infographic_result['format'],
            'filename': infographic_result['filename'],
            'size_bytes': infographic_result['size_bytes']
        }

    # Return response
    return DeepResearchResponse(
        success=True,
        main_question=request.main_question,
        direct_answer=synthesis.get('direct_answer', ''),
        key_findings=synthesis.get('key_findings', []),
        # ... rest of fields
        infographic=infographic_data
    )
```

---

### Frontend Changes

#### 1. Add Plan View Component

**File:** `frontend/src/components/research/PlanEditor.tsx`

```tsx
import { useState } from 'react'
import { Button } from '@/components/ui/button'

interface SubQuestion {
  id: string
  question: string
  intent_type: string
  desired_output: string
  priority: number
  editable: boolean
}

interface PlanEditorProps {
  plan: {
    main_question: string
    sub_questions: SubQuestion[]
    estimated_time: string
    research_stages: string[]
  }
  onExecute: (editedPlan: any) => void
  onCancel: () => void
}

export function PlanEditor({ plan, onExecute, onCancel }: PlanEditorProps) {
  const [subQuestions, setSubQuestions] = useState(plan.sub_questions)

  const updateQuestion = (id: string, newText: string) => {
    setSubQuestions(prev =>
      prev.map(sq => sq.id === id ? { ...sq, question: newText } : sq)
    )
  }

  const removeQuestion = (id: string) => {
    setSubQuestions(prev => prev.filter(sq => sq.id !== id))
  }

  const addQuestion = () => {
    const newQ: SubQuestion = {
      id: `sq_${Date.now()}`,
      question: '',
      intent_type: 'descriptive',
      desired_output: 'table',
      priority: 2,
      editable: true
    }
    setSubQuestions(prev => [...prev, newQ])
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">{plan.main_question}</h2>
        <p className="text-sm text-gray-600 mt-2">
          Review and edit the research plan before execution
        </p>
      </div>

      {/* Research Stages */}
      <div className="space-y-3">
        {plan.research_stages.map((stage, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              {i === 0 ? '📚' : i === 1 ? '≡' : '📊'}
            </div>
            <span className="font-medium">{stage}</span>
          </div>
        ))}

        {/* Show first stage expanded */}
        {plan.research_stages[0] === 'Research Websites' && (
          <div className="ml-11 space-y-2 border-l-2 border-gray-200 pl-6">
            {subQuestions.map((sq, i) => (
              <div key={sq.id} className="bg-white border rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <span className="text-sm text-gray-500">({i + 1})</span>
                  <input
                    type="text"
                    value={sq.question}
                    onChange={(e) => updateQuestion(sq.id, e.target.value)}
                    className="flex-1 px-2 py-1 border rounded text-sm"
                    placeholder="Enter research question..."
                  />
                  <button
                    onClick={() => removeQuestion(sq.id)}
                    className="text-red-500 hover:text-red-700 text-sm"
                  >
                    ✕
                  </button>
                </div>
                <div className="ml-6 mt-2 flex gap-2 text-xs text-gray-500">
                  <span>Type: {sq.intent_type}</span>
                  <span>•</span>
                  <span>Output: {sq.desired_output}</span>
                </div>
              </div>
            ))}

            <button
              onClick={addQuestion}
              className="ml-6 text-sm text-blue-600 hover:text-blue-700"
            >
              + Add question
            </button>
          </div>
        )}

        {/* Collapsed stages */}
        <div className="ml-11 text-sm text-gray-500">
          <button className="hover:text-gray-700">More ▼</button>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-gray-500">
          ⏱️ Ready in {plan.estimated_time}
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={onCancel}>
            Edit plan
          </Button>
          <Button
            onClick={() => onExecute({
              main_question: plan.main_question,
              sub_questions: subQuestions
            })}
            className="bg-blue-500 hover:bg-blue-600"
          >
            Start research
          </Button>
        </div>
      </div>
    </div>
  )
}
```

#### 2. Update DatasetDetail Flow

**File:** `frontend/src/pages/DatasetDetail.tsx`

```tsx
// Add state for planning
const [showPlanEditor, setShowPlanEditor] = useState(false)
const [currentPlan, setCurrentPlan] = useState<any>(null)

// Modify handleQuerySubmit for deep-research mode
const handleQuerySubmit = async (query: string, mode?: AnalysisMode) => {
  // ... existing code ...

  if (mode === 'deep-research') {
    try {
      // Step 1: Generate plan
      const planResponse = await fetch(`${apiUrl}/deep-research/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: id!,
          question: query,
          max_sub_questions: 10
        })
      })

      const plan = await planResponse.json()

      // Step 2: Show plan editor
      setCurrentPlan(plan)
      setShowPlanEditor(true)

    } catch (error) {
      console.error('Plan generation failed:', error)
    }
    return
  }

  // ... rest of code ...
}

// Handle plan execution
const handleExecutePlan = async (editedPlan: any) => {
  setShowPlanEditor(false)

  setMessages((prev) => [...prev, {
    role: 'assistant',
    content: '🧠 Executing research plan...'
  }])

  try {
    const response = await fetch(`${apiUrl}/deep-research/execute-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: id!,
        main_question: editedPlan.main_question,
        sub_questions: editedPlan.sub_questions,
        enable_python: true,
        enable_world_knowledge: true,
        generate_infographic: generateInfographic,
        infographic_format: infographicFormat,
        infographic_color_scheme: infographicColorScheme
      })
    })

    const result = await response.json()

    // Save results and show in report view
    setDeepResearchReport(result)
    if (result.infographic) {
      setCurrentInfographic(result.infographic)
    }
    setCurrentView('report')

    setMessages((prev) => {
      const newMessages = [...prev]
      newMessages[newMessages.length - 1] = {
        role: 'assistant',
        content: `✅ Research complete! View in Report tab.`
      }
      return newMessages
    })

  } catch (error) {
    console.error('Execution failed:', error)
  }
}

// Add in render
return (
  <div className="flex h-screen">
    {/* Existing sidebar */}
    <ChatSidebar {...props} />

    {/* Plan Editor Modal */}
    {showPlanEditor && currentPlan && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-auto">
          <PlanEditor
            plan={currentPlan}
            onExecute={handleExecutePlan}
            onCancel={() => setShowPlanEditor(false)}
          />
        </div>
      </div>
    )}

    {/* Rest of UI */}
  </div>
)
```

---

## Summary

### What You Need to Do

1. **Backend (30 mins)**
   - Add `/plan` endpoint (returns decomposed questions)
   - Add `/execute-plan` endpoint (executes with edited plan)

2. **Frontend (1 hour)**
   - Create `PlanEditor.tsx` component
   - Update deep research flow to show plan editor
   - Add execute plan handler

### User Flow

```
1. User asks: "What are health trends?"
   ↓
2. System generates plan with sub-questions
   ↓
3. Plan editor modal appears (like your screenshot)
   ↓
4. User edits questions, adds/removes items
   ↓
5. User clicks "Start research"
   ↓
6. System executes with edited plan
   ↓
7. Results shown in report view
```

Would you like me to implement this planning feature for you?
