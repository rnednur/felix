"""
Skills API Endpoints - manage and discover skills
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.skills.catalog import get_skill_catalog
from app.skills.context_builder import get_context_builder
from app.schemas.skill import (
    Skill,
    SkillMetadata,
    SkillDiscoveryRequest,
    SkillDiscoveryResponse,
    SkillScope,
    SkillEvaluation
)


router = APIRouter()


# Request/Response Models

class SkillListResponse(BaseModel):
    """Response for listing skills"""
    skills: List[Skill]
    total_count: int
    enabled_count: int


class SkillDetailResponse(BaseModel):
    """Response for single skill"""
    skill: Skill


class SkillContextRequest(BaseModel):
    """Request for skill context"""
    skill_names: List[str]
    include_examples: bool = True
    include_best_practices: bool = True
    include_warnings: bool = True
    max_tokens: int = 2000


class SkillContextResponse(BaseModel):
    """Response with formatted skill context"""
    context: str
    skill_count: int
    estimated_tokens: int


class SkillEnableRequest(BaseModel):
    """Request to enable/disable skill"""
    enabled: bool


# Endpoints

@router.get("/", response_model=SkillListResponse)
async def list_skills(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (any match)"),
    enabled_only: bool = Query(True, description="Only return enabled skills")
):
    """
    List all available skills

    Optionally filter by scope and tags.
    """
    catalog = get_skill_catalog()

    # Parse scope
    scope_enum = None
    if scope:
        try:
            scope_enum = SkillScope(scope)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scope. Must be one of: {[s.value for s in SkillScope]}"
            )

    # Get skills
    skills = catalog.list_skills(
        scope=scope_enum,
        tags=tags,
        enabled_only=enabled_only
    )

    return SkillListResponse(
        skills=skills,
        total_count=catalog.get_skill_count(),
        enabled_count=catalog.get_enabled_count()
    )


@router.get("/{skill_name}", response_model=SkillDetailResponse)
async def get_skill(skill_name: str):
    """
    Get a specific skill by name

    Returns full skill details including all sections and examples.
    """
    catalog = get_skill_catalog()
    skill = catalog.get_skill(skill_name)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill not found: {skill_name}"
        )

    return SkillDetailResponse(skill=skill)


@router.post("/discover", response_model=SkillDiscoveryResponse)
async def discover_skills(request: SkillDiscoveryRequest):
    """
    Discover skills relevant to a task

    Given a task description, finds the most relevant skills
    with confidence scores.
    """
    catalog = get_skill_catalog()
    response = catalog.discover_skills(request)

    return response


@router.post("/context", response_model=SkillContextResponse)
async def get_skill_context(request: SkillContextRequest):
    """
    Get formatted context for specific skills

    Returns LLM-ready context string for the specified skills,
    formatted for injection into prompts.
    """
    catalog = get_skill_catalog()

    # Get skills
    skills = [
        catalog.get_skill(name)
        for name in request.skill_names
        if catalog.get_skill(name) is not None
    ]

    if not skills:
        raise HTTPException(
            status_code=404,
            detail=f"No skills found with names: {request.skill_names}"
        )

    # Build context
    context_builder = get_context_builder(max_tokens=request.max_tokens)

    context = context_builder.build_context(
        skills=skills,
        include_examples=request.include_examples,
        include_best_practices=request.include_best_practices,
        include_warnings=request.include_warnings
    )

    return SkillContextResponse(
        context=context,
        skill_count=len(skills),
        estimated_tokens=len(context) // 4  # Rough estimate
    )


@router.get("/search/tags", response_model=SkillListResponse)
async def search_by_tags(
    tags: List[str] = Query(..., description="Tags to search for"),
    match_all: bool = Query(False, description="Require all tags (AND) vs any tag (OR)")
):
    """
    Search skills by tags

    With match_all=False (default), returns skills with any of the tags.
    With match_all=True, returns only skills with all tags.
    """
    catalog = get_skill_catalog()
    skills = catalog.search_by_tags(tags, match_all=match_all)

    return SkillListResponse(
        skills=skills,
        total_count=catalog.get_skill_count(),
        enabled_count=catalog.get_enabled_count()
    )


@router.get("/search/name", response_model=SkillListResponse)
async def search_by_name(
    query: str = Query(..., description="Search query")
):
    """
    Search skills by name or description

    Performs fuzzy matching on skill names and descriptions.
    """
    catalog = get_skill_catalog()
    skills = catalog.search_by_name(query)

    return SkillListResponse(
        skills=skills,
        total_count=catalog.get_skill_count(),
        enabled_count=catalog.get_enabled_count()
    )


@router.get("/scopes", response_model=List[str])
async def get_scopes():
    """
    Get list of all skill scopes

    Returns unique scopes from all registered skills.
    """
    catalog = get_skill_catalog()
    scopes = catalog.get_scopes()

    return [scope.value for scope in scopes]


@router.get("/scope/{scope}", response_model=SkillListResponse)
async def get_skills_by_scope(scope: str):
    """
    Get all skills in a specific scope

    Scope must be one of: global, agent, workflow, task.
    """
    try:
        scope_enum = SkillScope(scope)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope. Must be one of: {[s.value for s in SkillScope]}"
        )

    catalog = get_skill_catalog()
    skills = catalog.get_skills_by_scope(scope_enum)

    return SkillListResponse(
        skills=skills,
        total_count=catalog.get_skill_count(),
        enabled_count=catalog.get_enabled_count()
    )


@router.patch("/{skill_name}/enable", response_model=SkillDetailResponse)
async def toggle_skill(skill_name: str, request: SkillEnableRequest):
    """
    Enable or disable a skill

    Disabled skills will not be discovered or used by agents.
    """
    catalog = get_skill_catalog()
    skill = catalog.get_skill(skill_name)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill not found: {skill_name}"
        )

    if request.enabled:
        catalog.enable_skill(skill_name)
    else:
        catalog.disable_skill(skill_name)

    # Return updated skill
    updated_skill = catalog.get_skill(skill_name)

    return SkillDetailResponse(skill=updated_skill)


@router.get("/{skill_name}/evaluation", response_model=SkillEvaluation)
async def get_skill_evaluation(skill_name: str):
    """
    Get evaluation metrics for a skill

    Returns usage statistics and success rate.
    """
    catalog = get_skill_catalog()
    skill = catalog.get_skill(skill_name)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill not found: {skill_name}"
        )

    evaluation = catalog.get_skill_evaluation(skill_name)

    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluation data available for skill: {skill_name}"
        )

    return evaluation


@router.get("/stats", response_model=dict)
async def get_skill_stats():
    """
    Get overall skill system statistics

    Returns counts and usage metrics.
    """
    catalog = get_skill_catalog()

    # Get scope distribution
    scopes = catalog.get_scopes()
    scope_distribution = {
        scope.value: len(catalog.get_skills_by_scope(scope))
        for scope in scopes
    }

    # Get tag distribution
    all_skills = catalog.list_skills(enabled_only=False)
    all_tags = set()
    for skill in all_skills:
        all_tags.update(skill.metadata.tags)

    tag_counts = {
        tag: sum(1 for skill in all_skills if tag in skill.metadata.tags)
        for tag in all_tags
    }

    return {
        "total_skills": catalog.get_skill_count(),
        "enabled_skills": catalog.get_enabled_count(),
        "disabled_skills": catalog.get_skill_count() - catalog.get_enabled_count(),
        "scopes": list(scope_distribution.keys()),
        "scope_distribution": scope_distribution,
        "total_tags": len(all_tags),
        "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    }
