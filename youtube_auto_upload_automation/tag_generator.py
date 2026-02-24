"""Trending tag generation via Groq web search."""

import logging
from typing import List

from groq import Groq

logger = logging.getLogger(__name__)


class TagGenerator:
    """Generate trending YouTube/Instagram tags using Groq with web search."""

    def __init__(self, api_key: str, model: str = "compound-beta"):
        """Initialize the tag generator.

        Args:
            api_key: Groq API key
            model: Groq model to use. 'compound-beta' has built-in web search.
        """
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_tags(self, title: str, description: str) -> List[str]:
        """Search for trending YouTube & Instagram tags for a news video.

        Uses Groq's compound-beta model which performs live web searches
        to find what is currently trending on YouTube and Instagram for
        the given topic.

        Args:
            title: Video title
            description: Video description

        Returns:
            List of trending tag strings (without # symbols)
        """
        prompt = (
            "You are a YouTube SEO expert for 'Pradesh 24 Gujarati', a Gujarati-language news channel. "
            "Search YouTube and Instagram right now to find the most trending hashtags and search keywords "
            "for the following news video.\n\n"
            f"Video Title: {title}\n"
            f"Video Description: {description}\n\n"
            "Requirements:\n"
            "- Find tags that are actually trending TODAY on YouTube and Instagram\n"
            "- This is a legitimate NEWS channel — the content may cover accidents, crime, or other "
            "sensitive news events. Tags must be JOURNALISTIC and NEUTRAL in tone (e.g. 'road accident news', "
            "'crime report', 'police investigation') — never sensational, graphic, or violent in wording\n"
            "- Absolutely AVOID any tags that could trigger YouTube content flags, such as words implying "
            "gore, shock, explicit violence, death glorification, or adult content\n"
            "- Include a mix of Gujarati-language tags (transliterated in Roman script or Gujarati script) "
            "and English tags, since the audience searches in both languages\n"
            "- Always include channel-relevant tags: Pradesh 24, Pradesh24, Gujarati news, Gujarat news, "
            "ગુજરાત સમાચાર, Gujarati samachar\n"
            "- Include a mix of broad news tags and topic-specific tags\n"
            "- Do NOT include # symbols\n"
            "- Return ONLY a single comma-separated list of 20-30 tags\n"
            "- No explanations, no numbering, no extra text — just the tags\n\n"
            "Example output format:\n"
            "Pradesh 24, Pradesh24, Gujarati news, Gujarat news, Gujarati samachar, breaking news, "
            "latest news, today headlines, Gujarat samachar, live news, news update, top stories, "
            "current events, news today, trending news"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.choices[0].message.content.strip()
            logger.debug(f"Groq raw tag response: {raw}")

            # Parse comma-separated list; strip # and extra whitespace
            tags = [
                t.strip().lstrip("#").strip()
                for t in raw.split(",")
                if t.strip()
            ]

            # Remove any lines that look like explanatory text (contain spaces > 4 words)
            tags = [t for t in tags if len(t.split()) <= 5]

            # Deduplicate preserving order
            seen = set()
            unique_tags = []
            for tag in tags:
                key = tag.lower()
                if key not in seen:
                    seen.add(key)
                    unique_tags.append(tag)

            logger.info(
                f"Generated {len(unique_tags)} tags for '{title}': {unique_tags}"
            )
            return unique_tags[:30]

        except Exception as e:
            logger.error(f"Tag generation failed for '{title}': {e}")
            return []
