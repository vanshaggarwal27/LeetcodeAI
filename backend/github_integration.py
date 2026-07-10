import base64

import requests


def push_solution_to_github(title: str, code: str, access_token: str, repo_name: str) -> dict:
    """
    Pushes the LeetCode solution code to the user's GitHub repository.
    """
    if not access_token or not repo_name:
        raise ValueError("GitHub credentials missing.")

    # Sanitize title for filename
    filename = title.replace(" ", "_").replace("/", "-")
    file_path = f"solutions/{filename}.py"

    url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists to get the SHA (required for updating)
    sha = None
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            sha = response.json().get("sha")
    except Exception as e:
        print(f"Error checking GitHub file: {e}")

    # Create or update the file
    commit_message = f"Add solution for {title} via LeetLog AI"
    encoded_content = base64.b64encode(code.encode("utf-8")).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    try:
        response = requests.put(url, headers=headers, json=payload, timeout=15)
        if response.status_code in (200, 201):
            return {"status": "success", "data": response.json()}
        else:
            raise Exception(f"GitHub API Error: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Failed to push to GitHub: {str(e)}")
