import os
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor

class ImageHandler:
    """处理图像相关操作的类，包括裁剪、显示等功能"""
    
    def __init__(self, app):
        """初始化图像处理器
        
        参数:
            app: TerrainApp 实例的引用
        """
        self.app = app
        # 初始化图像相关变量
        self.current_image = None
        self.backup_image = None
        self.original_image = None
        self.cropping = False
        self.crop_start_pos = None
        self.crop_rect = None
        
    def display_image(self, pixmap):
        """在显示区域显示图片，考虑当前的缩放比例"""
        if pixmap:
            self.current_image = pixmap
            # 应用当前缩放
            self.app.zoom_controller.apply_zoom()
        else:
            self.app.image_display.setText("无图像可显示")
    
    def view_original_image(self):
        """查看原始图片"""
        if self.original_image:
            # 存储当前状态
            self.temp_current_image = self.current_image
            self.temp_crop_state = self.cropping
            
            # 显示原始图片
            self.current_image = self.original_image  # 确保当前图像指向原图
            self.display_image(self.original_image)
            
            # 更新状态栏和信息
            self.app.statusBar.showMessage("正在查看原始图片 - 可以进行裁剪或点击'恢复当前'返回")
            self.app.image_info.setText(
                f"原始图片: {os.path.basename(getattr(self.app, 'original_file_path', '未知'))} | "
                f"尺寸: {self.original_image.width()}x{self.original_image.height()}"
            )
            
            # 修改按钮为恢复按钮
            self.app.view_original_btn.setText("恢复当前")
            self.app.view_original_btn.clicked.disconnect()
            self.app.view_original_btn.clicked.connect(self.restore_current_image)
            
            # 确保裁剪按钮可用（在原图上进行裁剪）
            self.app.crop_btn.setEnabled(True)
            
            # 如果已经在裁剪模式，重置以确保正确应用到原图
            if self.cropping:
                self.cancel_crop_action()
                self.reset_crop_state()
    
    def restore_current_image(self):
        """从查看原图状态恢复到当前图片状态"""
        if hasattr(self, 'temp_current_image') and self.temp_current_image:
            # 恢复当前图片
            self.current_image = self.temp_current_image
            self.display_image(self.temp_current_image)
            
            # 恢复状态
            self.app.statusBar.showMessage("已恢复到当前编辑状态")
            
            self.app.view_original_btn.setText("查看原图")
            self.app.view_original_btn.clicked.disconnect()
            self.app.view_original_btn.clicked.connect(self.view_original_image)
            
            # 如果当前在裁剪模式，取消裁剪
            if self.cropping:
                self.cancel_crop_action()
            
            # 恢复裁剪按钮状态
            self.app.crop_btn.setEnabled(True)
            
            # 清理临时变量
            delattr(self, 'temp_current_image')
            if hasattr(self, 'temp_crop_state'):
                delattr(self, 'temp_crop_state')

    def toggle_crop(self):
        """切换裁剪模式"""
        if not self.cropping:
            self.start_crop_action()
        else:
            self.cancel_crop_action()

    def start_crop_action(self):
        """开始裁剪"""
        if self.current_image:
            self.backup_image = self.current_image.copy()  # 保存当前图像的副本
            self.cropping = True
            self.app.statusBar.showMessage("请在图片上拖动以选择裁剪区域")
            self.app.confirm_crop_btn.setEnabled(True)
            self.app.cancel_crop_btn.setEnabled(True)
        else:
            self.app.statusBar.showMessage("没有可裁剪的图像")

    def cancel_crop_action(self):
        """取消裁剪"""
        self.cropping = False
        self.reset_crop_state()
        self.app.confirm_crop_btn.setEnabled(False)
        self.app.cancel_crop_btn.setEnabled(False)
        self.app.statusBar.showMessage("已取消裁剪")

    def confirm_crop(self):
        """确认裁剪"""
        if self.crop_rect and self.current_image:
            try:
                # 使用backup_image（原始图像）而不是可能包含遮罩的current_image
                cropped_pixmap = self.backup_image.copy(self.crop_rect)
                # 递增图片计数器
                self.app.image_counter += 1
                # 使用新命名格式保存裁剪后的图片
                image_name = f"image_crop_{self.app.image_counter}"
                timestamp = os.path.basename(str(os.times())).replace(".", "_")
                # 如果当前正在原图上裁剪，可以在文件名中添加标记(但用户看不见此标记)
                if self.current_image == self.original_image:
                    save_path = os.path.join(self.app.cropped_dir, f"{image_name}_original_{timestamp}.png")
                else:
                    save_path = os.path.join(self.app.cropped_dir, f"{image_name}_{timestamp}.png")
                cropped_pixmap.save(save_path)
                # 显示裁剪后的图片
                self.current_image = cropped_pixmap
                self.display_image(cropped_pixmap)
                # 更新状态
                self.app.statusBar.showMessage(f"裁剪成功，已保存为: {image_name}")
                self.app.image_info.setText(
                    f"裁剪后图片: {image_name} | "
                    f"尺寸: {cropped_pixmap.width()}x{cropped_pixmap.height()}"
                )
                self.add_to_history(cropped_pixmap)
                # 刷新文件列表
                self.app.file_operations.load_cropped_images()
                # 判断之前是否在原图模式
                if hasattr(self, 'temp_current_image'):
                    # 之前在原图模式，恢复"查看原图"按钮
                    self.app.view_original_btn.setText("查看原图")
                    self.app.view_original_btn.clicked.disconnect()
                    self.app.view_original_btn.clicked.connect(self.view_original_image)
                    # 清理临时变量
                    delattr(self, 'temp_current_image')
                    if hasattr(self, 'temp_crop_state'):
                        delattr(self, 'temp_crop_state')
            except Exception as e:
                self.app.statusBar.showMessage(f"裁剪出错: {str(e)}")
            # 重置裁剪状态
            self.reset_crop_state()

    def reset_crop_state(self):
        """重置裁剪状态"""
        self.crop_rect = None
        self.cropping = False
        self.app.confirm_crop_btn.setEnabled(False)
        self.app.cancel_crop_btn.setEnabled(False)

    def add_to_history(self, pixmap):
        """添加到历史记录"""
        # 清除当前位置之后的历史
        if self.app.current_history_index < len(self.app.history) - 1:
            self.app.history = self.app.history[:self.app.current_history_index + 1]
        # 添加到历史
        self.app.history.append(pixmap)
        self.app.current_history_index = len(self.app.history) - 1
        
    def image_mouse_press_event(self, event):
        """鼠标按下事件"""
        if self.cropping and self.current_image:
            # 获取相对于图像的坐标
            pos = self.get_image_position(event.pos())
            if pos:
                self.crop_start_pos = pos
                self.app.statusBar.showMessage("正在选择裁剪区域...")

    def image_mouse_move_event(self, event):
        """鼠标移动事件"""
        if self.cropping and self.crop_start_pos and self.current_image:
            # 获取相对于图像的坐标
            pos = self.get_image_position(event.pos())
            if pos:
                # 计算裁剪矩形
                x = min(self.crop_start_pos.x(), pos.x())
                y = min(self.crop_start_pos.y(), pos.y())
                width = abs(pos.x() - self.crop_start_pos.x())
                height = abs(pos.y() - self.crop_start_pos.y())
                self.crop_rect = QRect(x, y, width, height)
                # 在图像上绘制裁剪矩形
                self.draw_crop_rect()

    def image_mouse_release_event(self, event):
        """鼠标释放事件"""
        if self.cropping and self.crop_start_pos and self.current_image:
            # 获取相对于图像的坐标
            pos = self.get_image_position(event.pos())
            if pos:
                # 计算最终的裁剪矩形
                x = min(self.crop_start_pos.x(), pos.x())
                y = min(self.crop_start_pos.y(), pos.y())
                width = abs(pos.x() - self.crop_start_pos.x())
                height = abs(pos.y() - self.crop_start_pos.y())
                self.crop_rect = QRect(x, y, width, height)
                # 在图像上绘制最终的裁剪矩形
                self.draw_crop_rect()
                self.app.statusBar.showMessage(
                    f"已选择裁剪区域: ({x},{y},{width},{height})，点击'确认裁剪'完成裁剪"
                )

    def get_image_position(self, pos):
        """获取相对于图像的位置，考虑缩放因子"""
        if not self.app.image_display.pixmap():
            return None
        # 由于图像可能已经缩放，我们需要将鼠标位置映射回原始图像坐标
        original_x = int(pos.x() / self.app.zoom_controller.zoom_factor)
        original_y = int(pos.y() / self.app.zoom_controller.zoom_factor)
        # 确保坐标在原始图像范围内
        if 0 <= original_x < self.current_image.width() and 0 <= original_y < self.current_image.height():
            return QPoint(original_x, original_y)
        return None

    def draw_crop_rect(self):
        """在图像上绘制裁剪矩形，裁剪区域内保持原图像，区域外添加半透明遮罩"""
        if self.backup_image and self.crop_rect:
            # 创建临时画布
            temp_pixmap = self.backup_image.copy()
            painter = QPainter(temp_pixmap)
            # 创建半透明遮罩颜色
            mask_color = QColor(0, 0, 0, 128)  # 黑色，50%透明度
            # 设置画笔用于绘制矩形边框
            pen = QPen(Qt.red)
            pen.setWidth(2)
            painter.setPen(pen)
            # 保存当前画家状态
            painter.save()
            # 获取裁剪区域外的四个矩形区域
            left = QRect(0, 0, self.crop_rect.left(), temp_pixmap.height())
            top = QRect(self.crop_rect.left(), 0, self.crop_rect.width(), self.crop_rect.top())
            right = QRect(self.crop_rect.right(), 0, temp_pixmap.width() - self.crop_rect.right(), temp_pixmap.height())
            bottom = QRect(self.crop_rect.left(), self.crop_rect.bottom(), self.crop_rect.width(), temp_pixmap.height() - self.crop_rect.bottom())
            # 只在裁剪区域外绘制半透明遮罩
            painter.fillRect(left, mask_color)
            painter.fillRect(top, mask_color)
            painter.fillRect(right, mask_color)
            painter.fillRect(bottom, mask_color)
            # 恢复画家状态
            painter.restore()
            # 绘制裁剪区域边框
            painter.drawRect(self.crop_rect)
            painter.end()
            self.display_image(temp_pixmap)
