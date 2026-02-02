"""
Service for managing order contacts
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import OrderContact


class OrderContactService:
    """Service for order contact operations"""
    
    @staticmethod
    def get_active_contacts(db: Session) -> List[OrderContact]:
        """Get all active contacts"""
        return db.query(OrderContact).filter(
            OrderContact.is_active == True
        ).order_by(OrderContact.created_at).all()
    
    @staticmethod
    def get_all_contacts(db: Session) -> List[OrderContact]:
        """Get all contacts (including inactive)"""
        return db.query(OrderContact).order_by(OrderContact.created_at).all()
    
    @staticmethod
    def get_contact_by_id(db: Session, contact_id: int) -> Optional[OrderContact]:
        """Get contact by ID"""
        return db.query(OrderContact).filter(OrderContact.id == contact_id).first()
    
    @staticmethod
    def get_contact_by_value(db: Session, contact_value: str) -> Optional[OrderContact]:
        """Get contact by value"""
        return db.query(OrderContact).filter(OrderContact.contact_value == contact_value).first()
    
    @staticmethod
    def create_contact(db: Session, contact_value: str) -> OrderContact:
        """Create a new contact"""
        contact = OrderContact(
            contact_value=contact_value.strip(),
            is_active=True
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact
    
    @staticmethod
    def deactivate_contact(db: Session, contact_id: int) -> Optional[OrderContact]:
        """Deactivate a contact (soft delete)"""
        contact = OrderContactService.get_contact_by_id(db, contact_id)
        if not contact:
            return None
        
        contact.is_active = False
        contact.updated_at = datetime.now()
        db.commit()
        db.refresh(contact)
        return contact
    
    @staticmethod
    def format_contacts_for_display(contacts: List[OrderContact]) -> str:
        """
        Format contacts for display to users
        
        Args:
            contacts: List of OrderContact objects
            
        Returns:
            Formatted string
        """
        if not contacts:
            return "❌ Hozircha buyurtma uchun kontaktlar mavjud emas"
        
        text = "📞 Buyurtma berish uchun bog'laning:\n\n"
        
        for contact in contacts:
            contact_value = contact.contact_value
            if contact_value.startswith("@"):
                # Telegram username
                text += f"💬 {contact_value}\n"
            elif contact_value.startswith("+"):
                # Phone number
                text += f"☎️ {contact_value}\n"
            else:
                # Other format
                text += f"📱 {contact_value}\n"
        
        return text
