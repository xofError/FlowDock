"""
Test script for shared folder ZIP download.
Tests the fix for archive_folder to handle both owned and shared folders.
"""

import httpx
import asyncio
import sys
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8003"
MEDIA_SERVICE_URL = BASE_URL

# Test data - replace with real IDs from your system
TEST_SHARED_FOLDER_ID = None  # Will need to get from setup
TEST_OWNER_JWT_TOKEN = None
TEST_USER_JWT_TOKEN = None

async def test_shared_folder_download():
    """Test downloading a shared folder as ZIP"""
    
    async with httpx.AsyncClient() as client:
        try:
            print("=" * 80)
            print("TEST: Shared Folder ZIP Download")
            print("=" * 80)
            
            # Step 1: Create a folder as owner
            print("\n1. Creating folder as owner...")
            create_response = await client.post(
                f"{MEDIA_SERVICE_URL}/folders",
                json={"name": "test_shared_zip_folder", "description": "Test folder for ZIP download"},
                headers={"Authorization": f"Bearer {TEST_OWNER_JWT_TOKEN}"}
            )
            
            if create_response.status_code not in [200, 201]:
                print(f"   ❌ Failed to create folder: {create_response.status_code}")
                print(f"   Response: {create_response.text}")
                return False
            
            folder_data = create_response.json()
            folder_id = folder_data.get("id")
            if not folder_id:
                print(f"   ❌ No folder ID in response")
                print(f"   Response: {folder_data}")
                return False
            print(f"   ✓ Created folder: {folder_id}")
            
            # Step 2: Upload a test file to the folder
            print("\n2. Uploading test file...")
            with open(__file__, 'rb') as f:
                files = {"file": f}
                upload_response = await client.post(
                    f"{MEDIA_SERVICE_URL}/files/upload",
                    params={"folder_id": folder_id},
                    files=files,
                    headers={"Authorization": f"Bearer {TEST_OWNER_JWT_TOKEN}"}
                )
            
            if upload_response.status_code not in [200, 201]:
                print(f"   ❌ Failed to upload file: {upload_response.status_code}")
                print(f"   Response: {upload_response.text}")
                return False
            
            file_data = upload_response.json()
            file_id = file_data.get("id")
            if not file_id:
                print(f"   ❌ No file ID in response")
                print(f"   Response: {file_data}")
                return False
            print(f"   ✓ Uploaded file: {file_id}")
            
            # Step 3: Share folder with test user
            print("\n3. Sharing folder with test user...")
            share_response = await client.post(
                f"{MEDIA_SERVICE_URL}/folders/{folder_id}/share",
                json={
                    "target_id": "test_user_id",  # Replace with actual test user ID
                    "permission": "view"
                },
                headers={"Authorization": f"Bearer {TEST_OWNER_JWT_TOKEN}"}
            )
            
            if share_response.status_code not in [200, 201]:
                print(f"   ❌ Failed to share folder: {share_response.status_code}")
                print(f"   Response: {share_response.text}")
                return False
            
            print(f"   ✓ Shared folder")
            
            # Step 4: Download shared folder as ZIP (as non-owner user)
            print("\n4. Downloading shared folder as ZIP...")
            download_response = await client.get(
                f"{MEDIA_SERVICE_URL}/folders/{folder_id}/download-zip",
                headers={"Authorization": f"Bearer {TEST_USER_JWT_TOKEN}"}
            )
            
            if download_response.status_code != 200:
                print(f"   ❌ Failed to download folder: {download_response.status_code}")
                try:
                    error_detail = download_response.json().get("detail", download_response.text)
                except:
                    error_detail = download_response.text
                print(f"   Response: {error_detail}")
                return False
            
            # Check response headers
            content_type = download_response.headers.get("content-type")
            content_disposition = download_response.headers.get("content-disposition")
            content_length = len(download_response.content)
            
            print(f"   ✓ Downloaded successfully")
            print(f"     - Content-Type: {content_type}")
            print(f"     - Content-Disposition: {content_disposition}")
            print(f"     - Size: {content_length} bytes")
            
            # Verify it's a valid ZIP
            if not download_response.content.startswith(b'PK'):
                print(f"   ❌ Downloaded file is not a valid ZIP")
                print(f"   First bytes: {download_response.content[:50]}")
                return False
            
            print(f"   ✓ ZIP file is valid (starts with PK magic bytes)")
            
            print("\n" + "=" * 80)
            print("✓ All tests passed!")
            print("=" * 80)
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test runner"""
    
    # Check if JWT tokens are set
    if not TEST_OWNER_JWT_TOKEN or not TEST_USER_JWT_TOKEN:
        print("ERROR: Test JWT tokens not configured")
        print("Please set TEST_OWNER_JWT_TOKEN and TEST_USER_JWT_TOKEN in this script")
        print("\nTo get tokens:")
        print("1. POST /auth/login with owner credentials")
        print("2. POST /auth/login with test user credentials")
        sys.exit(1)
    
    success = await test_shared_folder_download()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
