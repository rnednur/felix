"""
Research Job Persistence Service

Saves research results to filesystem for later retrieval
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings


class ResearchPersistenceService:
    """Persist and retrieve research jobs from filesystem"""

    def __init__(self):
        # Create research results directory
        self.research_dir = Path(settings.DATA_DIR) / "research_jobs"
        self.research_dir.mkdir(parents=True, exist_ok=True)

    def save_research(
        self,
        dataset_id: str,
        research_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save research result to filesystem

        Args:
            dataset_id: ID of dataset analyzed
            research_result: Complete research output from DeepResearchService
            metadata: Optional metadata (user info, tags, etc.)

        Returns:
            research_id: Unique ID for this research job
        """
        # Generate unique research ID
        research_id = research_result.get('research_id')
        if not research_id:
            timestamp = datetime.utcnow().timestamp()
            research_id = f"research_{int(timestamp)}"

        # Prepare complete record
        record = {
            'research_id': research_id,
            'dataset_id': dataset_id,
            'saved_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {},
            'result': research_result
        }

        # Save to JSON file
        file_path = self.research_dir / f"{research_id}.json"
        with open(file_path, 'w') as f:
            json.dump(record, f, indent=2, default=str)

        print(f"✅ Saved research job: {research_id}")
        return research_id

    def load_research(self, research_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved research result

        Args:
            research_id: ID of research to load

        Returns:
            Complete research record or None if not found
        """
        file_path = self.research_dir / f"{research_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            record = json.load(f)

        return record

    def list_research_jobs(
        self,
        dataset_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List saved research jobs

        Args:
            dataset_id: Filter by dataset (optional)
            limit: Maximum number of results

        Returns:
            List of research job summaries (most recent first)
        """
        jobs = []

        # Read all research files
        for file_path in self.research_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    record = json.load(f)

                # Filter by dataset if specified
                if dataset_id and record.get('dataset_id') != dataset_id:
                    continue

                # Create summary (exclude full result to keep response small)
                summary = {
                    'research_id': record['research_id'],
                    'dataset_id': record['dataset_id'],
                    'main_question': record['result'].get('main_question', 'Unknown'),
                    'direct_answer': record['result'].get('direct_answer', '')[:200],  # Truncate
                    'key_findings_count': len(record['result'].get('key_findings', [])),
                    'has_verbose_analysis': 'executive_summary' in record['result'],
                    'saved_at': record['saved_at'],
                    'execution_time': record['result'].get('execution_time_seconds', 0),
                    'stages_completed': record['result'].get('stages_completed', []),
                    'metadata': record.get('metadata', {})
                }

                jobs.append(summary)

            except Exception as e:
                print(f"⚠️ Failed to read research file {file_path}: {str(e)}")
                continue

        # Sort by saved_at (most recent first)
        jobs.sort(key=lambda x: x['saved_at'], reverse=True)

        return jobs[:limit]

    def delete_research(self, research_id: str) -> bool:
        """
        Delete a saved research job

        Args:
            research_id: ID of research to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self.research_dir / f"{research_id}.json"

        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ Deleted research job: {research_id}")
            return True

        return False

    def get_research_summary(self, research_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of a research job (without full result)

        Args:
            research_id: ID of research

        Returns:
            Summary dict or None
        """
        record = self.load_research(research_id)

        if not record:
            return None

        return {
            'research_id': record['research_id'],
            'dataset_id': record['dataset_id'],
            'main_question': record['result'].get('main_question'),
            'direct_answer': record['result'].get('direct_answer'),
            'key_findings': record['result'].get('key_findings', []),
            'saved_at': record['saved_at'],
            'execution_time': record['result'].get('execution_time_seconds'),
            'has_verbose_analysis': 'executive_summary' in record['result'],
            'metadata': record.get('metadata', {})
        }

    def update_metadata(
        self,
        research_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for a research job (e.g., add tags, notes)

        Args:
            research_id: ID of research
            metadata: New metadata to merge

        Returns:
            True if updated, False if not found
        """
        record = self.load_research(research_id)

        if not record:
            return False

        # Merge metadata
        record['metadata'].update(metadata)
        record['updated_at'] = datetime.utcnow().isoformat()

        # Save back
        file_path = self.research_dir / f"{research_id}.json"
        with open(file_path, 'w') as f:
            json.dump(record, f, indent=2, default=str)

        return True

    def search_research(
        self,
        query: str,
        dataset_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search research jobs by question or findings

        Args:
            query: Search term
            dataset_id: Filter by dataset (optional)
            limit: Maximum results

        Returns:
            List of matching research summaries
        """
        query_lower = query.lower()
        matches = []

        for file_path in self.research_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    record = json.load(f)

                # Filter by dataset
                if dataset_id and record.get('dataset_id') != dataset_id:
                    continue

                # Search in question and answer
                main_question = record['result'].get('main_question', '').lower()
                direct_answer = record['result'].get('direct_answer', '').lower()
                key_findings = ' '.join(record['result'].get('key_findings', [])).lower()

                if (query_lower in main_question or
                    query_lower in direct_answer or
                    query_lower in key_findings):

                    matches.append({
                        'research_id': record['research_id'],
                        'dataset_id': record['dataset_id'],
                        'main_question': record['result'].get('main_question'),
                        'direct_answer': record['result'].get('direct_answer')[:200],
                        'saved_at': record['saved_at'],
                        'relevance_score': self._calculate_relevance(
                            query_lower, main_question, direct_answer, key_findings
                        )
                    })

            except Exception as e:
                continue

        # Sort by relevance
        matches.sort(key=lambda x: x['relevance_score'], reverse=True)

        return matches[:limit]

    def _calculate_relevance(
        self,
        query: str,
        question: str,
        answer: str,
        findings: str
    ) -> float:
        """Simple relevance scoring"""
        score = 0.0

        # Question match = highest weight
        if query in question:
            score += 10.0

        # Answer match = medium weight
        if query in answer:
            score += 5.0

        # Findings match = lower weight
        if query in findings:
            score += 2.0

        return score
