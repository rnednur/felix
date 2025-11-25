"""
Deep Research Agent Service

Multi-stage pipeline for comprehensive data analysis:
1. Question Understanding & Decomposition
2. Question Classification & Schema Mapping
3. Query Execution (SQL + Python)
4. World Knowledge Enrichment
5. Synthesis & Insight Generation
6. (Optional) Iterative Deepening
"""

import json
import httpx
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.nl_to_sql_service import NLToSQLService
from app.services.nl_to_python_service import NLToPythonService
from app.services.code_executor_service import CodeExecutorService
from app.services.duckdb_service import DuckDBService


class SubQuestion:
    """Structured representation of a sub-question"""
    def __init__(self,
                 question: str,
                 intent_type: str,
                 desired_output: str,
                 priority: int = 1):
        self.question = question
        self.intent_type = intent_type  # descriptive, comparative, causal, etc.
        self.desired_output = desired_output  # table, number, explanation, chart
        self.priority = priority


class ClassifiedQuestion:
    """Question with data/knowledge classification"""
    def __init__(self,
                 sub_question: SubQuestion,
                 category: str,
                 candidate_tables: List[str] = None,
                 candidate_columns: List[str] = None,
                 feasibility: str = "unknown",
                 notes: str = ""):
        self.sub_question = sub_question
        self.category = category  # data_backed, world_knowledge, insufficient_data, mixed
        self.candidate_tables = candidate_tables or []
        self.candidate_columns = candidate_columns or []
        self.feasibility = feasibility
        self.notes = notes


class AnalysisResult:
    """Result from query execution"""
    def __init__(self,
                 question: str,
                 method: str,  # sql, python, llm
                 success: bool,
                 data: Any = None,
                 visualization: Any = None,
                 error: str = None):
        self.question = question
        self.method = method
        self.success = success
        self.data = data
        self.visualization = visualization
        self.error = error


class DeepResearchService:
    """Orchestrates multi-stage deep research pipeline"""

    def __init__(self):
        self.storage_service = StorageService()
        self.nl_to_sql = NLToSQLService()
        self.nl_to_python = NLToPythonService()
        self.code_executor = CodeExecutorService()
        self.duckdb_service = DuckDBService()

    async def research(self,
                      main_question: str,
                      dataset_id: str,
                      max_sub_questions: int = 10,
                      enable_python: bool = True,
                      enable_world_knowledge: bool = True,
                      verbose_mode: bool = True,
                      progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Execute full deep research pipeline

        Returns comprehensive analysis with:
        - Direct answer
        - Key findings
        - Supporting details
        - Data coverage & gaps
        - Suggested next questions
        - (Optional) Verbose analysis with executive summary, methodology, detailed findings, etc.
        """

        start_time = time.time()
        research_id = f"research_{datetime.utcnow().timestamp()}"

        # Load dataset schema
        schema = self.storage_service.load_schema(dataset_id)

        # Stage 1: Question Understanding & Decomposition
        print(f"[{research_id}] Stage 1: Decomposing question...")
        if progress_callback:
            await progress_callback(1, "Decomposing question into sub-questions...")
        sub_questions = await self._decompose_question(
            main_question,
            schema,
            max_sub_questions
        )

        # Stage 2: Question Classification & Schema Mapping
        print(f"[{research_id}] Stage 2: Classifying {len(sub_questions)} sub-questions...")
        if progress_callback:
            await progress_callback(2, f"Classifying {len(sub_questions)} sub-questions and mapping to schema...")
        classified = await self._classify_and_map(sub_questions, schema)

        # Stage 3: Query Execution
        print(f"[{research_id}] Stage 3: Executing queries...")
        if progress_callback:
            await progress_callback(3, "Executing SQL and Python queries...")
        results = await self._execute_queries(
            classified,
            dataset_id,
            schema,
            enable_python
        )

        # Stage 4: World Knowledge Enrichment
        world_knowledge = {}
        if enable_world_knowledge:
            print(f"[{research_id}] Stage 4: Enriching with world knowledge...")
            if progress_callback:
                await progress_callback(4, "Enriching with world knowledge and context...")
            world_knowledge = await self._enrich_world_knowledge(
                classified,
                results
            )
        else:
            if progress_callback:
                await progress_callback(4, "Skipping world knowledge enrichment...")

        # Stage 5: Synthesis & Insight Generation
        print(f"[{research_id}] Stage 5: Synthesizing insights...")
        if progress_callback:
            await progress_callback(5, "Synthesizing insights and generating findings...")
        synthesis = await self._synthesize_insights(
            main_question,
            sub_questions,
            classified,
            results,
            world_knowledge,
            schema
        )

        # Stage 6: Suggest Follow-ups
        print(f"[{research_id}] Stage 6: Generating follow-up questions...")
        if progress_callback:
            await progress_callback(6, "Generating follow-up questions...")
        follow_ups = await self._suggest_follow_ups(
            main_question,
            synthesis,
            schema
        )

        # Stage 7 (Optional): Generate Verbose Analysis
        verbose_analysis = {}
        if verbose_mode:
            print(f"[{research_id}] Stage 7: Generating verbose multi-page analysis...")
            if progress_callback:
                await progress_callback(7, "Generating comprehensive report with detailed analysis...")
            verbose_analysis = await self._generate_verbose_analysis(
                main_question,
                sub_questions,
                classified,
                results,
                world_knowledge,
                synthesis,
                schema
            )

        # Track execution time
        execution_time = time.time() - start_time

        # Build data coverage
        data_coverage = {
            'questions_answered': sum(1 for r in results if r.success),
            'total_questions': len(sub_questions),
            'gaps': synthesis.get('gaps', []),
            'methods_used': list(set(r.method for r in results))
        }

        # Extract just the question text from follow_ups
        follow_up_questions = []
        if isinstance(follow_ups, list):
            for item in follow_ups:
                if isinstance(item, dict):
                    follow_up_questions.append(item.get('question', str(item)))
                else:
                    follow_up_questions.append(str(item))

        # Collect all visualizations from results
        visualizations = []
        for r in results:
            if r.success and r.visualization:
                viz_list = r.visualization if isinstance(r.visualization, list) else [r.visualization]
                for viz in viz_list:
                    visualizations.append({
                        'question': r.question,
                        'type': viz.get('type', 'image'),
                        'format': viz.get('format', 'png'),
                        'data': viz.get('data'),
                        'caption': r.question
                    })

        result = {
            'research_id': research_id,
            'main_question': main_question,
            'sub_questions_count': len(sub_questions),
            'direct_answer': synthesis.get('direct_answer', 'Analysis in progress...'),
            'key_findings': synthesis.get('key_findings', []),
            'supporting_details': synthesis.get('supporting_details', {}),
            'data_coverage': data_coverage,
            'follow_up_questions': follow_up_questions,
            'visualizations': visualizations,
            'stages_completed': [
                'Question decomposition',
                'Schema mapping',
                'Query execution',
                'Knowledge enrichment' if enable_world_knowledge else 'Knowledge enrichment (skipped)',
                'Insight synthesis',
                'Follow-up generation',
                'Verbose analysis generation' if verbose_mode else None
            ],
            'execution_time_seconds': execution_time,
            'execution_summary': {
                'total_queries': len(results),
                'successful': sum(1 for r in results if r.success),
                'failed': sum(1 for r in results if not r.success),
                'methods_used': list(set(r.method for r in results))
            }
        }

        # Add verbose analysis fields if generated
        if verbose_mode and verbose_analysis:
            result.update({
                'executive_summary': verbose_analysis.get('executive_summary'),
                'methodology': verbose_analysis.get('methodology'),
                'detailed_findings': verbose_analysis.get('detailed_findings'),
                'cross_analysis': verbose_analysis.get('cross_analysis'),
                'limitations': verbose_analysis.get('limitations'),
                'recommendations': verbose_analysis.get('recommendations'),
                'technical_appendix': verbose_analysis.get('technical_appendix')
            })

        # Filter out None values from stages_completed
        result['stages_completed'] = [s for s in result['stages_completed'] if s is not None]

        return result

    async def _decompose_question(self,
                                  main_question: str,
                                  schema: Dict,
                                  max_count: int) -> List[SubQuestion]:
        """Stage 1: Break down main question into focused sub-questions"""

        prompt = f"""You are a data analysis expert. Decompose the user's question into specific sub-questions.

Main Question: {main_question}

Available Data Context:
- Tables: {', '.join([t['name'] for t in schema.get('tables', [])])}
- Total Columns: {len(schema.get('columns', []))}
- Row Count: {schema.get('row_count', 'unknown')}

Task: Generate {max_count} focused sub-questions that, if answered, would fully address the main question.

For each sub-question, provide:
1. question: The specific question text
2. intent_type: One of [descriptive, comparative, causal, trend_analysis, anomaly_detection, forecasting, segmentation]
3. desired_output: One of [table, number, chart, explanation]
4. priority: 1-3 (1=critical, 2=important, 3=nice-to-have)

Return ONLY valid JSON in this exact format:
{{
  "sub_questions": [
    {{
      "question": "What is the total revenue?",
      "intent_type": "descriptive",
      "desired_output": "number",
      "priority": 1
    }}
  ]
}}"""

        response = await self._call_llm(prompt)
        parsed = self._parse_json_response(response)

        sub_questions = []
        for sq in parsed.get('sub_questions', []):
            sub_questions.append(SubQuestion(
                question=sq['question'],
                intent_type=sq['intent_type'],
                desired_output=sq['desired_output'],
                priority=sq.get('priority', 2)
            ))

        return sub_questions

    async def _classify_and_map(self,
                                sub_questions: List[SubQuestion],
                                schema: Dict) -> List[ClassifiedQuestion]:
        """Stage 2: Classify each sub-question and map to schema"""

        # Build detailed schema description
        schema_desc = self._build_schema_description(schema)

        questions_text = "\n".join([
            f"{i+1}. {sq.question} (intent: {sq.intent_type})"
            for i, sq in enumerate(sub_questions)
        ])

        prompt = f"""You are a database expert. Classify each sub-question and map it to the available schema.

Database Schema:
{schema_desc}

Sub-Questions to Classify:
{questions_text}

For each question, determine:
1. category: One of [data_backed, world_knowledge, insufficient_data, mixed]
   - data_backed: Can be fully answered from the database
   - world_knowledge: Requires external domain knowledge
   - insufficient_data: Cannot be answered with available data
   - mixed: Needs both database data and external knowledge

2. candidate_tables: List of relevant table names (if data_backed or mixed)
3. candidate_columns: List of relevant column names (if data_backed or mixed)
4. feasibility: One of [high, medium, low, impossible]
5. notes: Brief explanation of reasoning

Return ONLY valid JSON:
{{
  "classifications": [
    {{
      "question_number": 1,
      "category": "data_backed",
      "candidate_tables": ["sales"],
      "candidate_columns": ["revenue", "date"],
      "feasibility": "high",
      "notes": "Direct aggregation of revenue column"
    }}
  ]
}}"""

        response = await self._call_llm(prompt)
        parsed = self._parse_json_response(response)

        classified = []
        for i, classification in enumerate(parsed.get('classifications', [])):
            if i < len(sub_questions):
                classified.append(ClassifiedQuestion(
                    sub_question=sub_questions[i],
                    category=classification['category'],
                    candidate_tables=classification.get('candidate_tables', []),
                    candidate_columns=classification.get('candidate_columns', []),
                    feasibility=classification.get('feasibility', 'unknown'),
                    notes=classification.get('notes', '')
                ))

        return classified

    async def _execute_queries(self,
                               classified: List[ClassifiedQuestion],
                               dataset_id: str,
                               schema: Dict,
                               enable_python: bool) -> List[AnalysisResult]:
        """Stage 3: Execute SQL/Python queries for data-backed questions"""

        results = []

        for cq in classified:
            if cq.category in ['data_backed', 'mixed'] and cq.feasibility in ['high', 'medium']:
                # Decide: SQL or Python?
                use_python = enable_python and cq.sub_question.intent_type in [
                    'causal', 'forecasting', 'anomaly_detection', 'trend_analysis'
                ]

                if use_python:
                    # Use Python for complex analytics
                    result = await self._execute_python_analysis(
                        cq.sub_question.question,
                        dataset_id,
                        cq.sub_question.intent_type
                    )
                else:
                    # Use SQL for straightforward queries
                    result = await self._execute_sql_query(
                        cq.sub_question.question,
                        dataset_id
                    )

                results.append(result)

            elif cq.category == 'world_knowledge':
                # Will be handled in enrichment stage
                pass

            elif cq.category == 'insufficient_data':
                results.append(AnalysisResult(
                    question=cq.sub_question.question,
                    method='none',
                    success=False,
                    error="Insufficient data to answer this question"
                ))

        return results

    async def _execute_sql_query(self,
                                 question: str,
                                 dataset_id: str) -> AnalysisResult:
        """Execute SQL query"""
        try:
            # Generate SQL
            sql_result = await self.nl_to_sql.generate_sql(question, dataset_id)

            # Execute
            df = self.duckdb_service.execute_query(
                sql_result['sql'],
                dataset_id
            )

            return AnalysisResult(
                question=question,
                method='sql',
                success=True,
                data={
                    'sql': sql_result['sql'],
                    'rows': len(df),
                    'preview': df.head(10).to_dict('records') if not df.empty else []
                }
            )
        except Exception as e:
            return AnalysisResult(
                question=question,
                method='sql',
                success=False,
                error=str(e)
            )

    async def _execute_python_analysis(self,
                                       question: str,
                                       dataset_id: str,
                                       intent_type: str) -> AnalysisResult:
        """Execute Python analysis"""
        try:
            # Generate Python code
            code_result = await self.nl_to_python.generate_python_code(
                nl_query=question,
                dataset_id=dataset_id,
                mode='stats' if intent_type in ['trend_analysis', 'forecasting'] else 'python'
            )

            # Execute
            exec_result = self.code_executor.execute_python(
                code=code_result['code'],
                dataset_id=dataset_id
            )

            if exec_result['status'] == 'SUCCESS':
                return AnalysisResult(
                    question=question,
                    method='python',
                    success=True,
                    data=exec_result.get('output'),
                    visualization=exec_result.get('visualizations')
                )
            else:
                return AnalysisResult(
                    question=question,
                    method='python',
                    success=False,
                    error=exec_result.get('error')
                )
        except Exception as e:
            return AnalysisResult(
                question=question,
                method='python',
                success=False,
                error=str(e)
            )

    async def _enrich_world_knowledge(self,
                                      classified: List[ClassifiedQuestion],
                                      results: List[AnalysisResult]) -> Dict[str, Any]:
        """Stage 4: Add world knowledge context"""

        world_knowledge_questions = [
            cq for cq in classified
            if cq.category in ['world_knowledge', 'mixed']
        ]

        if not world_knowledge_questions:
            return {}

        questions_text = "\n".join([
            f"- {cq.sub_question.question}"
            for cq in world_knowledge_questions
        ])

        prompt = f"""You are a domain expert. Provide context and world knowledge for these questions:

{questions_text}

For each question, provide:
1. A concise answer (2-3 sentences)
2. Industry benchmarks or typical values (if applicable)
3. Key concepts or definitions needed to understand the answer

Return as JSON:
{{
  "knowledge": [
    {{
      "question": "question text",
      "answer": "...",
      "benchmarks": "...",
      "concepts": ["concept1", "concept2"]
    }}
  ]
}}"""

        response = await self._call_llm(prompt)
        parsed = self._parse_json_response(response)

        return parsed

    async def _synthesize_insights(self,
                                   main_question: str,
                                   sub_questions: List[SubQuestion],
                                   classified: List[ClassifiedQuestion],
                                   results: List[AnalysisResult],
                                   world_knowledge: Dict,
                                   schema: Dict) -> Dict[str, Any]:
        """Stage 5: Synthesize all findings into comprehensive answer"""

        # Prepare context for LLM
        results_summary = self._summarize_results(results)
        coverage = self._analyze_coverage(classified, results)

        prompt = f"""You are a senior data analyst. Synthesize a comprehensive answer to the main question.

Main Question: {main_question}

Analysis Results:
{results_summary}

World Knowledge Context:
{json.dumps(world_knowledge, indent=2)}

Data Coverage:
- Questions answered from data: {coverage['data_backed']}
- Questions requiring world knowledge: {coverage['world_knowledge']}
- Questions unanswerable: {coverage['insufficient_data']}

Task: Create a comprehensive synthesis with:
1. direct_answer: 2-3 sentence direct answer to the main question
2. key_findings: 5-7 bullet points with specific numbers and insights
3. data_coverage: What was answered vs what's missing
4. gaps: List of data gaps that limited the analysis

Return as JSON:
{{
  "direct_answer": "...",
  "key_findings": ["finding 1", "finding 2", ...],
  "data_coverage": {{
    "answered_fully": ["question 1", ...],
    "answered_partially": ["question 2", ...],
    "not_answered": ["question 3", ...]
  }},
  "gaps": ["gap 1", "gap 2"]
}}"""

        response = await self._call_llm(prompt)
        synthesis = self._parse_json_response(response)

        # Add supporting details
        synthesis['supporting_details'] = [
            {
                'question': r.question,
                'method': r.method,
                'success': r.success,
                'data': r.data if r.success else None,
                'error': r.error if not r.success else None
            }
            for r in results
        ]

        return synthesis

    async def _suggest_follow_ups(self,
                                  main_question: str,
                                  synthesis: Dict,
                                  schema: Dict) -> List[Dict[str, str]]:
        """Stage 6: Suggest follow-up questions for deeper research"""

        prompt = f"""Based on the analysis results, suggest follow-up questions for deeper insights.

Original Question: {main_question}

Key Findings:
{json.dumps(synthesis.get('key_findings', []), indent=2)}

Gaps Identified:
{json.dumps(synthesis.get('gaps', []), indent=2)}

Generate 3-5 follow-up questions that would:
- Dig deeper into interesting findings
- Address identified gaps
- Provide actionable insights

Return as JSON:
{{
  "follow_ups": [
    {{
      "question": "Follow-up question text",
      "rationale": "Why this question is valuable",
      "category": "data_backed|world_knowledge|requires_new_data"
    }}
  ]
}}"""

        response = await self._call_llm(prompt)
        parsed = self._parse_json_response(response)

        return parsed.get('follow_ups', [])

    async def _generate_verbose_analysis(self,
                                        main_question: str,
                                        sub_questions: List[SubQuestion],
                                        classified: List[ClassifiedQuestion],
                                        results: List[Any],
                                        world_knowledge: Dict,
                                        synthesis: Dict,
                                        schema: Dict) -> Dict[str, Any]:
        """Generate comprehensive verbose analysis with multiple sections"""

        results_summary = self._summarize_results(results)

        # 1. Executive Summary (2-3 paragraphs)
        exec_summary_prompt = f"""You are a senior research analyst writing an executive summary.

Main Question: {main_question}

Key Findings:
{json.dumps(synthesis.get('key_findings', []), indent=2)}

Direct Answer:
{synthesis.get('direct_answer', '')}

Write a comprehensive 2-3 paragraph executive summary that:
- Opens with the most important insight
- Highlights critical findings with specific numbers
- Mentions methodology briefly
- Concludes with implications or recommendations

Return as JSON:
{{
  "executive_summary": "Full multi-paragraph text here..."
}}"""

        exec_response = await self._call_llm(exec_summary_prompt)
        exec_summary = self._parse_json_response(exec_response).get('executive_summary', '')

        # 2. Methodology & Data Sources
        methodology = {
            "total_sub_questions": len(sub_questions),
            "data_sources": {
                "dataset_columns": len(schema.get('columns', [])),
                "total_rows": schema.get('row_count', 0),
                "data_backed_queries": len([c for c in classified if c.category == 'data_backed']),
                "world_knowledge_queries": len([c for c in classified if c.category == 'world_knowledge'])
            },
            "analysis_methods": [
                "SQL queries for structured data analysis",
                "Python for statistical analysis and computations",
                "World knowledge enrichment via AI",
                "Cross-referential validation"
            ],
            "quality_metrics": {
                "successful_queries": len([r for r in results if r.success]),
                "total_queries": len(results),
                "coverage_percentage": round((len([r for r in results if r.success]) / len(results) * 100) if results else 0, 1)
            }
        }

        # 3. Detailed Findings (one entry per sub-question)
        detailed_findings_prompt = f"""For each sub-question analyzed, provide detailed findings with context and implications.

Main Question: {main_question}

Sub-Questions and Results:
{json.dumps([{{'question': sq.question, 'results': self._get_result_for_question(sq.question, results)}} for sq in sub_questions[:10]], indent=2)}

For each sub-question, provide:
- finding_title: Short descriptive title
- analysis: 2-3 sentences explaining what was found
- data_points: Specific numbers or facts discovered
- implications: What this means in context
- confidence: high/medium/low based on data quality

Return as JSON:
{{
  "detailed_findings": [
    {{
      "question": "sub-question text",
      "finding_title": "title",
      "analysis": "detailed explanation...",
      "data_points": ["specific fact 1", "specific fact 2"],
      "implications": "what this means...",
      "confidence": "high"
    }}
  ]
}}"""

        detailed_response = await self._call_llm(detailed_findings_prompt)
        detailed_findings = self._parse_json_response(detailed_response).get('detailed_findings', [])

        # 4. Cross-Analysis & Patterns
        cross_analysis_prompt = f"""Analyze patterns and connections across all findings.

Key Findings:
{json.dumps(synthesis.get('key_findings', []), indent=2)}

World Knowledge:
{json.dumps(world_knowledge, indent=2)[:2000]}

Identify:
- Common themes or patterns
- Surprising correlations
- Contradictions or anomalies
- Temporal trends if applicable

Return as JSON:
{{
  "patterns": ["pattern 1", "pattern 2"],
  "correlations": ["correlation 1"],
  "anomalies": ["anomaly 1"],
  "trends": ["trend 1"]
}}"""

        cross_response = await self._call_llm(cross_analysis_prompt)
        cross_analysis = self._parse_json_response(cross_response)

        # 5. Limitations & Caveats
        limitations_prompt = f"""Identify limitations and caveats of this analysis.

Data Coverage:
{json.dumps(synthesis.get('data_coverage', {}), indent=2)}

Gaps:
{json.dumps(synthesis.get('gaps', []), indent=2)}

Analysis Methods:
- SQL queries, Python analysis, World knowledge

Provide honest assessment of:
- Data quality issues
- Missing information
- Assumptions made
- Methodological limitations
- Generalizability constraints

Return as JSON:
{{
  "limitations": [
    "Limitation 1 with explanation",
    "Limitation 2 with explanation"
  ]
}}"""

        limitations_response = await self._call_llm(limitations_prompt)
        limitations = self._parse_json_response(limitations_response).get('limitations', [])

        # 6. Recommendations & Next Steps
        recommendations_prompt = f"""Based on findings, provide actionable recommendations.

Main Question: {main_question}

Key Findings:
{json.dumps(synthesis.get('key_findings', []), indent=2)}

Limitations:
{json.dumps(limitations, indent=2)}

Provide 3-5 specific, actionable recommendations with:
- What to do
- Why it matters
- Priority (high/medium/low)
- Required resources/data if applicable

Return as JSON:
{{
  "recommendations": [
    {{
      "recommendation": "specific action",
      "rationale": "why this is important",
      "priority": "high",
      "requirements": "what's needed"
    }}
  ]
}}"""

        recommendations_response = await self._call_llm(recommendations_prompt)
        recommendations = self._parse_json_response(recommendations_response).get('recommendations', [])

        # 7. Technical Appendix
        technical_appendix = {
            "queries_executed": [
                {
                    "question": r.question,
                    "method": r.method,
                    "success": r.success,
                    "execution_time_ms": getattr(r, 'execution_time_ms', None)
                }
                for r in results[:20]  # Limit to first 20
            ],
            "schema_summary": {
                "columns": [
                    {
                        "name": col.get('name'),
                        "type": col.get('dtype'),
                        "sample_values": col.get('stats', {}).get('top_values', [])[:3] if 'stats' in col else []
                    }
                    for col in schema.get('columns', [])[:15]
                ],
                "total_columns": len(schema.get('columns', [])),
                "total_rows": schema.get('row_count', 0)
            },
            "classification_breakdown": {
                "data_backed": len([c for c in classified if c.category == 'data_backed']),
                "world_knowledge": len([c for c in classified if c.category == 'world_knowledge']),
                "mixed": len([c for c in classified if c.category == 'mixed']),
                "insufficient_data": len([c for c in classified if c.category == 'insufficient_data'])
            }
        }

        return {
            "executive_summary": exec_summary,
            "methodology": methodology,
            "detailed_findings": detailed_findings,
            "cross_analysis": cross_analysis,
            "limitations": limitations,
            "recommendations": recommendations,
            "technical_appendix": technical_appendix
        }

    def _get_result_for_question(self, question: str, results: List[Any]) -> Dict:
        """Helper to find result for a specific question"""
        for r in results:
            if r.question == question:
                return {
                    "success": r.success,
                    "data": r.data if r.success else None,
                    "error": r.error if not r.success else None
                }
        return {"success": False, "data": None, "error": "Not found"}

    # Helper methods

    def _build_schema_description(self, schema: Dict) -> str:
        """Build human-readable schema description"""
        lines = []
        for col in schema.get('columns', [])[:20]:  # Limit to first 20 columns
            stats_info = ""
            if 'stats' in col:
                if 'top_values' in col['stats']:
                    examples = [v[0] for v in col['stats']['top_values'][:3]]
                    stats_info = f" (examples: {examples})"
                elif 'min' in col['stats'] and 'max' in col['stats']:
                    stats_info = f" (range: {col['stats']['min']} to {col['stats']['max']})"

            lines.append(f"- {col['name']} ({col['dtype']}){stats_info}")

        return "\n".join(lines)

    def _summarize_results(self, results: List[AnalysisResult]) -> str:
        """Create text summary of results"""
        summary_lines = []
        for i, r in enumerate(results, 1):
            if r.success:
                summary_lines.append(f"{i}. ✓ {r.question} ({r.method})")
                if r.data:
                    summary_lines.append(f"   Result: {str(r.data)[:200]}")
            else:
                summary_lines.append(f"{i}. ✗ {r.question} - Error: {r.error}")

        return "\n".join(summary_lines)

    def _analyze_coverage(self,
                         classified: List[ClassifiedQuestion],
                         results: List[AnalysisResult]) -> Dict[str, int]:
        """Analyze what was covered"""
        return {
            'data_backed': sum(1 for c in classified if c.category == 'data_backed'),
            'world_knowledge': sum(1 for c in classified if c.category == 'world_knowledge'),
            'mixed': sum(1 for c in classified if c.category == 'mixed'),
            'insufficient_data': sum(1 for c in classified if c.category == 'insufficient_data'),
            'successful_queries': sum(1 for r in results if r.success)
        }

    async def _call_llm(self, prompt: str) -> str:
        """Call OpenRouter API"""
        print(f"🤖 [Deep Research] Calling OpenRouter API with model: {settings.OPENROUTER_MODEL}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

    def _parse_json_response(self, response: str) -> Dict:
        """Extract and parse JSON from LLM response"""
        # Try to find JSON in response
        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)

        # Fallback: try to parse entire response
        return json.loads(response)
