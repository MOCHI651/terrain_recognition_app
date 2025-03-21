import sys
import os
import warnings
from PyQt5.QtWidgets import QApplication

# 添加当前目录到系统路径，确保能找到模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 直接从当前目录导入
from terrain_app import TerrainApp

if __name__ == "__main__":
    # 抑制TIFF警告的方法
    warnings.filterwarnings("ignore", message=".*Unknown field with tag.*")
    
    app = QApplication(sys.argv)
    window = TerrainApp()
    
    # 使窗口最大化显示
    window.showMaximized()
    
    sys.exit(app.exec_())