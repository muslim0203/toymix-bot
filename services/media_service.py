"""
Service for managing toy media (multiple images/videos)
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from database.models import ToyMedia, Toy


class MediaService:
    """Service for toy media operations"""
    
    @staticmethod
    def get_toy_media(db: Session, toy_id: int) -> List[ToyMedia]:
        """Get all media for a toy, ordered by sort_order"""
        return db.query(ToyMedia).filter(
            ToyMedia.toy_id == toy_id
        ).order_by(ToyMedia.sort_order).all()
    
    @staticmethod
    def add_media(
        db: Session,
        toy_id: int,
        file_id: str,
        media_type: str,
        sort_order: int = 0
    ) -> ToyMedia:
        """
        Add media to a toy
        
        Args:
            db: Database session
            toy_id: Toy ID
            file_id: Telegram file_id
            media_type: "photo" or "video"
            sort_order: Order position
            
        Returns:
            Created ToyMedia object
        """
        media = ToyMedia(
            toy_id=toy_id,
            file_id=file_id,
            media_type=media_type,
            sort_order=sort_order
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        return media
    
    @staticmethod
    def add_multiple_media(
        db: Session,
        toy_id: int,
        media_list: List[tuple]  # List of (file_id, media_type) tuples
    ) -> List[ToyMedia]:
        """
        Add multiple media items to a toy
        
        Args:
            db: Database session
            toy_id: Toy ID
            media_list: List of (file_id, media_type) tuples
            
        Returns:
            List of created ToyMedia objects
        """
        media_items = []
        for idx, (file_id, media_type) in enumerate(media_list):
            media = ToyMedia(
                toy_id=toy_id,
                file_id=file_id,
                media_type=media_type,
                sort_order=idx
            )
            db.add(media)
            media_items.append(media)
        
        db.commit()
        for media in media_items:
            db.refresh(media)
        
        return media_items
    
    @staticmethod
    def delete_toy_media(db: Session, toy_id: int) -> int:
        """
        Delete all media for a toy
        
        Args:
            db: Database session
            toy_id: Toy ID
            
        Returns:
            Number of deleted media items
        """
        count = db.query(ToyMedia).filter(ToyMedia.toy_id == toy_id).delete()
        db.commit()
        return count
    
    @staticmethod
    def get_media_for_media_group(toy_media: List[ToyMedia], caption: str = None, parse_mode: str = None) -> List:
        """
        Convert ToyMedia objects to InputMedia for send_media_group
        
        Args:
            toy_media: List of ToyMedia objects
            caption: Caption text (only first media will have caption)
            parse_mode: Parse mode for caption (HTML, Markdown, etc.)
            
        Returns:
            List of InputMediaPhoto/InputMediaVideo objects
        """
        from aiogram.types import InputMediaPhoto, InputMediaVideo
        
        media_group = []
        for idx, media in enumerate(toy_media):
            # Only first media can have caption in media group
            if idx == 0 and caption:
                if media.media_type == "photo":
                    media_group.append(InputMediaPhoto(
                        media=media.file_id,
                        caption=caption,
                        parse_mode=parse_mode
                    ))
                elif media.media_type == "video":
                    media_group.append(InputMediaVideo(
                        media=media.file_id,
                        caption=caption,
                        parse_mode=parse_mode
                    ))
            else:
                if media.media_type == "photo":
                    media_group.append(InputMediaPhoto(media=media.file_id))
                elif media.media_type == "video":
                    media_group.append(InputMediaVideo(media=media.file_id))
        
        return media_group
