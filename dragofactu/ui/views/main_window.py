from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QStatusBar, QLabel,
    QMessageBox, QToolBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QAction

from dragofactu.models.database import SessionLocal
from dragofactu.services.auth.auth_service import PermissionService
from dragofactu.config.config import AppConfig

from dragofactu.ui.views.dashboard_view import DashboardView
from dragofactu.ui.views.clients_view import ClientsView
from dragofactu.ui.views.documents_view import DocumentsView
from dragofactu.ui.views.inventory_view import InventoryView
from dragofactu.ui.views.diary_view import DiaryView


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.permission_service = PermissionService()
        
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {AppConfig.APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Setup UI components
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_main_shell()
        
        # Setup timers for updates
        self.setup_timers()
    
    def set_current_user(self, user):
        """Set current logged-in user"""
        self.current_user = user
        self.update_user_ui()
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {user.full_name}")
    
    def update_user_ui(self):
        """Update UI based on user permissions"""
        # Update menu items based on permissions
        self.update_menu_permissions()
        
        # Update tab visibility based on permissions
        self.update_tab_permissions()
    
    def setup_menu_bar(self):
        """Setup main menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_quote_action = QAction("New Quote", self)
        new_quote_action.setShortcut(QKeySequence("Ctrl+Q"))
        new_quote_action.triggered.connect(self.create_new_quote)
        file_menu.addAction(new_quote_action)
        
        new_invoice_action = QAction("New Invoice", self)
        new_invoice_action.setShortcut(QKeySequence("Ctrl+I"))
        new_invoice_action.triggered.connect(self.create_new_invoice)
        file_menu.addAction(new_invoice_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Reports", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_reports)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh_current_tab)
        view_menu.addAction(refresh_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        backup_action = QAction("Backup Database", self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        self.menus = {
            'file': file_menu,
            'edit': edit_menu,
            'view': view_menu,
            'tools': tools_menu,
            'help': help_menu
        }
    
    def setup_toolbar(self):
        """Setup main toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # New document actions
        new_quote_action = QAction("New Quote", self)
        new_quote_action.triggered.connect(self.create_new_quote)
        toolbar.addAction(new_quote_action)
        
        new_invoice_action = QAction("New Invoice", self)
        new_invoice_action.triggered.connect(self.create_new_invoice)
        toolbar.addAction(new_invoice_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        toolbar.addAction(refresh_action)
        
        self.addToolBar(toolbar)
        self.toolbar = toolbar
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # User info
        self.user_label = QLabel("No user logged in")
        self.status_bar.addPermanentWidget(self.user_label)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
    
    def setup_main_shell(self):
        """Setup web-like shell: sidebar navigation + stacked content."""
        shell_layout = QHBoxLayout()
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("mainNavigation")
        self.nav_list.setFixedWidth(220)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("mainContentStack")

        self.pages = []
        self.page_permissions = {}

        page_specs = [
            ("dashboard", "Dashboard", DashboardView, None),
            ("clients", "Clients", ClientsView, "clients.read"),
            ("documents", "Documents", DocumentsView, "documents.read"),
            ("inventory", "Inventory", InventoryView, "inventory.read"),
            ("diary", "Diary", DiaryView, "diary.read"),
        ]

        for key, label, page_cls, permission in page_specs:
            page = page_cls()
            page.setObjectName(key)
            index = self.content_stack.addWidget(page)

            nav_item = QListWidgetItem(label)
            nav_item.setData(Qt.UserRole, key)
            self.nav_list.addItem(nav_item)

            self.pages.append((index, key, label, permission))
            self.page_permissions[key] = permission

        self.nav_list.currentRowChanged.connect(self.on_nav_changed)

        shell_layout.addWidget(self.nav_list)
        shell_layout.addWidget(self.content_stack, 1)
        self.main_layout.addLayout(shell_layout)

        # Default landing view
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)
    
    def setup_timers(self):
        """Setup periodic timers"""
        # Timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(60000)  # Update every minute
    
    def apply_styles(self):
        """Deprecated: global styling is applied at QApplication level."""
        return
    
    def update_menu_permissions(self):
        """Update menu items based on user permissions"""
        if not self.current_user:
            return
        
        # Example: Hide admin-only features for non-admin users
        has_admin = self.permission_service.has_permission(self.current_user, 'system.config')
        has_documents_create = self.permission_service.has_permission(self.current_user, 'documents.create')
        
        # Update menu visibility based on permissions
        for menu_name, menu in self.menus.items():
            for action in menu.actions():
                # This is a simple example - in practice you'd want more sophisticated permission checking
                if hasattr(action, 'permission_required'):
                    action.setVisible(self.permission_service.has_permission(self.current_user, action.permission_required))
    
    def update_tab_permissions(self):
        """Update navigation visibility based on user permissions."""
        if not self.current_user:
            return
 
        first_visible_row = None
        for row, (_, key, _, permission) in enumerate(self.pages):
            is_visible = True
            if permission:
                is_visible = self.permission_service.has_permission(self.current_user, permission)
            self.nav_list.setRowHidden(row, not is_visible)
            if is_visible and first_visible_row is None:
                first_visible_row = row

        current_row = self.nav_list.currentRow()
        if current_row < 0 or self.nav_list.isRowHidden(current_row):
            if first_visible_row is not None:
                self.nav_list.setCurrentRow(first_visible_row)
    
    def on_nav_changed(self, row):
        """Handle sidebar navigation changes."""
        if row < 0 or row >= len(self.pages) or self.nav_list.isRowHidden(row):
            return

        index, _, label, _ = self.pages[row]
        self.content_stack.setCurrentIndex(index)

        widget = self.content_stack.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()

        self.status_label.setText(f"Viewing {label}")
    
    def create_new_quote(self):
        """Create new quote document"""
        # This will be implemented when we add the document creation dialog
        self.status_label.setText("Creating new quote...")
    
    def create_new_invoice(self):
        """Create new invoice document"""
        # This will be implemented when we add the document creation dialog
        self.status_label.setText("Creating new invoice...")
    
    def export_reports(self):
        """Export reports"""
        # This will be implemented when we add report generation
        self.status_label.setText("Exporting reports...")
    
    def show_preferences(self):
        """Show preferences dialog"""
        # This will be implemented when we add preferences
        self.status_label.setText("Opening preferences...")
    
    def backup_database(self):
        """Backup database"""
        # This will be implemented when we add backup functionality
        self.status_label.setText("Backing up database...")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            f"About {AppConfig.APP_NAME}",
            f"""
            <h2>{AppConfig.APP_NAME}</h2>
            <p>Version {AppConfig.APP_VERSION}</p>
            <p>Professional Business Management System</p>
            <p>© 2024 Dragofactu Team</p>
            """
        )
    
    def refresh_current_tab(self):
        """Refresh the current active tab"""
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
        self.status_label.setText("Refreshed")
    
    def update_status(self):
        """Update status information"""
        if self.current_user:
            self.user_label.setText(f"User: {self.current_user.full_name} ({self.current_user.role.value})")
        else:
            self.user_label.setText("No user logged in")
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()