from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from dragofactu.models.entities import Worker, Course
from dragofactu.models.database import SessionLocal
from dragofactu.services.auth.auth_service import require_permission


class WorkerService:
    """Service for managing workers and their courses"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('workers.create')
    def create_worker(self, code: str, first_name: str, last_name: str,
                    phone: str = None, email: str = None, address: str = None,
                    position: str = None, department: str = None,
                    hire_date: datetime = None, salary: float = None) -> Worker:
        """
        Create a new worker
        
        Args:
            code: Worker code (unique)
            first_name: First name
            last_name: Last name
            phone: Phone number
            email: Email address
            address: Home address
            position: Job position
            department: Department
            hire_date: Hire date
            salary: Monthly salary
            
        Returns:
            Created Worker object
        """
        # Check if code already exists
        existing = self.db.query(Worker).filter(Worker.code == code).first()
        if existing:
            raise ValueError(f"Worker code {code} already exists")
        
        # Generate full name
        full_name = f"{first_name} {last_name}"
        
        worker = Worker(
            code=code,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            position=position,
            department=department,
            hire_date=hire_date,
            salary=salary
        )
        
        self.db.add(worker)
        self.db.commit()
        self.db.refresh(worker)
        
        return worker
    
    @require_permission('workers.read')
    def get_worker_by_id(self, worker_id: str) -> Optional[Worker]:
        """Get worker by ID"""
        return self.db.query(Worker).filter(Worker.id == worker_id).first()
    
    @require_permission('workers.read')
    def get_worker_by_code(self, code: str) -> Optional[Worker]:
        """Get worker by code"""
        return self.db.query(Worker).filter(Worker.code == code).first()
    
    @require_permission('workers.read')
    def search_workers(self, query: str = None, department: str = None,
                      position: str = None, active_only: bool = True) -> List[Worker]:
        """
        Search workers with various filters
        
        Args:
            query: Search query for names, codes, emails
            department: Filter by department
            position: Filter by position
            active_only: Only active workers
            
        Returns:
            List of Worker objects
        """
        db_query = self.db.query(Worker)
        
        if active_only:
            db_query = db_query.filter(Worker.is_active == True)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Worker.code.ilike(f"%{query}%"),
                    Worker.first_name.ilike(f"%{query}%"),
                    Worker.last_name.ilike(f"%{query}%"),
                    Worker.full_name.ilike(f"%{query}%"),
                    Worker.email.ilike(f"%{query}%")
                )
            )
        
        if department:
            db_query = db_query.filter(Worker.department.ilike(f"%{department}%"))
        
        if position:
            db_query = db_query.filter(Worker.position.ilike(f"%{position}%"))
        
        return db_query.order_by(Worker.last_name, Worker.first_name).all()
    
    @require_permission('workers.update')
    def update_worker(self, worker_id: str, **kwargs) -> Optional[Worker]:
        """
        Update worker information
        
        Args:
            worker_id: Worker ID
            **kwargs: Fields to update
            
        Returns:
            Updated Worker object or None
        """
        worker = self.db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'email', 'address',
            'position', 'department', 'hire_date', 'salary', 'is_active'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(worker, field, value)
        
        # Update full name if first or last name changed
        if 'first_name' in kwargs or 'last_name' in kwargs:
            worker.full_name = f"{worker.first_name} {worker.last_name}"
        
        self.db.commit()
        self.db.refresh(worker)
        
        return worker
    
    @require_permission('workers.delete')
    def delete_worker(self, worker_id: str) -> bool:
        """
        Delete worker (soft delete)
        
        Args:
            worker_id: Worker ID
            
        Returns:
            True if successful
        """
        worker = self.db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return False
        
        # Soft delete
        worker.is_active = False
        self.db.commit()
        
        return True
    
    @require_permission('workers.read')
    def get_all_departments(self) -> List[str]:
        """Get all unique departments"""
        departments = self.db.query(Worker.department).filter(
            Worker.department.isnot(None),
            Worker.is_active == True
        ).distinct().all()
        
        return sorted([dept[0] for dept in departments if dept[0]])
    
    @require_permission('workers.read')
    def get_all_positions(self) -> List[str]:
        """Get all unique positions"""
        positions = self.db.query(Worker.position).filter(
            Worker.position.isnot(None),
            Worker.is_active == True
        ).distinct().all()
        
        return sorted([pos[0] for pos in positions if pos[0]])
    
    @require_permission('workers.read')
    def get_worker_statistics(self) -> Dict[str, Any]:
        """Get worker statistics"""
        total_workers = self.db.query(Worker).filter(Worker.is_active == True).count()
        
        # Workers by department
        dept_stats = self.db.query(
            Worker.department,
            func.count(Worker.id).label('count')
        ).filter(
            Worker.department.isnot(None),
            Worker.is_active == True
        ).group_by(Worker.department).all()
        
        # Workers by position
        pos_stats = self.db.query(
            Worker.position,
            func.count(Worker.id).label('count')
        ).filter(
            Worker.position.isnot(None),
            Worker.is_active == True
        ).group_by(Worker.position).all()
        
        # Recent hires (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_hires = self.db.query(Worker).filter(
            Worker.hire_date >= six_months_ago,
            Worker.is_active == True
        ).count()
        
        return {
            'total_workers': total_workers,
            'recent_hires': recent_hires,
            'departments': {dept[0]: dept[1] for dept in dept_stats if dept[0]},
            'positions': {pos[0]: pos[1] for pos in pos_stats if pos[0]}
        }


class CourseService:
    """Service for managing worker courses and certifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('workers.update')
    def create_course(self, worker_id: str, name: str, description: str = None,
                    provider: str = None, issue_date: datetime = None,
                    expiration_date: datetime = None, certificate_path: str = None) -> Course:
        """
        Create a new course record
        
        Args:
            worker_id: Worker ID
            name: Course name
            description: Course description
            provider: Training provider
            issue_date: Issue/completion date
            expiration_date: Expiration date
            certificate_path: Path to certificate PDF
            
        Returns:
            Created Course object
        """
        course = Course(
            worker_id=worker_id,
            name=name,
            description=description,
            provider=provider,
            issue_date=issue_date,
            expiration_date=expiration_date,
            certificate_path=certificate_path,
            is_valid=True  # Will be updated by check_expiring_courses
        )
        
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    @require_permission('workers.read')
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        return self.db.query(Course).filter(Course.id == course_id).first()
    
    @require_permission('workers.read')
    def get_worker_courses(self, worker_id: str, include_expired: bool = True) -> List[Course]:
        """
        Get all courses for a worker
        
        Args:
            worker_id: Worker ID
            include_expired: Include expired courses
            
        Returns:
            List of Course objects
        """
        query = self.db.query(Course).filter(Course.worker_id == worker_id)
        
        if not include_expired:
            query = query.filter(Course.is_valid == True)
        
        return query.order_by(Course.issue_date.desc()).all()
    
    @require_permission('workers.read')
    def search_courses(self, query: str = None, worker_id: str = None,
                    provider: str = None, include_expired: bool = True) -> List[Course]:
        """
        Search courses with filters
        
        Args:
            query: Search query for course names
            worker_id: Filter by worker ID
            provider: Filter by provider
            include_expired: Include expired courses
            
        Returns:
            List of Course objects
        """
        db_query = self.db.query(Course)
        
        if query:
            db_query = db_query.filter(Course.name.ilike(f"%{query}%"))
        
        if worker_id:
            db_query = db_query.filter(Course.worker_id == worker_id)
        
        if provider:
            db_query = db_query.filter(Course.provider.ilike(f"%{provider}%"))
        
        if not include_expired:
            db_query = db_query.filter(Course.is_valid == True)
        
        return db_query.order_by(Course.issue_date.desc()).all()
    
    @require_permission('workers.update')
    def update_course(self, course_id: str, **kwargs) -> Optional[Course]:
        """
        Update course information
        
        Args:
            course_id: Course ID
            **kwargs: Fields to update
            
        Returns:
            Updated Course object or None
        """
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'provider', 'issue_date',
            'expiration_date', 'certificate_path', 'is_valid'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(course, field, value)
        
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    @require_permission('workers.update')
    def delete_course(self, course_id: str) -> bool:
        """
        Delete course record
        
        Args:
            course_id: Course ID
            
        Returns:
            True if successful
        """
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return False
        
        self.db.delete(course)
        self.db.commit()
        
        return True
    
    @require_permission('workers.read')
    def get_expiring_courses(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get courses that will expire within specified days
        
        Args:
            days: Number of days to check ahead
            
        Returns:
            List of expiring course information
        """
        future_date = datetime.utcnow() + timedelta(days=days)
        
        courses = self.db.query(Course).filter(
            Course.expiration_date <= future_date,
            Course.expiration_date >= datetime.utcnow(),
            Course.is_valid == True
        ).all()
        
        expiring = []
        for course in courses:
            days_to_expire = (course.expiration_date - datetime.utcnow()).days
            
            expiring.append({
                'id': str(course.id),
                'worker_name': course.worker.full_name if course.worker else 'Unknown',
                'course_name': course.name,
                'provider': course.provider,
                'expiration_date': course.expiration_date.isoformat() if course.expiration_date else None,
                'days_to_expire': days_to_expire,
                'is_critical': days_to_expire <= 7  # Critical if expires within 7 days
            })
        
        return sorted(expiring, key=lambda x: x['days_to_expire'])
    
    @require_permission('workers.read')
    def get_expired_courses(self) -> List[Dict[str, Any]]:
        """Get all expired courses"""
        courses = self.db.query(Course).filter(
            or_(
                Course.expiration_date < datetime.utcnow(),
                Course.is_valid == False
            )
        ).all()
        
        expired = []
        for course in courses:
            expired.append({
                'id': str(course.id),
                'worker_name': course.worker.full_name if course.worker else 'Unknown',
                'course_name': course.name,
                'provider': course.provider,
                'expiration_date': course.expiration_date.isoformat() if course.expiration_date else None,
                'days_expired': (datetime.utcnow() - course.expiration_date).days if course.expiration_date else None,
                'is_valid': course.is_valid
            })
        
        return sorted(expired, key=lambda x: x['days_expired'])
    
    @require_permission('workers.update')
    def update_course_validity(self) -> Dict[str, Any]:
        """
        Update validity status for all courses based on expiration dates
        
        Returns:
            Summary of updates made
        """
        # Mark expired courses as invalid
        expired_count = self.db.query(Course).filter(
            Course.expiration_date < datetime.utcnow(),
            Course.is_valid == True
        ).update({'is_valid': False})
        
        # Re-validate courses that were marked invalid but expiration date is in future
        # (in case expiration dates were extended)
        future_valid_count = self.db.query(Course).filter(
            Course.expiration_date >= datetime.utcnow(),
            Course.is_valid == False
        ).update({'is_valid': True})
        
        self.db.commit()
        
        return {
            'courses_expired': expired_count,
            'courses_revalidated': future_valid_count
        }
    
    @require_permission('workers.read')
    def get_course_statistics(self) -> Dict[str, Any]:
        """Get course statistics"""
        total_courses = self.db.query(Course).count()
        
        # Valid vs expired
        valid_courses = self.db.query(Course).filter(Course.is_valid == True).count()
        expired_courses = total_courses - valid_courses
        
        # Expiring soon (next 30 days)
        expiring_soon = len(self.get_expiring_courses(30))
        
        # Courses by provider
        provider_stats = self.db.query(
            Course.provider,
            func.count(Course.id).label('count')
        ).filter(Course.provider.isnot(None)).group_by(Course.provider).all()
        
        return {
            'total_courses': total_courses,
            'valid_courses': valid_courses,
            'expired_courses': expired_courses,
            'expiring_soon': expiring_soon,
            'providers': {provider[0]: provider[1] for provider in provider_stats if provider[0]}
        }