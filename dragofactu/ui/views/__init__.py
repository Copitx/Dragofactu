"""UI views and widgets"""

from .login_dialog import LoginDialog
from .main_window import MainWindow
from .dashboard_view import DashboardView
from .clients_view import ClientsView
from .documents_view import DocumentsView
from .inventory_view import InventoryView
from .diary_view import DiaryView

__all__ = [
    'LoginDialog',
    'MainWindow',
    'DashboardView',
    'ClientsView',
    'DocumentsView',
    'InventoryView',
    'DiaryView'
]