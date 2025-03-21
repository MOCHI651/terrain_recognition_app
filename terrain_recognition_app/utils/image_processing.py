import os
from PyQt5.QtGui import QPixmap

# 尝试导入PIL库，用于处理图像
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 是否尝试使用GDAL
GDAL_AVAILABLE = False

def load_image_with_pil(file_path):
    """
    使用PIL库加载图像文件，特别是对TIFF格式的支持
    
    参数:
        file_path: 图像文件路径
    
    返回:
        (pixmap, temp_file): 加载好的QPixmap对象和临时文件路径(如果有的话)
    """
    if not PIL_AVAILABLE:
        raise ImportError("未安装PIL库，无法进行高级图像处理")
        
    # 使用PIL打开图像文件
    img = Image.open(file_path)
    
    # 转换为RGB模式(如果不是)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 保存为临时PNG文件
    temp_file = os.path.join(os.path.dirname(file_path), "temp_converted.png")
    img.save(temp_file)
    
    # 用QPixmap加载PNG文件
    pixmap = QPixmap(temp_file)
    
    return pixmap, temp_file
