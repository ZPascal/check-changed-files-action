#!/usr/bin/env python

import argparse
import os
import logging

from pygit2 import Repository, GIT_STATUS_CURRENT, GitError


class CheckedChangedFiles:
    """
    A class to check for changed files in a Git repository and validates them against a list of allowed files/folders.

    Attributes:
        _logger (logging.Logger): Logger instance for tracking operations
        _checked_location (str): Files and folder to check
        _git_location (str): Git location folder as a relative or absolute path
        _check_all_files (bool): Whether to check all files in the repository
    """

    def __init__(self):
        """
        Initializes the CheckedChangedFiles instance by parsing arguments and setting up logging.
        """

        args = self._parse_args()

        self._logger: logging.Logger = logging.getLogger("CheckedChangedFilesLogger")
        self._checked_location: str = args.checked_location
        self._git_location: str = args.git_location
        self._check_all_files: bool = args.check_all_files

    @staticmethod
    def _parse_args() -> argparse.Namespace:
        """
         Parses command-line arguments for checked location, git location, and check_all_files a flag.

        Returns:
             _checked_location (str): Files and folder to check (semicolon-separated)
             _git_location (str): Git location folder as a relative or absolute path (default is the current working directory)
             _check_all_files (bool): Whether to check all files in the repository (default is False)
        """

        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument(
            "-cl",
            "--checked-location",
            help="Checked Location",
            type=str,
            required=True,
        )
        arg_parser.add_argument(
            "-gl",
            "--git-location",
            help="Git repository Location",
            type=str,
            required=False,
            default=os.getcwd(),
        )
        arg_parser.add_argument(
            "-caf",
            "--check-all-files",
            help="Git repository Location",
            action="store_true",
            required=False,
            default=False,
        )

        return arg_parser.parse_args()

    @staticmethod
    def _is_file_in_allowed_locations(file: str, checked_locations: list[str]) -> bool:
        """
        Checks if a file path matches any of the allowed locations.

        Args:
            file (str): The file path to check
            checked_locations (list[str]): List of allowed location patterns

        Returns:
            bool: True if the file matches any allowed location, False otherwise
        """
        return any(loc in file for loc in checked_locations)

    def _validate_git_path(self):
        """
        Validates that the provided git location is a valid Git repository.

        Raises:
            SystemExit: If the path is not a valid Git repository.
        """

        if os.path.exists(self._git_location):
            repo_path = os.path.abspath(self._git_location)

            if not os.path.isdir(os.path.join(repo_path, ".git")):
                self._logger.error(f"Error: {repo_path} is not a Git repository.")
                raise SystemExit(1)
        else:
            raise ValueError(f"Error: {self._git_location} is not available.")

    def _get_changed_files(self) -> list[str]:
        """
        Gets a list of changed files in the Git repository.

        Returns:
            list[str]: List of changed file paths.

        Raises:
            SystemExit: If the repository is invalid.
        """

        self._validate_git_path()

        try:
            git_repository: Repository = Repository(self._git_location)
        except (KeyError, GitError):
            self._logger.error(
                f"Error: {self._git_location} is not a valid Git repository."
            )
            raise SystemExit(1)

        status: dict[str, int] = git_repository.status()
        changed_files: list[str] = []
        for filepath, flags in status.items():
            if flags != GIT_STATUS_CURRENT:
                changed_files.append(filepath)
        return changed_files

    def _check_all_files_allowed(self, changed_files: list[str], checked_locations: list[str]) -> bool:
        """
        Checks if ALL changed files are in allowed locations.

        Args:
            changed_files (list[str]): List of changed file paths
            checked_locations (list[str]): List of allowed location patterns

        Returns:
            bool: True if all files are allowed, False otherwise
        """
        if all(self._is_file_in_allowed_locations(file, checked_locations) for file in changed_files):
            self._logger.info(
                f"All changed files are allowed in checked locations {checked_locations}."
            )
            return True

        for file in changed_files:
            if not self._is_file_in_allowed_locations(file, checked_locations):
                self._logger.info(
                    f"Changed file {file} is not a part of the checked locations {checked_locations}."
                )
                break
        return False

    def _check_any_file_allowed(self, changed_files: list[str], checked_locations: list[str]) -> bool:
        """
        Checks if ANY changed file is in allowed locations.

        Args:
            changed_files (list[str]): List of changed file paths
            checked_locations (list[str]): List of allowed location patterns

        Returns:
            bool: True if at least one file is allowed, False otherwise
        """
        for file in changed_files:
            if self._is_file_in_allowed_locations(file, checked_locations):
                self._logger.info(
                    f"Changed file {file} is allowed in checked locations {checked_locations}."
                )
                return True

        if changed_files:
            self._logger.info(
                f"Changed file {changed_files[0]} is not a part of the checked locations {checked_locations}."
            )
        return False

    def files_changed(self) -> bool:
        """
        Validates that changed files are within the allowed checked locations.

        Returns:
            bool: True if validation passes based on check mode, False otherwise
        """
        changed_files = self._get_changed_files()
        checked_locations = self._checked_location.split(";")

        if not changed_files:
            self._logger.info("No changed files found.")
            return False

        if self._check_all_files:
            return self._check_all_files_allowed(changed_files, checked_locations)
        else:
            return self._check_any_file_allowed(changed_files, checked_locations)


if __name__ == "__main__":
    checked_changed_files: CheckedChangedFiles = CheckedChangedFiles()
    files_changed: bool = checked_changed_files.files_changed()
    print(str(files_changed).lower())
