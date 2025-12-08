"""
SQLAlchemy ORM Models for PostgreSQL Database.

This module defines all database tables using SQLAlchemy ORM models with proper:
- Primary keys and foreign key relationships
- Indexes for performance optimization
- JSON columns for complex data types
- Timestamps with automatic updates
- Nullable/non-nullable constraints

Tables:
    - projects: Real estate project listings
    - leads: Customer leads and preferences
    - bookings: Property bookings linking leads to projects
    - history: Conversation/chat history tracking
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# Create base class for declarative models
Base = declarative_base()


##?==============================================================================================================================
##* Projects Table - Real Estate Project Listings
##?==============================================================================================================================

class Project(Base):
    """
    Real estate project listings with property details.
    
    Represents property projects including identification, location, pricing, 
    features, and descriptive metadata.
    """
    __tablename__ = "projects"
    
    # Primary Key
    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Project Details
    project_name        = Column(String(255), nullable=True, index=True)
    no_of_bedrooms      = Column(Integer, nullable=True, index=True)
    completion_status   = Column(String(50), nullable=True)
    bathrooms           = Column(Integer, nullable=True)
    unit_type           = Column(String(100), nullable=True, index=True)
    developer_name      = Column(String(255), nullable=True)
    
    # Pricing and Area
    price_usd           = Column(Float, nullable=True, index=True)
    area_sq_mtrs        = Column(Float, nullable=True)
    property_type       = Column(String(100), nullable=True)
    
    # Location
    city                = Column(String(100), nullable=True, index=True)
    country             = Column(String(100), nullable=True)
    
    # Dates and Descriptions
    completion_date     = Column(String(50), nullable=True)
    features            = Column(JSON, nullable=True)  # List[str] stored as JSON
    facilities          = Column(JSON, nullable=True)  # List[str] stored as JSON
    project_description = Column(Text, nullable=True)
    
    # Timestamps
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    bookings            = relationship("Booking", back_populates="project", cascade="all, delete-orphan")
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_projects_city_bedrooms', 'city', 'no_of_bedrooms'),
        Index('idx_projects_city_bedrooms_price', 'city', 'no_of_bedrooms', 'price_usd'),
        Index('idx_projects_price_range', 'price_usd'),
        Index('idx_projects_property_type_city', 'property_type', 'city'),
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', city='{self.city}')>"


##?==============================================================================================================================
##* Leads Table - Customer Leads and Preferences
##?==============================================================================================================================

class Lead(Base):
    """
    Customer leads with contact information and property preferences.
    
    Represents potential customers interested in buying or renting properties.
    """
    __tablename__ = "leads"
    
    # Primary Key
    id                       = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Contact Information
    first_name               = Column(String(100), nullable=True)
    last_name                = Column(String(100), nullable=True)
    email                    = Column(String(255), nullable=True, unique=True, index=True)
    
    # Preferences
    preferred_city           = Column(String(100), nullable=True, index=True)
    preferred_budget_usd     = Column(Integer, nullable=True, index=True)
    preferred_property_type  = Column(String(100), nullable=True)
    preferred_bedrooms       = Column(Integer, nullable=True)
    metadata_json            = Column(JSON, nullable=True)  # Dict[str, Any] stored as JSON
    
    # Timestamps
    created_at               = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at               = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    bookings                 = relationship("Booking", back_populates="lead", cascade="all, delete-orphan")
    history                  = relationship("History", back_populates="lead", cascade="all, delete-orphan")
    
    
    def __repr__(self):
        return f"<Lead(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"


##?==============================================================================================================================
##* Bookings Table - Property Bookings
##?==============================================================================================================================

class Booking(Base):
    """
    Property booking records linking leads to projects.
    
    Represents the relationship between a customer lead and a project, 
    capturing the booking event and its status.
    """
    __tablename__ = "bookings"
    
    # Primary Key
    id             = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign Keys
    lead_id        = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=True, index=True)
    project_id     = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Booking Details
    booking_date   = Column(String(50), nullable=True, index=True)
    booking_status = Column(String(50), nullable=True, index=True)
    
    # Timestamps
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead           = relationship("Lead", back_populates="bookings")
    project        = relationship("Project", back_populates="bookings")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_bookings_lead_status', 'lead_id', 'booking_status'),
        Index('idx_bookings_project_status', 'project_id', 'booking_status'),
        Index('idx_bookings_date_status', 'booking_date', 'booking_status'),
    )
    
    def __repr__(self):
        return f"<Booking(id={self.id}, lead_id={self.lead_id}, project_id={self.project_id}, status='{self.booking_status}')>"


##?==============================================================================================================================
##* History Table - Conversation/Chat History
##?==============================================================================================================================

class History(Base):
    """
    Chat or conversation history entries.
    
    Represents a conversation session, optionally linked to a customer lead.
    The conversation_id field is required (NOT NULL).
    """
    __tablename__ = "history"
    
    # Primary Key
    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Conversation Identifier (Required)
    conversation_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Foreign Key (Optional)
    lead_id         = Column(Integer, ForeignKey('leads.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead            = relationship("Lead", back_populates="history")
    
    # Additional indexes
    __table_args__ = (
        Index('idx_history_lead_conversation', 'lead_id', 'conversation_id'),
        Index('idx_history_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<History(id={self.id}, conversation_id='{self.conversation_id}', lead_id={self.lead_id})>"
