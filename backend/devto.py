import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TAGS = ["leetcode", "dsa", "programming", "tutorial"]


@dataclass(frozen=True)
class PublishResult:
    platform: str
    status: str
    url: str | None = None
    response: dict[str, Any] | None = None
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "platform": self.platform,
            "status": self.status,
        }
        if self.url:
            payload["url"] = self.url
        if self.response is not None:
            payload["response"] = self.response
        if self.message:
            payload["message"] = self.message
        return payload


class PublisherError(Exception):
    """Raised when a selected publishing provider cannot complete."""


class BasePublisher:
    platform = "base"

    def publish(
        self,
        title: str,
        content: str,
        *,
        tags: list[str],
        published: bool,
        credentials: dict[str, Any] | None = None,
    ) -> PublishResult:
        raise NotImplementedError

    @staticmethod
    def _post_with_retries(
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        platform: str,
        retries: int = 2,
    ) -> dict[str, Any]:
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                if response.status_code in (200, 201):
                    return response.json()
                if attempt == retries:
                    raise PublisherError(
                        f"{platform} API Error {response.status_code}: {response.text}"
                    )
            except requests.RequestException as exc:
                if attempt == retries:
                    raise PublisherError(f"{platform} network error: {exc}") from exc
            time.sleep(1)
        raise PublisherError(f"{platform} API request failed.")


class DevToPublisher(BasePublisher):
    platform = "devto"

    def publish(
        self,
        title: str,
        content: str,
        *,
        tags: list[str],
        published: bool,
        credentials: dict[str, Any] | None = None,
    ) -> PublishResult:
        api_key = (credentials or {}).get("devto_api_key") or os.getenv("DEVTO_API_KEY")
        if not api_key:
            raise PublisherError(
                "Dev.to API key missing. Add it in Settings > Integrations."
            )

        response = self._post_with_retries(
            "https://dev.to/api/articles",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            payload={
                "article": {
                    "title": f"LeetCode Solution: {title}",
                    "body_markdown": content,
                    "published": published,
                    "tags": tags,
                }
            },
            platform="Dev.to",
        )
        return PublishResult(
            platform=self.platform,
            status="success",
            url=response.get("url"),
            response=response,
        )


class HashnodePublisher(BasePublisher):
    platform = "hashnode"

    async def publish(
        self,
        title: str,
        content: str,
        *,
        tags: list[str],
        published: bool,
        credentials: dict[str, Any] | None = None,
    ) -> PublishResult:
        credentials = credentials or {}
        token = credentials.get("hashnode_token") or os.getenv("HASHNODE_TOKEN")
        publication_id = credentials.get("hashnode_publication_id") or os.getenv("HASHNODE_PUBLICATION_ID")
        if not token or not publication_id:
            raise PublisherError(
                "Hashnode publishing requires HASHNODE_TOKEN and HASHNODE_PUBLICATION_ID."
            )

        mutation = """
        mutation PublishPost($input: PublishPostInput!) {
          publishPost(input: $input) {
            post {
              id
              url
              title
            }
          }
        }
        """
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                http_response = await client.post(
                    "https://gql.hashnode.com/",
                    headers={
                        "Authorization": token,
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": mutation,
                        "variables": {
                            "input": {
                                "publicationId": publication_id,
                                "title": f"LeetCode Solution: {title}",
                                "contentMarkdown": content,
                                "tags": [{"name": tag, "slug": tag} for tag in tags],
                                "draft": not published,
                            }
                        },
                    },
                )
            if http_response.status_code not in (200, 201):
                raise PublisherError(
                    f"Hashnode API Error {http_response.status_code}: {http_response.text}"
                )
            response = http_response.json()
        except httpx.RequestError as exc:
            raise PublisherError(f"Hashnode network error: {exc}") from exc
        # GraphQL always returns HTTP 200; check the response-level errors field.
        gql_errors = response.get("errors")
        if gql_errors:
            message = gql_errors[0].get("message", "Hashnode GraphQL error")
            raise PublisherError(f"Hashnode GraphQL error: {message}")
        post = response.get("data", {}).get("publishPost", {}).get("post", {})
        return PublishResult(
            platform=self.platform,
            status="success",
            url=post.get("url"),
            response=response,
        )


class MediumPublisher(BasePublisher):
    platform = "medium"

    def publish(
        self,
        title: str,
        content: str,
        *,
        tags: list[str],
        published: bool,
        credentials: dict[str, Any] | None = None,
    ) -> PublishResult:
        credentials = credentials or {}
        token = credentials.get("medium_token") or os.getenv("MEDIUM_TOKEN")
        user_id = credentials.get("medium_user_id") or os.getenv("MEDIUM_USER_ID")
        if not token or not user_id:
            raise PublisherError(
                "Medium publishing requires MEDIUM_TOKEN and MEDIUM_USER_ID."
            )

        response = self._post_with_retries(
            f"https://api.medium.com/v1/users/{user_id}/posts",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            payload={
                "title": f"LeetCode Solution: {title}",
                "contentFormat": "markdown",
                "content": content,
                "tags": tags[:5],
                "publishStatus": "public" if published else "draft",
            },
            platform="Medium",
        )
        data = response.get("data", {})
        return PublishResult(
            platform=self.platform,
            status="success",
            url=data.get("url"),
            response=response,
        )


class WebhookPublisher(BasePublisher):
    platform = "webhook"

    def publish(
        self,
        title: str,
        content: str,
        *,
        tags: list[str],
        published: bool,
        credentials: dict[str, Any] | None = None,
    ) -> PublishResult:
        webhook_url = (credentials or {}).get("blog_webhook_url") or os.getenv("BLOG_WEBHOOK_URL")
        if not webhook_url:
            raise PublisherError("Personal blog publishing requires BLOG_WEBHOOK_URL.")

        response = self._post_with_retries(
            webhook_url,
            headers={"Content-Type": "application/json"},
            payload={
                "title": f"LeetCode Solution: {title}",
                "body_markdown": content,
                "tags": tags,
                "published": published,
                "source": "leetlog-ai",
            },
            platform="Custom webhook",
        )
        return PublishResult(
            platform=self.platform,
            status="success",
            url=response.get("url"),
            response=response,
        )


PUBLISHERS: dict[str, BasePublisher] = {
    "devto": DevToPublisher(),
    "hashnode": HashnodePublisher(),
    "medium": MediumPublisher(),
    "webhook": WebhookPublisher(),
}


def normalize_platforms(platforms: list[str] | None) -> list[str]:
    selected = platforms or ["devto"]
    normalized: list[str] = []
    for platform in selected:
        key = platform.strip().lower().replace(".", "").replace("-", "")
        if key == "dev":
            key = "devto"
        if key == "custom":
            key = "webhook"
        if key not in PUBLISHERS:
            raise PublisherError(f"Unsupported publishing platform: {platform}")
        if key not in normalized:
            normalized.append(key)
    return normalized or ["devto"]


async def publish_to_platforms(
    title: str,
    content: str,
    *,
    platforms: list[str] | None = None,
    published: bool = True,
    tags: list[str] | None = None,
    credentials: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    selected_platforms = normalize_platforms(platforms)
    clean_tags = [
        tag.strip().lower().replace(" ", "-")
        for tag in (tags or DEFAULT_TAGS)
        if tag and tag.strip()
    ][:4] or DEFAULT_TAGS

    results: list[PublishResult] = []
    for platform in selected_platforms:
        try:
            publisher = PUBLISHERS[platform]
            publish_call = publisher.publish(
                title,
                content,
                tags=clean_tags,
                published=published,
                credentials=credentials,
            )
            # HashnodePublisher.publish is async; await it if it's a coroutine
            if asyncio.iscoroutine(publish_call):
                result = await publish_call
            else:
                result = publish_call
            results.append(result)
        except PublisherError as exc:
            results.append(
                PublishResult(
                    platform=platform,
                    status="error",
                    message=str(exc),
                )
            )

    return [result.as_dict() for result in results]


def post_to_platform(title: str, content: str) -> dict[str, Any]:
    """Backward-compatible Dev.to-only wrapper used by older integrations."""
    result = DevToPublisher().publish(
        title,
        content,
        tags=DEFAULT_TAGS,
        published=True,
    )
    if result.status != "success":
        raise Exception(result.message or "Dev.to publishing failed.")
    return result.response or result.as_dict()
