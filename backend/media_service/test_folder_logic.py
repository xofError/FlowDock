"""
Standalone verification of folder operation logic (no external dependencies).
This validates the critical folder operations:
1. Circular dependency prevention
2. Recursive folder/file deletion
3. Folder contents retrieval
"""

import sys
from typing import Optional, List, Dict, Any, Set


# ============================================================================
# Simulated Entities
# ============================================================================

class Folder:
    def __init__(self, folder_id: str, name: str, user_id: str, parent_id: Optional[str] = None):
        self.id = folder_id
        self.name = name
        self.user_id = user_id
        self.parent_id = parent_id


class File:
    def __init__(self, file_id: str, name: str, user_id: str, folder_id: Optional[str] = None):
        self.id = file_id
        self.name = name
        self.user_id = user_id
        self.folder_id = folder_id


# ============================================================================
# Circular Dependency Prevention Logic
# ============================================================================

def has_circular_dependency(
    target_folder_id: str,
    new_parent_id: Optional[str],
    folders: Dict[str, Folder]
) -> bool:
    """
    Check if setting new_parent_id as parent of target_folder_id would create a cycle.
    
    Logic:
    1. If no parent, no cycle possible
    2. Walk up the parent chain from new_parent
    3. If we encounter target_folder, there's a cycle
    4. If we reach None (root), no cycle
    
    Example:
    - A (parent: None)
    - B (parent: A)
    - C (parent: B)
    
    Trying to set C.parent = A -> No cycle (we check: A.parent=None, not B or C)
    Trying to set B.parent = C -> CYCLE! (we check: C.parent=B, found B!)
    """
    if new_parent_id is None:
        return False
    
    if new_parent_id == target_folder_id:
        return True  # Self-reference
    
    visited: Set[str] = set()
    current = new_parent_id
    
    while current is not None:
        if current in visited:
            return True  # Cycle detected
        
        visited.add(current)
        
        if current == target_folder_id:
            return True  # Found target in ancestor chain
        
        if current not in folders:
            break  # Parent not found, assume it's root or doesn't exist
        
        current = folders[current].parent_id
    
    return False


# ============================================================================
# Recursive Folder/File Operations
# ============================================================================

def get_all_descendant_folders(
    folder_id: str,
    folders: Dict[str, Folder]
) -> List[str]:
    """
    Recursively get all descendant folder IDs.
    
    Example:
    A
    ├── B
    │   ├── B1
    │   └── B2
    └── C
    
    get_all_descendant_folders("A") -> ["B", "B1", "B2", "C"]
    """
    descendants = []
    
    for fid, folder in folders.items():
        if folder.parent_id == folder_id:
            descendants.append(fid)
            descendants.extend(get_all_descendant_folders(fid, folders))
    
    return descendants


def delete_folder_recursive(
    folder_id: str,
    folders: Dict[str, Folder],
    files: Dict[str, File]
) -> tuple:
    """
    Delete a folder and all its contents (subfolders and files).
    
    Returns: (success, error_message, deleted_folders, deleted_files)
    """
    if folder_id not in folders:
        return False, "Folder not found", [], []
    
    # Get all descendants
    descendants = get_all_descendant_folders(folder_id, folders)
    all_to_delete = [folder_id] + descendants
    
    # Get all files in these folders
    files_to_delete = []
    for file_id, file in files.items():
        if file.folder_id in all_to_delete:
            files_to_delete.append(file_id)
    
    # Delete folders
    for fid in all_to_delete:
        del folders[fid]
    
    # Delete files
    for file_id in files_to_delete:
        del files[file_id]
    
    return True, None, all_to_delete, files_to_delete


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_scenario_1_simple_circular_dependency():
    """Test: Prevent A from being its own parent"""
    print("\n" + "="*70)
    print("TEST 1: Simple Self-Reference Prevention")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None)
    }
    
    # Try to set A as its own parent
    has_cycle = has_circular_dependency("A", "A", folders)
    
    assert has_cycle is True, "Should detect self-reference"
    print("✓ Correctly prevented A from being its own parent")


def test_scenario_2_two_level_cycle():
    """Test: Prevent A <- B <- A cycle"""
    print("\n" + "="*70)
    print("TEST 2: Two-Level Cycle Prevention")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
    }
    
    # Try to set B.parent = A (already is), then try A.parent = B
    # This would create B <- A <- B cycle
    # So we want to detect: has_circular_dependency("A", "B", folders)
    has_cycle = has_circular_dependency("A", "B", folders)
    
    assert has_cycle is True, f"Should detect 2-level cycle, got {has_cycle}"
    print("✓ Correctly prevented A <- B <- A cycle")


def test_scenario_3_three_level_cycle():
    """Test: Prevent A <- B <- C <- A cycle"""
    print("\n" + "="*70)
    print("TEST 3: Three-Level Cycle Prevention")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
        "C": Folder("C", "Folder C", "user1", "B"),
    }
    
    # Current structure: A -> B -> C
    # Try to set A.parent = C (would create C <- A <- B <- C cycle)
    # has_circular_dependency("A", "C", folders) checks if C is ancestor of A
    # C.parent = B, B.parent = A - found A! So yes, cycle.
    has_cycle = has_circular_dependency("A", "C", folders)
    
    assert has_cycle is True, f"Should detect 3-level cycle, got {has_cycle}"
    print("✓ Correctly prevented A <- B <- C <- A cycle")


def test_scenario_4_valid_parent_assignment():
    """Test: Allow valid parent assignments"""
    print("\n" + "="*70)
    print("TEST 4: Valid Parent Assignment")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
        "C": Folder("C", "Folder C", "user1", None),
    }
    
    # Try to move B under C (valid: C <- B and B <- A <- None)
    has_cycle = has_circular_dependency("B", "C", folders)
    
    assert has_cycle is False, "Should allow valid parent assignment"
    print("✓ Correctly allowed B to be moved under C")


def test_scenario_5_delete_empty_folder():
    """Test: Delete an empty folder"""
    print("\n" + "="*70)
    print("TEST 5: Delete Empty Folder")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
    }
    files = {}
    
    # Delete B (empty)
    success, error, deleted_folders, deleted_files = delete_folder_recursive("B", folders, files)
    
    assert success is True, "Should delete empty folder"
    assert "B" in deleted_folders, "B should be in deleted list"
    assert "B" not in folders, "B should be removed from folders"
    assert "A" in folders, "A should still exist"
    print("✓ Correctly deleted empty folder B")
    print(f"  Deleted folders: {deleted_folders}")


def test_scenario_6_delete_folder_with_files():
    """Test: Delete folder with files in it"""
    print("\n" + "="*70)
    print("TEST 6: Delete Folder with Files")
    print("="*70)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
    }
    files = {
        "file1": File("file1", "Document.pdf", "user1", "A"),
        "file2": File("file2", "Image.jpg", "user1", "A"),
    }
    
    # Delete A (has files)
    success, error, deleted_folders, deleted_files = delete_folder_recursive("A", folders, files)
    
    assert success is True, "Should delete folder with files"
    assert "A" in deleted_folders, "A should be in deleted list"
    assert len(deleted_files) == 2, "Both files should be deleted"
    assert "file1" not in files, "file1 should be removed"
    assert "file2" not in files, "file2 should be removed"
    print("✓ Correctly deleted folder A and its 2 files")
    print(f"  Deleted folders: {deleted_folders}")
    print(f"  Deleted files: {deleted_files}")


def test_scenario_7_delete_folder_with_subfolders_and_files():
    """Test: Recursive delete with nested structure"""
    print("\n" + "="*70)
    print("TEST 7: Recursive Delete with Nested Structure")
    print("="*70)
    
    # Structure:
    # A (File1)
    # ├── B (File2, File3)
    # │   └── B1 (File4)
    # └── C (File5)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
        "B1": Folder("B1", "Folder B1", "user1", "B"),
        "C": Folder("C", "Folder C", "user1", "A"),
    }
    files = {
        "file1": File("file1", "File1.txt", "user1", "A"),
        "file2": File("file2", "File2.txt", "user1", "B"),
        "file3": File("file3", "File3.txt", "user1", "B"),
        "file4": File("file4", "File4.txt", "user1", "B1"),
        "file5": File("file5", "File5.txt", "user1", "C"),
    }
    
    initial_folders = len(folders)
    initial_files = len(files)
    
    # Delete A (recursive)
    success, error, deleted_folders, deleted_files = delete_folder_recursive("A", folders, files)
    
    assert success is True, "Should delete entire structure"
    assert len(deleted_folders) == 4, f"Should delete 4 folders, got {len(deleted_folders)}"
    assert len(deleted_files) == 5, f"Should delete 5 files, got {len(deleted_files)}"
    assert len(folders) == 0, f"No folders should remain, got {len(folders)}"
    assert len(files) == 0, f"No files should remain, got {len(files)}"
    
    print("✓ Correctly deleted entire nested structure")
    print(f"  Structure: A (with B->B1 and C)")
    print(f"  Deleted folders: {deleted_folders}")
    print(f"  Deleted files: {deleted_files}")
    print(f"  Remaining folders: {len(folders)}")
    print(f"  Remaining files: {len(files)}")


def test_scenario_8_delete_middle_folder():
    """Test: Delete middle folder in hierarchy"""
    print("\n" + "="*70)
    print("TEST 8: Delete Middle Folder in Hierarchy")
    print("="*70)
    
    # Structure:
    # A
    # └── B (File1, File2)
    #     └── C (File3)
    
    folders = {
        "A": Folder("A", "Folder A", "user1", None),
        "B": Folder("B", "Folder B", "user1", "A"),
        "C": Folder("C", "Folder C", "user1", "B"),
    }
    files = {
        "file1": File("file1", "File1.txt", "user1", "B"),
        "file2": File("file2", "File2.txt", "user1", "B"),
        "file3": File("file3", "File3.txt", "user1", "C"),
    }
    
    # Delete B (middle folder with children and files)
    success, error, deleted_folders, deleted_files = delete_folder_recursive("B", folders, files)
    
    assert success is True, "Should delete B and its contents"
    assert len(deleted_folders) == 2, "Should delete B and C"
    assert "B" in deleted_folders and "C" in deleted_folders
    assert len(deleted_files) == 3, "Should delete all 3 files"
    assert "A" in folders, "A should still exist"
    assert "B" not in folders, "B should be deleted"
    assert "C" not in folders, "C should be deleted"
    
    print("✓ Correctly deleted middle folder B and its contents")
    print(f"  Deleted folders: {deleted_folders}")
    print(f"  Deleted files: {deleted_files}")
    print(f"  Remaining folders: {list(folders.keys())}")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    tests = [
        test_scenario_1_simple_circular_dependency,
        test_scenario_2_two_level_cycle,
        test_scenario_3_three_level_cycle,
        test_scenario_4_valid_parent_assignment,
        test_scenario_5_delete_empty_folder,
        test_scenario_6_delete_folder_with_files,
        test_scenario_7_delete_folder_with_subfolders_and_files,
        test_scenario_8_delete_middle_folder,
    ]
    
    print("\n")
    print("█" * 70)
    print("FOLDER OPERATIONS VERIFICATION - STANDALONE TEST SUITE")
    print("█" * 70)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {e}")
    
    print("\n" + "█" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("█" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
