"""AI Services - Mentor Matching"""

import logging

logger = logging.getLogger(__name__)


class MentorMatchingEngine:
    """AI-powered mentor matching"""
    
    @staticmethod
    async def recommend_mentors(
        student_skills: list,
        student_goals: list,
        student_interests: list,
        db
    ) -> list:
        """Recommend mentors based on student profile"""
        
        from core.config.settings import settings
        from openai import AsyncOpenAI
        from sqlalchemy import select
        from modules.users.models import User
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get all mentors
        stmt = select(User).where(User.is_mentor == True).limit(50)
        result = await db.execute(stmt)
        mentors = result.scalars().all()
        
        # Create matching prompt
        mentor_profiles = "\n".join([
            f"- {m.first_name} {m.last_name}: {', '.join(m.mentor_expertise or [])}"
            for m in mentors
        ])
        
        prompt = f"""Based on student profile, recommend best mentors:
Student Skills: {', '.join(student_skills)}
Student Goals: {', '.join(student_goals)}
Student Interests: {', '.join(student_interests)}

Available Mentors:
{mentor_profiles}

Return top 5 recommended mentor names."""
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at matching students with mentors."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        logger.info("Mentor recommendations generated")
        return mentors[:5]  # Return top 5
