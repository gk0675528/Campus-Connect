"""Application Constants"""

# User Roles
class UserRole:
    STUDENT = "student"
    PEER_MENTOR = "peer_mentor"
    ALUMNI = "alumni"
    PROFESSOR = "professor"
    INDUSTRY_EXPERT = "industry_expert"
    ADMIN = "admin"
    
    CHOICES = [STUDENT, PEER_MENTOR, ALUMNI, PROFESSOR, INDUSTRY_EXPERT, ADMIN]


# Mentor Verification Status
class VerificationStatus:
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    
    CHOICES = [PENDING, VERIFIED, REJECTED]


# Session Status
class SessionStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

    CHOICES = [PENDING, CONFIRMED, COMPLETED, CANCELLED, REJECTED]


# Payment Status
class PaymentStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    
    CHOICES = [PENDING, COMPLETED, FAILED, REFUNDED]


# Community Types
class CommunityType:
    ACADEMIC = "academic"
    CAREER = "career"
    HOBBY = "hobby"
    SKILL = "skill"
    
    CHOICES = [ACADEMIC, CAREER, HOBBY, SKILL]


# Post Status
class PostStatus:
    PUBLISHED = "published"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DELETED = "deleted"
    
    CHOICES = [PUBLISHED, DRAFT, ARCHIVED, DELETED]


# Mentorship Cost Rules
MENTORSHIP_COST_RULES = {
    "same_college_professor": 0.00,
    "same_college_senior": 0.00,
    "same_college_alumni": 0.55,  # 45% discount means pay 55%
    "external_mentor": 1.00,  # 100% = standard pricing
}

# Default values
DEFAULT_SESSION_DURATION_MINUTES = 60
DEFAULT_PLATFORM_COMMISSION = 0.15

# Moderation keywords
BANNED_CONTACT_PATTERNS = [
    r'\+\d{10,}',  # Phone numbers
    r'\d+@[\w\.-]+\.\w+',  # Email addresses (partially masked in rules)
    r'(?:whatsapp|telegram|discord|wa\.me)',  # Contact app mentions
]
