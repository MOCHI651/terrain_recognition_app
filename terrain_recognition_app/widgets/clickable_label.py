from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSignal, Qt

class ClickableLabel(QLabel):
    """可点击的标签控件，用于显示图像并响应鼠标事件"""
    
    clicked = pyqtSignal()  # 点击信号
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        
    def mousePressEvent(self, event):
        # 默认实现，将被重写
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        # 默认实现，将被重写
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        # 默认实现，将被重写
        super().mouseMoveEvent(event)
        
    def wheelEvent(self, event):
        # 默认实现，将被重写
        super().wheelEvent(event)
