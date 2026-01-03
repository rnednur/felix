#!/usr/bin/env python3
"""
Quick script to create a test workspace for demo purposes
"""
import requests
import sys

# Configuration
API_BASE = "http://localhost:8000/api/v1"

def create_test_workspace(token: str, dataset_id: str = None):
    """Create a test workspace"""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create workspace
    workspace_data = {
        "name": "Sales Analysis Canvas",
        "description": "Interactive canvas for sales data exploration",
    }

    if dataset_id:
        workspace_data["dataset_id"] = dataset_id

    response = requests.post(
        f"{API_BASE}/workspaces",
        json=workspace_data,
        headers=headers
    )

    if response.status_code == 201:
        workspace = response.json()
        print(f"✅ Workspace created successfully!")
        print(f"   ID: {workspace['id']}")
        print(f"   Name: {workspace['name']}")
        print(f"\n🚀 Demo URL: http://localhost:5173/workspaces/{workspace['id']}")
        return workspace
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_test_workspace.py <auth_token> [dataset_id]")
        print("\nTo get your auth token:")
        print("1. Login to Felix in browser")
        print("2. Open browser DevTools > Application > Local Storage")
        print("3. Copy the 'access_token' value")
        sys.exit(1)

    token = sys.argv[1]
    dataset_id = sys.argv[2] if len(sys.argv) > 2 else None

    create_test_workspace(token, dataset_id)
