"""
ML/Prediction Agent - machine learning and prediction capabilities
"""
from typing import Dict, Any
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.nl_to_python_service import NLToPythonService
from app.services.code_executor_service import CodeExecutorService


class MLAgent(BaseAgent):
    """
    ML/Prediction Agent - performs machine learning tasks

    Uses the Python Analysis service to:
    - Generate ML/prediction code
    - Execute predictions on the data
    - Return insights and forecasts
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.python_service = NLToPythonService()
        self.executor = CodeExecutorService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling ML requests

        High confidence for queries like:
        - "Predict sales"
        - "Classify customers"
        - "Find customer segments"
        - "Train a model to..."
        - "What factors influence..."
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process ML request by generating and executing Python ML code

        Args:
            request: Agent request with ML intent
            context: Execution context

        Returns:
            AgentResponse with ML predictions and insights
        """
        try:
            self.logger.info(f"Generating ML analysis for dataset: {request.dataset_id}")

            # Determine ML task type
            ml_task = self._determine_ml_task(request.query)

            # Generate Python ML code
            code_result = await self.python_service.generate_python_code(
                nl_query=request.query,
                dataset_id=request.dataset_id,
                mode='ml'  # Force ML mode
            )

            # Execute the generated code
            execution_result = self.executor.execute_python(
                code=code_result['code'],
                dataset_id=request.dataset_id
            )

            # Check execution status
            if execution_result['status'] == 'SUCCESS':
                output = execution_result.get('output', {})

                # Create summary based on output
                summary = output.get('summary', f"Completed {ml_task} analysis")
                if not summary or summary == "":
                    summary = f"Executed ML analysis: {ml_task}"

                response_data = {
                    'summary': summary,
                    'ml_task': ml_task,
                    'predictions': output.get('predictions'),
                    'metrics': output.get('metrics'),
                    'insights': output.get('insights', []),
                    'visualizations': execution_result.get('visualizations', []),
                    'code': code_result['code'],
                    'type': 'ml_analysis'
                }

                response = AgentResponse(
                    agent_name=self.config.name,
                    success=True,
                    data=response_data,
                    code=code_result['code'],
                    metadata={
                        'ml_task': ml_task,
                        'execution_time_ms': execution_result.get('execution_time_ms'),
                        'mode': code_result.get('mode')
                    }
                )
            else:
                # Execution failed - return recommendation instead
                recommendation = self._generate_ml_recommendation(
                    query=request.query,
                    ml_task=ml_task,
                    dataset_id=request.dataset_id
                )

                response_data = {
                    'summary': f"{recommendation['summary']} (automated analysis failed)",
                    'ml_task': ml_task,
                    'recommendation': recommendation['description'],
                    'approach': recommendation['approach'],
                    'next_steps': recommendation['next_steps'],
                    'error_details': execution_result.get('error'),
                    'type': 'ml_recommendation'
                }

                response = AgentResponse(
                    agent_name=self.config.name,
                    success=True,  # Still successful, just providing recommendations
                    data=response_data,
                    metadata={
                        'ml_task': ml_task,
                        'requires_python': True,
                        'execution_failed': True
                    }
                )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"ML agent failed: {str(e)}", exc_info=True)

            # Fallback to recommendations on error
            try:
                ml_task = self._determine_ml_task(request.query)
                recommendation = self._generate_ml_recommendation(
                    query=request.query,
                    ml_task=ml_task,
                    dataset_id=request.dataset_id
                )

                error_response = AgentResponse(
                    agent_name=self.config.name,
                    success=True,
                    data={
                        'summary': f"{recommendation['summary']} (automated analysis unavailable)",
                        'ml_task': ml_task,
                        'recommendation': recommendation['description'],
                        'approach': recommendation['approach'],
                        'next_steps': recommendation['next_steps'],
                        'type': 'ml_recommendation'
                    },
                    error=f"Automated ML failed: {str(e)}"
                )
            except:
                error_response = AgentResponse(
                    agent_name=self.config.name,
                    success=False,
                    data={},
                    error=f"ML task failed: {str(e)}"
                )

            self.log_execution(request, error_response)
            return error_response

    def _determine_ml_task(self, query: str) -> str:
        """Determine the type of ML task from query"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['predict', 'forecast', 'estimate', 'regression']):
            return 'regression'
        elif any(word in query_lower for word in ['classify', 'categorize', 'label']):
            return 'classification'
        elif any(word in query_lower for word in ['segment', 'cluster', 'group', 'similar']):
            return 'clustering'
        elif any(word in query_lower for word in ['important', 'influence', 'factor', 'feature']):
            return 'feature_importance'
        else:
            return 'general_ml'

    def _generate_ml_recommendation(
        self,
        query: str,
        ml_task: str,
        dataset_id: str
    ) -> Dict[str, Any]:
        """Generate ML approach recommendation"""

        recommendations = {
            'regression': {
                'summary': 'Regression model recommended for prediction',
                'description': 'Use regression to predict numeric values based on input features',
                'approach': [
                    'Identify target variable (what to predict)',
                    'Select relevant features',
                    'Split data into train/test sets',
                    'Train model (Linear Regression, Random Forest, or XGBoost)',
                    'Evaluate with R², MAE, RMSE metrics'
                ],
                'next_steps': [
                    'Switch to Python mode',
                    'Specify: "Train a regression model to predict [target] using [features]"',
                    'Review generated code and execute'
                ]
            },
            'classification': {
                'summary': 'Classification model recommended',
                'description': 'Use classification to categorize data into discrete classes',
                'approach': [
                    'Identify target classes',
                    'Prepare features for classification',
                    'Handle class imbalance if needed',
                    'Train classifier (Logistic Regression, Random Forest, or XGBoost)',
                    'Evaluate with accuracy, precision, recall, F1-score'
                ],
                'next_steps': [
                    'Switch to Python mode',
                    'Specify: "Train a classification model for [target] using [features]"',
                    'Review model performance metrics'
                ]
            },
            'clustering': {
                'summary': 'Clustering analysis recommended for segmentation',
                'description': 'Use clustering to find natural groups in your data',
                'approach': [
                    'Select features for clustering',
                    'Normalize/scale features',
                    'Determine optimal number of clusters (elbow method)',
                    'Apply K-Means or DBSCAN clustering',
                    'Analyze cluster characteristics'
                ],
                'next_steps': [
                    'Switch to Python mode',
                    'Specify: "Cluster the data into segments using [features]"',
                    'Visualize clusters and analyze patterns'
                ]
            },
            'feature_importance': {
                'summary': 'Feature importance analysis recommended',
                'description': 'Identify which factors have the most impact on your target variable',
                'approach': [
                    'Train a tree-based model (Random Forest or XGBoost)',
                    'Extract feature importance scores',
                    'Rank features by importance',
                    'Visualize top features',
                    'Analyze relationships'
                ],
                'next_steps': [
                    'Switch to Python mode',
                    'Specify: "Analyze feature importance for [target]"',
                    'Review top influencing factors'
                ]
            },
            'general_ml': {
                'summary': 'ML analysis recommended',
                'description': 'Apply machine learning to extract insights from your data',
                'approach': [
                    'Define the problem clearly',
                    'Choose appropriate ML technique',
                    'Prepare and clean data',
                    'Train and evaluate model',
                    'Interpret results'
                ],
                'next_steps': [
                    'Switch to Python mode',
                    'Describe your ML goal in detail',
                    'Review and execute generated code'
                ]
            }
        }

        return recommendations.get(ml_task, recommendations['general_ml'])
