# API Authentication & Authorization Summary

## Overview

All dataset and dataset group endpoints now require authentication and enforce row-level security based on user permissions.

## Authentication Flow

```
1. User logs in → Receives JWT access & refresh tokens
2. Frontend stores tokens in localStorage
3. Axios interceptor adds Authorization header to all requests
4. Backend validates JWT and loads current user
5. Permission checks applied before data access
```

## Datasets API

### POST /api/v1/datasets/upload
**Auth:** Required
**Permission:** Any authenticated user
**Behavior:**
- Sets `owner_id` to current user
- Creates `DatasetMember` entry with role=OWNER
- Returns created dataset

### GET /api/v1/datasets/
**Auth:** Required
**Permission:** Any authenticated user
**Behavior:**
- Returns datasets user owns
- Returns datasets user is a member of
- Returns datasets shared with user
- Returns public datasets
- Sorted by created_at descending

### GET /api/v1/datasets/{id}
**Auth:** Required
**Permission:** Must have access to dataset
**Behavior:**
- Checks if user can access dataset
- Returns 403 if denied
- Returns dataset metadata if allowed

### DELETE /api/v1/datasets/{id}
**Auth:** Required
**Permission:** Owner only
**Behavior:**
- Soft deletes dataset
- Only owner can delete

## Dataset Groups API

### POST /api/v1/dataset-groups/
**Auth:** Required
**Permission:** Any authenticated user
**Behavior:**
- Sets `owner_id` to current user
- Creates `DatasetGroupMember` entry with role=OWNER
- Returns created group

### GET /api/v1/dataset-groups/
**Auth:** Required
**Permission:** Any authenticated user
**Behavior:**
- Returns groups user owns
- Returns groups user is a member of
- Returns groups shared with user
- Sorted by created_at descending

### GET /api/v1/dataset-groups/{id}
**Auth:** Required
**Permission:** Must have access to group
**Behavior:**
- Checks if user can access group
- Returns 403 if denied
- Returns group with memberships if allowed

### PATCH /api/v1/dataset-groups/{id}
**Auth:** Required
**Permission:** EDITOR role or higher
**Behavior:**
- Updates group name/description
- Requires EDITOR, ADMIN, or OWNER role

### DELETE /api/v1/dataset-groups/{id}
**Auth:** Required
**Permission:** Owner only
**Behavior:**
- Soft deletes group
- Only owner can delete

## Permission Checks

### PermissionService.can_access_dataset(db, user, dataset_id, required_role?)

Checks in order:
1. Is user the owner? → Allow
2. Is user a dataset member? → Check role hierarchy
3. Is dataset shared with user? → Check expiration
4. Is dataset public? → Check expiration

### PermissionService.can_access_group(db, user, group_id, required_role?)

Checks in order:
1. Is user the owner? → Allow
2. Is user a group member? → Check role hierarchy
3. Is group shared with user? → Check expiration

### Role Hierarchy

```
OWNER (5)     - Full control
  ↓
ADMIN (4)     - Manage members, edit
  ↓
EDITOR (3)    - Edit metadata, query
  ↓
ANALYST (2)   - Query only
  ↓
VIEWER (1)    - Read-only
```

## Frontend Integration

### Axios Interceptors (src/services/api.ts)

**Request Interceptor:**
```typescript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**Response Interceptor:**
```typescript
// On 401 error:
// 1. Try to refresh token
// 2. Retry original request with new token
// 3. If refresh fails, redirect to /login
```

### Protected Routes

All routes except `/login` and `/register` are wrapped in `<ProtectedRoute>`:

```tsx
<Route path="/" element={
  <ProtectedRoute>
    <Home />
  </ProtectedRoute>
} />
```

## Error Responses

### 401 Unauthorized
- Token missing, invalid, or expired
- Frontend automatically tries to refresh
- Redirects to login if refresh fails

### 403 Forbidden
- User authenticated but lacks permission
- Examples:
  - Trying to edit when only VIEWER
  - Trying to delete when not OWNER
  - Trying to access dataset they don't have access to

### 404 Not Found
- Resource doesn't exist
- Or exists but user has no access (security through obscurity)

## Security Features

1. **JWT Authentication** - Industry standard tokens
2. **Row-Level Security** - Users only see their data
3. **Role-Based Access** - Granular permissions
4. **Soft Deletes** - Data retention with deleted_at
5. **Audit Logging** - Track all user actions
6. **Token Refresh** - Automatic token renewal
7. **Expiring Shares** - Time-limited access

## Migration

Run migration to add auth tables:
```bash
cd backend
./run_migrations.sh aispreadsheets 007
```

Or use Python setup:
```bash
python setup_database.py
```

## Testing

1. Register user: `POST /api/v1/auth/register`
2. Login: `POST /api/v1/auth/login` → Get tokens
3. Upload dataset with token → Becomes owner
4. List datasets → See only your datasets
5. Try accessing another user's dataset → 403
