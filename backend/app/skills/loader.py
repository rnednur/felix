"""
Skill Loader - parse and load SKILL.md files

Parses Anthropic-style skills with YAML frontmatter and markdown content.
"""
import yaml
import re
from pathlib import Path
from typing import Optional, List
import logging

from app.schemas.skill import (
    Skill,
    SkillMetadata,
    SkillContent,
    SkillSection,
    SkillExample,
    SkillType,
    SkillScope
)


logger = logging.getLogger("skill.loader")


class SkillLoader:
    """
    Loads and parses SKILL.md files

    Format:
    ```markdown
    ---
    name: skill-name
    description: Skill description
    tags: [tag1, tag2]
    version: 1.0.0
    ---

    # Skill Content

    ## Section 1
    Content...

    ## Examples
    ...
    ```
    """

    def load_from_file(self, file_path: Path) -> Optional[Skill]:
        """
        Load skill from SKILL.md file

        Args:
            file_path: Path to SKILL.md file

        Returns:
            Skill object or None if failed
        """
        try:
            if not file_path.exists():
                logger.error(f"Skill file not found: {file_path}")
                return None

            # Read file
            content = file_path.read_text(encoding='utf-8')

            # Parse
            skill = self.parse_skill_content(content)

            if skill:
                logger.info(f"Loaded skill: {skill.metadata.name}")
                return skill

            return None

        except Exception as e:
            logger.error(f"Failed to load skill from {file_path}: {str(e)}", exc_info=True)
            return None

    def parse_skill_content(self, content: str) -> Optional[Skill]:
        """
        Parse skill content with YAML frontmatter

        Args:
            content: Full SKILL.md content

        Returns:
            Skill object or None if parsing failed
        """
        try:
            # Split frontmatter and body
            parts = content.split('---', 2)

            if len(parts) < 3:
                logger.error("Invalid skill format: missing frontmatter delimiters")
                return None

            # Parse YAML frontmatter
            frontmatter = parts[1].strip()
            markdown_body = parts[2].strip()

            metadata_dict = yaml.safe_load(frontmatter)

            # Validate required fields
            if 'name' not in metadata_dict or 'description' not in metadata_dict:
                logger.error("Skill missing required fields: name, description")
                return None

            # Parse metadata
            metadata = self._parse_metadata(metadata_dict)

            # Parse markdown content
            skill_content = self._parse_markdown_content(markdown_body)

            # Create skill
            skill = Skill(
                metadata=metadata,
                content=skill_content,
                raw_content=markdown_body,
                type=SkillType.BUILTIN  # Default, can be changed
            )

            return skill

        except Exception as e:
            logger.error(f"Failed to parse skill content: {str(e)}", exc_info=True)
            return None

    def _parse_metadata(self, data: dict) -> SkillMetadata:
        """Parse metadata from frontmatter dict"""
        # Handle scope enum
        scope_str = data.get('scope', 'general')
        try:
            scope = SkillScope(scope_str)
        except ValueError:
            scope = SkillScope.GENERAL

        return SkillMetadata(
            name=data['name'],
            description=data['description'],
            tags=data.get('tags', []),
            version=data.get('version', '1.0.0'),
            author=data.get('author'),
            scope=scope,
            prerequisites=data.get('prerequisites', []),
            related_skills=data.get('related_skills', []),
            recommended_tools=data.get('recommended_tools', [])
        )

    def _parse_markdown_content(self, markdown: str) -> SkillContent:
        """
        Parse markdown content into structured format

        Args:
            markdown: Markdown content after frontmatter

        Returns:
            SkillContent object
        """
        # Split by h2 headers (##)
        sections = []
        current_section = None
        overview = ""
        workflow = None
        examples = []
        best_practices = []
        warnings = []

        lines = markdown.split('\n')
        current_content = []

        for line in lines:
            # H1 header (skip, usually just title)
            if line.startswith('# '):
                continue

            # H2 header
            elif line.startswith('## '):
                # Save previous section
                if current_section:
                    content = '\n'.join(current_content).strip()

                    # Handle special sections
                    if current_section.lower() == 'overview':
                        overview = content
                    elif current_section.lower() == 'workflow':
                        workflow = content
                    elif current_section.lower() == 'examples':
                        examples = self._parse_examples(content)
                    elif current_section.lower() == 'best practices':
                        best_practices = self._parse_list_items(content)
                    elif current_section.lower() in ['warnings', 'important warnings', 'cautions']:
                        warnings = self._parse_list_items(content)
                    else:
                        # Regular section
                        sections.append(SkillSection(
                            title=current_section,
                            content=content
                        ))

                    current_content = []

                # Start new section
                current_section = line[3:].strip()

            else:
                current_content.append(line)

        # Save last section
        if current_section:
            content = '\n'.join(current_content).strip()

            if current_section.lower() == 'overview':
                overview = content
            elif current_section.lower() == 'workflow':
                workflow = content
            elif current_section.lower() == 'examples':
                examples = self._parse_examples(content)
            elif current_section.lower() == 'best practices':
                best_practices = self._parse_list_items(content)
            elif current_section.lower() in ['warnings', 'important warnings']:
                warnings = self._parse_list_items(content)
            else:
                sections.append(SkillSection(
                    title=current_section,
                    content=content
                ))

        # If no overview section, use first paragraph
        if not overview and markdown:
            first_para = markdown.split('\n\n')[0]
            if not first_para.startswith('#'):
                overview = first_para

        return SkillContent(
            overview=overview,
            workflow=workflow,
            sections=sections,
            examples=examples,
            best_practices=best_practices,
            warnings=warnings
        )

    def _parse_examples(self, content: str) -> List[SkillExample]:
        """Parse examples from content"""
        examples = []

        # Split by h3 headers (###)
        example_parts = re.split(r'\n### ', content)

        for part in example_parts:
            if not part.strip():
                continue

            lines = part.strip().split('\n')
            title = lines[0].strip()

            # Extract goal, steps, expected
            goal = ""
            steps = []
            expected = None

            current_section = None

            for line in lines[1:]:
                if line.startswith('**Goal**:'):
                    goal = line.replace('**Goal**:', '').strip()
                    current_section = 'goal'
                elif line.startswith('**Steps**:'):
                    current_section = 'steps'
                elif line.startswith('**Expected'):
                    expected = line.split(':', 1)[1].strip() if ':' in line else ""
                    current_section = 'expected'
                elif current_section == 'steps' and (line.startswith('1.') or line.strip().startswith('-')):
                    # Parse step
                    step_text = re.sub(r'^\d+\.\s*|^-\s*', '', line).strip()
                    if step_text:
                        steps.append(step_text)

            if title and (goal or steps):
                examples.append(SkillExample(
                    title=title,
                    goal=goal,
                    steps=steps,
                    expected_outcome=expected
                ))

        return examples

    def _parse_list_items(self, content: str) -> List[str]:
        """Parse list items (best practices, warnings)"""
        items = []

        for line in content.split('\n'):
            line = line.strip()

            # Match list items
            if line.startswith('- ') or line.startswith('* '):
                item = line[2:].strip()
                # Remove warning emoji if present
                item = item.replace('⚠️', '').strip()
                if item:
                    items.append(item)
            elif line.startswith('•'):
                item = line[1:].strip()
                if item:
                    items.append(item)

        return items

    def load_from_directory(self, directory: Path) -> List[Skill]:
        """
        Load all skills from a directory

        Args:
            directory: Directory containing skill folders

        Returns:
            List of loaded skills
        """
        skills = []

        if not directory.exists():
            logger.warning(f"Skills directory not found: {directory}")
            return skills

        # Find all SKILL.md files
        for skill_file in directory.rglob('SKILL.md'):
            skill = self.load_from_file(skill_file)
            if skill:
                skills.append(skill)

        logger.info(f"Loaded {len(skills)} skills from {directory}")
        return skills
