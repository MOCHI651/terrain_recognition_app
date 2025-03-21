import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class FileOperations:
    """处理文件相关操作，包括导入、保存和管理文件"""
    
    def __init__(self, app):
        """初始化文件操作处理器
        
        参数:
            app: TerrainApp 实例的引用
        """
        self.app = app
        # 使用主应用中定义的裁剪目录路径
        self.cropped_dir = self.app.cropped_dir
    
    def import_image_action(self):
        """导入图片按钮的动作"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.app,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;所有文件 (*)"
        )
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):
        """加载图片"""
        try:
            # 显示正在加载提示
            self.app.statusBar.showMessage(f"正在加载 {os.path.basename(file_path)}，请稍候...")
            self.app.image_display.setText("正在加载图片，请稍候...")
            # 刷新UI确保提示立即可见
            self.app.statusBar.repaint()
            self.app.image_display.repaint()
            
            # 根据文件类型调用不同的加载函数
            if file_path.lower().endswith(('.tif', '.tiff')):
                from modules.image_import import load_geotiff_with_gdal, load_tiff_image, GDAL_AVAILABLE
                
                # 优先使用GDAL库加载GeoTIFF文件
                if GDAL_AVAILABLE:
                    try:
                        pixmap = load_geotiff_with_gdal(file_path)
                        self.app.statusBar.showMessage("使用GDAL库成功加载GeoTIFF文件")
                    except Exception as e:
                        self.app.statusBar.showMessage(f"GDAL加载失败，尝试备选方法: {str(e)}")
                        # 如果GDAL失败，回退到PIL方法
                        pixmap = load_tiff_image(file_path)
                else:
                    # GDAL不可用时使用PIL
                    pixmap = load_tiff_image(file_path)
            else:
                pixmap = QPixmap(file_path)
                
            if not pixmap.isNull():
                self.app.original_file_path = file_path  # 保存原始文件路径
                self.app.image_handler.display_image(pixmap)
                
                # 初始化备份图像
                self.app.image_handler.backup_image = pixmap.copy()
                
                # 更新状态和按钮
                self.app.statusBar.showMessage(f"已加载图片: {os.path.basename(file_path)}")
                self.app.image_info.setText(
                    f"图片: {os.path.basename(file_path)} | 尺寸: {pixmap.width()}x{pixmap.height()}"
                )
                self.app.crop_btn.setEnabled(True)
                self.app.view_original_btn.setEnabled(True)  # 启用查看原图按钮
                
                # 重置裁剪状态
                self.app.image_handler.reset_crop_state()
                self.app.image_handler.original_image = pixmap
                
                # 启用缩放控件
                self.app.zoom_in_btn.setEnabled(True)
                self.app.zoom_out_btn.setEnabled(True)
                self.app.reset_zoom_btn.setEnabled(True)
                self.app.zoom_controller.reset_zoom()  # 重置缩放比例
            else:
                self.app.image_display.setText("无法加载图片")
        except Exception as e:
            self.app.statusBar.showMessage(f"加载图片出错: {str(e)}")
            self.app.image_display.setText(f"加载图片出错: {str(e)}")
    
    def load_cropped_images(self):
        """加载裁剪后的图片文件列表"""
        if not os.path.exists(self.cropped_dir):
            return
        # 清空现有列表
        self.app.file_list.clear()
        # 重置计数器，我们将根据实际文件重新计算
        max_counter = 0  # 使用局部变量记录最大编号
        # 获取所有图片文件并排序
        image_files = [f for f in os.listdir(self.cropped_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
        # 添加到列表，并使用更友好的显示名称
        for i, file_name in enumerate(sorted(image_files)):
            # 提取数字编号
            counter = i + 1  # 默认按顺序编号
            # 尝试从文件名中提取实际编号
            if file_name.startswith("image_crop_"):
                try:
                    parts = file_name.split('_')
                    if len(parts) > 2:
                        num = int(parts[2].split('_')[0])  # 从"image_crop_X"中提取X
                        counter = num
                        max_counter = max(max_counter, counter)
                except:
                    pass
            # 创建显示名称
            display_name = f"裁剪图片 {counter}"
            self.app.file_list.addItem(display_name)
            self.app.file_list.item(self.app.file_list.count() - 1).setData(
                Qt.UserRole, os.path.join(self.cropped_dir, file_name))
            self.app.file_list.item(self.app.file_list.count() - 1).setToolTip(file_name)
        # 更新计数器为最大值，避免引用可能不存在的counter变量
        self.app.image_counter = max_counter

    def open_file_dialog(self):
        """打开文件选择对话框"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.app,
            "选择裁剪后的图片文件",
            self.cropped_dir if os.path.exists(self.cropped_dir) else "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        # 将所选文件添加到列表
        for path in file_paths:
            file_name = os.path.basename(path)
            item = self.app.file_list.findItems(file_name, Qt.MatchExactly)
            if not item:  # 避免重复添加
                self.app.file_list.addItem(file_name)
                # 存储完整路径作为item的数据
                self.app.file_list.item(self.app.file_list.count() - 1).setData(Qt.UserRole, path)

    def on_file_selected(self, item):
        """当文件列表中的文件被选中时显示图片"""
        file_path = item.data(Qt.UserRole)
        if not file_path:
            # 如果路径不存在，尝试从裁剪目录构建路径
            file_name = item.text()
            file_path = os.path.join(self.cropped_dir, file_name)
        
        if file_path and os.path.exists(file_path):
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # 更新当前图像
                    self.app.image_handler.current_image = pixmap
                    # 初始化备份图像
                    self.app.image_handler.backup_image = pixmap.copy()
                    
                    # 保持原始尺寸比例调整图像大小
                    display_size = self.app.image_display.size()
                    scaled_pixmap = pixmap.scaled(
                        display_size, 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.app.image_display.setPixmap(scaled_pixmap)
                    
                    # 更新图片信息 - 使用显示名称而不是文件名
                    display_name = item.text()
                    self.app.image_info.setText(f"图片: {display_name} | "
                                          f"尺寸: {pixmap.width()}x{pixmap.height()}")
                    
                    # 启用裁剪和标注按钮
                    self.app.crop_btn.setEnabled(True)
                    self.app.annotation_btn.setEnabled(True)  # 启用标注按钮
                    
                    # 启用缩放控件和重置缩放
                    self.app.zoom_in_btn.setEnabled(True)
                    self.app.zoom_out_btn.setEnabled(True)
                    self.app.reset_zoom_btn.setEnabled(True)
                    self.app.zoom_controller.reset_zoom()  # 重置缩放比例
                    
                    # 保存当前显示的文件路径，用于删除功能
                    self.app.current_file_path = file_path
                    
                    # 加载标注数据
                    self.app.annotation_handler.load_annotations(file_path)
                else:
                    self.app.image_display.setText("无法加载图片")
                    self.app.image_info.setText(f"无法加载: {file_path}")
            except Exception as e:
                self.app.image_display.setText(f"加载图片出错: {str(e)}")
                self.app.image_info.setText(f"错误: {file_path}")
        else:
            self.app.image_display.setText("图片文件不存在")
            self.app.image_info.setText(f"文件不存在: {file_path}")
            
    def view_selected_image(self):
        """查看选中的图片"""
        selected_items = self.app.file_list.selectedItems()
        if selected_items:
            self.on_file_selected(selected_items[0])

    def delete_selected_image(self):
        """删除选中的图片"""
        selected_items = self.app.file_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self.app, "提示", "请先选择要删除的图片")
            return
            
        # 获取所选图片的路径
        selected_item = selected_items[0]
        file_path = selected_item.data(Qt.UserRole)
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self.app, "错误", "无法找到选中的图片文件")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self.app, 
            "确认删除", 
            f"确定要删除图片 {selected_item.text()} 吗？\n此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从磁盘删除文件
                os.remove(file_path)
                
                # 从列表中移除项
                row = self.app.file_list.row(selected_item)
                self.app.file_list.takeItem(row)
                
                # 提示删除成功
                self.app.statusBar.showMessage(f"已删除图片: {selected_item.text()}")
                
                # 如果当前显示的是被删除的图片，清除显示
                if hasattr(self.app, 'current_file_path') and self.app.current_file_path == file_path:
                    self.app.image_display.setText("请选择或导入图片")
                    self.app.image_info.setText("未选择图片")
                    self.app.image_handler.current_image = None
                    self.app.crop_btn.setEnabled(False)
                    
            except Exception as e:
                QMessageBox.warning(self.app, "删除失败", f"删除图片时出错: {str(e)}")
                
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 检查是否有选中的项
        if not self.app.file_list.selectedItems():
            return
            
        # 创建菜单
        from PyQt5.QtWidgets import QMenu, QAction, QStyle
        context_menu = QMenu(self.app)
        
        # 添加菜单项
        view_action = QAction("查看图片", self.app)
        view_action.triggered.connect(self.view_selected_image)
        
        delete_action = QAction("删除图片", self.app)
        delete_action.triggered.connect(self.delete_selected_image)
        delete_action.setIcon(self.app.style().standardIcon(QStyle.SP_TrashIcon))
        
        context_menu.addAction(view_action)
        context_menu.addAction(delete_action)
        
        # 显示菜单
        context_menu.exec_(self.app.file_list.mapToGlobal(position))
