from PyQt5.QtCore import Qt

class ZoomController:
    """处理图像缩放相关功能"""
    
    def __init__(self, app):
        """初始化缩放控制器
        
        参数:
            app: TerrainApp 实例的引用
        """
        self.app = app
        self.zoom_factor = 1.0  # 初始缩放因子
        self.min_zoom = 0.1  # 最小缩放比例
        self.max_zoom = 5.0  # 最大缩放比例
        
    def zoom_image(self, factor):
        """
        按指定比例缩放当前图像
        参数:
            factor: 缩放因子，大于1表示放大，小于1表示缩小
        """
        if not self.app.image_handler.current_image:
            return
        
        new_zoom = self.zoom_factor * factor
        
        # 确保缩放比例在范围内
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_factor = new_zoom
            
            # 更新滑块位置
            self.app.zoom_slider.setValue(int(self.zoom_factor * 100))
            
            # 应用缩放
            self.apply_zoom()
            
            # 更新状态栏
            self.app.statusBar.showMessage(f"当前缩放比例: {int(self.zoom_factor * 100)}%")
    
    def slider_zoom_changed(self, value):
        """
        响应滑块值变化，调整缩放比例
        参数:
            value: 滑块的值
        """
        if not self.app.image_handler.current_image:
            return
        
        new_zoom = value / 100.0
        
        # 只有当缩放比例真的改变时才应用
        if abs(new_zoom - self.zoom_factor) > 0.01:
            self.zoom_factor = new_zoom
            self.apply_zoom()
            self.app.statusBar.showMessage(f"当前缩放比例: {int(self.zoom_factor * 100)}%")
    
    def apply_zoom(self):
        """应用当前缩放因子到图像"""
        if self.app.image_handler.current_image:
            # 计算缩放后的尺寸
            new_width = int(self.app.image_handler.current_image.width() * self.zoom_factor)
            new_height = int(self.app.image_handler.current_image.height() * self.zoom_factor)
            
            # 确保尺寸至少为1像素
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            # 创建缩放后的图像
            scaled_image = self.app.image_handler.current_image.scaled(
                new_width, 
                new_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # 更新显示
            self.app.image_display.setPixmap(scaled_image)
            self.app.image_display.setFixedSize(new_width, new_height)
    
    def reset_zoom(self):
        """重置缩放比例为100%"""
        self.zoom_factor = 1.0
        self.app.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.apply_zoom()
        self.app.statusBar.showMessage("缩放重置为100%")
        
    def image_wheel_event(self, event):
        """
        处理鼠标滚轮事件，实现快速缩放
        参数:
            event: 滚轮事件
        """
        if not self.app.image_handler.current_image:
            return
            
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        
        # 接受事件，防止事件传递
        event.accept()
        self.zoom_image(factor)
