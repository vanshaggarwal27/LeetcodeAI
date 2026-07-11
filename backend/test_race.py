import threading

import requests


def send_request():
    payload = {
        "title": "Race Condition Test",
        "code": "print('hello')",
        "author": "Anonymous Developer",
        "publish_as_draft": True
    }
    # You might need to add authentication headers depending on your setup
    response = requests.post("http://127.0.0.1:10000/generate-blog", json=payload)
    print(f"Response: {response.json()}")

threads = []
for _ in range(5):
    t = threading.Thread(target=send_request)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
