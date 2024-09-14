# gitcommit
A Python-based Git repository migration tool that preserves commit history, authorship, and merge commits while preventing duplicates. It features AI-enhanced commit message generation, author-specific branching, and detailed progress tracking, making it ideal for complex repository transfers or Git history restructuring.
# Git Repository Migration Tool

A Python-based Git repository migration tool that preserves commit history, authorship, and merge commits while preventing duplicates. It features AI-enhanced commit message generation, author-specific branching, and detailed progress tracking, making it ideal for complex repository transfers or Git history restructuring.

## Features

- Selective commit migration
- Author-specific branching
- Merge commit preservation
- Duplicate commit prevention
- AI-enhanced commit messages
- Credential management
- Progress tracking
- Excel report generation

## Requirements

- Python 3.x
- Git command-line tools
- Access to Google's Generative AI API

## Usage

1. Clone this repository
2. Install required Python packages: `pip install -r requirements.txt`
3. Set up your Google API key for commit message generation
4. Modify the `gitMigration.py` file with your source and target repository details
5. Run the script: `python gitMigration.py`

## Configuration

Edit the following variables in `gitMigration.py`:

- `API_KEY`: Your Google Generative AI API key
- `LOCAL_REPO_PATH`: Path for local repository storage
- `old_repo_url`: URL of the source repository
- `new_repo_url`: URL of the target repository

## Note

Ensure you have the necessary permissions for both source and target repositories before running the migration.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/yourusername/your-repo-name/issues) if you want to contribute.

## License

[MIT](https://choosealicense.com/licenses/mit/)
