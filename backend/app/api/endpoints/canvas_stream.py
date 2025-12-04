from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import asyncio
import json
import uuid

from app.core.database import get_db
from app.core.security import get_user_from_token_param
from app.models import Workspace, CanvasItem, User, Dataset, DatasetGroup
from app.schemas.workspace import CanvasStreamRequest
from app.services.nl_to_sql_service import NLToSQLService
from app.services.duckdb_service import DuckDBService
from app.services.visualization_service import VizService

router = APIRouter()


async def generate_ag_ui_events(
    stream_request: CanvasStreamRequest,
    db: Session,
    current_user: User
) -> AsyncGenerator[dict, None]:
    """
    Generate AG-UI protocol events for canvas item creation
    """
    try:
        # Note: For canvas mode integrated into dataset view, we don't require
        # a pre-existing workspace. The workspace_id is just used as an identifier.
        # In the future, when users create actual workspaces, we can add validation here.

        # Calculate starting Y position based on existing items (if any)
        # This allows stacking questions vertically
        base_y = 100  # Will be passed from frontend in future, for now use fixed position

        # First, emit a header/title card for this query
        yield {
            "event": "canvas.item.create",
            "data": json.dumps({
                "itemType": "insight-note",
                "position": {"x": 50, "y": base_y},
                "width": 1400,
                "height": 80,
                "content": {
                    "content": f"## 🔍 {stream_request.message}\n\n_Analysis in progress..._",
                    "aiGenerated": True,
                    "tags": ["query-header"]
                }
            })
        }

        # Agent thinking
        yield {
            "event": "agent.thinking",
            "data": json.dumps({
                "status": "Analyzing your question...",
                "timestamp": asyncio.get_event_loop().time()
            })
        }
        await asyncio.sleep(0.5)

        # Generate SQL
        nl_service = NLToSQLService(db)
        yield {
            "event": "agent.tool.use",
            "data": json.dumps({
                "tool": "sql_generator",
                "input": {"query": stream_request.message}
            })
        }

        try:
            sql_result = await nl_service.generate_sql(
                stream_request.message,
                dataset_id=stream_request.dataset_id,
                group_id=stream_request.dataset_group_id
            )
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Failed to generate SQL: {str(e)}"})
            }
            return

        # Emit code block canvas item (below header)
        code_item_position = {"x": 50, "y": base_y + 100}
        yield {
            "event": "canvas.item.create",
            "data": json.dumps({
                "itemType": "code-block",
                "position": code_item_position,
                "width": 600,
                "height": 250,
                "content": {
                    "language": "sql",
                    "code": sql_result['sql'],
                    "editable": False
                }
            })
        }

        yield {
            "event": "agent.tool.result",
            "data": json.dumps({
                "tool": "sql_generator",
                "result": {"sql": sql_result['sql'][:100] + "..."}
            })
        }
        await asyncio.sleep(0.3)

        # Execute query
        yield {
            "event": "agent.tool.use",
            "data": json.dumps({
                "tool": "sql_executor",
                "input": {"sql": sql_result['sql'][:50] + "..."}
            })
        }

        duckdb_service = DuckDBService()
        try:
            if stream_request.dataset_id:
                df = duckdb_service.execute_query(
                    sql_result['sql'],
                    dataset_id=stream_request.dataset_id
                )
            else:
                # Group query
                group = db.query(DatasetGroup).filter(
                    DatasetGroup.id == stream_request.dataset_group_id
                ).first()
                dataset_configs = []
                for membership in sorted(group.memberships, key=lambda m: m.display_order):
                    dataset_configs.append({
                        'dataset_id': membership.dataset_id,
                        'alias': membership.alias or membership.dataset.name
                    })
                df = duckdb_service.execute_query(
                    sql_result['sql'],
                    dataset_configs=dataset_configs
                )
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Query execution failed: {str(e)}"})
            }
            return

        # Emit query result canvas item (next to code block)
        result_item_position = {"x": 700, "y": base_y + 100}
        columns = df.columns.tolist()
        rows = df.head(50).to_dict('records')

        yield {
            "event": "canvas.item.create",
            "data": json.dumps({
                "itemType": "query-result",
                "position": result_item_position,
                "width": 700,
                "height": 400,
                "content": {
                    "columns": columns,
                    "rows": rows,
                    "sql": sql_result['sql'],
                    "totalRows": len(df)
                }
            })
        }

        yield {
            "event": "agent.tool.result",
            "data": json.dumps({
                "tool": "sql_executor",
                "result": {"rows": len(df), "columns": len(columns)}
            })
        }
        await asyncio.sleep(0.3)

        # Generate visualizations
        try:
            viz_service = VizService()
            suggestions = viz_service.suggest_charts(df)

            if suggestions:
                yield {
                    "event": "agent.tool.use",
                    "data": json.dumps({
                        "tool": "chart_generator",
                        "input": {"count": len(suggestions)}
                    })
                }

                # Emit chart canvas items (up to 3 charts)
                for i, chart in enumerate(suggestions[:3]):
                    # Position charts side by side below code and results
                    chart_x = 50 + (i * 650)  # Space charts horizontally
                    chart_y = base_y + 370  # Below the code/results row

                    yield {
                        "event": "canvas.item.create",
                        "data": json.dumps({
                            "itemType": "chart",
                            "position": {"x": chart_x, "y": chart_y},
                            "width": 600,
                            "height": 400,
                            "content": {
                                "chartType": chart['type'],
                                "vegaSpec": chart['spec'],
                                "title": chart.get('title', f"{chart['type'].capitalize()} Chart")
                            }
                        })
                    }

                yield {
                    "event": "agent.tool.result",
                    "data": json.dumps({
                        "tool": "chart_generator",
                        "result": {"chartsCreated": len(suggestions[:3])}
                    })
                }
        except Exception as e:
            # Visualization is optional, don't fail the whole stream
            yield {
                "event": "agent.message",
                "data": json.dumps({
                    "message": f"Could not generate visualization: {str(e)}"
                })
            }

        # Complete
        yield {
            "event": "agent.complete",
            "data": json.dumps({
                "summary": f"Generated query with {len(df)} results",
                "timestamp": asyncio.get_event_loop().time()
            })
        }

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"message": f"Stream error: {str(e)}"})
        }


@router.get("/stream")
async def canvas_stream(
    request: Request,
    workspace_id: str,
    message: str,
    token: str,
    dataset_id: str = None,
    dataset_group_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token_param),
):
    """
    AG-UI compliant SSE endpoint for streaming canvas item creation

    Note: Using GET instead of POST because EventSource only supports GET.
    For production, consider using WebSockets or fetch() with ReadableStream for POST support.
    """
    # Convert query params to CanvasStreamRequest
    stream_request = CanvasStreamRequest(
        workspace_id=workspace_id,
        message=message,
        dataset_id=dataset_id,
        dataset_group_id=dataset_group_id
    )

    return EventSourceResponse(
        generate_ag_ui_events(stream_request, db, current_user),
        media_type="text/event-stream"
    )
