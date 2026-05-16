"""
Skills System - Anthropic-style skills for agent enhancement

This module provides the skills framework for enhancing agent capabilities
with instruction-based expertise.
"""
from pathlib import Path
import logging

from app.skills.loader import SkillLoader
from app.skills.catalog import get_skill_catalog, init_skill_catalog
from app.skills.context_builder import get_context_builder


logger = logging.getLogger("skills")


def init_skills_system(skills_dir: str = "backend/skills"):
    """
    Initialize the skills system by loading builtin skills

    Args:
        skills_dir: Directory containing SKILL.md files

    Returns:
        SkillCatalog instance
    """
    logger.info(f"🎓 Initializing skills system from: {skills_dir}")

    # Initialize catalog
    catalog = init_skill_catalog()

    # Load skills from directory
    skills_path = Path(skills_dir)

    if not skills_path.exists():
        logger.warning(f"⚠️  Skills directory not found: {skills_dir}")
        return catalog

    # Find all SKILL.md files
    skill_files = list(skills_path.glob("*.md"))

    if not skill_files:
        logger.warning(f"⚠️  No skill files found in: {skills_dir}")
        return catalog

    logger.info(f"📖 Found {len(skill_files)} skill files")

    # Load each skill
    loader = SkillLoader()
    loaded_count = 0

    for skill_file in skill_files:
        try:
            logger.info(f"Loading skill: {skill_file.name}")
            skill = loader.load_from_file(skill_file)

            if skill:
                catalog.register_skill(skill)
                logger.info(f"✅ Registered skill: {skill.metadata.name}")
                loaded_count += 1
            else:
                logger.warning(f"⚠️  Failed to parse skill: {skill_file.name}")

        except Exception as e:
            logger.error(f"❌ Error loading skill {skill_file.name}: {str(e)}")

    logger.info(
        f"✅ Skills system initialized: {loaded_count}/{len(skill_files)} skills loaded"
    )
    logger.info(
        f"📊 Catalog status: {catalog.get_enabled_count()} enabled, "
        f"{catalog.get_skill_count()} total"
    )

    return catalog


def setup_skills(skills_dir: str = "backend/skills"):
    """
    Setup skills system (alias for init_skills_system)

    Can be called during app startup.

    Args:
        skills_dir: Directory containing skill files
    """
    return init_skills_system(skills_dir)


__all__ = [
    'init_skills_system',
    'setup_skills',
    'get_skill_catalog',
    'get_context_builder'
]
