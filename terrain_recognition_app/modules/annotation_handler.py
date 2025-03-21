import os
import json
from PyQt5.QtCore import Qt, QPointF, QEvent  # 添加QEvent导入
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt5.QtWidgets import QListWidgetItem, QInputDialog, QMessageBox

class AnnotationHandler:
    """处理图像标注相关操作的类"""
    
    def __init__(self, app):
        """初始化标注处理器
        
        参数:
            app: TerrainApp 实例的引用
        """
        self.app = app
        self.annotating = False
        self.current_polygon = []
        self.polygons = []  # 多边形列表，每个元素为 (points, label, color)
        self.labels = {}  # 标签字典 {label_name: color}
        self.current_label = None
        
        # 创建标注数据目录
        self.annotations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "annotations")
        if not os.path.exists(self.annotations_dir):
            os.makedirs(self.annotations_dir)
        
        # 加载已有标签
        self.load_labels()
    
    def start_annotation(self):
        """开始标注模式"""
        if not self.app.image_handler.current_image:
            return
        
        if not self.labels:
            reply = QMessageBox.question(
                self.app,
                "没有标签",
                "还没有创建任何标签。是否现在创建？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.app.add_new_label()
            return
            
        # 选择要使用的标签
        if self.labels:
            label_name, ok = QInputDialog.getItem(
                self.app, 
                "选择标签", 
                "请选择标注类型:", 
                list(self.labels.keys()), 
                0, 
                False
            )
            if ok and label_name:
                self.current_label = label_name
                self.annotating = True
                self.current_polygon = []
                
                # 替换鼠标事件处理器
                self.original_press_event = self.app.image_display.mousePressEvent
                self.original_move_event = self.app.image_display.mouseMoveEvent
                self.original_release_event = self.app.image_display.mouseReleaseEvent
                
                self.app.image_display.mousePressEvent = self.annotation_mouse_press
                self.app.image_display.mouseMoveEvent = self.annotation_mouse_move
                self.app.image_display.mouseReleaseEvent = self.annotation_mouse_release
                
                # 更新UI
                self.app.statusBar.showMessage(f"正在使用 '{label_name}' 标签进行标注，单击添加点，双击完成当前多边形")
                
                # 禁用一些按钮
                self.app.crop_btn.setEnabled(False)
                self.app.annotation_btn.setText("完成标注")
                self.app.annotation_btn.clicked.disconnect()
                self.app.annotation_btn.clicked.connect(self.finish_annotation)
    
    def finish_annotation(self):
        """完成标注模式"""
        self.annotating = False
        
        # 恢复原始鼠标事件
        if hasattr(self, 'original_press_event'):
            self.app.image_display.mousePressEvent = self.original_press_event
            self.app.image_display.mouseMoveEvent = self.original_move_event
            self.app.image_display.mouseReleaseEvent = self.original_release_event
        
        # 保存标注
        if self.app.current_file_path:
            self.save_annotations(self.app.current_file_path)
        
        # 更新UI
        self.app.statusBar.showMessage("已完成标注")
        self.app.crop_btn.setEnabled(True)
        self.app.annotation_btn.setText("标注图片")
        self.app.annotation_btn.clicked.disconnect()
        self.app.annotation_btn.clicked.connect(self.app.start_annotation)
    
    def annotation_mouse_press(self, event):
        """标注模式下的鼠标按下事件"""
        if not self.annotating or not self.current_label:
            return
            
        pos = self.app.image_handler.get_image_position(event.pos())
        if pos:
            # 双击完成多边形
            if event.type() == QEvent.MouseButtonDblClick:  # 修改这里，使用QEvent.MouseButtonDblClick
                if len(self.current_polygon) >= 3:  # 至少需要3个点
                    # 添加到多边形列表
                    self.polygons.append((
                        self.current_polygon.copy(), 
                        self.current_label,
                        self.labels[self.current_label]
                    ))
                    self.current_polygon = []
                    self.draw_annotations()
                    self.app.statusBar.showMessage(f"多边形已添加，可以继续标注或点击'完成标注'")
            else:
                # 添加点
                self.current_polygon.append((pos.x(), pos.y()))
                self.draw_annotations()
    
    def annotation_mouse_move(self, event):
        """标注模式下的鼠标移动事件"""
        if self.annotating and self.current_polygon:
            # 在临时多边形上显示当前鼠标位置
            pos = self.app.image_handler.get_image_position(event.pos())
            if pos:
                temp_polygon = self.current_polygon.copy()
                temp_polygon.append((pos.x(), pos.y()))
                self.draw_annotations(temp_polygon)
    
    def annotation_mouse_release(self, event):
        """标注模式下的鼠标释放事件"""
        pass  # 不需要特殊处理
    
    def draw_annotations(self, temp_polygon=None):
        """绘制所有标注"""
        if not self.app.image_handler.current_image:
            return
            
        # 创建临时画布
        pixmap = self.app.image_handler.backup_image.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制已保存的多边形
        for points, label, color in self.polygons:
            poly = QPolygonF([QPointF(x, y) for x, y in points])
            
            # 设置半透明填充
            fill_color = QColor(color)
            fill_color.setAlpha(50)  # 20% 透明度
            painter.setBrush(QBrush(fill_color))
            
            # 设置边框
            pen = QPen(QColor(color))
            pen.setWidth(2)
            painter.setPen(pen)
            
            # 绘制多边形
            painter.drawPolygon(poly)
            
            # 绘制标签文字
            text_pen = QPen(Qt.black)
            painter.setPen(text_pen)
            painter.drawText(QPointF(points[0][0], points[0][1] - 5), label)
        
        # 绘制当前正在创建的多边形
        if self.current_polygon:
            points = self.current_polygon
            if temp_polygon:
                points = temp_polygon
                
            # 绘制线段
            pen = QPen(QColor(self.labels.get(self.current_label, "#FF0000")))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                painter.drawLine(
                    QPointF(points[i][0], points[i][1]),
                    QPointF(points[i+1][0], points[i+1][1])
                )
            
            # 如果是临时多边形，绘制回到起点的线
            if temp_polygon and len(points) > 2:
                painter.drawLine(
                    QPointF(points[-1][0], points[-1][1]),
                    QPointF(points[0][0], points[0][1])
                )
            
            # 绘制点
            point_pen = QPen(Qt.red)
            painter.setPen(point_pen)
            for x, y in points:
                painter.drawEllipse(QPointF(x, y), 3, 3)
        
        painter.end()
        
        # 显示标注后的图像
        self.app.image_handler.display_image(pixmap)
    
    def load_annotations(self, image_path):
        """加载图像的标注数据"""
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        anno_path = os.path.join(self.annotations_dir, f"{base_name}.json")
        
        if os.path.exists(anno_path):
            try:
                with open(anno_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.polygons = []
                for poly in data.get('polygons', []):
                    points = poly.get('points', [])
                    label = poly.get('label', 'unknown')
                    color = poly.get('color', '#FF0000')
                    
                    if points and label:
                        self.polygons.append((points, label, color))
                
                # 更新显示
                self.draw_annotations()
                return True
            except Exception as e:
                print(f"加载标注出错: {str(e)}")
        
        return False
    
    def save_annotations(self, image_path):
        """保存标注数据"""
        if not self.polygons:
            return
            
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        anno_path = os.path.join(self.annotations_dir, f"{base_name}.json")
        
        try:
            data = {
                'image': os.path.basename(image_path),
                'polygons': []
            }
            
            for points, label, color in self.polygons:
                data['polygons'].append({
                    'points': points,
                    'label': label,
                    'color': color
                })
            
            with open(anno_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.app.statusBar.showMessage(f"标注已保存到 {anno_path}")
            return True
        except Exception as e:
            self.app.statusBar.showMessage(f"保存标注出错: {str(e)}")
            return False
    
    def add_label(self, name, color):
        """添加新标签"""
        if name in self.labels:
            return False
            
        # 添加到标签字典
        self.labels[name] = color.name()
        
        # 添加到UI列表
        item = QListWidgetItem(name)
        item.setBackground(color)
        # 根据颜色亮度选择文本颜色
        if color.lightness() < 128:
            item.setForeground(Qt.white)
        self.app.labels_list.addItem(item)
        
        # 保存标签
        self.save_labels()
        
        # 如果还没有选中标签，设为当前标签
        if self.current_label is None:
            self.current_label = name
        
        return True
    
    def delete_label(self, name):
        """删除标签"""
        if name not in self.labels:
            return False
            
        # 从字典中删除
        del self.labels[name]
        
        # 从UI列表中删除
        for i in range(self.app.labels_list.count()):
            if self.app.labels_list.item(i).text() == name:
                self.app.labels_list.takeItem(i)
                break
        
        # 从多边形中删除相关标注
        self.polygons = [(p, l, c) for p, l, c in self.polygons if l != name]
        
        # 更新显示
        self.draw_annotations()
        
        # 保存标签
        self.save_labels()
        
        # 如果是当前标签，重置
        if self.current_label == name:
            self.current_label = None if not self.labels else list(self.labels.keys())[0]
        
        return True
    
    def update_label(self, old_name, new_name, color):
        """更新标签"""
        if old_name not in self.labels:
            return False
            
        # 更新字典
        self.labels[new_name] = color.name()
        if old_name != new_name:
            del self.labels[old_name]
        
        # 更新UI列表
        for i in range(self.app.labels_list.count()):
            if self.app.labels_list.item(i).text() == old_name:
                item = self.app.labels_list.item(i)
                item.setText(new_name)
                item.setBackground(color)
                if color.lightness() < 128:
                    item.setForeground(Qt.white)
                else:
                    item.setForeground(Qt.black)
                break
        
        # 更新多边形中的标签
        for i, (points, label, _) in enumerate(self.polygons):
            if label == old_name:
                self.polygons[i] = (points, new_name, color.name())
        
        # 更新显示
        self.draw_annotations()
        
        # 保存标签
        self.save_labels()
        
        # 更新当前标签
        if self.current_label == old_name:
            self.current_label = new_name
        
        return True
    
    def save_labels(self):
        """保存标签到文件"""
        labels_path = os.path.join(self.annotations_dir, "labels.json")
        try:
            with open(labels_path, 'w', encoding='utf-8') as f:
                json.dump(self.labels, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存标签出错: {str(e)}")
            return False
    
    def load_labels(self):
        """从文件加载标签"""
        labels_path = os.path.join(self.annotations_dir, "labels.json")
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r', encoding='utf-8') as f:
                    self.labels = json.load(f)
                
                # 更新UI列表
                self.app.labels_list.clear()
                for name, color_str in self.labels.items():
                    item = QListWidgetItem(name)
                    color = QColor(color_str)
                    item.setBackground(color)
                    if color.lightness() < 128:
                        item.setForeground(Qt.white)
                    self.app.labels_list.addItem(item)
                
                return True
            except Exception as e:
                print(f"加载标签出错: {str(e)}")
        
        return False
