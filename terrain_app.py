import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, 
                            QStatusBar, QScrollArea, QListWidget, QFileDialog,
                            QSlider, QGroupBox, QInputDialog, QColorDialog, QMessageBox,
                            QMenu, QAction, QStyle)
from PyQt5.QtCore import Qt

# 添加当前目录和父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if (current_dir not in sys.path):
    sys.path.append(current_dir)

# 导入自定义模块
from widgets.clickable_label import ClickableLabel
from modules.image_handlers import ImageHandler
from modules.file_operations import FileOperations
from modules.zoom_controller import ZoomController
from modules.annotation_handler import AnnotationHandler

# 添加PIL检测
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 主应用类
class TerrainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置主窗口
        self.setWindowTitle("地形识别应用")
        
        # 初始化状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 初始化应用数据
        self.history = []  # 历史记录
        self.current_history_index = -1  # 当前历史记录索引
        self.image_counter = 0  # 图片编号计数器
        
        # 初始加载裁剪后的图片目录
        self.cropped_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cropped")
        if not os.path.exists(self.cropped_dir):
            os.makedirs(self.cropped_dir)
        
        # 创建模块实例 - 调整顺序，先创建image_handler和zoom_controller，再创建file_operations
        self.image_handler = ImageHandler(self)
        self.zoom_controller = ZoomController(self)
        self.file_operations = FileOperations(self)
        self.annotation_handler = AnnotationHandler(self)  # 添加标注处理器
        
        # 创建UI组件
        self.setup_ui()
        
        # 加载裁剪后的图片
        self.file_operations.load_cropped_images()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧区域 - 包含图片显示和操作按钮
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 工具栏 - 导入和裁剪按钮
        tools_layout = QHBoxLayout()
        
        # 导入图片按钮
        self.import_btn = QPushButton("导入图片")
        self.import_btn.clicked.connect(self.file_operations.import_image_action)
        tools_layout.addWidget(self.import_btn)
        
        # 添加标注按钮
        self.annotation_btn = QPushButton("标注图片")
        self.annotation_btn.clicked.connect(self.start_annotation)
        self.annotation_btn.setEnabled(False)  # 初始时禁用
        self.annotation_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        tools_layout.addWidget(self.annotation_btn)
        
        # 查看原图按钮
        self.view_original_btn = QPushButton("查看原图")
        self.view_original_btn.clicked.connect(self.image_handler.view_original_image)
        self.view_original_btn.setEnabled(False)  # 初始时禁用
        tools_layout.addWidget(self.view_original_btn)
        
        # 裁剪功能按钮
        self.crop_btn = QPushButton("开始裁剪")
        self.crop_btn.clicked.connect(self.image_handler.toggle_crop)
        self.crop_btn.setEnabled(False)
        tools_layout.addWidget(self.crop_btn)
        
        # 确认裁剪按钮
        self.confirm_crop_btn = QPushButton("确认裁剪")
        self.confirm_crop_btn.clicked.connect(self.image_handler.confirm_crop)
        self.confirm_crop_btn.setEnabled(False)
        tools_layout.addWidget(self.confirm_crop_btn)
        
        # 取消裁剪按钮
        self.cancel_crop_btn = QPushButton("取消裁剪")
        self.cancel_crop_btn.clicked.connect(self.image_handler.cancel_crop_action)
        self.cancel_crop_btn.setEnabled(False)
        tools_layout.addWidget(self.cancel_crop_btn)
        
        left_layout.addLayout(tools_layout)
        
        # 添加缩放控制组
        zoom_group = QGroupBox("图像缩放")
        zoom_layout = QHBoxLayout()
        
        # 缩小按钮
        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_controller.zoom_image(0.8))
        self.zoom_out_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        # 缩放滑块
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(int(self.zoom_controller.min_zoom * 100), int(self.zoom_controller.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_controller.zoom_factor * 100))
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(20)
        self.zoom_slider.valueChanged.connect(self.zoom_controller.slider_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        # 放大按钮
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_controller.zoom_image(1.25))
        self.zoom_in_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        # 重置缩放按钮
        self.reset_zoom_btn = QPushButton("重置")
        self.reset_zoom_btn.clicked.connect(self.zoom_controller.reset_zoom)
        self.reset_zoom_btn.setEnabled(False)
        zoom_layout.addWidget(self.reset_zoom_btn)
        
        zoom_group.setLayout(zoom_layout)
        left_layout.addWidget(zoom_group)
        
        # 图片显示区域使用QScrollArea以支持滚动和缩放
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_display = ClickableLabel("请导入图片或选择右侧裁剪后的图片")
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setMinimumSize(600, 400)
        
        # 连接鼠标事件
        self.image_display.mousePressEvent = self.image_handler.image_mouse_press_event
        self.image_display.mouseMoveEvent = self.image_handler.image_mouse_move_event
        self.image_display.mouseReleaseEvent = self.image_handler.image_mouse_release_event
        self.image_display.wheelEvent = self.zoom_controller.image_wheel_event
        
        self.scroll_area.setWidget(self.image_display)
        left_layout.addWidget(self.scroll_area)
        
        # 当前选择的图片信息
        self.image_info = QLabel("未选择图片")
        left_layout.addWidget(self.image_info)
        
        # 创建右侧区域 - 分为文件列表和标签管理两部分
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 文件列表区域
        files_group = QGroupBox("裁剪后的图片文件:")
        files_layout = QVBoxLayout(files_group)
        
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.file_operations.on_file_selected)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.file_operations.show_context_menu)
        files_layout.addWidget(self.file_list)
        
        # 文件列表按钮布局
        file_buttons_layout = QHBoxLayout()
        
        # 选择文件按钮
        select_button = QPushButton("选择图片文件")
        select_button.clicked.connect(self.file_operations.open_file_dialog)
        file_buttons_layout.addWidget(select_button)
        
        # 删除图片按钮
        delete_button = QPushButton("删除选中图片")
        delete_button.clicked.connect(self.file_operations.delete_selected_image)
        delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        file_buttons_layout.addWidget(delete_button)
        
        files_layout.addLayout(file_buttons_layout)
        right_layout.addWidget(files_group)
        
        # 标签管理区域
        labels_group = QGroupBox("标注管理")
        labels_layout = QVBoxLayout(labels_group)
        
        # 标签列表
        self.labels_list = QListWidget()
        self.labels_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labels_list.customContextMenuRequested.connect(self.show_label_context_menu)
        labels_layout.addWidget(self.labels_list)
        
        # 标签操作按钮
        label_buttons_layout = QHBoxLayout()
        
        # 添加标签按钮
        add_label_btn = QPushButton("添加标签")
        add_label_btn.clicked.connect(self.add_new_label)
        label_buttons_layout.addWidget(add_label_btn)
        
        # 删除标签按钮
        delete_label_btn = QPushButton("删除标签")
        delete_label_btn.clicked.connect(self.delete_selected_label)
        delete_label_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; }")
        label_buttons_layout.addWidget(delete_label_btn)
        
        labels_layout.addLayout(label_buttons_layout)
        labels_group.setLayout(labels_layout)
        right_layout.addWidget(labels_group)
        
        # 添加左右两个区域到主布局
        main_layout.addWidget(left_panel, 4)  # 图片显示区域占4/6
        main_layout.addWidget(right_panel, 2)  # 文件列表和标签区域占2/6
        
    # 添加标注相关功能
    def start_annotation(self):
        """开始标注图片"""
        if self.image_handler.current_image:
            self.annotation_handler.start_annotation()
            self.statusBar.showMessage("已进入标注模式，请绘制多边形标注区域")
    
    def add_new_label(self):
        """添加新的标签类型"""
        # 弹出输入对话框获取标签名称
        label_name, ok = QInputDialog.getText(self, "添加标签", "请输入标签名称:")
        if ok and label_name:
            # 选择标签颜色
            color = QColorDialog.getColor()
            if color.isValid():
                # 添加到标签列表
                self.annotation_handler.add_label(label_name, color)
                self.statusBar.showMessage(f"已添加标签: {label_name}")
    
    def delete_selected_label(self):
        """删除选中的标签"""
        selected_items = self.labels_list.selectedItems()
        if selected_items:
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除标签 {selected_items[0].text()} 吗？\n相关的标注也将被删除。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.annotation_handler.delete_label(selected_items[0].text())
    
    def show_label_context_menu(self, position):
        """显示标签的右键菜单"""
        if not self.labels_list.selectedItems():
            return
        
        menu = QMenu(self)
        
        edit_action = QAction("编辑标签", self)
        edit_action.triggered.connect(self.edit_selected_label)
        
        delete_action = QAction("删除标签", self)
        delete_action.triggered.connect(self.delete_selected_label)
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec_(self.labels_list.mapToGlobal(position))
    
    def edit_selected_label(self):
        """编辑选中的标签"""
        selected_items = self.labels_list.selectedItems()
        if selected_items:
            old_name = selected_items[0].text()
            
            # 获取新名称
            new_name, ok = QInputDialog.getText(
                self, "编辑标签", "请输入新的标签名称:", 
                text=old_name
            )
            
            if ok and new_name:
                # 选择新颜色
                color = QColorDialog.getColor()
                if color.isValid():
                    self.annotation_handler.update_label(old_name, new_name, color)
                    self.statusBar.showMessage(f"已更新标签: {old_name} → {new_name}")

# 主程序入口
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TerrainApp()
    window.resize(1200, 800)  # 设置初始窗口大小
    window.show()
    sys.exit(app.exec_())