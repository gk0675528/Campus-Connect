"""Database Models"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Table, Uuid, JSON
from sqlalchemy.orm import relationship
from core.config.database import Base
from core.config.constants import *
from datetime import datetime
import uuid


# Association tables
mentor_connections = Table(
    'mentor_connections',
    Base.metadata,
    Column('mentor_id', Uuid(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('student_id', Uuid(as_uuid=True), ForeignKey('users.id'), primary_key=True),
)

community_members = Table(
    'community_members',
    Base.metadata,
    Column('community_id', Uuid(as_uuid=True), ForeignKey('communities.id'), primary_key=True),
    Column('user_id', Uuid(as_uuid=True), ForeignKey('users.id'), primary_key=True),
)

post_upvotes = Table(
    'post_upvotes',
    Base.metadata,
    Column('post_id', Uuid(as_uuid=True), ForeignKey('posts.id'), primary_key=True),
    Column('user_id', Uuid(as_uuid=True), ForeignKey('users.id'), primary_key=True),
)


class User(Base):
    """User Model"""
    __tablename__ = "users"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    profile_photo = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String(50), nullable=False, default=UserRole.STUDENT)
    
    # Profile Info
    college = Column(String(255), nullable=True)
    skills = Column(JSON, default=list, nullable=True)
    interests = Column(JSON, default=list, nullable=True)
    experience_years = Column(Integer, nullable=True)
    
    # Mentor Fields
    is_mentor = Column(Boolean, default=False)
    mentor_bio = Column(Text, nullable=True)
    mentor_hourly_rate = Column(Float, nullable=True)
    mentor_expertise = Column(JSON, default=list, nullable=True)
    mentor_verified = Column(Boolean, default=False)
    mentor_rating = Column(Float, default=0.0)
    mentor_total_sessions = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    
    # OAuth
    google_id = Column(String(255), unique=True, nullable=True)
    linkedin_id = Column(String(255), unique=True, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="mentor", foreign_keys="Session.mentor_id")
    bookings = relationship("Session", back_populates="student", foreign_keys="Session.student_id")
    communities = relationship("Community", secondary=community_members, back_populates="members")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    # Compatibility properties for response schemas
    @property
    def expertise(self):
        return self.mentor_expertise or self.skills or []

    @property
    def hourly_rate(self):
        return self.mentor_hourly_rate or 0.0

    @property
    def rating(self):
        return self.mentor_rating or 0.0

    @property
    def total_sessions(self):
        return self.mentor_total_sessions or 0


class Session(Base):
    """Mentorship Session Model"""
    __tablename__ = "sessions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mentor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=60)
    
    # Pricing
    mentor_rate = Column(Float, nullable=False, default=0.0)
    platform_commission_rate = Column(Float, default=0.15)
    student_pays = Column(Float, nullable=False, default=0.0)
    mentor_receives = Column(Float, nullable=False, default=0.0)
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default=SessionStatus.PENDING)
    meeting_link = Column(String(500), nullable=True)
    
    # Feedback
    student_rating = Column(Float, nullable=True)
    student_review = Column(Text, nullable=True)
    mentor_feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="sessions")
    student = relationship("User", foreign_keys=[student_id], back_populates="bookings")
    payment = relationship("Payment", uselist=False, back_populates="session")


class Community(Base):
    """Community Model"""
    __tablename__ = "communities"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    community_type = Column(String(50), default=CommunityType.ACADEMIC)
    
    creator_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    thumbnail = Column(String(500), nullable=True)
    members_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("User", secondary=community_members, back_populates="communities")
    posts = relationship("Post", back_populates="community")


class Post(Base):
    """Community Post Model"""
    __tablename__ = "posts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id = Column(Uuid(as_uuid=True), ForeignKey("communities.id"), nullable=False)
    author_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(50), default=PostStatus.PUBLISHED)
    
    upvote_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    community = relationship("Community", back_populates="posts")
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    upvoted_by = relationship("User", secondary=post_upvotes)


class Comment(Base):
    """Post Comment Model"""
    __tablename__ = "comments"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(Uuid(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    author_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    upvote_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Message(Base):
    """Direct Message Model"""
    __tablename__ = "messages"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")


class Notification(Base):
    """Notification Model"""
    __tablename__ = "notifications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    related_id = Column(Uuid(as_uuid=True), nullable=True)  # Session, Post, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Payment Model"""
    __tablename__ = "payments"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    platform_commission = Column(Float, nullable=False)
    mentor_amount = Column(Float, nullable=False)
    
    payment_method = Column(String(50), nullable=False)  # stripe, razorpay
    transaction_id = Column(String(255), unique=True, nullable=True)
    
    status = Column(String(50), default=PaymentStatus.PENDING)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="payment")


class Wallet(Base):
    """User Wallet Model"""
    __tablename__ = "wallets"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VerificationRequest(Base):
    """Mentor Verification Request Model"""
    __tablename__ = "verification_requests"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(String(50), default=VerificationStatus.PENDING)
    documents = Column(JSON, default=list, nullable=True)  # URLs / document references
    rejection_reason = Column(Text, nullable=True)
    
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

