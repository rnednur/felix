"""
Celery tasks for async deep research execution
"""
from celery import Task
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.research_job import ResearchJob, ResearchJobStatus
from app.services.deep_research_service import DeepResearchService


class CallbackTask(Task):
    """Base task with callbacks for status updates"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        db = SessionLocal()
        try:
            job = db.query(ResearchJob).filter(ResearchJob.celery_task_id == task_id).first()
            if job:
                job.status = ResearchJobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.utcnow()
                if job.started_at:
                    job.execution_time_seconds = int((job.completed_at - job.started_at).total_seconds())
                db.commit()
        finally:
            db.close()


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.research_tasks.run_deep_research")
def run_deep_research(self, job_id: str, dataset_id: str, main_question: str, verbose: int = 0):
    """
    Run deep research analysis asynchronously

    Args:
        job_id: ResearchJob ID
        dataset_id: Dataset ID
        main_question: Main research question
        verbose: Verbose mode (0 or 1)
    """
    db = SessionLocal()

    try:
        # Update job status to running
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = ResearchJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.current_stage = "Initializing deep research..."
        job.progress_percentage = 5
        db.commit()

        # Initialize service
        research_service = DeepResearchService()

        # Stage 1: Decompose question
        job.current_stage = "Stage 1/7: Decomposing question"
        job.progress_percentage = 10
        db.commit()

        sub_questions = research_service._decompose_question(main_question)

        # Stage 2: Classify queries
        job.current_stage = "Stage 2/7: Classifying queries"
        job.progress_percentage = 20
        db.commit()

        classified_queries = research_service._classify_queries(sub_questions, dataset_id)

        # Stage 3: Execute queries
        job.current_stage = "Stage 3/7: Executing queries"
        job.progress_percentage = 35
        db.commit()

        analysis_results = research_service._execute_queries(classified_queries, dataset_id)

        # Stage 4: Enrich with follow-ups
        job.current_stage = "Stage 4/7: Enriching with follow-ups"
        job.progress_percentage = 55
        db.commit()

        enriched_results = research_service._enrich_with_followups(analysis_results, dataset_id)

        # Stage 5: Synthesize findings
        job.current_stage = "Stage 5/7: Synthesizing findings"
        job.progress_percentage = 70
        db.commit()

        synthesis = research_service._synthesize_findings(main_question, enriched_results)

        # Stage 6: Generate additional follow-ups
        job.current_stage = "Stage 6/7: Generating follow-ups"
        job.progress_percentage = 80
        db.commit()

        additional_followups = research_service._generate_additional_followups(
            main_question, synthesis, enriched_results
        )

        # Build response
        response = {
            "research_id": job_id,
            "main_question": main_question,
            "direct_answer": synthesis.get("direct_answer", ""),
            "key_findings": synthesis.get("key_findings", []),
            "supporting_details": [
                {
                    "question": r.question,
                    "query_type": r.query_type,
                    "answer": r.answer,
                    "data": r.data,
                    "code": r.code,
                    "error": r.error,
                    "confidence": r.confidence,
                    "follow_up_questions": r.follow_up_questions,
                }
                for r in enriched_results
            ],
            "limitations": synthesis.get("limitations", []),
            "suggested_follow_ups": additional_followups,
            "execution_time": None,  # Will be set below
        }

        # Stage 7: Generate verbose analysis (if requested)
        if verbose == 1:
            job.current_stage = "Stage 7/7: Generating verbose analysis"
            job.progress_percentage = 90
            db.commit()

            verbose_analysis = research_service._generate_verbose_analysis(
                main_question, enriched_results, synthesis
            )

            response.update({
                "methodology": verbose_analysis.get("methodology"),
                "data_quality_assessment": verbose_analysis.get("data_quality_assessment"),
                "statistical_rigor": verbose_analysis.get("statistical_rigor"),
                "alternative_interpretations": verbose_analysis.get("alternative_interpretations"),
                "confidence_intervals": verbose_analysis.get("confidence_intervals"),
                "recommendations": verbose_analysis.get("recommendations"),
                "technical_appendix": verbose_analysis.get("technical_appendix"),
            })

        # Mark as completed
        job.status = ResearchJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.execution_time_seconds = int((job.completed_at - job.started_at).total_seconds())
        job.current_stage = "Completed"
        job.progress_percentage = 100

        response["execution_time"] = job.execution_time_seconds
        job.result = response

        db.commit()

        return response

    except Exception as e:
        # Error handling is done in on_failure callback
        raise

    finally:
        db.close()
