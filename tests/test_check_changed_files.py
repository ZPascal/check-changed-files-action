from unittest import TestCase
from unittest.mock import patch, MagicMock, Mock

from check_changed_files import CheckedChangedFiles

from pygit2 import GitError


class TestCheckedChangedFiles(TestCase):

    @patch("check_changed_files.CheckedChangedFiles._parse_args", autospec=True)
    def setUp(self, parse_args_mock):
        parse_args_mock.return_value = Mock(
            checked_location="test",
            git_location="test",
            check_all_files=False,
        )
        self.check_changed_files = CheckedChangedFiles()

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_args_returns_expected_namespace(self, parse_args_mock):
        parse_args_mock.return_value = Mock(
            checked_location="test",
            git_location="test",
            check_all_files=False,
        )

        args = CheckedChangedFiles._parse_args()
        self.assertEqual(args.checked_location, "test")
        self.assertEqual(args.git_location, "test")
        self.assertFalse(args.check_all_files)

    @patch(
        "sys.argv",
        [
            "check_changed_files.py",
            "-cl",
            "file1.txt;folder",
            "-gl",
            "./test",
            "-caf",
        ],
    )
    def test_parse_args_with_sys_argv(self):
        args = CheckedChangedFiles._parse_args()
        self.assertEqual(args.checked_location, "file1.txt;folder")
        self.assertEqual(args.git_location, "./test")
        self.assertTrue(args.check_all_files)

    @patch("check_changed_files.os.path.isdir")
    @patch("check_changed_files.os.path.abspath")
    @patch("check_changed_files.os.path.exists")
    def test_validate_git_path_valid(self, path_exists_mock, abspath_mock, isdir_mock):
        path_exists_mock.return_value = True
        abspath_mock.return_value = "/repo"
        isdir_mock.return_value = True

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()

        self.assertIsNone(self.check_changed_files._validate_git_path())

    @patch("check_changed_files.os.path.isdir")
    @patch("check_changed_files.os.path.abspath")
    @patch("check_changed_files.os.path.exists")
    def test_validate_git_path_invalid(
        self, path_exists_mock, abspath_mock, isdir_mock
    ):
        path_exists_mock.return_value = True
        abspath_mock.return_value = "/repo"
        isdir_mock.return_value = False

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()

        with self.assertRaises(SystemExit):
            self.check_changed_files._validate_git_path()

    @patch("check_changed_files.os.path.exists")
    def test_validate_git_path_path_not_available(self, path_exists_mock):
        path_exists_mock.return_value = False

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()

        with self.assertRaises(ValueError):
            self.check_changed_files._validate_git_path()

    @patch("check_changed_files.CheckedChangedFiles._validate_git_path")
    @patch("check_changed_files.Repository")
    def test_get_changed_files(self, mock_repo, mock_validate):
        mock_status = {"file1.py": 1, "file2.py": 0}
        mock_repo.return_value.status.return_value = mock_status

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()
        result = self.check_changed_files._get_changed_files()

        self.assertIn("file1.py", result)
        self.assertNotIn("file2.py", result)

    @patch("check_changed_files.CheckedChangedFiles._validate_git_path")
    @patch("check_changed_files.Repository")
    def test_get_changed_files_git_issue(self, mock_repo, mock_validate):

        mock_repo.side_effect = GitError

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()

        with self.assertRaises(SystemExit):
            self.check_changed_files._get_changed_files()

        self.check_changed_files._logger.error.assert_called_with(
            f"Error: /repo is not a valid Git repository."
        )

    @patch("check_changed_files.CheckedChangedFiles._validate_git_path")
    @patch("check_changed_files.Repository")
    def test_get_changed_files_key_error(self, mock_repo, mock_validate):
        mock_repo.side_effect = KeyError

        self.check_changed_files._git_location = "/repo"
        self.check_changed_files._logger = MagicMock()

        with self.assertRaises(SystemExit):
            self.check_changed_files._get_changed_files()

        self.check_changed_files._logger.error.assert_called_with(
            f"Error: /repo is not a valid Git repository."
        )

    @patch("check_changed_files.CheckedChangedFiles._get_changed_files")
    def test_validate_changed_files_with_changes(self, get_changed_files_mock):
        get_changed_files_mock.return_value = ["src/test.py"]

        self.check_changed_files._checked_location = "src/"
        self.check_changed_files._check_all_files = False
        self.check_changed_files._logger = MagicMock()
        self.check_changed_files.validate_changed_files()

        self.check_changed_files._logger.info.assert_called_with(
            "Changed file src/test.py is allowed in checked location src/."
        )

    @patch("check_changed_files.CheckedChangedFiles._get_changed_files")
    def test_validate_changed_files_no_changes(self, get_changed_files_mock):
        get_changed_files_mock.return_value = []

        self.check_changed_files._checked_location = "src/"
        self.check_changed_files._check_all_files = False
        self.check_changed_files._logger = MagicMock()

        with self.assertRaises(ValueError):
            self.check_changed_files.validate_changed_files()

    @patch("check_changed_files.CheckedChangedFiles._get_changed_files")
    def test_validate_changed_files_with_changes_all_changes(self, get_changed_files_mock):
        get_changed_files_mock.return_value = ["src/test.py"]

        self.check_changed_files._checked_location = "src/"
        self.check_changed_files._check_all_files = True
        self.check_changed_files._logger = MagicMock()
        self.check_changed_files.validate_changed_files()

        self.check_changed_files._logger.info.assert_called_with(
            "All changed files are allowed in checked location src/."
        )