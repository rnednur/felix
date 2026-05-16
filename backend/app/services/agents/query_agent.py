"""
Query Agent - wraps NLToSQLService for SQL query generation
"""
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.nl_to_sql_service import NLToSQLService


class QueryAgent(BaseAgent):
    """
    SQL Query Agent - translates natural language to SQL queries

    Wraps the existing NLToSQLService to provide SQL query generation
    capabilities through the agent interface.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.nl_to_sql_service = NLToSQLService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling SQL query requests

        High confidence for queries like:
        - "Show me all records where..."
        - "Count the number of..."
        - "What is the average/sum/max..."
        - "Group by..."
        - "Filter/select..."
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process SQL query generation request

        Args:
            request: Agent request with natural language query
            context: Execution context

        Returns:
            AgentResponse with SQL query and results
        """
        try:
            self.logger.info(f"Processing query: {request.query}")

            # Generate SQL using existing service
            result = await self.nl_to_sql_service.generate_sql(
                request.query,
                request.dataset_id
            )

            # Format response
            response_data = {
                'summary': f"Generated SQL query for: {request.query}",
                'sql': result['sql'],
                'explanation': result.get('explanation', ''),
                'result_preview': result.get('result', []),
                'row_count': len(result.get('result', [])),
                'type': 'sql_query'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                code=result['sql'],
                metadata={
                    'query_type': 'sql',
                    'has_results': len(result.get('result', [])) > 0
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Query agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"SQL generation failed: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response
