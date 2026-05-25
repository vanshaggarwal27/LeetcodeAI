import requests

query = """
query {
  recentAcSubmissionList(username: "vanshaggarwal27", limit: 5) {
    title
    timestamp
  }
}
"""

r = requests.post("https://leetcode.com/graphql", json={"query": query})
print(r.json())
