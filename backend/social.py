import os
from dataclasses import dataclass
from typing import Any

import requests
import tweepy


@dataclass(frozen=True)
class SocialResult:
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


class SocialSharerError(Exception):
    """Raised when a selected social platform cannot be shared to."""


class BaseSocialSharer:
    platform = "base"

    def share(
        self,
        title: str,
        post_url: str,
        tags: list[str],
        credentials: dict[str, Any] | None = None,
    ) -> SocialResult:
        raise NotImplementedError


class TwitterSharer(BaseSocialSharer):
    platform = "twitter"

    def share(
        self,
        title: str,
        post_url: str,
        tags: list[str],
        credentials: dict[str, Any] | None = None,
    ) -> SocialResult:
        credentials = credentials or {}
        api_key = credentials.get("twitter_api_key") or os.getenv("TWITTER_API_KEY")
        api_secret = credentials.get("twitter_api_secret") or os.getenv("TWITTER_API_SECRET")
        access_token = credentials.get("twitter_access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
        access_secret = credentials.get("twitter_access_secret") or os.getenv("TWITTER_ACCESS_SECRET")

        if not all([api_key, api_secret, access_token, access_secret]):
            raise SocialSharerError("Twitter API credentials missing in environment.")

        hashtags = " ".join([f"#{t.replace(' ', '')}" for t in tags[:3]])
        tweet_text = f"Just published a new LeetCode solution! 🚀\n\n{title}\n\nCheck it out here: {post_url}\n\n{hashtags}"

        try:
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret,
            )
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data.get("id")
            tweet_url = (
                f"https://twitter.com/user/status/{tweet_id}" if tweet_id else None
            )

            return SocialResult(
                platform=self.platform,
                status="success",
                url=tweet_url,
                response=response.data,
            )
        except Exception as e:
            raise SocialSharerError(f"Twitter sharing failed: {str(e)}")


class LinkedInSharer(BaseSocialSharer):
    platform = "linkedin"

    def share(
        self,
        title: str,
        post_url: str,
        tags: list[str],
        credentials: dict[str, Any] | None = None,
    ) -> SocialResult:
        credentials = credentials or {}
        access_token = credentials.get("linkedin_access_token") or os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = credentials.get("linkedin_person_urn") or os.getenv("LINKEDIN_PERSON_URN") # e.g., urn:li:person:123456789

        if not access_token or not person_urn:
            raise SocialSharerError(
                "LinkedIn API credentials (token or URN) missing in environment."
            )

        hashtags = " ".join([f"#{t.replace(' ', '')}" for t in tags[:3]])
        post_text = (
            f"I just published a new LeetCode solution!\n\n{title}\n\n{hashtags}"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": post_url,
                            "title": {"text": title},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        try:
            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=payload,
                timeout=20,
            )
            if response.status_code in (200, 201):
                data = response.json()
                post_id = data.get("id")
                linkedin_url = (
                    f"https://www.linkedin.com/feed/update/{post_id}"
                    if post_id
                    else None
                )
                return SocialResult(
                    platform=self.platform,
                    status="success",
                    url=linkedin_url,
                    response=data,
                )
            else:
                raise SocialSharerError(
                    f"LinkedIn API Error {response.status_code}: {response.text}"
                )
        except requests.RequestException as e:
            raise SocialSharerError(f"LinkedIn network error: {str(e)}")


SHARERS: dict[str, BaseSocialSharer] = {
    "twitter": TwitterSharer(),
    "linkedin": LinkedInSharer(),
}

def share_to_platforms(
    title: str,
    post_url: str,
    tags: list[str] | None = None,
    credentials: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    clean_tags = [
        tag.strip().lower().replace(" ", "-")
        for tag in (tags or ["leetcode", "dsa"])
        if tag and tag.strip()
    ][:4]

    results: list[SocialResult] = []

    for platform_name, sharer in SHARERS.items():
        try:
            results.append(
                sharer.share(title, post_url, clean_tags)
                if credentials is None
                else sharer.share(title, post_url, clean_tags, credentials)
            )
        except SocialSharerError as exc:
            results.append(
                SocialResult(platform=platform_name, status="error", message=str(exc))
            )

    return [r.as_dict() for r in results]
