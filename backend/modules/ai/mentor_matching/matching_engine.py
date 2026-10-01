"""AI Services - Mentor Matching"""

import json
import logging
from typing import Any

from sqlalchemy import select

from core.config.settings import settings
from modules.users.models import User

logger = logging.getLogger(__name__)


class MentorMatchingEngine:
    """AI-powered mentor matching engine."""

    @staticmethod
    async def recommend_mentors(
        student_skills: list[str],
        student_goals: list[str],
        student_interests: list[str],
        db,
    ) -> list[User]:
        """
        Recommend mentors using AI-generated mentor ranking.

        The AI returns mentor IDs in ranked order. The final result is
        resolved against the database so that only real mentor records
        are returned.
        """

        # ---------------------------------------------------------
        # 1. Fetch available mentors
        # ---------------------------------------------------------
        stmt = (
            select(User)
            .where(
                User.is_mentor.is_(True),
                User.is_active.is_(True),
            )
            .limit(50)
        )

        result = await db.execute(stmt)
        mentors = list(result.scalars().all())

        if not mentors:
            logger.info("No active mentors available for matching.")
            return []

        # ---------------------------------------------------------
        # 2. Build compact mentor profiles
        # ---------------------------------------------------------
        mentor_profiles = []

        for mentor in mentors:
            mentor_profiles.append(
                {
                    "id": str(mentor.id),
                    "name": (
                        f"{mentor.first_name or ''} "
                        f"{mentor.last_name or ''}"
                    ).strip(),
                    "expertise": mentor.mentor_expertise or [],
                }
            )

        # ---------------------------------------------------------
        # 3. Build AI prompt
        # ---------------------------------------------------------
        prompt = f"""
You are a professional mentor-matching engine.

Match the student with the most relevant mentors.

STUDENT:
Skills: {json.dumps(student_skills)}
Goals: {json.dumps(student_goals)}
Interests: {json.dumps(student_interests)}

AVAILABLE MENTORS:
{json.dumps(mentor_profiles, ensure_ascii=False)}

Return ONLY valid JSON in this exact format:

{{
  "mentor_ids": ["mentor_id_1", "mentor_id_2", "mentor_id_3"]
}}

Rules:
- Return maximum 5 mentor IDs.
- Only use IDs from AVAILABLE MENTORS.
- Rank mentors from most relevant to least relevant.
- Do not invent IDs.
- Do not include explanations.
"""

        # ---------------------------------------------------------
        # 4. Call OpenAI
        # ---------------------------------------------------------
        try:
            from openai import AsyncOpenAI

            if not settings.OPENAI_API_KEY:
                logger.warning(
                    "OPENAI_API_KEY is not configured. "
                    "Using deterministic fallback matching."
                )
                return MentorMatchingEngine._fallback_match(mentors)

            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise mentor matching engine. "
                            "Always return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError(
                    "AI returned an empty mentor matching response."
                )

            parsed: dict[str, Any] = json.loads(content)

            recommended_ids = parsed.get("mentor_ids", [])

            if not isinstance(recommended_ids, list):
                raise ValueError(
                    "AI response mentor_ids must be a list."
                )

            # -----------------------------------------------------
            # 5. Validate AI output against actual DB mentors
            # -----------------------------------------------------
            mentor_map = {
                str(mentor.id): mentor
                for mentor in mentors
            }

            ranked_mentors = []

            for mentor_id in recommended_ids:
                mentor_id = str(mentor_id)

                mentor = mentor_map.get(mentor_id)

                if mentor and mentor not in ranked_mentors:
                    ranked_mentors.append(mentor)

                if len(ranked_mentors) >= 5:
                    break

            # -----------------------------------------------------
            # 6. AI returned nothing useful -> fallback
            # -----------------------------------------------------
            if not ranked_mentors:
                logger.warning(
                    "AI mentor matching returned no valid mentor IDs. "
                    "Using fallback matching."
                )
                return MentorMatchingEngine._fallback_match(mentors)

            logger.info(
                "AI mentor matching generated %d recommendations.",
                len(ranked_mentors),
            )

            return ranked_mentors

        except Exception:
            logger.exception(
                "AI mentor matching failed. "
                "Using deterministic fallback matching."
            )

            return MentorMatchingEngine._fallback_match(mentors)

    # =============================================================
    # Deterministic fallback
    # =============================================================

    @staticmethod
    def _fallback_match(
        mentors: list[User],
    ) -> list[User]:
        """
        Safe fallback when AI is unavailable.

        Currently keeps the existing mentor ordering instead of
        returning an empty result.
        """

        return mentors[:5]