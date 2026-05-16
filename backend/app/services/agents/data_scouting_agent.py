"""
Data Scouting Agent - wraps DataScoutingService for data profiling
"""
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.data_scouting_service import DataScoutingService


class DataScoutingAgent(BaseAgent):
    """
    Data Scouting Agent - profiles data and detects quality issues

    Wraps the existing DataScoutingService to provide data profiling,
    pattern detection, PII detection, and quality assessment capabilities.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.scouting_service = DataScoutingService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling data profiling requests

        High confidence for queries like:
        - "Profile this data"
        - "Check data quality"
        - "Find PII in the data"
        - "What patterns are in the data?"
        - "Describe the dataset"
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process data profiling request

        Args:
            request: Agent request with dataset to profile
            context: Execution context

        Returns:
            AgentResponse with profiling results
        """
        try:
            self.logger.info(f"Profiling dataset: {request.dataset_id}")

            # Scout the dataset
            scout_result = self.scouting_service.scout_dataset(
                dataset_id=request.dataset_id,
                sample_size=1000
            )

            if not scout_result.get('success'):
                raise Exception("Data scouting failed")

            # Format observations into natural language summary
            observations = scout_result.get('observations', [])
            questions = scout_result.get('scouting_questions', [])
            discrepancies = scout_result.get('discrepancies', [])

            summary_parts = []

            if observations:
                summary_parts.append(f"Found {len(observations)} observations about the data")

            if discrepancies:
                high_severity = [d for d in discrepancies if d.get('severity') == 'high']
                if high_severity:
                    summary_parts.append(f"{len(high_severity)} high-severity issues detected")

            summary = ". ".join(summary_parts) if summary_parts else "Data profiling complete"

            # Format response
            response_data = {
                'summary': summary,
                'observations': observations[:10],  # Top 10 observations
                'scouting_questions': questions[:10],  # Top 10 questions
                'discrepancies': discrepancies,
                'total_rows': scout_result.get('total_rows', 0),
                'sample_size': scout_result.get('sample_size', 0),
                'column_profiles': scout_result.get('column_profiles', [])[:5],  # Top 5 columns
                'type': 'data_profiling'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                metadata={
                    'observation_count': len(observations),
                    'question_count': len(questions),
                    'discrepancy_count': len(discrepancies),
                    'high_severity_count': len([d for d in discrepancies if d.get('severity') == 'high'])
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Data scouting agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"Data profiling failed: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response
