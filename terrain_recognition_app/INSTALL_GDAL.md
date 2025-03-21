# 如何安装 GDAL

GDAL 是一个用于处理地理空间数据的开源库，用于本应用中增强对 GeoTIFF 图像的支持。由于 GDAL 需要复杂的系统级依赖，安装方式因操作系统而异。

## Windows

在 Windows 上安装 GDAL 的最佳方法是使用预编译的二进制文件或 Conda：

### 方法1：使用 OSGeo4W 安装程序

1. 下载 OSGeo4W 安装程序：https://trac.osgeo.org/osgeo4w/
2. 运行安装程序并选择安装 GDAL
3. 安装后，将以下目录添加到系统 PATH 环境变量：
   ```
   C:\OSGeo4W\bin
   ```

### 方法2：使用 Conda（推荐）

1. 安装 Miniconda 或 Anaconda：https://docs.conda.io/en/latest/miniconda.html
2. 打开 Anaconda Prompt 并运行：
   ```
   conda create -n geo_env python=3.8
   conda activate geo_env
   conda install -c conda-forge gdal
   ```
3. 在这个环境中安装其他依赖：
   ```
   pip install -r requirements.txt
   ```

## Linux

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y libgdal-dev gdal-bin
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL==$(gdal-config --version)
```

### CentOS/RHEL

```bash
sudo yum install gdal gdal-devel
pip install GDAL==$(gdal-config --version)
```

## macOS

使用 Homebrew：

```bash
brew install gdal
pip install GDAL
```

## 验证安装

安装完成后，可以通过运行以下 Python 代码验证 GDAL 是否正确安装：

```python
from osgeo import gdal
print(gdal.__version__)
```

如果没有错误，则 GDAL 已成功安装。

## 注意事项

- **版本匹配很重要**：确保 pip 安装的 GDAL 版本与系统安装的 GDAL 库版本匹配
- **不使用 GDAL**：本应用程序也可以在没有 GDAL 的情况下工作，但某些高级 GeoTIFF 功能可能受限
