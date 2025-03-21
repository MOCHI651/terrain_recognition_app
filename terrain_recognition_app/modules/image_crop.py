import os
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QRect, QSize, QPoint

# 导入自定义标签
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from widgets.clickable_label import ClickableLabel

def start_crop(app):
    """
    开始裁剪模式
    
    参数:
        app: TerrainApp实例
    """
    if app.current_pixmap is not None:
        app.is_cropping = True
        app.statusBar.showMessage("请在图像上点击要裁剪的起始位置（从该位置向右下方裁剪）")
        
def cancel_crop(app):
    """
    取消裁剪
    
    参数:
        app: TerrainApp实例
    """
    if app.original_pixmap is not None:
        reset_crop_state(app)
        app.current_pixmap = app.original_pixmap.scaled(
            app.image_label.width(),
            app.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        app.image_label.setPixmap(app.current_pixmap)
        app.statusBar.showMessage("已取消裁剪")
        
def reset_crop_state(app):
    """
    重置裁剪状态
    
    参数:
        app: TerrainApp实例
    """
    app.is_cropping = False
    app.crop_start_pos = None
    app.crop_end_pos = None

def image_mouse_press(app, event):
    """
    处理鼠标按下事件
    
    参数:
        app: TerrainApp实例
        event: 鼠标事件
    """
    if app.is_cropping and app.current_pixmap is not None:
        # 设置裁剪起始点为点击位置
        app.crop_start_pos = event.pos()
        
        # 自动计算结束点（右下角），这里设置一个固定大小的裁剪区域
        # 默认裁剪区域大小为200x200像素
        crop_width = 200
        crop_height = 200
        
        # 计算右下角坐标
        x = app.crop_start_pos.x() + crop_width
        y = app.crop_start_pos.y() + crop_height
        
        # 确保不超出图像范围
        x = min(x, app.current_pixmap.width())
        y = min(y, app.current_pixmap.height())
        
        app.crop_end_pos = QPoint(x, y)
        
        # 立即显示裁剪框
        draw_crop_rect(app)

def image_mouse_move(app, event):
    """
    处理鼠标移动事件
    
    参数:
        app: TerrainApp实例
        event: 鼠标事件
    """
    if app.is_cropping and app.crop_start_pos is not None:
        # 在移动过程中持续更新裁剪框的右下角位置
        x = event.pos().x()
        y = event.pos().y()
        
        # 确保x和y不小于起始点坐标
        x = max(x, app.crop_start_pos.x())
        y = max(y, app.crop_start_pos.y())
        
        # 确保不超出图像范围
        x = min(x, app.current_pixmap.width())
        y = min(y, app.current_pixmap.height())
        
        app.crop_end_pos = QPoint(x, y)
        
        # 绘制选择框
        draw_crop_rect(app)

def image_mouse_release(app, event):
    """
    处理鼠标释放事件
    
    参数:
        app: TerrainApp实例
        event: 鼠标事件
    """
    if app.is_cropping and app.crop_start_pos is not None:
        app.crop_end_pos = event.pos()
        # 执行裁剪
        perform_crop(app)

def draw_crop_rect(app):
    """
    在图像上绘制裁剪框
    
    参数:
        app: TerrainApp实例
    """
    if app.current_pixmap is None or app.crop_start_pos is None or app.crop_end_pos is None:
        return
    
    # 创建临时pixmap用于显示
    temp_pixmap = app.current_pixmap.copy()
    painter = QPainter(temp_pixmap)
    pen = QPen(Qt.red)
    pen.setWidth(2)
    painter.setPen(pen)
    
    # 计算矩形
    rect = QRect(app.crop_start_pos, app.crop_end_pos)
    painter.drawRect(rect)
    painter.end()
    
    # 更新显示
    app.image_label.setPixmap(temp_pixmap)

def perform_crop(app):
    """
    执行裁剪操作
    
    参数:
        app: TerrainApp实例
    """
    if app.current_pixmap is None or app.crop_start_pos is None or app.crop_end_pos is None:
        return
    
    # 计算裁剪区域
    x1 = app.crop_start_pos.x()
    y1 = app.crop_start_pos.y()
    x2 = app.crop_end_pos.x()
    y2 = app.crop_end_pos.y()
    
    # 确保裁剪区域在图像范围内
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(app.current_pixmap.width(), x2)
    y2 = min(app.current_pixmap.height(), y2)
    
    # 计算裁剪区域的宽高
    width = x2 - x1
    height = y2 - y1
    
    if width > 0 and height > 0:
        # 在当前显示的图像上裁剪
        cropped_pixmap = app.current_pixmap.copy(x1, y1, width, height)
        
        # 添加到裁剪历史
        add_to_history(app, cropped_pixmap)
        
        # 显示恢复原图的信息，而不是覆盖原图
        app.statusBar.showMessage(f"已裁剪图像 ({width}x{height}) 并添加到右侧历史列表")
        
        # 恢复原图显示（清除裁剪选择框）
        app.image_label.setPixmap(app.current_pixmap)
    
    # 重置裁剪状态
    reset_crop_state(app)

def add_to_history(app, pixmap):
    """
    添加裁剪结果到历史记录
    
    参数:
        app: TerrainApp实例
        pixmap: 要添加的裁剪图像
    """
    # 添加到历史列表
    app.crop_history.append(pixmap)
    
    # 计算在网格中的位置
    row = len(app.crop_history) - 1  # 每个条目占用一行
    
    # 创建缩略图
    thumbnail = pixmap.scaled(
        QSize(120, 120),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )
    
    # 创建一个显示缩略图的标签
    thumbnail_label = ClickableLabel()
    thumbnail_label.setPixmap(thumbnail)
    thumbnail_label.setAlignment(Qt.AlignCenter)
    thumbnail_label.setStyleSheet("QLabel { border: 1px solid #ddd; padding: 5px; }")
    thumbnail_label.setFixedSize(130, 130)
    
    # 添加点击事件处理
    index = len(app.crop_history) - 1
    thumbnail_label.clicked.connect(lambda: show_history_item(app, index))
    
    # 创建名称输入框
    name_edit = QLineEdit(f"裁剪图片 #{index+1}")
    name_edit.setMaximumWidth(120)
    name_edit.setPlaceholderText("输入图片名称")
    name_edit.textChanged.connect(lambda text: rename_history_item(app, index, text))
    
    # 创建删除按钮
    delete_button = QPushButton("删除")
    delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
    delete_button.setMaximumWidth(60)
    delete_button.clicked.connect(lambda: delete_history_item(app, index))
    
    # 创建控件容器
    item_widget = QWidget()
    item_layout = QVBoxLayout(item_widget)
    item_layout.setSpacing(5)
    
    # 添加缩略图
    item_layout.addWidget(thumbnail_label, alignment=Qt.AlignCenter)
    
    # 添加名称输入框和删除按钮的水平布局
    buttons_layout = QHBoxLayout()
    buttons_layout.addWidget(name_edit)
    buttons_layout.addWidget(delete_button)
    item_layout.addLayout(buttons_layout)
    
    # 将整个item添加到网格布局
    app.history_layout.addWidget(item_widget, row, 0)
    
    # 存储名称输入框和其他信息
    if not hasattr(app, 'crop_history_names'):
        app.crop_history_names = {}
    app.crop_history_names[index] = name_edit.text()
    
    # 更新状态栏
    app.statusBar.showMessage(f"已添加裁剪图像 #{len(app.crop_history)}")

def delete_history_item(app, index):
    """
    从历史记录中删除指定索引的图像
    
    参数:
        app: TerrainApp实例
        index: 要删除的历史图像索引
    """
    if 0 <= index < len(app.crop_history):
        # 找到要删除的Widget
        item_to_remove = app.history_layout.itemAtPosition(index, 0).widget()
        
        # 从布局中移除
        app.history_layout.removeWidget(item_to_remove)
        item_to_remove.deleteLater()
        
        # 从列表中删除
        del app.crop_history[index]
        if hasattr(app, 'crop_history_names') and index in app.crop_history_names:
            del app.crop_history_names[index]
        
        # 重新排列剩下的项
        rebuild_history_layout(app)
        
        # 更新状态栏
        app.statusBar.showMessage(f"已删除裁剪图像 #{index+1}")

def rename_history_item(app, index, new_name):
    """
    重命名历史记录中的图像
    
    参数:
        app: TerrainApp实例
        index: 历史图像索引
        new_name: 新的名称
    """
    if 0 <= index < len(app.crop_history) and hasattr(app, 'crop_history_names'):
        app.crop_history_names[index] = new_name

def rebuild_history_layout(app):
    """
    重新构建历史记录布局
    
    参数:
        app: TerrainApp实例
    """
    # 临时存储所有裁剪历史
    temp_history = app.crop_history.copy()
    temp_names = {}
    if hasattr(app, 'crop_history_names'):
        temp_names = app.crop_history_names.copy()
    
    # 清除历史记录
    app.crop_history = []
    if hasattr(app, 'crop_history_names'):
        app.crop_history_names = {}
    
    # 清除布局中的所有小部件
    while app.history_layout.count():
        item = app.history_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    
    # 重新添加所有项目
    for i, pixmap in enumerate(temp_history):
        name = f"裁剪图片 #{i+1}"  # 默认名称
        if i in temp_names:
            name = temp_names[i]
        
        # 添加到历史记录
        app.crop_history.append(pixmap)
        if not hasattr(app, 'crop_history_names'):
            app.crop_history_names = {}
        app.crop_history_names[i] = name
        
        # 创建并添加UI元素
        add_history_item_ui(app, i, pixmap, name)

def add_history_item_ui(app, index, pixmap, name):
    """
    为历史记录添加UI元素
    
    参数:
        app: TerrainApp实例
        index: 索引
        pixmap: 图像
        name: 名称
    """
    # 创建缩略图
    thumbnail = pixmap.scaled(
        QSize(120, 120),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )
    
    # 创建一个显示缩略图的标签
    thumbnail_label = ClickableLabel()
    thumbnail_label.setPixmap(thumbnail)
    thumbnail_label.setAlignment(Qt.AlignCenter)
    thumbnail_label.setStyleSheet("QLabel { border: 1px solid #ddd; padding: 5px; }")
    thumbnail_label.setFixedSize(130, 130)
    thumbnail_label.clicked.connect(lambda: show_history_item(app, index))
    
    # 创建名称输入框
    name_edit = QLineEdit(name)
    name_edit.setMaximumWidth(120)
    name_edit.setPlaceholderText("输入图片名称")
    name_edit.textChanged.connect(lambda text: rename_history_item(app, index, text))
    
    # 创建删除按钮
    delete_button = QPushButton("删除")
    delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
    delete_button.setMaximumWidth(60)
    delete_button.clicked.connect(lambda: delete_history_item(app, index))
    
    # 创建控件容器
    item_widget = QWidget()
    item_layout = QVBoxLayout(item_widget)
    item_layout.setSpacing(5)
    
    # 添加缩略图
    item_layout.addWidget(thumbnail_label, alignment=Qt.AlignCenter)
    
    # 添加名称输入框和删除按钮的水平布局
    buttons_layout = QHBoxLayout()
    buttons_layout.addWidget(name_edit)
    buttons_layout.addWidget(delete_button)
    item_layout.addLayout(buttons_layout)
    
    # 将整个item添加到网格布局
    app.history_layout.addWidget(item_widget, index, 0)

def show_history_item(app, index):
    """
    显示历史中指定索引的图像
    
    参数:
        app: TerrainApp实例
        index: 历史图像索引
    """
    if 0 <= index < len(app.crop_history):
        # 获取历史图像
        selected_pixmap = app.crop_history[index]
        
        # 更新当前显示的图像
        app.current_pixmap = selected_pixmap.scaled(
            app.image_label.width(),
            app.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        app.image_label.setPixmap(app.current_pixmap)
        
        # 更新状态栏
        app.statusBar.showMessage(f"显示历史裁剪图像 #{index+1}")

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor

def start_crop(self):
    """开始裁剪操作的占位函数"""
    pass

def cancel_crop(self):
    """取消裁剪操作的占位函数"""
    pass

def reset_crop_state(self):
    """重置裁剪状态的占位函数"""
    pass

def image_mouse_press(self, event):
    """图像鼠标按下事件的占位函数"""
    pass

def image_mouse_move(self, event):
    """图像鼠标移动事件的占位函数"""
    pass

def image_mouse_release(self, event):
    """图像鼠标释放事件的占位函数"""
    pass

def draw_crop_rect(self, image, rect):
    """绘制裁剪矩形的占位函数"""
    pass

def perform_crop(self, image, rect):
    """执行裁剪的占位函数"""
    pass

def add_to_history(self, image):
    """添加到历史记录的占位函数"""
    pass

def show_history_item(self, index):
    """显示历史记录项的占位函数"""
    pass
