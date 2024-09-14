import subprocess
import os
import json
import requests
import time
from datetime import datetime
from openpyxl import Workbook

API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
LOCAL_REPO_PATH = r"C:\path\to\local\repo"

def login_to_gitlab():
    username = input("Enter your GitLab username: ")
    password = input("Enter your GitLab password: ")
    return username, password

def clone_repo(repo_url, local_path, username, password):
    if not os.path.exists(local_path):
        try:
            repo_url = repo_url.replace("https://", f"https://{username}:{password}@")
            subprocess.run(['git', 'clone', repo_url, local_path], check=True)
            print(f"Repository cloned to {local_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")

def extract_commit_info(repo_path, start_from_commit=1, allowed_authors=None):
    if not os.path.isdir(repo_path):
        print(f"Error: Provided path '{repo_path}' is not a valid directory.")
        return []
    changes = []
    try:
        os.chdir(repo_path)
        print(f"Current working directory: {os.getcwd()}")

        current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.STDOUT).decode('utf-8').strip()
        print(f"Current branch: {current_branch}")

        remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], stderr=subprocess.STDOUT).decode('utf-8').strip()
        print(f"Remote URL: {remote_url}")

        output = subprocess.check_output(['git', 'log', '--all', '--reverse', '--pretty=format:%H - %s - %an - %cd', '--date=format:%Y-%m-%d %H:%M:%S'], stderr=subprocess.STDOUT).decode('utf-8')
        all_commits = output.strip().split('\n')

        commits_to_process = all_commits[start_from_commit-1:]

        for line in commits_to_process:
            parts = line.split(" - ", 3)
            if len(parts) == 4:
                commit_hash, commit_message, author, commit_date = parts
                if allowed_authors is None or author in allowed_authors:
                    changes.append(parts)

        print(f"Total commits found: {len(changes)}")
        if changes:
            print(f"First commit to process: {changes[0][0]}")
            print(f"Last commit to process: {changes[-1][0]}")

        wb = Workbook()
        ws = wb.active
        ws.title = "Commit Information"

        ws.append(["Commit Hash", "Commit Message", "Author", "Date"])

        for change in changes:
            ws.append(change)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"commit_info_{timestamp}.xlsx"
        wb.save(excel_filename)
        print(f"Commit information saved to {excel_filename}")

        return changes
    except subprocess.CalledProcessError as e:
        print(f"Error reading git history: {e.output.decode()}")
        return []

def commit_and_push_changes(repo_path, commit_message, author, commit_date, username, password, branch_name):
    os.chdir(repo_path)
    
    os.environ['GIT_AUTHOR_NAME'] = author
    os.environ['GIT_AUTHOR_EMAIL'] = f"{username}@example.com"
    os.environ['GIT_AUTHOR_DATE'] = commit_date
    os.environ['GIT_COMMITTER_NAME'] = author
    os.environ['GIT_COMMITTER_EMAIL'] = f"{username}@example.com"
    os.environ['GIT_COMMITTER_DATE'] = commit_date

    status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True).stdout.strip()
    if status:
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print(f"Committed changes with message: {commit_message}")
            
            remote_url = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                        capture_output=True, text=True).stdout.strip()
            encoded_username = requests.utils.quote(username)
            encoded_password = requests.utils.quote(password)
            push_url = remote_url.replace("https://", f"https://{encoded_username}:{encoded_password}@")
            
            print(f"Pushing to branch: {branch_name}")
            print(f"Remote URL: {remote_url}")
            
            result = subprocess.run(['git', 'push', '-u', push_url, branch_name], 
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Changes pushed to GitLab on branch {branch_name}.")
                print(f"Push output: {result.stdout}")
            else:
                print(f"Error pushing to GitLab. Error message: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error during commit or push: {e}")
            print(f"Error output: {e.stderr}")
    else:
        print("No changes to commit.")

def get_existing_commits(repo_path):
    os.chdir(repo_path)
    existing_commits = subprocess.run(['git', 'log', '--format=%H'], capture_output=True, text=True).stdout.strip().split('\n')
    return set(existing_commits)

def is_merge_commit(repo_path, commit_hash):
    os.chdir(repo_path)
    parents = subprocess.run(['git', 'rev-parse', f'{commit_hash}^@'], 
                             capture_output=True, text=True).stdout.strip().split('\n')
    return len(parents) > 1

def get_merge_message(repo_path, commit_hash):
    os.chdir(repo_path)
    merge_message = subprocess.run(['git', 'log', '-1', '--pretty=%B', commit_hash],
                                   capture_output=True, text=True).stdout.strip()
    return merge_message

def get_changes(repo_path, commit_hash):
    os.chdir(repo_path)
    files_changed = subprocess.run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash], 
                                   capture_output=True, text=True).stdout.strip().split('\n')
    
    changes = []
    for file in files_changed:
        diff = subprocess.run(['git', 'diff', f'{commit_hash}^..{commit_hash}', '--', file], 
                              capture_output=True, text=True).stdout
        changes.append(f"File: {file}\n{diff}")
    
    return "\n".join(changes)

def generate_commit_message(changes, old_commit_message):
    headers = {
        "Content-Type": "application/json"
    }
    
    initial_prompt = f"""Generate a detailed and informative commit message for the following changes:

Changes:
{changes}

Previous commit message:
{old_commit_message}

The commit message should:
1. Start with a brief summary line (50 characters or less)
2. Follow with a blank line
3. Provide a more detailed explanation, including:
   - What files were modified
   - How they were changed
   - Why the changes were necessary
   - Any potential impacts or side effects of the changes
4. Use bullet points for multiple changes if needed

Please generate the commit message directly, without asking for more information."""

    data = {
        "contents": [{
            "parts": [{
                "text": initial_prompt
            }]
        }]
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        generated_message = response.json()['candidates'][0]['content']['parts'][0]['text']
        
        validation_prompt = f"""Is the following text a valid commit message? Please answer with only 'Yes' or 'No'.

{generated_message}"""

        validation_data = {
            "contents": [{
                "parts": [{
                    "text": validation_prompt
                }]
            }]
        }
        
        validation_response = requests.post(API_URL, headers=headers, json=validation_data)
        
        if validation_response.status_code == 200:
            validation_result = validation_response.json()['candidates'][0]['content']['parts'][0]['text'].strip().lower()
            
            if validation_result == 'yes':
                return generated_message.strip()
            else:
                return f"""Changes:
{changes}

Previous commit message:
{old_commit_message}"""
        else:
            print(f"Error validating commit message: {validation_response.status_code}")
            return None
    else:
        print(f"Error generating commit message: {response.status_code}")
        return None

def process_commits(old_repo_path, new_repo_path, commits, credentials):
    existing_commits = get_existing_commits(new_repo_path)
    
    for commit_hash, old_commit_message, author, commit_date in commits:
        if commit_hash in existing_commits:
            print(f"\nSkipping commit {commit_hash} as it already exists in the new repository.")
            continue

        print(f"\nProcessing commit:")
        print(f"Hash: {commit_hash}")
        print(f"Old Message: {old_commit_message}")
        print(f"Author: {author}")
        print(f"Date: {commit_date}")

        if is_merge_commit(old_repo_path, commit_hash):
            new_commit_message = get_merge_message(old_repo_path, commit_hash)
            print("This is a merge commit. Using the original merge message.")
        else:
            changes = get_changes(old_repo_path, commit_hash)
            new_commit_message = generate_commit_message(changes, old_commit_message)
            if new_commit_message is None:
                print("Using original commit message due to API error.")
                new_commit_message = old_commit_message
        
        print(f"New commit message:\n{new_commit_message}")

        os.chdir(new_repo_path)

        author_branch = f"branch_{author}"
        try:
            subprocess.run(['git', 'checkout', author_branch], check=True)
        except subprocess.CalledProcessError:
            print(f"Branch {author_branch} does not exist. Creating it...")
            subprocess.run(['git', 'checkout', '-b', author_branch], check=True)

        subprocess.run(['git', '-C', old_repo_path, 'checkout', commit_hash], check=True)
        subprocess.run(['robocopy', old_repo_path, new_repo_path, '/MIR', '/XD', '.git'], check=False)

        if author in credentials:
            username, password = credentials[author]
        else:
            print(f"Credentials not found for {author}. Please enter them now:")
            username = input(f"Enter GitLab username for {author}: ")
            password = input(f"Enter GitLab password for {author}: ")
            credentials[author] = (username, password)

        commit_and_push_changes(new_repo_path, new_commit_message, author, commit_date, username, password, author_branch)

        existing_commits.add(commit_hash)

    print("\nFinished processing specified commits")

def main():
    old_repo_url = "https://gitlab.example.com/old-repo.git"
    new_repo_url = "https://gitlab.example.com/new-repo.git"

    old_repo_path = os.path.join(LOCAL_REPO_PATH, "old_repo")
    new_repo_path = os.path.join(LOCAL_REPO_PATH, "new_repo")

    print(f"Old repository URL: {old_repo_url}")
    print(f"New repository URL: {new_repo_url}")
    print(f"Old repository local path: {old_repo_path}")
    print(f"New repository local path: {new_repo_path}")

    credentials = {}

    print("Please provide initial login credentials:")
    username = input("Enter your GitLab username: ")
    password = input("Enter your GitLab password: ")
    credentials[username] = (username, password)

    clone_repo(old_repo_url, old_repo_path, username, password)
    clone_repo(new_repo_url, new_repo_path, username, password)

    allowed_authors = [
        "author1",
        "author2",
        "author3"
    ]

    commits = extract_commit_info(old_repo_path, start_from_commit=1, allowed_authors=allowed_authors)

    process_commits(old_repo_path, new_repo_path, commits, credentials)

    print("Migration process completed.")

if __name__ == "__main__":
    main()
