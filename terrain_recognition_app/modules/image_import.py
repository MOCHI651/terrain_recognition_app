import os
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import sys

# 尝试导入GDAL库，用于处理GeoTIFF
try:
    from osgeo import gdal
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False
    print("GDAL库不可用。GeoTIFF功能将受限。")

# 尝试导入PIL库，作为备用
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL库不可用。图像处理功能将受限。")

def import_image(file_path):
    """
    导入图像文件
    
    参数:
        file_path: 图像文件路径
    
    返回:
        QPixmap对象或None
    """
    if os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.tif', '.tiff']:
            return load_tiff_image(file_path)
        else:
            # 使用Qt自带功能加载常见图像格式
            pixmap = QPixmap(file_path)
            return pixmap
    return None

# 伪彩色映射函数 - 常规版本
def apply_colormap_jet(gray_image):
    """
    将灰度图像转换为伪彩色图像（使用jet颜色映射）
    
    参数:
        gray_image: 单通道灰度图像数组
    
    返回:
        RGB彩色图像数组
    """
    # 创建空的RGB数组
    height, width = gray_image.shape
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 简化版的Jet颜色映射
    # 将0-255的灰度值映射到蓝-青-黄-红的渐变色
    for i in range(height):
        for j in range(width):
            v = gray_image[i, j]
            
            # 红色通道
            if v < 64:
                r = 0
            elif v < 128:
                r = (v - 64) * 4
            else:
                r = 255
                
            # 绿色通道
            if v < 64:
                g = v * 4
            elif v < 192:
                g = 255
            else:
                g = 255 - (v - 192) * 4
                
            # 蓝色通道
            if v < 128:
                b = 255
            elif v < 192:
                b = 255 - (v - 128) * 4
            else:
                b = 0
                
            rgb_image[i, j, 0] = r
            rgb_image[i, j, 1] = g
            rgb_image[i, j, 2] = b
    
    return rgb_image

# 更高效的向量化版本（处理大图像时速度更快）
def apply_colormap_jet_vectorized(gray_image):
    """
    将灰度图像转换为伪彩色图像（使用jet颜色映射）- 向量化版本
    
    参数:
        gray_image: 单通道灰度图像数组
    
    返回:
        RGB彩色图像数组
    """
    # 创建空的RGB数组
    height, width = gray_image.shape
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 归一化为0-1范围（便于计算）
    v = gray_image.astype(np.float32) / 255.0
    
    # 红色通道
    rgb_image[..., 0] = np.clip(np.minimum(4 * v - 1.5, -4 * v + 4.5) * 255, 0, 255).astype(np.uint8)
    
    # 绿色通道
    rgb_image[..., 1] = np.clip(np.minimum(4 * v - 0.5, -4 * v + 3.5) * 255, 0, 255).astype(np.uint8)
    
    # 蓝色通道
    rgb_image[..., 2] = np.clip(np.minimum(4 * v + 0.5, -4 * v + 2.5) * 255, 0, 255).astype(np.uint8)
    
    return rgb_image

def load_tiff_image(file_path):
    """
    加载TIFF/GeoTIFF图像，使用PIL库处理
    
    参数:
        file_path: TIFF图像文件路径
    
    返回:
        QPixmap对象
    """
    if not PIL_AVAILABLE:
        raise ImportError("需要安装PIL库来处理TIFF图片")
    
    try:
        # 使用PIL打开TIFF图片
        img = Image.open(file_path)
        print(f"PIL打开图像: 模式={img.mode}, 大小={img.size}")
        
        # 如果是灰度图像，保持灰度模式
        if img.mode not in ['RGB', 'RGBA']:
            print("保持原始灰度图像")
            # 不再转换为彩色
        
        # 确保图像是RGB模式
        if img.mode != 'RGB' and img.mode != 'RGBA':
            img = img.convert('RGB')
            print(f"已转换为RGB模式")
        
        # 使用PIL的内置方法转换为QPixmap (更可靠的方法)
        # 先将PIL图像保存为临时文件
        temp_path = os.path.join(os.path.dirname(file_path), "temp_convert.png")
        img.save(temp_path)
        
        # 从临时文件加载QPixmap
        pixmap = QPixmap(temp_path)
        
        # 删除临时文件
        try:
            os.remove(temp_path)
        except:
            pass
            
        # 如果上面的方法失败，尝试通过numpy数组转换
        if pixmap.isNull():
            print("临时文件加载失败，尝试numpy转换...")
            # 转换为numpy数组
            img_array = np.array(img)
            
            # 检查是否是灰度图像 - 保持灰度，不应用伪彩色
            if len(img_array.shape) == 2:  # 灰度图像
                # 转换为RGB但保持灰度值
                print("将单通道灰度图像转换为RGB格式但保持灰度")
                img_array = np.stack([img_array, img_array, img_array], axis=2)
            elif img_array.shape[2] == 4:  # RGBA图像
                img_array = img_array[:, :, :3]  # 只保留RGB通道
            
            # 确保数组连续
            if not img_array.flags["C_CONTIGUOUS"]:
                img_array = np.ascontiguousarray(img_array)
            
            # 创建QImage
            height, width, channels = img_array.shape
            bytes_per_line = channels * width
            qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
        
        return pixmap
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"PIL处理TIFF失败: {error_detail}")
        raise Exception(f"加载TIFF图片出错: {str(e)}")

def load_geotiff_with_gdal(file_path):
    """
    使用GDAL库加载GeoTIFF图像
    
    参数:
        file_path: GeoTIFF文件路径
        
    返回:
        QPixmap对象
    """
    if not GDAL_AVAILABLE:
        raise ImportError("GDAL库不可用")
    
    try:
        # 注册所有GDAL驱动
        gdal.AllRegister()
        
        # 打开数据集
        dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
        if not dataset:
            raise IOError(f"GDAL无法打开文件: {file_path}")
        
        # 获取图像信息
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        bands = dataset.RasterCount
        
        # 检查文件大小，对大文件进行降采样处理
        scale_factor = 1.0
        if width * height > 100000000:  # 1亿像素以上的大图像
            scale_factor = 0.5  # 降采样到原来的一半大小
            print(f"检测到大图像，降采样处理 (缩小到{int(scale_factor*100)}%)")
        
        # 检查是否有调色板
        has_colormap = False
        color_table = None
        if bands == 1:
            band = dataset.GetRasterBand(1)
            color_table = band.GetColorTable()
            has_colormap = color_table is not None
        
        # 根据波段数和调色板情况选择不同的处理方法
        rgb_array = None
        
        # 1. 使用调色板处理单波段带调色板的图像
        if bands == 1 and has_colormap:
            # 读取单波段数据
            band_data = dataset.GetRasterBand(1).ReadAsArray()
            
            # 创建RGB数组
            rgb_array = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 优化：使用向量化操作替代循环 - 大大提高处理速度
            # 先创建调色板映射表
            ct_size = color_table.GetCount()
            colormap = np.zeros((ct_size, 3), dtype=np.uint8)
            for i in range(ct_size):
                entry = color_table.GetColorEntry(i)
                colormap[i, 0] = entry[0]  # R
                colormap[i, 1] = entry[1]  # G
                colormap[i, 2] = entry[2]  # B
            
            # 应用调色板 - 快速向量化操作
            # 确保索引值在有效范围内
            indices = np.clip(band_data, 0, ct_size-1).astype(int)
            rgb_array[:,:,0] = colormap[indices, 0]
            rgb_array[:,:,1] = colormap[indices, 1]
            rgb_array[:,:,2] = colormap[indices, 2]
            
        # 2. 处理多波段图像（3个及以上波段）
        elif bands >= 3:
            # 直接读取RGB波段
            r_band = dataset.GetRasterBand(1).ReadAsArray()
            g_band = dataset.GetRasterBand(2).ReadAsArray()
            b_band = dataset.GetRasterBand(3).ReadAsArray()
            
            # 将波段标准化到0-255
            def normalize_band(band):
                if band.dtype != np.uint8:
                    min_val = float(band.min())
                    max_val = float(band.max())
                    if max_val > min_val:
                        normalized = ((band.astype(float) - min_val) / (max_val - min_val) * 255.0)
                        return normalized.astype(np.uint8)
                    else:
                        return np.full_like(band, 128, dtype=np.uint8)
                return band
            
            r_normalized = normalize_band(r_band)
            g_normalized = normalize_band(g_band)
            b_normalized = normalize_band(b_band)
            
            # 组合RGB波段
            rgb_array = np.stack([r_normalized, g_normalized, b_normalized], axis=2)
            
        # 3. 处理单波段灰度图像
        else:
            # 读取单个波段
            band = dataset.GetRasterBand(1).ReadAsArray()
            
            # 标准化到0-255范围
            if band.dtype != np.uint8:
                min_val = float(band.min())
                max_val = float(band.max())
                if max_val > min_val:
                    band = ((band.astype(float) - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
                else:
                    band = np.full_like(band, 128, dtype=np.uint8)
            
            # 创建灰度RGB图像
            rgb_array = np.stack([band, band, band], axis=2)
        
        # 应用降采样处理以提高性能
        if scale_factor < 1.0:
            new_height = int(height * scale_factor)
            new_width = int(width * scale_factor)
            from PIL import Image
            # 使用PIL的高质量缩放
            pil_img = Image.fromarray(rgb_array)
            pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
            rgb_array = np.array(pil_img)
            height, width = new_height, new_width

        # 确保数组内存连续
        if not rgb_array.flags["C_CONTIGUOUS"]:
            rgb_array = np.ascontiguousarray(rgb_array)
        
        # 创建QImage
        bytes_per_line = 3 * width
        qimage = QImage(rgb_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # 关闭数据集
        dataset = None
        
        # 转换为QPixmap
        pixmap = QPixmap.fromImage(qimage)
        return pixmap
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"GDAL处理失败: {error_detail}")
        raise IOError(f"GDAL处理失败: {str(e)}")

def load_tiff_with_pil(file_path):
    """
    使用PIL库加载TIFF图像
    
    参数:
        file_path: TIFF文件路径
        
    返回:
        QPixmap对象
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL库不可用")
    
    try:
        # 打开图像
        img = Image.open(file_path)
        
        # 确保图像是RGB模式
        if img.mode != 'RGB' and img.mode != 'RGBA':
            img = img.convert('RGB')
        
        # 获取图像数据
        width, height = img.size
        img_data = img.tobytes('raw', img.mode)
        
        # 创建QImage
        if img.mode == 'RGBA':
            q_img = QImage(img_data, width, height, QImage.Format_RGBA8888)
        else:  # RGB
            q_img = QImage(img_data, width, height, QImage.Format_RGB888)
        
        # 转换为QPixmap
        pixmap = QPixmap.fromImage(q_img)
        return pixmap
    
    except Exception as e:
        raise IOError(f"PIL处理失败: {str(e)}")