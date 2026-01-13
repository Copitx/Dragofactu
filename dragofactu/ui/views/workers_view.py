from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QMessageBox, QDialog, QFormLayout,
    QDateEdit, QCheckBox, QHeaderView, QFrame,
    QTabWidget, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap

from dragofactu.models.database import SessionLocal
from dragofactu.services.workers.worker_service import WorkerService, CourseService
from dragofactu.services.auth.auth_service import PermissionService
from dragofactu.ui.styles import get_primary_button_style, get_secondary_button_style, get_danger_button_style
from datetime import datetime, timedelta
import os


class WorkerDialog(QDialog):
    """Dialog for creating/editing workers"""
    
    def __init__(self, parent=None, worker=None, user_id=None):
        super().__init__(parent)
        self.worker = worker
        self.user_id = user_id
        self.worker_service = None
        
        self.setWindowTitle("Edit Worker" if worker else "New Worker")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        self.setup_ui()
        
        if worker:
            self.load_worker(worker)
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setHorizontalSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Code
        self.code_edit = QLineEdit()
        self.code_edit.setMinimumHeight(36)
        form_layout.addRow("Code *:", self.code_edit)
        
        # Personal Information
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setMinimumHeight(36)
        form_layout.addRow("First Name *:", self.first_name_edit)

        self.last_name_edit = QLineEdit()
        self.last_name_edit.setMinimumHeight(36)
        form_layout.addRow("Last Name *:", self.last_name_edit)

        # Contact Information
        self.phone_edit = QLineEdit()
        self.phone_edit.setMinimumHeight(36)
        form_layout.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setMinimumHeight(36)
        form_layout.addRow("Email:", self.email_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setMinimumHeight(36)
        form_layout.addRow("Address:", self.address_edit)

        # Employment Information
        self.position_edit = QLineEdit()
        self.position_edit.setMinimumHeight(36)
        form_layout.addRow("Position:", self.position_edit)

        self.department_edit = QLineEdit()
        self.department_edit.setMinimumHeight(36)
        form_layout.addRow("Department:", self.department_edit)

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setMinimumHeight(36)
        form_layout.addRow("Hire Date:", self.hire_date_edit)

        self.salary_edit = QLineEdit()
        self.salary_edit.setMinimumHeight(36)
        form_layout.addRow("Salary:", self.salary_edit)
        
        # Status
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(get_secondary_button_style())
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(get_primary_button_style())
        self.save_button.clicked.connect(self.save_worker)

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_worker(self, worker):
        """Load worker data into form"""
        self.code_edit.setText(worker.code or "")
        self.first_name_edit.setText(worker.first_name or "")
        self.last_name_edit.setText(worker.last_name or "")
        self.phone_edit.setText(worker.phone or "")
        self.email_edit.setText(worker.email or "")
        self.address_edit.setText(worker.address or "")
        self.position_edit.setText(worker.position or "")
        self.department_edit.setText(worker.department or "")
        
        if worker.hire_date:
            self.hire_date_edit.setDate(QDate.fromString(
                worker.hire_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'
            ))
        
        if worker.salary:
            self.salary_edit.setText(str(worker.salary))
        
        self.active_checkbox.setChecked(worker.is_active)
    
    def save_worker(self):
        """Save the worker"""
        code = self.code_edit.text().strip()
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        address = self.address_edit.text().strip()
        position = self.position_edit.text().strip()
        department = self.department_edit.text().strip()
        salary_text = self.salary_edit.text().strip()
        
        if not code:
            QMessageBox.warning(self, "Warning", "Please enter a worker code")
            return
        
        if not first_name or not last_name:
            QMessageBox.warning(self, "Warning", "Please enter first and last name")
            return
        
        salary = None
        if salary_text:
            try:
                salary = float(salary_text)
            except ValueError:
                QMessageBox.warning(self, "Warning", "Please enter a valid salary")
                return
        
        try:
            with SessionLocal() as db:
                self.worker_service = WorkerService(db)
                
                if self.worker:
                    # Update existing worker
                    self.worker_service.update_worker(
                        str(self.worker.id),
                        code=code,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        email=email,
                        address=address,
                        position=position,
                        department=department,
                        hire_date=self.hire_date_edit.date().toPython(),
                        salary=salary,
                        is_active=self.active_checkbox.isChecked()
                    )
                else:
                    # Create new worker
                    self.worker_service.create_worker(
                        code=code,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        email=email,
                        address=address,
                        position=position,
                        department=department,
                        hire_date=self.hire_date_edit.date().toPython(),
                        salary=salary
                    )
                
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save worker: {str(e)}")


class CourseDialog(QDialog):
    """Dialog for creating/editing courses"""
    
    def __init__(self, parent=None, course=None, worker_id=None, user_id=None):
        super().__init__(parent)
        self.course = course
        self.worker_id = worker_id
        self.user_id = user_id
        self.course_service = None
        
        self.setWindowTitle("Edit Course" if course else "New Course")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
        
        if course:
            self.load_course(course)
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setHorizontalSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Course Information
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumHeight(36)
        form_layout.addRow("Course Name *:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setMinimumHeight(80)
        form_layout.addRow("Description:", self.description_edit)

        self.provider_edit = QLineEdit()
        self.provider_edit.setMinimumHeight(36)
        form_layout.addRow("Provider:", self.provider_edit)

        # Dates
        self.issue_date_edit = QDateEdit()
        self.issue_date_edit.setCalendarPopup(True)
        self.issue_date_edit.setDate(QDate.currentDate())
        self.issue_date_edit.setMinimumHeight(36)
        form_layout.addRow("Issue Date:", self.issue_date_edit)

        self.expiration_date_edit = QDateEdit()
        self.expiration_date_edit.setCalendarPopup(True)
        self.expiration_date_edit.setMinimumHeight(36)
        form_layout.addRow("Expiration Date:", self.expiration_date_edit)
        
        # Certificate
        cert_layout = QHBoxLayout()
        self.cert_path_edit = QLineEdit()
        self.cert_path_edit.setReadOnly(True)
        cert_layout.addWidget(self.cert_path_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_certificate)
        cert_layout.addWidget(self.browse_button)
        
        form_layout.addRow("Certificate:", cert_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(get_secondary_button_style())
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(get_primary_button_style())
        self.save_button.clicked.connect(self.save_course)

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_course(self, course):
        """Load course data into form"""
        self.name_edit.setText(course.name or "")
        self.description_edit.setHtml(course.description or "")
        self.provider_edit.setText(course.provider or "")
        
        if course.issue_date:
            self.issue_date_edit.setDate(QDate.fromString(
                course.issue_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'
            ))
        
        if course.expiration_date:
            self.expiration_date_edit.setDate(QDate.fromString(
                course.expiration_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'
            ))
        
        if course.certificate_path:
            self.cert_path_edit.setText(course.certificate_path)
    
    def browse_certificate(self):
        """Browse for certificate file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Certificate",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.cert_path_edit.setText(file_path)
    
    def save_course(self):
        """Save the course"""
        name = self.name_edit.text().strip()
        description = self.description_edit.toHtml()
        provider = self.provider_edit.text().strip()
        issue_date = self.issue_date_edit.date().toPython()
        expiration_date = self.expiration_date_edit.date().toPython()
        certificate_path = self.cert_path_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a course name")
            return
        
        try:
            with SessionLocal() as db:
                self.course_service = CourseService(db)
                
                if self.course:
                    # Update existing course
                    self.course_service.update_course(
                        str(self.course.id),
                        name=name,
                        description=description,
                        provider=provider,
                        issue_date=issue_date,
                        expiration_date=expiration_date,
                        certificate_path=certificate_path
                    )
                else:
                    # Create new course
                    self.course_service.create_course(
                        worker_id=self.worker_id,
                        name=name,
                        description=description,
                        provider=provider,
                        issue_date=issue_date,
                        expiration_date=expiration_date,
                        certificate_path=certificate_path
                    )
                
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save course: {str(e)}")


class WorkersView(QWidget):
    """Workers management view"""
    
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.permission_service = PermissionService()
        self.worker_service = None
        self.course_service = None
        
        self.setup_ui()
        # Defer refresh to prevent blocking during initialization
        QTimer.singleShot(100, self.refresh)
    
    def setup_ui(self):
        """Setup workers UI"""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Workers tab
        self.setup_workers_tab()
        self.tab_widget.addTab(self.workers_tab, "Workers")
        
        # Courses tab
        self.setup_courses_tab()
        self.tab_widget.addTab(self.courses_tab, "Courses")
        
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Update UI based on permissions
        self.update_permissions()
        
        # Apply styles
        self.apply_styles()
    
    def setup_workers_tab(self):
        """Setup workers tab"""
        self.workers_tab = QWidget()
        layout = QVBoxLayout(self.workers_tab)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search workers...")
        self.search_edit.textChanged.connect(self.on_worker_search_changed)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_edit)
        
        self.department_combo = QComboBox()
        self.department_combo.addItem("All Departments")
        self.department_combo.currentTextChanged.connect(self.on_department_changed)
        toolbar_layout.addWidget(QLabel("Department:"))
        toolbar_layout.addWidget(self.department_combo)
        
        toolbar_layout.addStretch()
        
        self.new_worker_button = QPushButton("New Worker")
        self.new_worker_button.clicked.connect(self.create_new_worker)
        toolbar_layout.addWidget(self.new_worker_button)
        
        self.refresh_workers_button = QPushButton("Refresh")
        self.refresh_workers_button.clicked.connect(self.refresh_workers)
        toolbar_layout.addWidget(self.refresh_workers_button)
        
        layout.addLayout(toolbar_layout)
        
        # Workers table
        self.workers_table = QTableWidget()
        self.workers_table.setColumnCount(7)
        self.workers_table.setHorizontalHeaderLabels([
            "Code", "Name", "Department", "Position", 
            "Phone", "Email", "Status"
        ])
        
        # Configure table
        header = self.workers_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.workers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.workers_table.itemDoubleClicked.connect(self.on_worker_double_clicked)
        
        layout.addWidget(self.workers_table)
    
    def setup_courses_tab(self):
        """Setup courses tab"""
        self.courses_tab = QWidget()
        layout = QVBoxLayout(self.courses_tab)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.course_search_edit = QLineEdit()
        self.course_search_edit.setPlaceholderText("Search courses...")
        self.course_search_edit.textChanged.connect(self.on_course_search_changed)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.course_search_edit)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("All Providers")
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        toolbar_layout.addWidget(QLabel("Provider:"))
        toolbar_layout.addWidget(self.provider_combo)
        
        toolbar_layout.addStretch()
        
        self.new_course_button = QPushButton("New Course")
        self.new_course_button.clicked.connect(self.create_new_course)
        toolbar_layout.addWidget(self.new_course_button)
        
        self.refresh_courses_button = QPushButton("Refresh")
        self.refresh_courses_button.clicked.connect(self.refresh_courses)
        toolbar_layout.addWidget(self.refresh_courses_button)
        
        layout.addLayout(toolbar_layout)
        
        # Expiring courses alert
        self.expiring_frame = QFrame()
        self.expiring_layout = QVBoxLayout(self.expiring_frame)
        
        self.expiring_label = QLabel("⚠️ Courses expiring soon:")
        self.expiring_label.setStyleSheet("font-weight: bold; color: #d84315;")
        self.expiring_layout.addWidget(self.expiring_label)
        
        self.expiring_list = QLabel("No courses expiring soon")
        self.expiring_list.setWordWrap(True)
        self.expiring_layout.addWidget(self.expiring_list)
        
        self.expiring_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 1px solid #ffcc80;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 10px;
            }
        """)
        
        layout.addWidget(self.expiring_frame)
        
        # Courses table
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(6)
        self.courses_table.setHorizontalHeaderLabels([
            "Worker", "Course", "Provider", "Issue Date", 
            "Expiration", "Status"
        ])
        
        # Configure table
        header = self.courses_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.courses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.courses_table.itemDoubleClicked.connect(self.on_course_double_clicked)
        
        layout.addWidget(self.courses_table)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #0078d4;
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
    
    def update_permissions(self):
        """Update UI based on user permissions"""
        if not self.current_user:
            return
        
        can_create = self.permission_service.has_permission(self.current_user, 'workers.create')
        can_update = self.permission_service.has_permission(self.current_user, 'workers.update')
        can_delete = self.permission_service.has_permission(self.current_user, 'workers.delete')
        
        self.new_worker_button.setEnabled(can_create)
        self.new_course_button.setEnabled(can_update)
    
    def refresh(self):
        """Refresh all data"""
        self.refresh_workers()
        self.refresh_courses()
        self.load_departments()
        self.load_providers()
    
    def refresh_workers(self):
        """Refresh workers data"""
        try:
            with SessionLocal() as db:
                self.worker_service = WorkerService(db)
                
                workers = self.worker_service.search_workers(active_only=True)
                self.load_workers_data(workers)
        
        except Exception as e:
            self.workers_table.setRowCount(1)
            self.workers_table.setColumnCount(1)
            self.workers_table.setHorizontalHeaderLabels(["Error"])
            self.workers_table.setItem(0, 0, QTableWidgetItem(f"Error loading workers: {str(e)}"))
    
    def refresh_courses(self):
        """Refresh courses data"""
        try:
            with SessionLocal() as db:
                self.course_service = CourseService(db)
                
                # Load expiring courses
                expiring_courses = self.course_service.get_expiring_courses(30)
                self.load_expiring_courses(expiring_courses)
                
                # Load all courses
                courses = self.course_service.search_courses()
                self.load_courses_data(courses)
        
        except Exception as e:
            self.courses_table.setRowCount(1)
            self.courses_table.setColumnCount(1)
            self.courses_table.setHorizontalHeaderLabels(["Error"])
            self.courses_table.setItem(0, 0, QTableWidgetItem(f"Error loading courses: {str(e)}"))
    
    def load_workers_data(self, workers):
        """Load workers data into table"""
        self.workers_table.setRowCount(len(workers))
        
        for row, worker in enumerate(workers):
            # Code
            self.workers_table.setItem(row, 0, QTableWidgetItem(worker.code or ""))
            
            # Name
            self.workers_table.setItem(row, 1, QTableWidgetItem(worker.full_name or ""))
            
            # Department
            self.workers_table.setItem(row, 2, QTableWidgetItem(worker.department or ""))
            
            # Position
            self.workers_table.setItem(row, 3, QTableWidgetItem(worker.position or ""))
            
            # Phone
            self.workers_table.setItem(row, 4, QTableWidgetItem(worker.phone or ""))
            
            # Email
            self.workers_table.setItem(row, 5, QTableWidgetItem(worker.email or ""))
            
            # Status
            status_item = QTableWidgetItem("Active" if worker.is_active else "Inactive")
            if worker.is_active:
                status_item.setBackground(QColor('#e8f5e8'))
            else:
                status_item.setBackground(QColor('#ffebee'))
            
            self.workers_table.setItem(row, 6, status_item)
            
            # Store worker object
            self.workers_table.item(row, 0).setData(Qt.UserRole, worker)
    
    def load_courses_data(self, courses):
        """Load courses data into table"""
        self.courses_table.setRowCount(len(courses))
        
        for row, course in enumerate(courses):
            # Worker name
            worker_name = course.worker.full_name if course.worker else "Unknown"
            self.courses_table.setItem(row, 0, QTableWidgetItem(worker_name))
            
            # Course name
            self.courses_table.setItem(row, 1, QTableWidgetItem(course.name or ""))
            
            # Provider
            self.courses_table.setItem(row, 2, QTableWidgetItem(course.provider or ""))
            
            # Issue date
            issue_date = course.issue_date.strftime('%Y-%m-%d') if course.issue_date else ""
            self.courses_table.setItem(row, 3, QTableWidgetItem(issue_date))
            
            # Expiration date
            exp_date = course.expiration_date.strftime('%Y-%m-%d') if course.expiration_date else ""
            self.courses_table.setItem(row, 4, QTableWidgetItem(exp_date))
            
            # Status
            status_text = "Valid" if course.is_valid else "Expired"
            status_item = QTableWidgetItem(status_text)
            if course.is_valid:
                status_item.setBackground(QColor('#e8f5e8'))
            else:
                status_item.setBackground(QColor('#ffebee'))
            
            self.courses_table.setItem(row, 5, status_item)
            
            # Store course object
            self.courses_table.item(row, 0).setData(Qt.UserRole, course)
    
    def load_expiring_courses(self, expiring_courses):
        """Load expiring courses information"""
        if not expiring_courses:
            self.expiring_list.setText("No courses expiring soon")
            return
        
        expiring_text = []
        for course in expiring_courses[:5]:  # Show max 5
            status = "🚨" if course['is_critical'] else "⚠️"
            expiring_text.append(f"{status} {course['worker_name']} - {course['course_name']} ({course['days_to_expire']} days)")
        
        self.expiring_list.setText("\n".join(expiring_text))
    
    def load_departments(self):
        """Load departments into combo box"""
        try:
            if not self.worker_service:
                return
            
            departments = self.worker_service.get_all_departments()
            
            # Update combo box
            self.department_combo.clear()
            self.department_combo.addItem("All Departments")
            
            for department in departments:
                self.department_combo.addItem(department)
        
        except Exception as e:
            print(f"Error loading departments: {e}")
    
    def load_providers(self):
        """Load providers into combo box"""
        try:
            if not self.course_service:
                return
            
            stats = self.course_service.get_course_statistics()
            providers = list(stats.get('providers', {}).keys())
            
            # Update combo box
            self.provider_combo.clear()
            self.provider_combo.addItem("All Providers")
            
            for provider in sorted(providers):
                self.provider_combo.addItem(provider)
        
        except Exception as e:
            print(f"Error loading providers: {e}")
    
    def on_worker_search_changed(self, text):
        """Handle worker search"""
        if len(text) >= 3 or len(text) == 0:
            self.perform_worker_search()
    
    def on_department_changed(self):
        """Handle department filter change"""
        self.perform_worker_search()
    
    def on_course_search_changed(self, text):
        """Handle course search"""
        if len(text) >= 3 or len(text) == 0:
            self.perform_course_search()
    
    def on_provider_changed(self):
        """Handle provider filter change"""
        self.perform_course_search()
    
    def perform_worker_search(self):
        """Perform worker search"""
        query = self.search_edit.text().strip()
        department = self.department_combo.currentText()
        
        if department == "All Departments":
            department = None
        
        try:
            if not self.worker_service:
                return
            
            workers = self.worker_service.search_workers(
                query=query if query else None,
                department=department
            )
            self.load_workers_data(workers)
        
        except Exception as e:
            print(f"Search error: {e}")
    
    def perform_course_search(self):
        """Perform course search"""
        query = self.course_search_edit.text().strip()
        provider = self.provider_combo.currentText()
        
        if provider == "All Providers":
            provider = None
        
        try:
            if not self.course_service:
                return
            
            courses = self.course_service.search_courses(
                query=query if query else None,
                provider=provider
            )
            self.load_courses_data(courses)
        
        except Exception as e:
            print(f"Course search error: {e}")
    
    def on_worker_double_clicked(self, item):
        """Handle worker double click"""
        row = item.row()
        code_item = self.workers_table.item(row, 0)
        worker = code_item.data(Qt.UserRole)
        
        if worker:
            self.show_worker_dialog(worker)
    
    def on_course_double_clicked(self, item):
        """Handle course double click"""
        row = item.row()
        worker_item = self.courses_table.item(row, 0)
        course = worker_item.data(Qt.UserRole)
        
        if course:
            self.show_course_dialog(course)
    
    def create_new_worker(self):
        """Create new worker dialog"""
        dialog = WorkerDialog(self, user_id=self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_workers()
    
    def create_new_course(self):
        """Create new course dialog"""
        # Get selected worker to associate with course
        current_row = self.workers_table.currentRow()
        worker_id = None
        
        if current_row >= 0:
            code_item = self.workers_table.item(current_row, 0)
            worker = code_item.data(Qt.UserRole)
            if worker:
                worker_id = str(worker.id)
        
        if not worker_id:
            QMessageBox.information(self, "Info", "Please select a worker first")
            return
        
        dialog = CourseDialog(self, worker_id=worker_id, user_id=self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_courses()
    
    def show_worker_dialog(self, worker):
        """Show worker edit dialog"""
        dialog = WorkerDialog(self, worker=worker, user_id=self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_workers()
    
    def show_course_dialog(self, course):
        """Show course edit dialog"""
        dialog = CourseDialog(self, course=course, user_id=self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_courses()
    
    def set_current_user(self, user):
        """Set the current user and refresh"""
        self.current_user = user
        self.update_permissions()
        self.refresh()