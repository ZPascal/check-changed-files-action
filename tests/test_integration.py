#!/usr/bin/env python
"""
Integration tests for the Check Changed Files GitHub Action.

These tests create real Git repositories and verify the action's behavior
in realistic scenarios.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
import argparse

from pygit2 import Repository, init_repository, Signature

from check_changed_files import CheckedChangedFiles


class TestCheckChangedFilesIntegration(unittest.TestCase):
    """Integration tests for CheckedChangedFiles with real Git repositories."""

    def setUp(self):
        """Create a temporary directory for test repositories."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory after tests."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_git_repo(self, repo_path: str) -> Repository:
        """
        Create a new Git repository with an initial commit.

        Args:
            repo_path: Path where the repository should be created

        Returns:
            Repository: The initialized repository
        """
        repo = init_repository(repo_path)

        # Create an initial commit
        signature = Signature("Test User", "test@example.com")

        # Create initial file
        initial_file = os.path.join(repo_path, "README.md")
        with open(initial_file, "w") as f:
            f.write("# Test Repository\n")

        # Add and commit
        repo.index.add("README.md")
        repo.index.write()
        tree = repo.index.write_tree()
        repo.create_commit("HEAD", signature, signature, "Initial commit", tree, [])

        return repo

    def _modify_file(self, repo_path: str, file_path: str, content: str):
        """
        Modify or create a file in the repository.

        Args:
            repo_path: Path to the repository
            file_path: Relative path to the file
            content: Content to write to the file
        """
        full_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def test_integration_single_file_changed_in_allowed_location(self):
        """Test that a single file change in an allowed location is detected."""
        repo_path = os.path.join(self.test_dir, "test_repo_1")
        self._create_git_repo(repo_path)

        # Modify a file in the src directory
        self._modify_file(repo_path, "src/main.py", 'print("Hello World")\n')

        # Test the action
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_single_file_changed_in_disallowed_location(self):
        """Test that a single file change in a disallowed location is detected."""
        repo_path = os.path.join(self.test_dir, "test_repo_2")
        self._create_git_repo(repo_path)

        # Modify a file in the docs directory
        self._modify_file(repo_path, "docs/guide.md", "# User Guide\n")

        # Test the action with only src/ allowed
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertFalse(result)

    def test_integration_multiple_files_all_allowed(self):
        """Test multiple file changes where all are in allowed locations."""
        repo_path = os.path.join(self.test_dir, "test_repo_3")
        self._create_git_repo(repo_path)

        # Modify multiple files in allowed directories
        self._modify_file(repo_path, "src/main.py", 'print("Hello")\n')
        self._modify_file(repo_path, "src/utils.py", "def helper(): pass\n")
        self._modify_file(repo_path, "tests/test_main.py", "def test(): pass\n")

        # Test with check_all_files=True
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/;tests/",
                git_location=repo_path,
                check_all_files=True,
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_multiple_files_mixed_locations_check_all_files(self):
        """Test multiple file changes with mixed allowed/disallowed locations and check_all_files=True."""
        repo_path = os.path.join(self.test_dir, "test_repo_4")
        self._create_git_repo(repo_path)

        # Modify files in both allowed and disallowed directories
        self._modify_file(repo_path, "src/main.py", 'print("Hello")\n')
        self._modify_file(repo_path, "config/settings.yml", "key: value\n")

        # Test with check_all_files=True - should fail because config/ is not allowed
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=True
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertFalse(result)

    def test_integration_multiple_files_mixed_locations_check_any_file(self):
        """Test multiple file changes with mixed allowed/disallowed locations and check_all_files=False."""
        repo_path = os.path.join(self.test_dir, "test_repo_5")
        self._create_git_repo(repo_path)

        # Modify files in both allowed and disallowed directories
        self._modify_file(repo_path, "src/main.py", 'print("Hello")\n')
        self._modify_file(repo_path, "config/settings.yml", "key: value\n")

        # Test with check_all_files=False - should succeed because at least one file is allowed
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_no_changes(self):
        """Test repository with no changes."""
        repo_path = os.path.join(self.test_dir, "test_repo_6")
        self._create_git_repo(repo_path)

        # Don't modify any files

        # Test the action
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertFalse(result)

    def test_integration_nested_directory_structure(self):
        """Test with deeply nested directory structures."""
        repo_path = os.path.join(self.test_dir, "test_repo_7")
        self._create_git_repo(repo_path)

        # Create deeply nested structure
        self._modify_file(
            repo_path, "src/components/ui/button/Button.py", "class Button: pass\n"
        )
        self._modify_file(
            repo_path, "src/utils/helpers/string_helpers.py", "def trim(): pass\n"
        )

        # Test the action
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=True
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_specific_file_pattern(self):
        """Test with specific file patterns in checked_location."""
        repo_path = os.path.join(self.test_dir, "test_repo_8")
        self._create_git_repo(repo_path)

        # Modify specific files
        self._modify_file(repo_path, "docs/README.md", "# Updated README\n")
        self._modify_file(repo_path, "docs/guide.md", "# Guide\n")

        # Test the action with specific file in checked_location
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="docs/README.md",
                git_location=repo_path,
                check_all_files=False,
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_multiple_semicolon_separated_locations(self):
        """Test with multiple semicolon-separated locations."""
        repo_path = os.path.join(self.test_dir, "test_repo_9")
        self._create_git_repo(repo_path)

        # Modify files in different directories
        self._modify_file(repo_path, "src/main.py", 'print("Hello")\n')
        self._modify_file(repo_path, "docs/api.md", "# API\n")
        self._modify_file(repo_path, "tests/test_api.py", "def test(): pass\n")

        # Test the action with multiple locations
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/;docs/;tests/",
                git_location=repo_path,
                check_all_files=True,
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_file_deletion(self):
        """Test detection of deleted files."""
        repo_path = os.path.join(self.test_dir, "test_repo_10")
        repo = self._create_git_repo(repo_path)

        # Create and commit a file first
        signature = Signature("Test User", "test@example.com")
        self._modify_file(repo_path, "src/old_file.py", 'print("Old")\n')

        repo.index.add("src/old_file.py")
        repo.index.write()
        tree = repo.index.write_tree()
        parent = repo.head.target
        repo.create_commit("HEAD", signature, signature, "Add old file", tree, [parent])

        # Now delete the file
        os.remove(os.path.join(repo_path, "src/old_file.py"))

        # Test the action
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)

    def test_integration_new_file_creation(self):
        """Test detection of newly created files."""
        repo_path = os.path.join(self.test_dir, "test_repo_11")
        self._create_git_repo(repo_path)

        # Create a new file (not committed)
        self._modify_file(repo_path, "src/new_feature.py", "def new_feature(): pass\n")

        # Test the action
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                checked_location="src/", git_location=repo_path, check_all_files=False
            )

            checker = CheckedChangedFiles()
            result = checker.files_changed()

            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
