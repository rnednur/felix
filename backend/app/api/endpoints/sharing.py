from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dataset import Dataset, DatasetGroup
from app.models.user import User
from app.models.dataset_member import DatasetMember, DatasetGroupMember, DatasetRole
from app.models.dataset_share import (
    DatasetShare, DatasetGroupShare, PublicDataset,
    SharePermission
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/sharing", tags=["sharing"])


# Pydantic Schemas
class UserRoleResponse(BaseModel):
    role: Optional[DatasetRole]
    is_owner: bool
    can_share: bool  # ADMIN or higher



class AddMemberRequest(BaseModel):
    email: EmailStr
    role: DatasetRole


class ShareRequest(BaseModel):
    email: EmailStr
    permission: SharePermission
    expires_days: Optional[int] = None


class MakePublicRequest(BaseModel):
    allow_download: bool = False
    allow_query: bool = True
    expires_days: Optional[int] = None


class MemberResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    role: DatasetRole
    created_at: datetime

    class Config:
        from_attributes = True


class ShareResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    permission: SharePermission
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PublicAccessResponse(BaseModel):
    id: str
    dataset_id: str
    allow_download: bool
    allow_query: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== USER ROLE CHECK ==========

@router.get("/datasets/{dataset_id}/my-role", response_model=UserRoleResponse)
async def get_my_role(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's role for a dataset"""
    # Check dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Check if owner
    is_owner = dataset.owner_id == current_user.id

    # Check if member
    member = db.query(DatasetMember).filter(
        DatasetMember.dataset_id == dataset_id,
        DatasetMember.user_id == current_user.id,
        DatasetMember.removed_at.is_(None)
    ).first()

    role = member.role if member else None
    can_share = is_owner or (member and member.role in [DatasetRole.ADMIN, DatasetRole.OWNER])

    return {
        "role": role,
        "is_owner": is_owner,
        "can_share": can_share
    }


# ========== DATASET MEMBERS ==========

@router.post("/datasets/{dataset_id}/members", response_model=MemberResponse)
async def add_dataset_member(
    dataset_id: str,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a team member to a dataset"""
    # Check dataset exists and user has ADMIN permission
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Only ADMIN or OWNER can add members
    if not PermissionService.can_access_dataset(db, current_user, dataset_id, DatasetRole.ADMIN):
        raise HTTPException(403, "Access denied - ADMIN role required")

    # Find user by email
    target_user = db.query(User).filter(
        User.email == request.email,
        User.deleted_at.is_(None)
    ).first()

    if not target_user:
        raise HTTPException(404, f"User with email {request.email} not found")

    # Check if already a member
    existing = db.query(DatasetMember).filter(
        DatasetMember.dataset_id == dataset_id,
        DatasetMember.user_id == target_user.id,
        DatasetMember.removed_at.is_(None)
    ).first()

    if existing:
        raise HTTPException(400, "User is already a member")

    # Cannot add someone as OWNER
    if request.role == DatasetRole.OWNER:
        raise HTTPException(400, "Cannot add additional owners")

    # Create member
    member = DatasetMember(
        dataset_id=dataset_id,
        user_id=target_user.id,
        role=request.role
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return {
        **member.__dict__,
        "user_email": target_user.email,
        "user_name": target_user.full_name or target_user.username
    }


@router.get("/datasets/{dataset_id}/members", response_model=List[MemberResponse])
async def list_dataset_members(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of a dataset"""
    # Check access
    if not PermissionService.can_access_dataset(db, current_user, dataset_id):
        raise HTTPException(403, "Access denied")

    members = db.query(DatasetMember).filter(
        DatasetMember.dataset_id == dataset_id,
        DatasetMember.removed_at.is_(None)
    ).all()

    result = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            result.append({
                **member.__dict__,
                "user_email": user.email,
                "user_name": user.full_name or user.username
            })

    return result


@router.delete("/datasets/{dataset_id}/members/{member_id}")
async def remove_dataset_member(
    dataset_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from a dataset"""
    # Check ADMIN permission
    if not PermissionService.can_access_dataset(db, current_user, dataset_id, DatasetRole.ADMIN):
        raise HTTPException(403, "Access denied - ADMIN role required")

    member = db.query(DatasetMember).filter(
        DatasetMember.id == member_id,
        DatasetMember.dataset_id == dataset_id,
        DatasetMember.removed_at.is_(None)
    ).first()

    if not member:
        raise HTTPException(404, "Member not found")

    # Cannot remove owner
    if member.role == DatasetRole.OWNER:
        raise HTTPException(400, "Cannot remove owner")

    member.removed_at = datetime.utcnow()
    db.commit()

    return {"message": "Member removed successfully"}


# ========== DATASET SHARES (External/Temporary) ==========

@router.post("/datasets/{dataset_id}/shares", response_model=ShareResponse)
async def share_dataset(
    dataset_id: str,
    request: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share dataset with external user (temporary access)"""
    # Check ADMIN permission
    if not PermissionService.can_access_dataset(db, current_user, dataset_id, DatasetRole.ADMIN):
        raise HTTPException(403, "Access denied - ADMIN role required")

    # Find user by email
    target_user = db.query(User).filter(
        User.email == request.email,
        User.deleted_at.is_(None)
    ).first()

    if not target_user:
        raise HTTPException(404, f"User with email {request.email} not found")

    # Check if already shared
    existing = db.query(DatasetShare).filter(
        DatasetShare.dataset_id == dataset_id,
        DatasetShare.user_id == target_user.id,
        DatasetShare.revoked_at.is_(None)
    ).first()

    if existing:
        raise HTTPException(400, "Dataset already shared with this user")

    # Calculate expiration
    expires_at = None
    if request.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)

    # Create share
    share = DatasetShare(
        dataset_id=dataset_id,
        user_id=target_user.id,
        permission=request.permission,
        expires_at=expires_at
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return {
        **share.__dict__,
        "user_email": target_user.email,
        "user_name": target_user.full_name or target_user.username
    }


@router.get("/datasets/{dataset_id}/shares", response_model=List[ShareResponse])
async def list_dataset_shares(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all external shares for a dataset"""
    # Check access
    if not PermissionService.can_access_dataset(db, current_user, dataset_id):
        raise HTTPException(403, "Access denied")

    shares = db.query(DatasetShare).filter(
        DatasetShare.dataset_id == dataset_id,
        DatasetShare.revoked_at.is_(None)
    ).all()

    result = []
    for share in shares:
        user = db.query(User).filter(User.id == share.user_id).first()
        if user:
            result.append({
                **share.__dict__,
                "user_email": user.email,
                "user_name": user.full_name or user.username
            })

    return result


@router.delete("/datasets/{dataset_id}/shares/{share_id}")
async def revoke_dataset_share(
    dataset_id: str,
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a dataset share"""
    # Check ADMIN permission
    if not PermissionService.can_access_dataset(db, current_user, dataset_id, DatasetRole.ADMIN):
        raise HTTPException(403, "Access denied - ADMIN role required")

    share = db.query(DatasetShare).filter(
        DatasetShare.id == share_id,
        DatasetShare.dataset_id == dataset_id,
        DatasetShare.revoked_at.is_(None)
    ).first()

    if not share:
        raise HTTPException(404, "Share not found")

    share.revoked_at = datetime.utcnow()
    db.commit()

    return {"message": "Share revoked successfully"}


# ========== PUBLIC ACCESS ==========

@router.post("/datasets/{dataset_id}/public", response_model=PublicAccessResponse)
async def make_dataset_public(
    dataset_id: str,
    request: MakePublicRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make dataset publicly accessible"""
    # Only owner can make public
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(403, "Access denied - only owner can make dataset public")

    # Check if already public
    existing = db.query(PublicDataset).filter(
        PublicDataset.dataset_id == dataset_id,
        PublicDataset.revoked_at.is_(None)
    ).first()

    if existing:
        raise HTTPException(400, "Dataset is already public")

    # Calculate expiration
    expires_at = None
    if request.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)

    # Create public access
    public = PublicDataset(
        dataset_id=dataset_id,
        allow_download=request.allow_download,
        allow_query=request.allow_query,
        expires_at=expires_at
    )
    db.add(public)
    db.commit()
    db.refresh(public)

    return public


@router.get("/datasets/{dataset_id}/public", response_model=Optional[PublicAccessResponse])
async def get_public_access(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get public access settings for a dataset"""
    # Check access
    if not PermissionService.can_access_dataset(db, current_user, dataset_id):
        raise HTTPException(403, "Access denied")

    public = db.query(PublicDataset).filter(
        PublicDataset.dataset_id == dataset_id,
        PublicDataset.revoked_at.is_(None)
    ).first()

    return public


@router.delete("/datasets/{dataset_id}/public")
async def revoke_public_access(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke public access to a dataset"""
    # Only owner can revoke
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(403, "Access denied - only owner can revoke public access")

    public = db.query(PublicDataset).filter(
        PublicDataset.dataset_id == dataset_id,
        PublicDataset.revoked_at.is_(None)
    ).first()

    if not public:
        raise HTTPException(404, "Dataset is not public")

    public.revoked_at = datetime.utcnow()
    db.commit()

    return {"message": "Public access revoked successfully"}
