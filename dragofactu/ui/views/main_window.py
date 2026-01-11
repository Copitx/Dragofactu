from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QLabel, 
    QMessageBox, QToolBar, QAction, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QKeySequence

from models.database import SessionLocal
from services.auth.auth_service import PermissionService
from config.config import AppConfig

from .dashboard_view import DashboardView
from .clients_view import ClientsView
from .documents_view import DocumentsView
from .inventory_view import InventoryView
from .diary_view import DiaryView


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
        self.setup_main_tabs()
        
        # Setup timers for updates
        self.setup_timers()
        
        # Apply styles
        self.apply_styles()
    
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
    
    def setup_main_tabs(self):
        """Setup main tab widget"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Dashboard tab (always visible)
        self.dashboard_view = DashboardView()
        self.dashboard_view.setObjectName("dashboard")
        self.tab_widget.addTab(self.dashboard_view, "Dashboard")
        
        # Documents tab
        self.documents_view = DocumentsView()
        self.documents_view.setObjectName("documents")
        self.tab_widget.addTab(self.documents_view, "Documents")
        
        # Clients tab
        self.clients_view = ClientsView()
        self.clients_view.setObjectName("clients")
        self.tab_widget.addTab(self.clients_view, "Clients")
        
        # Inventory tab
        self.inventory_view = InventoryView()
        self.inventory_view.setObjectName("inventory")
        self.tab_widget.addTab(self.inventory_view, "Inventory")
        
        # Diary tab
        self.diary_view = DiaryView()
        self.diary_view.setObjectName("diary")
        self.tab_widget.addTab(self.diary_view, "Diary")
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def setup_timers(self):
        """Setup periodic timers"""
        # Timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(60000)  # Update every minute
    
    def apply_styles(self):
        """Apply application styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            QToolBar {
                background-color: #f8f8f8;
                border: 1px solid #e1e1e1;
                spacing: 3px;
                padding: 4px;
            }
            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #e1e1e1;
            }
        """)
    
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
        """Update tab visibility based on user permissions"""
        if not self.current_user:
            return
        
        # Hide tabs based on permissions
        has_clients = self.permission_service.has_permission(self.current_user, 'clients.read')
        has_documents = self.permission_service.has_permission(self.current_user, 'documents.read')
        has_inventory = self.permission_service.has_permission(self.current_user, 'inventory.read')
        has_diary = self.permission_service.has_permission(self.current_user, 'diary.read')
        
        # Find and hide tabs based on permissions
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            object_name = widget.objectName()
            
            if object_name == "clients":
                self.tab_widget.setTabVisible(i, has_clients)
            elif object_name == "documents":
                self.tab_widget.setTabVisible(i, has_documents)
            elif object_name == "inventory":
                self.tab_widget.setTabVisible(i, has_inventory)
            elif object_name == "diary":
                self.tab_widget.setTabVisible(i, has_diary)
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        widget = self.tab_widget.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()
        
        # Update status
        tab_name = self.tab_widget.tabText(index)
        self.status_label.setText(f"Viewing {tab_name}")
    
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
        current_widget = self.tab_widget.currentWidget()
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