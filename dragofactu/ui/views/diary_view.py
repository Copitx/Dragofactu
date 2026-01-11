from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QCalendarWidget, QListWidget, QListWidgetItem,
    QTextEdit, QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QDialog, QFormLayout,
    QCheckBox, QDateEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QTextCharFormat, QColor

from dragofactu.models.database import SessionLocal
from dragofactu.services.diary.diary_service import DiaryService
from dragofactu.services.auth.auth_service import PermissionService


class DiaryEntryDialog(QDialog):
    """Dialog for creating/editing diary entries"""
    
    def __init__(self, parent=None, entry=None, user_id=None):
        super().__init__(parent)
        self.entry = entry
        self.user_id = user_id
        self.diary_service = None
        
        self.setWindowTitle("Edit Entry" if entry else "New Entry")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        self.setup_ui()
        
        if entry:
            self.load_entry(entry)
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Entry title...")
        form_layout.addRow("Title:", self.title_edit)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_edit)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags...")
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Pinned checkbox
        self.pinned_checkbox = QCheckBox("Pin this entry")
        form_layout.addRow("", self.pinned_checkbox)
        
        layout.addLayout(form_layout)
        
        # Content editor
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Write your entry here...")
        layout.addWidget(QLabel("Content:"))
        layout.addWidget(self.content_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_entry)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_entry(self, entry):
        """Load entry data into form"""
        self.title_edit.setText(entry.title or "")
        self.date_edit.setDate(QDate.fromString(entry.entry_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
        
        # Load tags
        if entry.tags:
            import json
            try:
                tags = json.loads(entry.tags)
                if isinstance(tags, list):
                    self.tags_edit.setText(", ".join(tags))
            except (json.JSONDecodeError, TypeError):
                pass
        
        self.content_edit.setHtml(entry.content or "")
        self.pinned_checkbox.setChecked(entry.is_pinned or False)
    
    def save_entry(self):
        """Save the diary entry"""
        title = self.title_edit.text().strip()
        content = self.content_edit.toHtml()
        date = self.date_edit.date().toPython()
        tags_text = self.tags_edit.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a title")
            return
        
        if not content:
            QMessageBox.warning(self, "Warning", "Please enter content")
            return
        
        # Parse tags
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        try:
            with SessionLocal() as db:
                self.diary_service = DiaryService(db)
                
                if self.entry:
                    # Update existing entry
                    self.diary_service.update_entry(
                        str(self.entry.id), 
                        self.user_id,
                        title=title,
                        content=content,
                        entry_date=date,
                        tags=tags,
                        is_pinned=self.pinned_checkbox.isChecked()
                    )
                else:
                    # Create new entry
                    self.diary_service.create_entry(
                        title=title,
                        content=content,
                        user_id=self.user_id,
                        entry_date=date,
                        tags=tags,
                        is_pinned=self.pinned_checkbox.isChecked()
                    )
                
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {str(e)}")


class DiaryView(QWidget):
    """Diary/Agenda management view"""
    
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.permission_service = PermissionService()
        self.diary_service = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Setup diary UI"""
        layout = QHBoxLayout()
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Calendar and navigation
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)
        
        # Search
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search entries...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        
        left_layout.addLayout(search_layout)
        
        # Pinned entries
        left_layout.addWidget(QLabel("Pinned Entries:"))
        self.pinned_list = QListWidget()
        self.pinned_list.setMaximumHeight(150)
        self.pinned_list.itemDoubleClicked.connect(self.on_pinned_clicked)
        left_layout.addWidget(self.pinned_list)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel - Entry list and editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Entry list
        self.entries_list = QListWidget()
        self.entries_list.itemDoubleClicked.connect(self.on_entry_clicked)
        right_layout.addWidget(self.entries_list)
        
        # Entry details
        self.entry_display = QTextEdit()
        self.entry_display.setReadOnly(True)
        right_layout.addWidget(self.entry_display)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("New Entry")
        self.new_button.clicked.connect(self.create_new_entry)
        button_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_current_entry)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_current_entry)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
        # Update UI based on permissions
        self.update_permissions()
        
        # Style
        self.apply_styles()
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
            QCalendarWidget {
                font-size: 12px;
            }
            QPushButton {
                padding: 8px 16px;
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
        
        can_create = self.permission_service.has_permission(self.current_user, 'diary.create')
        can_update = self.permission_service.has_permission(self.current_user, 'diary.update')
        can_delete = self.permission_service.has_permission(self.current_user, 'diary.delete')
        
        self.new_button.setEnabled(can_create)
        self.edit_button.setEnabled(can_update)
        self.delete_button.setEnabled(can_delete)
    
    def refresh(self):
        """Refresh diary data"""
        try:
            with SessionLocal() as db:
                self.diary_service = DiaryService(db)
                
                # Load pinned entries
                if self.current_user:
                    pinned_entries = self.diary_service.get_pinned_entries(self.current_user.id)
                    self.load_pinned_entries(pinned_entries)
                
                # Load today's entries
                today = QDate.currentDate()
                self.load_entries_for_date(today)
        
        except Exception as e:
            self.entries_list.clear()
            self.entries_list.addItem(f"Error loading entries: {str(e)}")
    
    def load_pinned_entries(self, entries):
        """Load pinned entries into list"""
        self.pinned_list.clear()
        
        for entry in entries:
            item = QListWidgetItem(f"📌 {entry.title}")
            item.setData(Qt.UserRole, entry)
            item.setToolTip(entry.entry_date.strftime('%Y-%m-%d %H:%M'))
            self.pinned_list.addItem(item)
    
    def load_entries_for_date(self, date):
        """Load entries for selected date"""
        try:
            if not self.diary_service or not self.current_user:
                return
            
            py_date = date.toPython()
            entries = self.diary_service.get_entries_for_month(
                py_date.year, py_date.month, self.current_user.id
            )
            
            # Filter entries for selected date
            selected_date_entries = [
                entry for entry in entries 
                if entry.entry_date.date() == py_date.date()
            ]
            
            self.load_entries_list(selected_date_entries)
            
            # Highlight dates with entries
            self.highlight_calendar_dates(entries)
        
        except Exception as e:
            self.entries_list.clear()
            self.entries_list.addItem(f"Error: {str(e)}")
    
    def load_entries_list(self, entries):
        """Load entries into the list widget"""
        self.entries_list.clear()
        
        for entry in entries:
            # Format entry item
            time_str = entry.entry_date.strftime('%H:%M')
            title = entry.title or "No title"
            
            if entry.is_pinned:
                display_text = f"📌 {time_str} - {title}"
            else:
                display_text = f"{time_str} - {title}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, entry)
            item.setToolTip(entry.entry_date.strftime('%Y-%m-%d %H:%M'))
            
            self.entries_list.addItem(item)
    
    def highlight_calendar_dates(self, entries):
        """Highlight dates on calendar that have entries"""
        # Clear previous formatting
        format = QTextCharFormat()
        format.setBackground(QColor('white'))
        self.calendar.setDateTextFormat(QDate(), format)
        
        # Highlight dates with entries
        entry_format = QTextCharFormat()
        entry_format.setBackground(QColor('#e6f3ff'))
        entry_format.setForeground(QColor('#0078d4'))
        
        for entry in entries:
            q_date = QDate(
                entry.entry_date.year,
                entry.entry_date.month,
                entry.entry_date.day
            )
            self.calendar.setDateTextFormat(q_date, entry_format)
    
    def on_date_selected(self, date):
        """Handle calendar date selection"""
        self.load_entries_for_date(date)
    
    def on_search_changed(self, text):
        """Handle search text change"""
        if len(text) >= 3 or len(text) == 0:
            self.perform_search()
    
    def perform_search(self):
        """Perform diary entry search"""
        query = self.search_edit.text().strip()
        
        if not query:
            self.refresh()
            return
        
        try:
            if not self.diary_service or not self.current_user:
                return
            
            entries = self.diary_service.search_entries(
                query, self.current_user.id, limit=50
            )
            self.load_entries_list(entries)
        
        except Exception as e:
            self.entries_list.clear()
            self.entries_list.addItem(f"Search error: {str(e)}")
    
    def on_pinned_clicked(self, item):
        """Handle pinned entry click"""
        entry = item.data(Qt.UserRole)
        if entry:
            self.display_entry(entry)
    
    def on_entry_clicked(self, item):
        """Handle entry click"""
        entry = item.data(Qt.UserRole)
        if entry:
            self.display_entry(entry)
    
    def display_entry(self, entry):
        """Display entry content in the detail view"""
        title = f"<h2>{entry.title}</h2>"
        date = f"<p><strong>Date:</strong> {entry.entry_date.strftime('%Y-%m-%d %H:%M')}</p>"
        
        # Load tags
        if entry.tags:
            import json
            try:
                tags = json.loads(entry.tags)
                if isinstance(tags, list):
                    tags_html = ", ".join([f"<span style='background:#e1e1e1;padding:2px 6px;border-radius:3px;'>{tag}</span>" for tag in tags])
                    tags = f"<p><strong>Tags:</strong> {tags_html}</p>"
                else:
                    tags = ""
            except (json.JSONDecodeError, TypeError):
                tags = ""
        else:
            tags = ""
        
        content = entry.content or ""
        
        full_html = f"{title}{date}{tags}<hr>{content}"
        self.entry_display.setHtml(full_html)
    
    def create_new_entry(self):
        """Create a new diary entry"""
        dialog = DiaryEntryDialog(self, user_id=self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()
    
    def edit_current_entry(self):
        """Edit the currently selected entry"""
        current_item = self.entries_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select an entry to edit")
            return
        
        entry = current_item.data(Qt.UserRole)
        if entry:
            dialog = DiaryEntryDialog(self, entry=entry, user_id=self.current_user.id)
            if dialog.exec() == QDialog.Accepted:
                self.refresh()
    
    def delete_current_entry(self):
        """Delete the currently selected entry"""
        current_item = self.entries_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select an entry to delete")
            return
        
        entry = current_item.data(Qt.UserRole)
        if not entry:
            return
        
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f'Are you sure you want to delete "{entry.title}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with SessionLocal() as db:
                    diary_service = DiaryService(db)
                    diary_service.delete_entry(str(entry.id))
                    self.refresh()
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete entry: {str(e)}")
    
    def set_current_user(self, user):
        """Set the current user and refresh"""
        self.current_user = user
        self.update_permissions()
        self.refresh()