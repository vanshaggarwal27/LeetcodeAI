import requests
import os
import markdown
import time

TOKEN = os.getenv("MEDIUM_TOKEN")
USER_ID = os.getenv("MEDIUM_USER_ID")

def post_to_medium(title, content):
    if not TOKEN or not USER_ID:
        raise Exception("Medium credentials missing. Please set MEDIUM_TOKEN and MEDIUM_USER_ID in environment variables.")
        
    url = f"https://api.medium.com/v1/users/{USER_ID}/posts"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    html_content = markdown.markdown(content)

    data = {
        "title": f"LeetCode Solution: {title}",
        "contentFormat": "html",
        "content": html_content,
        "publishStatus": "public",
        "tags": ["LeetCode", "DSA", "Coding Interview"]
    }

    retries = 2
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # Check for generic failure or API restriction
            if response.status_code in (200, 201):
                return response.json()
            else:
                 if attempt < retries:
                     time.sleep(1) # wait before retrying
                 else:
                     raise Exception(f"Medium API Error Status {response.status_code}: {response.text}")
        except Exception as e:
            if attempt == retries:
                raise Exception(f"Network Error reaching Medium API: {str(e)}")
            time.sleep(1)
