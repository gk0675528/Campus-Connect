"""AI Services - Resume Analyzer"""

import logging

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """AI Resume Analyzer Service"""
    
    @staticmethod
    async def analyze_resume(resume_text: str) -> dict:
        """Analyze resume using OpenAI"""
        
        from core.config.settings import settings
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""Analyze this resume and provide:
1. Key skills identified
2. Experience level assessment
3. Suggested improvements
4. Skill gaps for target roles

Resume:
{resume_text}

Provide JSON formatted response."""
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert career advisor analyzing resumes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        logger.info("Resume analyzed")
        return {"analysis": response.choices[0].message.content}
    
    @staticmethod
    async def get_skill_gap_analysis(current_skills: list, target_role: str) -> dict:
        """Analyze skill gaps for target role"""
        
        from core.config.settings import settings
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""For a {target_role} position, analyze the skill gaps.
Current skills: {', '.join(current_skills)}

Provide:
1. Skills to develop
2. Learning resources
3. Timeline for development

Respond in JSON format."""
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert career advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        logger.info("Skill gap analysis completed")
        return {"analysis": response.choices[0].message.content}
