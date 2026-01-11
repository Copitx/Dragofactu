from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from dragofactu.models.entities import DiaryEntry
from dragofactu.models.database import SessionLocal
from dragofactu.services.auth.auth_service import require_permission
import json


class DiaryService:
    """Service for managing diary/agenda entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('diary.create')
    def create_entry(self, title: str, content: str, user_id: str,
                     entry_date: datetime = None, tags: List[str] = None,
                     related_document_id: str = None, related_payment_id: str = None,
                     is_pinned: bool = False) -> DiaryEntry:
        """
        Create a new diary entry
        
        Args:
            title: Entry title
            content: Entry content (rich text)
            user_id: ID of user creating the entry
            entry_date: Entry date (defaults to now)
            tags: List of tags for categorization
            related_document_id: Related document ID (optional)
            related_payment_id: Related payment ID (optional)
            is_pinned: Whether entry is pinned
            
        Returns:
            Created DiaryEntry
        """
        if not entry_date:
            entry_date = datetime.utcnow()
        
        # Convert tags to JSON string
        tags_json = json.dumps(tags) if tags else None
        
        entry = DiaryEntry(
            title=title,
            content=content,
            entry_date=entry_date,
            user_id=user_id,
            tags=tags_json,
            related_document_id=related_document_id,
            related_payment_id=related_payment_id,
            is_pinned=is_pinned
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    @require_permission('diary.read')
    def get_entry_by_id(self, entry_id: str) -> Optional[DiaryEntry]:
        """Get diary entry by ID"""
        return self.db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    
    @require_permission('diary.read')
    def get_entries_by_date_range(self, user_id: str, start_date: datetime,
                                 end_date: datetime, tags: List[str] = None) -> List[DiaryEntry]:
        """
        Get entries within date range
        
        Args:
            user_id: User ID (None for all users)
            start_date: Start date
            end_date: End date
            tags: Filter by tags (optional)
            
        Returns:
            List of DiaryEntry objects
        """
        query = self.db.query(DiaryEntry).filter(
            DiaryEntry.entry_date.between(start_date, end_date)
        )
        
        if user_id:
            query = query.filter(DiaryEntry.user_id == user_id)
        
        if tags:
            # Filter by tags - contains any of the specified tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(DiaryEntry.tags.ilike(f'%"{tag}"%'))
            query = query.filter(or_(*tag_conditions))
        
        return query.order_by(DiaryEntry.entry_date.desc()).all()
    
    @require_permission('diary.read')
    def search_entries(self, query: str, user_id: str = None,
                      tags: List[str] = None, limit: int = 50) -> List[DiaryEntry]:
        """
        Search diary entries
        
        Args:
            query: Search query (searches title and content)
            user_id: User ID (None for all users)
            tags: Filter by tags (optional)
            limit: Maximum number of results
            
        Returns:
            List of DiaryEntry objects
        """
        db_query = self.db.query(DiaryEntry)
        
        # Search in title and content
        if query:
            search_condition = or_(
                DiaryEntry.title.ilike(f"%{query}%"),
                DiaryEntry.content.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_condition)
        
        # Filter by user
        if user_id:
            db_query = db_query.filter(DiaryEntry.user_id == user_id)
        
        # Filter by tags
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(DiaryEntry.tags.ilike(f'%"{tag}"%'))
            db_query = db_query.filter(or_(*tag_conditions))
        
        return db_query.order_by(
            DiaryEntry.is_pinned.desc(),
            DiaryEntry.entry_date.desc()
        ).limit(limit).all()
    
    @require_permission('diary.read')
    def get_pinned_entries(self, user_id: str = None) -> List[DiaryEntry]:
        """Get all pinned entries"""
        query = self.db.query(DiaryEntry).filter(DiaryEntry.is_pinned == True)
        
        if user_id:
            query = query.filter(DiaryEntry.user_id == user_id)
        
        return query.order_by(DiaryEntry.entry_date.desc()).all()
    
    @require_permission('diary.read')
    def get_entries_for_month(self, year: int, month: int, user_id: str = None) -> List[DiaryEntry]:
        """Get all entries for a specific month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return self.get_entries_by_date_range(user_id, start_date, end_date)
    
    @require_permission('diary.update')
    def update_entry(self, entry_id: str, user_id: str, **kwargs) -> Optional[DiaryEntry]:
        """
        Update diary entry
        
        Args:
            entry_id: Entry ID
            user_id: User ID performing the update
            **kwargs: Fields to update
            
        Returns:
            Updated DiaryEntry or None
        """
        entry = self.db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
        if not entry:
            return None
        
        # Update allowed fields
        allowed_fields = ['title', 'content', 'entry_date', 'tags', 'is_pinned']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                # Special handling for tags
                if field == 'tags' and value is not None:
                    value = json.dumps(value) if isinstance(value, list) else value
                
                setattr(entry, field, value)
        
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    @require_permission('diary.delete')
    def delete_entry(self, entry_id: str) -> bool:
        """Delete diary entry"""
        entry = self.db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
        if not entry:
            return False
        
        self.db.delete(entry)
        self.db.commit()
        
        return True
    
    @require_permission('diary.read')
    def get_all_tags(self, user_id: str = None) -> List[str]:
        """Get all unique tags from diary entries"""
        query = self.db.query(DiaryEntry).filter(DiaryEntry.tags.isnot(None))
        
        if user_id:
            query = query.filter(DiaryEntry.user_id == user_id)
        
        entries = query.all()
        
        # Extract all tags from entries
        all_tags = set()
        for entry in entries:
            if entry.tags:
                try:
                    tags = json.loads(entry.tags)
                    if isinstance(tags, list):
                        all_tags.update(tags)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sorted(list(all_tags))
    
    @require_permission('diary.read')
    def get_entry_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get diary statistics
        
        Args:
            user_id: User ID (None for all users)
            
        Returns:
            Dictionary with statistics
        """
        query = self.db.query(DiaryEntry)
        
        if user_id:
            query = query.filter(DiaryEntry.user_id == user_id)
        
        total_entries = query.count()
        pinned_entries = query.filter(DiaryEntry.is_pinned == True).count()
        
        # Entries in current month
        now = datetime.utcnow()
        current_month_start = datetime(now.year, now.month, 1)
        current_month_entries = query.filter(
            DiaryEntry.entry_date >= current_month_start
        ).count()
        
        # Get tag statistics
        all_tags = self.get_all_tags(user_id)
        
        return {
            'total_entries': total_entries,
            'pinned_entries': pinned_entries,
            'current_month_entries': current_month_entries,
            'total_tags': len(all_tags),
            'tags': all_tags[:10]  # Top 10 tags
        }
    
    def get_related_entries(self, document_id: str = None, payment_id: str = None) -> List[DiaryEntry]:
        """Get entries related to a document or payment"""
        query = self.db.query(DiaryEntry)
        
        if document_id:
            query = query.filter(DiaryEntry.related_document_id == document_id)
        
        if payment_id:
            query = query.filter(DiaryEntry.related_payment_id == payment_id)
        
        return query.order_by(DiaryEntry.entry_date.desc()).all()