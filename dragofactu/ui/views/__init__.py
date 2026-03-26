"""UI views and widgets"""

from .login_dialog import LoginDialog
from .main_window import MainWindow
from .dashboard_view import DashboardView
from .clients_view import ClientsView
from .products_view import ProductsView
from .suppliers_view import SuppliersView
from .documents_view import DocumentsView
from .inventory_view import InventoryView
from .diary_view import DiaryView
from .workers_parity_view import WorkersParityView
from .reminders_view import RemindersView

__all__ = [
    'LoginDialog',
    'MainWindow',
    'DashboardView',
    'ClientsView',
    'ProductsView',
    'SuppliersView',
    'DocumentsView',
    'InventoryView',
    'DiaryView',
    'WorkersParityView',
    'RemindersView'
]