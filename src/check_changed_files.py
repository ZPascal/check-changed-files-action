#!/usr/bin/env python

import argparse
import os
import logging

from pygit2 import Repository, GIT_STATUS_CURRENT, GitError


class CheckedChangedFiles:
    """
    A class to check for changed files in a Git repository and validates them against a list of allowed files/folders list.

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
             _git_location (str): Git location folder as a relative or absolute path (default is current working directory)
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

    def validate_changed_files(self):
        """
        Validates that all changed files are within the allowed checked locations.

        Raises:
            ValueError: If no changed files are found.
        """

        changed_files: list[str] = self._get_changed_files()
        checked_files_and_folders: list[str] = self._checked_location.split(";")
        checked_files_and_folders_counter: int = 0

        if len(changed_files) > 0:
            for changed_file in changed_files:
                for checked_files_and_folder in checked_files_and_folders:
                    if checked_files_and_folder in changed_file:
                        if self._check_all_files:
                            checked_files_and_folders_counter += 1

                            if len(changed_files) == checked_files_and_folders_counter:
                                self._logger.info(
                                    f"All changed files are allowed in checked location {checked_files_and_folder}."
                                )
                                return
                        else:
                            self._logger.info(
                                f"Changed file {changed_file} is allowed in checked location "
                                f"{checked_files_and_folder}."
                            )
                            break
        else:
            raise ValueError("No changed files found.")


if __name__ == "__main__":
    checked_changed_files: CheckedChangedFiles = CheckedChangedFiles()
    checked_changed_files.validate_changed_files()
