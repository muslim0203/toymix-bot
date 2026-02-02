"""
Service for managing store locations
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from database.models import StoreLocation


class StoreLocationService:
    """Service for store location operations"""
    
    @staticmethod
    def get_active_locations(db: Session) -> List[StoreLocation]:
        """Get all active store locations"""
        return db.query(StoreLocation).filter(
            StoreLocation.is_active == True
        ).order_by(StoreLocation.created_at).all()
    
    @staticmethod
    def get_all_locations(db: Session) -> List[StoreLocation]:
        """Get all store locations (including inactive)"""
        return db.query(StoreLocation).order_by(StoreLocation.created_at).all()
    
    @staticmethod
    def get_location_by_id(db: Session, location_id: int) -> Optional[StoreLocation]:
        """Get location by ID"""
        return db.query(StoreLocation).filter(StoreLocation.id == location_id).first()
    
    @staticmethod
    def get_location_by_name(db: Session, name: str) -> Optional[StoreLocation]:
        """Get location by name"""
        return db.query(StoreLocation).filter(StoreLocation.name == name).first()
    
    @staticmethod
    def create_location(
        db: Session,
        name: str,
        address_text: str,
        latitude: str,
        longitude: str
    ) -> StoreLocation:
        """Create a new store location"""
        location = StoreLocation(
            name=name.strip(),
            address_text=address_text.strip(),
            latitude=latitude.strip(),
            longitude=longitude.strip(),
            is_active=True
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location
    
    @staticmethod
    def deactivate_location(db: Session, location_id: int) -> Optional[StoreLocation]:
        """Deactivate a location (soft delete)"""
        location = StoreLocationService.get_location_by_id(db, location_id)
        if not location:
            return None
        
        location.is_active = False
        db.commit()
        db.refresh(location)
        return location
