# Dataset Sharing Implementation

## Overview

Complete three-tier sharing system for datasets with permission-based UI controls.

## Architecture

### Three-Layer Permission System

1. **Team Members** (Permanent Collaboration)
   - Table: `dataset_members`
   - Roles: OWNER, ADMIN, EDITOR, ANALYST, VIEWER
   - Use for: Internal team collaboration
   - Permissions persist until explicitly removed

2. **External Shares** (Temporary Access)
   - Table: `dataset_shares`
   - Permissions: VIEW, EDIT, ADMIN
   - Features: Optional expiration, revocable
   - Use for: External contractors, time-limited access

3. **Public Access** (Anonymous)
   - Table: `public_datasets`
   - Controls: allow_download, allow_query
   - Features: Optional expiration, revocable
   - Use for: Open datasets, public APIs

## Backend API

### Endpoints

#### User Role Check
```
GET /api/v1/sharing/datasets/{dataset_id}/my-role
Response: { role, is_owner, can_share }
```

#### Team Members
```
POST   /api/v1/sharing/datasets/{dataset_id}/members
GET    /api/v1/sharing/datasets/{dataset_id}/members
DELETE /api/v1/sharing/datasets/{dataset_id}/members/{member_id}
```

#### External Shares
```
POST   /api/v1/sharing/datasets/{dataset_id}/shares
GET    /api/v1/sharing/datasets/{dataset_id}/shares
DELETE /api/v1/sharing/datasets/{dataset_id}/shares/{share_id}
```

#### Public Access
```
POST   /api/v1/sharing/datasets/{dataset_id}/public
GET    /api/v1/sharing/datasets/{dataset_id}/public
DELETE /api/v1/sharing/datasets/{dataset_id}/public
```

### Permission Checks

All sharing operations require ADMIN role or higher. Permission hierarchy:

```
OWNER (5)     - Full control, can delete
  ↓
ADMIN (4)     - Manage members, shares, public access
  ↓
EDITOR (3)    - Edit metadata, query
  ↓
ANALYST (2)   - Query only
  ↓
VIEWER (1)    - Read-only
```

## Frontend Components

### ShareModal Component

Location: `/frontend/src/components/sharing/ShareModal.tsx`

**Features:**
- Three-tab interface (Members, Shares, Public)
- Add/remove team members with role selection
- Share with external users with expiration
- Enable/disable public access
- Real-time updates with React Query

**Integration:**
```typescript
<ShareModal
  datasetId={id}
  datasetName={dataset.name}
  onClose={() => setShowShareModal(false)}
/>
```

### DatasetDetail Integration

Location: `/frontend/src/pages/DatasetDetail.tsx`

**Permission-based Share Button:**
```typescript
// Fetch user role
const { data: userRole } = useQuery({
  queryKey: ['user-role', id],
  queryFn: async () => {
    const { data } = await axios.get(`/sharing/datasets/${id}/my-role`)
    return data
  }
})

// Conditionally render Share button
{userRole?.can_share && (
  <IconButton
    variant="default"
    tooltip="Share Dataset"
    onClick={() => setShowShareModal(true)}
  >
    <Share2 className="h-5 w-5" />
  </IconButton>
)}
```

## Database Schema

### dataset_members
```sql
CREATE TABLE dataset_members (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- OWNER, ADMIN, EDITOR, ANALYST, VIEWER
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    UNIQUE(dataset_id, user_id)
);
```

### dataset_shares
```sql
CREATE TABLE dataset_shares (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    permission VARCHAR NOT NULL DEFAULT 'VIEW',
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### public_datasets
```sql
CREATE TABLE public_datasets (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL UNIQUE,
    allow_download BOOLEAN NOT NULL DEFAULT FALSE,
    allow_query BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Features

1. **Row-Level Security** - Users only see datasets they can access
2. **Role-Based Access Control** - Granular permissions per user
3. **Expiring Access** - Time-limited shares and public access
4. **Revocable Shares** - Admin can revoke access anytime
5. **Permission Validation** - All operations require appropriate role
6. **Soft Deletes** - Audit trail with removed_at/revoked_at timestamps

## Usage Examples

### Share with Team Member

```typescript
// Add user as ADMIN
await axios.post(`/sharing/datasets/${datasetId}/members`, {
  email: 'colleague@company.com',
  role: 'ADMIN'
})
```

### Share Externally with Expiration

```typescript
// Share with external user for 7 days
await axios.post(`/sharing/datasets/${datasetId}/shares`, {
  email: 'contractor@external.com',
  permission: 'VIEW',
  expires_days: 7
})
```

### Make Public

```typescript
// Enable public access with query only (no download)
await axios.post(`/sharing/datasets/${datasetId}/public`, {
  allow_download: false,
  allow_query: true,
  expires_days: 30  // Optional expiration
})
```

## Testing Checklist

- [ ] Register two users
- [ ] User A uploads dataset (becomes owner)
- [ ] User A sees Share button
- [ ] User A adds User B as ADMIN
- [ ] User B logs in and sees dataset
- [ ] User B can open Share modal (has ADMIN role)
- [ ] User A shares externally with 7-day expiration
- [ ] User A makes dataset public
- [ ] User B (ADMIN) can revoke shares
- [ ] User C (VIEWER) cannot see Share button
- [ ] Expired shares are not accessible
- [ ] Revoked shares are not accessible

## Files Modified

### Backend
- `app/api/endpoints/sharing.py` - Complete sharing API (456 lines)
- `app/models/dataset_member.py` - Member and role models
- `app/models/dataset_share.py` - Share and public access models
- `app/services/permission_service.py` - Permission checking logic
- `migrations/007_add_user_authentication.sql` - Database schema

### Frontend
- `src/components/sharing/ShareModal.tsx` - Sharing UI (456 lines)
- `src/pages/DatasetDetail.tsx` - Share button integration
- `src/services/api.ts` - Axios with auth headers

## Next Steps

1. Test complete flow with multiple users
2. Add similar sharing to Dataset Groups
3. Add email notifications for shares
4. Add sharing analytics dashboard
5. Implement share links (public URLs)
