"""Service for applying query rules to SQL generation"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.column_metadata import QueryRule, ColumnMetadata


class RuleService:
    """Apply business rules to queries"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_rules(self, dataset_id: str) -> List[QueryRule]:
        """Get all active rules for a dataset, ordered by priority"""
        return self.db.query(QueryRule).filter(
            QueryRule.dataset_id == dataset_id,
            QueryRule.is_active == True
        ).order_by(QueryRule.priority.desc()).all()

    def get_column_metadata(self, dataset_id: str) -> Dict[str, ColumnMetadata]:
        """Get column metadata as a dictionary"""
        metadata_list = self.db.query(ColumnMetadata).filter(
            ColumnMetadata.dataset_id == dataset_id
        ).all()

        return {m.column_name: m for m in metadata_list}

    def apply_rules_to_sql(self, sql: str, dataset_id: str) -> str:
        """Apply query rules to modify SQL"""
        rules = self.get_active_rules(dataset_id)

        if not rules:
            return sql

        # Parse and modify SQL based on rules
        modified_sql = sql

        for rule in rules:
            if rule.rule_type == "filter":
                modified_sql = self._apply_filter_rule(modified_sql, rule)
            elif rule.rule_type == "exclude_column":
                modified_sql = self._apply_exclude_column_rule(modified_sql, rule)
            elif rule.rule_type == "always_include":
                modified_sql = self._apply_always_include_rule(modified_sql, rule)

        return modified_sql

    def _apply_filter_rule(self, sql: str, rule: QueryRule) -> str:
        """Add WHERE clause filter"""
        condition = rule.condition
        column = condition.get('column')
        operator = condition.get('operator', '=')
        value = condition.get('value')

        # Build filter clause
        if operator.lower() == 'between':
            filter_clause = f'"{column}" BETWEEN \'{value[0]}\' AND \'{value[1]}\''
        elif operator in ['=', '!=', '>', '<', '>=', '<=']:
            if isinstance(value, str):
                filter_clause = f'"{column}" {operator} \'{value}\''
            else:
                filter_clause = f'"{column}" {operator} {value}'
        elif operator.lower() == 'in':
            values_str = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in value])
            filter_clause = f'"{column}" IN ({values_str})'
        else:
            return sql  # Unknown operator

        # Add to WHERE clause
        if 'WHERE' in sql.upper():
            # Already has WHERE, add AND
            sql = sql.replace('WHERE', f'WHERE {filter_clause} AND', 1)
        else:
            # Add WHERE before ORDER BY, GROUP BY, or LIMIT
            for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT']:
                if keyword in sql.upper():
                    sql = sql.replace(keyword, f'WHERE {filter_clause} {keyword}', 1)
                    return sql
            # No sorting/grouping, add at end
            sql = f'{sql.rstrip()} WHERE {filter_clause}'

        return sql

    def _apply_exclude_column_rule(self, sql: str, rule: QueryRule) -> str:
        """Remove column from SELECT"""
        column = rule.condition.get('column')

        # Replace SELECT * with explicit columns minus excluded
        if 'SELECT *' in sql.upper():
            # Would need schema to expand *, skip for now
            pass
        else:
            # Remove specific column reference
            # This is simplified - production would need proper SQL parsing
            sql = sql.replace(f'"{column}"', '')
            sql = sql.replace(f', ,', ',')  # Clean up double commas

        return sql

    def _apply_always_include_rule(self, sql: str, rule: QueryRule) -> str:
        """Ensure a filter is always applied"""
        # Same as filter rule
        return self._apply_filter_rule(sql, rule)

    def get_rules_context_for_llm(self, dataset_id: str) -> str:
        """Generate context about rules to include in LLM prompt"""
        rules = self.get_active_rules(dataset_id)
        metadata = self.get_column_metadata(dataset_id)

        if not rules and not metadata:
            return ""

        context = "\n\nBUSINESS RULES AND METADATA:\n"

        # Add column metadata
        if metadata:
            context += "\nColumn Metadata:\n"
            for col_name, meta in metadata.items():
                parts = [f'- "{col_name}"']
                if meta.display_name:
                    parts.append(f"(Display: {meta.display_name})")
                if meta.description:
                    parts.append(f": {meta.description}")
                if meta.semantic_type:
                    parts.append(f"[Type: {meta.semantic_type}]")
                if meta.unit:
                    parts.append(f"[Unit: {meta.unit}]")
                if meta.is_pii:
                    parts.append("[PII - Handle with care]")
                if meta.default_aggregation:
                    parts.append(f"[Default agg: {meta.default_aggregation}]")

                context += ' '.join(parts) + "\n"

        # Add rules
        if rules:
            context += "\nAutomatic Query Rules (will be applied to your query):\n"
            for rule in rules:
                context += f"- {rule.name}: {rule.description or 'No description'}\n"
                context += f"  Type: {rule.rule_type}, Condition: {rule.condition}\n"

        return context
