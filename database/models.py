"""
Database models for Toymix Bot
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Category(Base):
    """
    Category model for organizing toys
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship with toys
    toys = relationship("Toy", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Toy(Base):
    """
    Toy model representing a single toy item in the catalog
    """
    __tablename__ = "toys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    price = Column(String(50), nullable=False)  # Store as string to support currency symbols
    description = Column(Text, nullable=False)
    media_type = Column(String(10), nullable=True)  # 'image' or 'video' (deprecated, kept for backward compatibility)
    media_file_id = Column(String(255), nullable=True)  # Telegram file_id (deprecated, kept for backward compatibility)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship with category
    category = relationship("Category", back_populates="toys")
    # Relationship with media
    media_items = relationship("ToyMedia", back_populates="toy", order_by="ToyMedia.sort_order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Toy(id={self.id}, title='{self.title}', price='{self.price}', is_active={self.is_active})>"

    def to_dict(self):
        """Convert toy to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "media_type": self.media_type,
            "media_file_id": self.media_file_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ToyMedia(Base):
    """
    Multiple media files (images/videos) for a toy
    """
    __tablename__ = "toy_media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    toy_id = Column(Integer, ForeignKey("toys.id"), nullable=False, index=True)
    file_id = Column(String(255), nullable=False)
    media_type = Column(String(10), nullable=False)  # "photo" or "video"
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship with toy
    toy = relationship("Toy", back_populates="media_items")

    def __repr__(self):
        return f"<ToyMedia(id={self.id}, toy_id={self.toy_id}, media_type='{self.media_type}', sort_order={self.sort_order})>"

    def to_dict(self):
        """Convert media to dictionary"""
        return {
            "id": self.id,
            "toy_id": self.toy_id,
            "file_id": self.file_id,
            "media_type": self.media_type,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DailyAd(Base):
    """
    Track which toys were posted on which day to prevent duplicates
    """
    __tablename__ = "daily_ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    toy_id = Column(Integer, nullable=False)
    posted_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    posted_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DailyAd(toy_id={self.toy_id}, posted_date='{self.posted_date}')>"


class DailyAdsLog(Base):
    """
    Detailed log of daily advertisements with category information
    """
    __tablename__ = "daily_ads_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    toy_id = Column(Integer, ForeignKey("toys.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    posted_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    posted_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DailyAdsLog(toy_id={self.toy_id}, category_id={self.category_id}, posted_date='{self.posted_date}')>"


class OrderContact(Base):
    """
    Order contact information (phone numbers or usernames)
    """
    __tablename__ = "order_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_value = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<OrderContact(id={self.id}, contact_value='{self.contact_value}', is_active={self.is_active})>"

    def to_dict(self):
        """Convert contact to dictionary"""
        return {
            "id": self.id,
            "contact_value": self.contact_value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalesLog(Base):
    """
    Sales tracking log - tracks user interest when they click Buyurtma berish
    """
    __tablename__ = "sales_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    toy_id = Column(Integer, ForeignKey("toys.id"), nullable=False, index=True)
    toy_name = Column(String(255), nullable=False)  # Denormalized for fast analytics
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    category_name = Column(String(100), nullable=True)  # Denormalized for fast analytics
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<SalesLog(id={self.id}, user_id={self.user_id}, toy_id={self.toy_id}, created_at='{self.created_at}')>"

    def to_dict(self):
        """Convert sales log to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "toy_id": self.toy_id,
            "toy_name": self.toy_name,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BestsellerCategory(Base):
    """
    Bestseller categories - TOP-5 categories by period
    """
    __tablename__ = "bestseller_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    category_name = Column(String(100), nullable=False)  # Denormalized
    source = Column(String(10), nullable=False)  # "auto" or "manual"
    period = Column(String(10), nullable=False)  # "weekly", "monthly", "yearly"
    rank = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        return f"<BestsellerCategory(id={self.id}, category_id={self.category_id}, rank={self.rank}, period='{self.period}', source='{self.source}')>"

    def to_dict(self):
        """Convert bestseller to dictionary"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "source": self.source,
            "period": self.period,
            "rank": self.rank,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StoreLocation(Base):
    """
    Store location information with map coordinates
    """
    __tablename__ = "store_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address_text = Column(Text, nullable=False)
    latitude = Column(String(50), nullable=False)  # Store as string for precision
    longitude = Column(String(50), nullable=False)  # Store as string for precision
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<StoreLocation(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def to_dict(self):
        """Convert store location to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "address_text": self.address_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CartItem(Base):
    """
    Shopping cart items for users
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    toy_id = Column(Integer, ForeignKey("toys.id"), nullable=False, index=True)
    toy_name = Column(String(255), nullable=False)  # Denormalized
    price = Column(String(50), nullable=False)  # Denormalized
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id={self.user_id}, toy_id={self.toy_id}, quantity={self.quantity})>"

    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "toy_id": self.toy_id,
            "toy_name": self.toy_name,
            "price": self.price,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Favorite(Base):
    """
    User favorites (saved toys)
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    toy_id = Column(Integer, ForeignKey("toys.id"), nullable=False, index=True)
    toy_name = Column(String(255), nullable=False)  # Denormalized
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, toy_id={self.toy_id})>"

    def to_dict(self):
        """Convert favorite to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "toy_id": self.toy_id,
            "toy_name": self.toy_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
