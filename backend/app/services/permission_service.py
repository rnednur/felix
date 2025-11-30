from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional
from app.models.dataset import Dataset, DatasetGroup
from app.models.user import User
from app.models.dataset_member import DatasetMember, DatasetGroupMember, DatasetRole
from app.models.dataset_share import DatasetShare, DatasetGroupShare, PublicDataset


class PermissionService:
    """Service for checking user permissions on datasets and groups"""

    @staticmethod
    def can_access_dataset(
        db: Session,
        user: User,
        dataset_id: str,
        required_role: Optional[DatasetRole] = None
    ) -> bool:
        """Check if user can access a dataset"""
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.deleted_at.is_(None)
        ).first()

        if not dataset:
            return False

        # 1. Owner always has access
        if dataset.owner_id == user.id:
            return True

        # 2. Check dataset members
        member = db.query(DatasetMember).filter(
            DatasetMember.dataset_id == dataset_id,
            DatasetMember.user_id == user.id,
            DatasetMember.removed_at.is_(None)
        ).first()

        if member:
            if required_role:
                return PermissionService._role_has_permission(member.role, required_role)
            return True

        # 3. Check dataset shares
        share = db.query(DatasetShare).filter(
            DatasetShare.dataset_id == dataset_id,
            DatasetShare.user_id == user.id,
            DatasetShare.revoked_at.is_(None)
        ).first()

        if share:
            # Check expiration
            if share.expires_at and share.expires_at < datetime.utcnow():
                return False
            return True

        # 4. Check public access
        public = db.query(PublicDataset).filter(
            PublicDataset.dataset_id == dataset_id,
            PublicDataset.revoked_at.is_(None)
        ).first()

        if public:
            # Check expiration
            if public.expires_at and public.expires_at < datetime.utcnow():
                return False
            return True

        return False

    @staticmethod
    def can_access_group(
        db: Session,
        user: User,
        group_id: str,
        required_role: Optional[DatasetRole] = None
    ) -> bool:
        """Check if user can access a dataset group"""
        group = db.query(DatasetGroup).filter(
            DatasetGroup.id == group_id,
            DatasetGroup.deleted_at.is_(None)
        ).first()

        if not group:
            return False

        # 1. Owner always has access
        if group.owner_id == user.id:
            return True

        # 2. Check group members
        member = db.query(DatasetGroupMember).filter(
            DatasetGroupMember.group_id == group_id,
            DatasetGroupMember.user_id == user.id,
            DatasetGroupMember.removed_at.is_(None)
        ).first()

        if member:
            if required_role:
                return PermissionService._role_has_permission(member.role, required_role)
            return True

        # 3. Check group shares
        share = db.query(DatasetGroupShare).filter(
            DatasetGroupShare.group_id == group_id,
            DatasetGroupShare.user_id == user.id,
            DatasetGroupShare.revoked_at.is_(None)
        ).first()

        if share:
            # Check expiration
            if share.expires_at and share.expires_at < datetime.utcnow():
                return False
            return True

        return False

    @staticmethod
    def get_user_datasets(db: Session, user: User):
        """Get all datasets a user has access to"""
        # Get datasets where user is owner
        owned_datasets = db.query(Dataset).filter(
            Dataset.owner_id == user.id,
            Dataset.deleted_at.is_(None)
        ).all()

        # Get datasets where user is a member
        member_dataset_ids = db.query(DatasetMember.dataset_id).filter(
            DatasetMember.user_id == user.id,
            DatasetMember.removed_at.is_(None)
        ).all()
        member_dataset_ids = [m[0] for m in member_dataset_ids]

        member_datasets = db.query(Dataset).filter(
            Dataset.id.in_(member_dataset_ids),
            Dataset.deleted_at.is_(None)
        ).all() if member_dataset_ids else []

        # Get datasets shared with user
        shared_dataset_ids = db.query(DatasetShare.dataset_id).filter(
            DatasetShare.user_id == user.id,
            DatasetShare.revoked_at.is_(None),
            or_(
                DatasetShare.expires_at.is_(None),
                DatasetShare.expires_at > datetime.utcnow()
            )
        ).all()
        shared_dataset_ids = [s[0] for s in shared_dataset_ids]

        shared_datasets = db.query(Dataset).filter(
            Dataset.id.in_(shared_dataset_ids),
            Dataset.deleted_at.is_(None)
        ).all() if shared_dataset_ids else []

        # Get public datasets
        public_dataset_ids = db.query(PublicDataset.dataset_id).filter(
            PublicDataset.revoked_at.is_(None),
            or_(
                PublicDataset.expires_at.is_(None),
                PublicDataset.expires_at > datetime.utcnow()
            )
        ).all()
        public_dataset_ids = [p[0] for p in public_dataset_ids]

        public_datasets = db.query(Dataset).filter(
            Dataset.id.in_(public_dataset_ids),
            Dataset.deleted_at.is_(None)
        ).all() if public_dataset_ids else []

        # Combine and deduplicate
        all_datasets = owned_datasets + member_datasets + shared_datasets + public_datasets
        unique_datasets = {d.id: d for d in all_datasets}.values()

        return list(unique_datasets)

    @staticmethod
    def get_user_groups(db: Session, user: User):
        """Get all dataset groups a user has access to"""
        # Get groups where user is owner
        owned_groups = db.query(DatasetGroup).filter(
            DatasetGroup.owner_id == user.id,
            DatasetGroup.deleted_at.is_(None)
        ).all()

        # Get groups where user is a member
        member_group_ids = db.query(DatasetGroupMember.group_id).filter(
            DatasetGroupMember.user_id == user.id,
            DatasetGroupMember.removed_at.is_(None)
        ).all()
        member_group_ids = [m[0] for m in member_group_ids]

        member_groups = db.query(DatasetGroup).filter(
            DatasetGroup.id.in_(member_group_ids),
            DatasetGroup.deleted_at.is_(None)
        ).all() if member_group_ids else []

        # Get groups shared with user
        shared_group_ids = db.query(DatasetGroupShare.group_id).filter(
            DatasetGroupShare.user_id == user.id,
            DatasetGroupShare.revoked_at.is_(None),
            or_(
                DatasetGroupShare.expires_at.is_(None),
                DatasetGroupShare.expires_at > datetime.utcnow()
            )
        ).all()
        shared_group_ids = [s[0] for s in shared_group_ids]

        shared_groups = db.query(DatasetGroup).filter(
            DatasetGroup.id.in_(shared_group_ids),
            DatasetGroup.deleted_at.is_(None)
        ).all() if shared_group_ids else []

        # Combine and deduplicate
        all_groups = owned_groups + member_groups + shared_groups
        unique_groups = {g.id: g for g in all_groups}.values()

        return list(unique_groups)

    @staticmethod
    def _role_has_permission(user_role: DatasetRole, required_role: DatasetRole) -> bool:
        """Check if user's role meets the required permission level"""
        role_hierarchy = {
            DatasetRole.OWNER: 5,
            DatasetRole.ADMIN: 4,
            DatasetRole.EDITOR: 3,
            DatasetRole.ANALYST: 2,
            DatasetRole.VIEWER: 1,
        }

        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
