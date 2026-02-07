from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DocumentsView(QWidget):
    """Documents management view"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup documents UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Documents")
        title_label.setText("Documents Management")
        layout.addWidget(title_label)
        
        placeholder = QLabel("Use dragofactu_complete.py for full document management")
        layout.addWidget(placeholder)
    
    def refresh(self):
        """Refresh documents view"""
        pass