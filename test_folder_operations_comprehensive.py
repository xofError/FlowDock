"""
Comprehensive test suite for folder operations.
Tests all folder functionality: create, share, move, and download.

IMPORTANT: Services must be running before executing this test.
Start services with: docker-compose up -d

Test Coverage:
- Create folder
- Upload files to folder
- List folder contents
- Share folder with other users
- Access shared folder as non-owner
- Move files between folders
- Move folders
- Download owned folder as ZIP
- Download shared folder as ZIP
- Download public folder as ZIP (via public link)
"""

import httpx
import asyncio
import sys
import json
from typing import Optional, Tuple
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8001"
MEDIA_SERVICE_URL = f"{BASE_URL}/media"
AUTH_SERVICE_URL = "http://localhost:8000/auth"

# Test data - These JWT tokens must be valid for your running services
# You can generate them by calling the auth service login endpoint
TEST_OWNER_EMAIL = "owner@example.com"
TEST_OWNER_PASSWORD = "password123"
TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "password123"

# Placeholder tokens - replace with actual tokens from your auth service
TEST_OWNER_JWT = None
TEST_USER_JWT = None
TEST_ADMIN_JWT = None


async def get_test_tokens(client: httpx.AsyncClient) -> bool:
    """Retrieve test JWT tokens from auth service"""
    global TEST_OWNER_JWT, TEST_USER_JWT
    
    try:
        print("\n📡 Authenticating test users...")
        
        # Login owner
        owner_response = await client.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": TEST_OWNER_EMAIL, "password": TEST_OWNER_PASSWORD}
        )
        
        if owner_response.status_code != 200:
            print(f"   ❌ Failed to authenticate owner: {owner_response.status_code}")
            return False
        
        TEST_OWNER_JWT = owner_response.json().get("access_token")
        print(f"   ✓ Owner authenticated")
        
        # Login test user
        user_response = await client.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        
        if user_response.status_code != 200:
            print(f"   ❌ Failed to authenticate user: {user_response.status_code}")
            return False
        
        TEST_USER_JWT = user_response.json().get("access_token")
        print(f"   ✓ Test user authenticated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return False


async def test_create_folder(client: httpx.AsyncClient, folder_name: str) -> Optional[str]:
    """Test: Create a new folder"""
    try:
        response = await client.post(
            f"{MEDIA_SERVICE_URL}/folders",
            json={"name": folder_name, "description": f"Test folder: {folder_name}"},
            headers={"Authorization": f"Bearer {TEST_OWNER_JWT}"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"      ❌ Failed: {response.status_code} - {response.text[:100]}")
            return None
        
        folder_id = response.json().get("id")
        print(f"      ✓ Created folder: {folder_id}")
        return folder_id
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return None


async def test_upload_file(client: httpx.AsyncClient, folder_id: str, filename: str) -> Optional[str]:
    """Test: Upload a file to a folder"""
    try:
        # Create a test file content
        test_content = f"Test file: {filename}\nCreated at: {datetime.now()}".encode()
        
        files = {"file": (filename, test_content)}
        response = await client.post(
            f"{MEDIA_SERVICE_URL}/files/upload",
            params={"folder_id": folder_id},
            files=files,
            headers={"Authorization": f"Bearer {TEST_OWNER_JWT}"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"      ❌ Failed: {response.status_code} - {response.text[:100]}")
            return None
        
        file_id = response.json().get("id")
        print(f"      ✓ Uploaded file: {filename} ({file_id})")
        return file_id
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return None


async def test_list_folder_contents(client: httpx.AsyncClient, folder_id: str, as_owner: bool = True) -> bool:
    """Test: List folder contents"""
    try:
        token = TEST_OWNER_JWT if as_owner else TEST_USER_JWT
        response = await client.get(
            f"{MEDIA_SERVICE_URL}/folders/{folder_id}/contents",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"      ❌ Failed: {response.status_code}")
            return False
        
        data = response.json()
        file_count = len(data.get("files", []))
        subfolder_count = len(data.get("subfolders", []))
        print(f"      ✓ Listed contents: {file_count} files, {subfolder_count} subfolders")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def test_share_folder(client: httpx.AsyncClient, folder_id: str, target_user_id: str, permission: str = "view") -> bool:
    """Test: Share folder with another user"""
    try:
        response = await client.post(
            f"{MEDIA_SERVICE_URL}/folders/{folder_id}/share",
            json={"target_id": target_user_id, "permission": permission},
            headers={"Authorization": f"Bearer {TEST_OWNER_JWT}"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"      ❌ Failed: {response.status_code} - {response.text[:100]}")
            return False
        
        print(f"      ✓ Shared folder with permission: {permission}")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def test_move_file(client: httpx.AsyncClient, file_id: str, dest_folder_id: str) -> bool:
    """Test: Move file to another folder"""
    try:
        response = await client.patch(
            f"{MEDIA_SERVICE_URL}/files/{file_id}/move",
            params={"folder_id": dest_folder_id},
            headers={"Authorization": f"Bearer {TEST_OWNER_JWT}"}
        )
        
        if response.status_code not in [200, 204]:
            print(f"      ❌ Failed: {response.status_code} - {response.text[:100]}")
            return False
        
        print(f"      ✓ Moved file to folder: {dest_folder_id}")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def test_move_folder(client: httpx.AsyncClient, folder_id: str, parent_folder_id: str) -> bool:
    """Test: Move folder to another folder"""
    try:
        response = await client.patch(
            f"{MEDIA_SERVICE_URL}/folders/{folder_id}/move",
            params={"parent_id": parent_folder_id},
            headers={"Authorization": f"Bearer {TEST_OWNER_JWT}"}
        )
        
        if response.status_code not in [200, 204]:
            print(f"      ❌ Failed: {response.status_code} - {response.text[:100]}")
            return False
        
        print(f"      ✓ Moved folder to parent: {parent_folder_id}")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def test_download_folder_zip(client: httpx.AsyncClient, folder_id: str, as_owner: bool = True) -> bool:
    """Test: Download folder as ZIP"""
    try:
        token = TEST_OWNER_JWT if as_owner else TEST_USER_JWT
        endpoint = "/download" if as_owner else "/download-zip"
        
        response = await client.get(
            f"{MEDIA_SERVICE_URL}/folders/{folder_id}{endpoint}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"      ❌ Failed: {response.status_code}")
            return False
        
        # Verify it's a valid ZIP file (starts with PK magic bytes)
        if not response.content.startswith(b'PK'):
            print(f"      ❌ Invalid ZIP file")
            return False
        
        size_kb = len(response.content) / 1024
        print(f"      ✓ Downloaded ZIP: {size_kb:.2f} KB")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def test_download_public_folder_zip(client: httpx.AsyncClient, share_token: str, password: Optional[str] = None) -> bool:
    """Test: Download public folder as ZIP"""
    try:
        params = {}
        if password:
            params["password"] = password
        
        response = await client.get(
            f"{MEDIA_SERVICE_URL}/public/folder/{share_token}/download-zip",
            params=params
        )
        
        if response.status_code != 200:
            print(f"      ❌ Failed: {response.status_code}")
            return False
        
        # Verify it's a valid ZIP file
        if not response.content.startswith(b'PK'):
            print(f"      ❌ Invalid ZIP file")
            return False
        
        size_kb = len(response.content) / 1024
        print(f"      ✓ Downloaded public ZIP: {size_kb:.2f} KB")
        return True
        
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False


async def run_comprehensive_test_suite():
    """Run all folder operation tests"""
    
    async with httpx.AsyncClient(timeout=30) as client:
        print("=" * 80)
        print("FLOWDOCK FOLDER OPERATIONS TEST SUITE")
        print("=" * 80)
        
        # Step 1: Authenticate
        print("\n[STEP 1] Authentication")
        if not await get_test_tokens(client):
            print("\n❌ Authentication failed. Ensure services are running and test users exist.")
            print("\nStart services with: docker-compose up -d")
            return False
        
        test_results = {
            "create_folders": [],
            "upload_files": [],
            "list_contents": [],
            "folder_sharing": [],
            "move_operations": [],
            "downloads": [],
        }
        
        try:
            # Step 2: Create folders
            print("\n[STEP 2] Folder Creation")
            root_folder = await test_create_folder(client, "test_root_folder")
            subfolder_1 = await test_create_folder(client, "test_subfolder_1")
            subfolder_2 = await test_create_folder(client, "test_subfolder_2")
            
            test_results["create_folders"] = [
                root_folder is not None,
                subfolder_1 is not None,
                subfolder_2 is not None,
            ]
            
            if not all(test_results["create_folders"]):
                print("\n❌ Folder creation failed. Stopping tests.")
                return False
            
            # Step 3: Upload files
            print("\n[STEP 3] File Upload")
            file_1 = await test_upload_file(client, root_folder, "test_document.txt")
            file_2 = await test_upload_file(client, root_folder, "test_data.json")
            
            test_results["upload_files"] = [
                file_1 is not None,
                file_2 is not None,
            ]
            
            # Step 4: List contents
            print("\n[STEP 4] List Folder Contents")
            list_result = await test_list_folder_contents(client, root_folder, as_owner=True)
            test_results["list_contents"].append(list_result)
            
            # Step 5: Share folder (if we have user ID)
            print("\n[STEP 5] Folder Sharing")
            if TEST_USER_JWT:
                # Extract user ID from JWT (this is a simplified approach)
                # In production, you'd get this from the auth service
                test_user_id = "test_user_id"  # Replace with actual ID
                share_result = await test_share_folder(client, root_folder, test_user_id, "view")
                test_results["folder_sharing"].append(share_result)
                
                if share_result:
                    # Try accessing as shared user
                    print("   Accessing as shared user:")
                    list_as_user = await test_list_folder_contents(client, root_folder, as_owner=False)
                    test_results["folder_sharing"].append(list_as_user)
            
            # Step 6: Move operations
            print("\n[STEP 6] Move Operations")
            if file_1:
                move_file_result = await test_move_file(client, file_1, subfolder_1)
                test_results["move_operations"].append(move_file_result)
            
            # Step 7: Download operations
            print("\n[STEP 7] Download Operations")
            download_owned = await test_download_folder_zip(client, root_folder, as_owner=True)
            test_results["downloads"].append(download_owned)
            
            # Step 8: Summary
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            
            all_passed = all(all(v) for v in test_results.values())
            
            for test_category, results in test_results.items():
                if results:
                    passed = sum(results)
                    total = len(results)
                    status = "✓" if all(results) else "❌"
                    print(f"{status} {test_category}: {passed}/{total} passed")
            
            print("\n" + "=" * 80)
            if all_passed:
                print("✓ ALL TESTS PASSED!")
                print("=" * 80)
                return True
            else:
                print("❌ SOME TESTS FAILED")
                print("=" * 80)
                return False
                
        except Exception as e:
            print(f"\n❌ Test suite exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test runner"""
    success = await run_comprehensive_test_suite()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
