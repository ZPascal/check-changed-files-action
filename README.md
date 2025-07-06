# GitHub Action: Check Changed Files

This GitHub Action checks for changed files in a Git repository and validates them against a list of allowed files and folders. It is useful for enforcing file or folder boundaries in pull requests or CI/CD pipelines.

## Features

- Checks for changed files in a Git repository and validates them against a list of allowed files and folders
- Define a custom location of the Git repository
- Supports checking all files and folders in the directory
- The functionality is implemented in Python using the `pygit2` library and fully tested by unit tests

---

## Inputs

| Name              | Description                                                                | Required | Default                     |
|-------------------|----------------------------------------------------------------------------|----------|-----------------------------|
| checked_location  | Enter the location of the files, separated by `;`. Example: `src/;docs/test.txt;tests/test*` | true     |                             |
| git_location      | Path to the Git repository.                                                | false    | (current working directory) |
| check_all_files   | Enables the check of all defined files and folders in the directory.       | false    | false                       |
| github_server_url   | Define the used GitHub server url.     | false    | https://github.com          |

---

## Usage

```yaml
- name: Check changed files
  uses: ZPascal/check-changed-files-action@v1
  with:
    checked_location: 'src/;docs/README.md'
    git_location: './'
    check_all_files: 'true'
```

---

## Example Workflow

```yaml
name: Check Changed Files

on:
  pull_request:
    paths:
      - 'src/**'
      - 'docs/**'

jobs:
  check-changes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check changed files
        uses: ZPascal/check-changed-files-action@v1
        with:
          checked_location: 'src/;docs/README.md'
          git_location: './'
          check_all_files: 'true'
```

---

## Output

- Logs info about changed files that are allowed or not allowed.
- The workflow fails if changed files are not within the allowed locations.

---

## Requirements

- Python 3.x
- [pygit2](https://www.pygit2.org/)

---

## License

The gcp-bucket-upload-action is licensed under the [Apache 2.0](LICENSE).
