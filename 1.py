import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QFileDialog, QWidget, QMessageBox, 
                            QStatusBar)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QRect
import cv2

# 尝试导入PIL库，用于处理图像
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 我们不再尝试导入GDAL，而是使用PIL处理TIFF
GDAL_AVAILABLE = False

class TerrainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # 初始化裁剪相关的变量
        self.is_cropping = False
        self.crop_start_pos = None
        self.crop_end_pos = None
        self.original_pixmap = None
        self.current_pixmap = None
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('地形识别应用')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央控件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建显示图片的标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("暂无图片")
        self.image_label.setStyleSheet("QLabel{border:1px solid #ccc; background-color:#f5f5f5;}")
        self.image_label.setMinimumSize(600, 400)
        
        # 启用鼠标跟踪以便实现裁剪功能
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.image_mouse_press
        self.image_label.mouseMoveEvent = self.image_mouse_move
        self.image_label.mouseReleaseEvent = self.image_mouse_release
        
        # 创建单行按钮布局
        button_layout = QHBoxLayout()
        
        # 创建导入按钮
        import_button = QPushButton("导入图片")
        import_button.clicked.connect(self.import_image)
        import_button.setMinimumWidth(12)  # 设置最小宽度
        button_layout.addWidget(import_button)
        
        # 创建导入卫星图片按钮
        satellite_button = QPushButton("导入卫星图片")
        satellite_button.clicked.connect(self.import_satellite_image)
        satellite_button.setMinimumWidth(120)  # 设置最小宽度
        button_layout.addWidget(satellite_button)
        
        # 创建裁剪按钮，添加更明显的样式
        crop_button = QPushButton("裁剪图片")
        crop_button.clicked.connect(self.start_crop)
        crop_button.setMinimumWidth(120)  # 设置最小宽度
        crop_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(crop_button)
        
        # 创建取消裁剪按钮
        cancel_crop_button = QPushButton("取消裁剪")
        cancel_crop_button.clicked.connect(self.cancel_crop)
        cancel_crop_button.setMinimumWidth(120)  # 设置最小宽度
        button_layout.addWidget(cancel_crop_button)
        
        # 添加各部分到主布局
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(button_layout)
        
        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
    def import_image(self):
        # 打开文件对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        
        # 如果用户选择了文件
        if file_path:
            # 加载图片
            self.original_pixmap = QPixmap(file_path)
            
            # 调整图片大小以适应标签
            self.current_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 在标签中显示图片
            self.image_label.setPixmap(self.current_pixmap)
            self.reset_crop_state()
            self.statusBar.showMessage(f"已加载图片: {os.path.basename(file_path)}")
            
    def import_satellite_image(self):
        # 打开文件对话框，指定卫星图片
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择卫星图片",
            "",
            "卫星图片文件 (*.tif *.tiff *.jpg *.png);;所有文件 (*)"
        )
        
        # 如果用户选择了文件
        if file_path:
            try:
                # 检查文件扩展名
                _, ext = os.path.splitext(file_path)
                
                # 对于TIFF文件，尝试使用PIL处理
                if ext.lower() in ['.tif', '.tiff'] and PIL_AVAILABLE:
                    self.load_tiff_with_pil(file_path)
                else:
                    # 加载卫星图片
                    self.original_pixmap = QPixmap(file_path)
                    
                    # 调整图片大小以适应标签
                    self.current_pixmap = self.original_pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    
                    # 在标签中显示图片
                    self.image_label.setPixmap(self.current_pixmap)
                    self.reset_crop_state()
                    self.statusBar.showMessage(f"成功加载图片: {os.path.basename(file_path)}")
                
                # 显示成功消息
                QMessageBox.information(self, "提示", "成功导入卫星图片！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入卫星图片时出错: {str(e)}")
                self.statusBar.showMessage(f"加载失败: {str(e)}")
                
                # 如果处理失败，给出安装建议
                if not PIL_AVAILABLE:
                    QMessageBox.information(self, "提示", 
                        "要更好地处理TIFF格式图像，建议安装Pillow库:\n"
                        "pip install pillow\n\n"
                        "如果您想更全面地处理卫星影像，可以考虑安装GDAL，"
                        "但这需要更复杂的安装步骤，请参考文档。")
    
    def load_tiff_with_pil(self, file_path):
        """使用PIL库加载TIFF文件"""
        try:
            # 使用PIL打开TIFF文件
            img = Image.open(file_path)
            
            # 转换为RGB模式(如果不是)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 保存为临时PNG文件
            temp_file = os.path.join(os.path.dirname(file_path), "temp_converted.png")
            img.save(temp_file)
            
            # 用QPixmap加载PNG文件
            self.original_pixmap = QPixmap(temp_file)
            self.current_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 显示图片
            self.image_label.setPixmap(self.current_pixmap)
            self.reset_crop_state()
            self.statusBar.showMessage(f"成功加载TIFF图像: {os.path.basename(file_path)}")
            
            # 删除临时文件
            os.remove(temp_file)
        except Exception as e:
            # 如果PIL处理失败，回退到标准方法
            self.statusBar.showMessage(f"PIL处理TIFF失败，尝试标准方法: {str(e)}")
            
            # 标准加载方法
            self.original_pixmap = QPixmap(file_path)
            if self.original_pixmap.isNull():
                # 如果标准方法也失败，则直接告诉用户
                raise Exception(f"无法加载TIFF图像，请检查文件或安装支持库")
            
            self.current_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(self.current_pixmap)
            self.reset_crop_state()
    
    # 裁剪相关方法
    def start_crop(self):
        """开始裁剪模式"""
        if self.current_pixmap is not None:
            self.is_cropping = True
            self.statusBar.showMessage("请在图像上拖动选择要裁剪的区域")
    
    def cancel_crop(self):
        """取消裁剪"""
        if self.original_pixmap is not None:
            self.reset_crop_state()
            self.current_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(self.current_pixmap)
            self.statusBar.showMessage("已取消裁剪")
    
    def reset_crop_state(self):
        """重置裁剪状态"""
        self.is_cropping = False
        self.crop_start_pos = None
        self.crop_end_pos = None
    
    def image_mouse_press(self, event):
        """处理鼠标按下事件"""
        if self.is_cropping and self.current_pixmap is not None:
            self.crop_start_pos = event.pos()
    
    def image_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.is_cropping and self.crop_start_pos is not None:
            self.crop_end_pos = event.pos()
            # 绘制选择框
            self.draw_crop_rect()
    
    def image_mouse_release(self, event):
        """处理鼠标释放事件"""
        if self.is_cropping and self.crop_start_pos is not None:
            self.crop_end_pos = event.pos()
            # 执行裁剪
            self.perform_crop()
    
    def draw_crop_rect(self):
        """在图像上绘制裁剪框"""
        if self.current_pixmap is None or self.crop_start_pos is None or self.crop_end_pos is None:
            return
        
        # 创建临时pixmap用于显示
        temp_pixmap = self.current_pixmap.copy()
        painter = QPainter(temp_pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 计算矩形
        rect = QRect(self.crop_start_pos, self.crop_end_pos)
        painter.drawRect(rect)
        painter.end()
        
        # 更新显示
        self.image_label.setPixmap(temp_pixmap)
    
    def perform_crop(self):
        """执行裁剪操作"""
        if self.current_pixmap is None or self.crop_start_pos is None or self.crop_end_pos is None:
            return
        
        # 计算裁剪区域
        x1 = min(self.crop_start_pos.x(), self.crop_end_pos.x())
        y1 = min(self.crop_start_pos.y(), self.crop_end_pos.y())
        x2 = max(self.crop_start_pos.x(), self.crop_end_pos.x())
        y2 = max(self.crop_start_pos.y(), self.crop_end_pos.y())
        
        # 确保裁剪区域在图像范围内
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(self.current_pixmap.width(), x2)
        y2 = min(self.current_pixmap.height(), y2)
        
        # 计算裁剪区域的宽高
        width = x2 - x1
        height = y2 - y1
        
        if width > 0 and height > 0:
            # 在当前显示的图像上裁剪
            cropped_pixmap = self.current_pixmap.copy(x1, y1, width, height)
            
            # 更新原始图像和当前图像
            self.original_pixmap = cropped_pixmap
            self.current_pixmap = cropped_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(self.current_pixmap)
            self.statusBar.showMessage(f"已裁剪图像 ({width}x{height})")
        
        # 重置裁剪状态
        self.reset_crop_state()

if __name__ == "__main__":
    # 抑制TIFF警告的方法
    import warnings
    warnings.filterwarnings("ignore", message=".*Unknown field with tag.*")
    
    app = QApplication(sys.argv)
    window = TerrainApp()
    window.show()
    sys.exit(app.exec_())