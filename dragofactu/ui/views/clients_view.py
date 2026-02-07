from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ClientsView(QWidget):
    """Clients management view"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup clients UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Clients")
        title_label.setText("Clients Management")
        layout.addWidget(title_label)
        
        placeholder = QLabel("Use dragofactu_complete.py for full client management")
        layout.addWidget(placeholder)
    
    def refresh(self):
        """Refresh clients view"""
        pass