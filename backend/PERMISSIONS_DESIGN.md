# Dataset Permissions & Access Control Design

## Overview

The system has **three layers** of access control for datasets:

1. **Members** (Team Collaboration) - `dataset_members`
2. **Shares** (External/Temporary Access) - `dataset_shares`
3. **Public Access** - `public_datasets`

## 1. Dataset Members (Team Collaboration)

**Table:** `dataset_members`

**Use Case:** Team members who regularly work on the dataset together

**Roles:**
- `OWNER` - Full control, can delete dataset, manage all members
- `ADMIN` - Can edit, query, manage members (except owner changes)
- `EDITOR` - Can edit metadata, run queries, view results
- `ANALYST` - Can run queries and view results (no editing)
- `VIEWER` - Read-only access to dataset and results

**Example:**
```python
# Alice owns a sales dataset
dataset.owner_id = alice.id

# Bob is an admin who helps manage it
DatasetMember(dataset_id=dataset.id, user_id=bob.id, role='ADMIN')

# Carol is an analyst who runs reports
DatasetMember(dataset_id=dataset.id, user_id=carol.id, role='ANALYST')
```

**Characteristics:**
- Permanent team membership (until removed)
- One role per user per dataset
- Cannot have duplicate user+dataset combinations
- Soft delete with `removed_at` timestamp

## 2. Dataset Shares (External/Temporary Sharing)

**Table:** `dataset_shares`

**Use Case:** Share dataset with external users or temporary collaborators

**Permissions:**
- `VIEW` - Read-only access
- `QUERY` - Can run queries
- `EDIT` - Can edit metadata
- `ADMIN` - Full access (but not ownership)

**Example:**
```python
# Share with external consultant for 30 days
DatasetShare(
    dataset_id=dataset.id,
    user_id=consultant.id,
    permission='QUERY',
    expires_at=datetime.now() + timedelta(days=30)
)
```

**Characteristics:**
- Can have expiration dates (`expires_at`)
- Can be revoked (`revoked_at`)
- More flexible than team membership
- Designed for temporary or limited access

## 3. Public Datasets

**Table:** `public_datasets`

**Use Case:** Make dataset publicly accessible (anyone with link)

**Example:**
```python
# Make dataset public for queries only
PublicDataset(
    dataset_id=dataset.id,
    allow_query=True,
    allow_download=False
)
```

**Characteristics:**
- No user authentication required
- Can control what's allowed (query vs download)
- Can have expiration
- Can be revoked

## Permission Hierarchy

```
OWNER (highest)
  ↓
ADMIN (dataset_members)
  ↓
EDITOR (dataset_members)
  ↓
ANALYST (dataset_members)
  ↓
ADMIN (dataset_shares) - external
  ↓
EDIT (dataset_shares) - external
  ↓
QUERY (dataset_shares) - external
  ↓
VIEWER (dataset_members)
  ↓
VIEW (dataset_shares) - external
  ↓
Public Access (lowest)
```

## Access Control Logic

To check if a user can access a dataset:

```python
def can_user_access_dataset(user_id: str, dataset_id: str, required_permission: str) -> bool:
    # 1. Check if user is owner
    dataset = get_dataset(dataset_id)
    if dataset.owner_id == user_id:
        return True

    # 2. Check if user is a member with sufficient role
    member = get_dataset_member(dataset_id, user_id)
    if member and member.removed_at is None:
        return has_permission(member.role, required_permission)

    # 3. Check if dataset is shared with user
    share = get_dataset_share(dataset_id, user_id)
    if share and share.revoked_at is None:
        if share.expires_at is None or share.expires_at > now():
            return has_permission(share.permission, required_permission)

    # 4. Check if dataset is public
    public = get_public_dataset(dataset_id)
    if public and public.revoked_at is None:
        if public.expires_at is None or public.expires_at > now():
            return check_public_permission(public, required_permission)

    return False
```

## When to Use Each

### Use `dataset_members` when:
- Building a team/workspace
- Long-term collaboration
- Clear roles and responsibilities
- Need audit trail of who has what access

### Use `dataset_shares` when:
- Sharing with external users
- Temporary access needed
- One-off collaboration
- Want expiration/revocation

### Use `public_datasets` when:
- Open data/public reports
- No login required
- Want to embed in public website
- Maximum accessibility

## Database Schema

```sql
-- Team members (permanent collaboration)
CREATE TABLE dataset_members (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- OWNER, ADMIN, EDITOR, ANALYST, VIEWER
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    removed_at TIMESTAMP,
    UNIQUE(dataset_id, user_id)
);

-- External/temporary sharing
CREATE TABLE dataset_shares (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    permission VARCHAR NOT NULL,  -- VIEW, QUERY, EDIT, ADMIN
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Public access
CREATE TABLE public_datasets (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL UNIQUE,
    allow_download BOOLEAN,
    allow_query BOOLEAN,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);
```

## Migration Path

When a dataset is created:
1. Set `owner_id` on dataset
2. Automatically create a `DatasetMember` entry with role=OWNER for the owner

This ensures consistency and allows the owner to appear in the members list.
