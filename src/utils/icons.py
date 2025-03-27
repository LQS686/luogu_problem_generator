"""
图标资源模块 - 包含基于Base64编码的图标资源
"""
import base64
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QByteArray, QSize

# 使用简单的SVG图标替代复杂的PNG图标，避免libpng错误

# 应用图标 - 简单风格
APP_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="8" y="8" width="48" height="48" rx="6" fill="#007ACC" />
  <rect x="16" y="24" width="32" height="4" rx="2" fill="white" />
  <rect x="16" y="32" width="32" height="4" rx="2" fill="white" />
  <rect x="16" y="40" width="32" height="4" rx="2" fill="white" />
</svg>
"""

# 刷新图标
REFRESH_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="#007ACC"/>
</svg>
"""

# 删除图标
DELETE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="#CC0000"/>
</svg>
"""

# 保存图标
SAVE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z" fill="#007ACC"/>
</svg>
"""

# 文件夹图标
FOLDER_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" fill="#FFB900"/>
</svg>
"""

# 进度图标
PROGRESS_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M13 2.05v3.03c3.39.49 6 3.39 6 6.92 0 .9-.18 1.75-.48 2.54l2.6 1.53c.56-1.24.88-2.62.88-4.07 0-5.18-3.95-9.45-9-9.95zM12 19c-3.87 0-7-3.13-7-7 0-3.53 2.61-6.43 6-6.92V2.05c-5.06.5-9 4.76-9 9.95 0 5.52 4.47 10 9.99 10 3.31 0 6.24-1.61 8.06-4.09l-2.6-1.53C16.17 17.98 14.21 19 12 19z" fill="#007ACC"/>
</svg>
"""

# 编辑图标
EDIT_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" fill="#007ACC"/>
</svg>
"""

# 文件图标
FILE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M6 2c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6H6zm7 7V3.5L18.5 9H13z" fill="#007ACC"/>
</svg>
"""

# 主题切换图标
THEME_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69zM12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z" fill="#007ACC"/>
</svg>
"""

# 帮助图标
HELP_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z" fill="#007ACC"/>
</svg>
"""

# 关于图标
ABOUT_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="#007ACC"/>
</svg>
"""

# 搜索图标（暗色主题）
SEARCH_DARK_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" fill="#FFFFFF"/>
</svg>
"""

# 搜索图标（浅色主题）
SEARCH_LIGHT_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" fill="#333333"/>
</svg>
"""

# 图标缓存，延迟初始化
ICON_CACHE = {}

def get_icon_from_base64(base64_str):
    """从Base64字符串或SVG创建QIcon"""
    # 检查是否是SVG图标
    if base64_str.strip().startswith('<svg'):
        try:
            # 是SVG字符串，直接从SVG数据创建
            byte_array = QByteArray(base64_str.strip().encode('utf-8'))
            pixmap = QPixmap()
            pixmap.loadFromData(byte_array, "SVG")
            
            # 确保图标大小合适（防止某些平台上的渲染问题）
            if pixmap.isNull():
                raise ValueError("SVG图标加载失败")
                
            # 如果图标很小或为空，设置默认大小
            if pixmap.width() < 10 or pixmap.height() < 10:
                pixmap = QPixmap(QSize(24, 24))
                
            return QIcon(pixmap)
        except Exception as e:
            print(f"加载SVG图标出错: {str(e)}")
            # 出错时创建默认图标
            default_pixmap = QPixmap(24, 24)
            default_pixmap.fill() 
            return QIcon(default_pixmap)
    else:
        # 是Base64编码的图像，解码后创建
        try:
            byte_array = base64.b64decode(base64_str.strip())
            pixmap = QPixmap()
            pixmap.loadFromData(byte_array)
            
            if pixmap.isNull():
                raise ValueError("Base64图标加载失败")
                
            return QIcon(pixmap)
        except Exception as e:
            print(f"加载Base64图标出错: {str(e)}")
            # 出错时创建默认图标
            default_pixmap = QPixmap(24, 24)
            default_pixmap.fill() 
            return QIcon(default_pixmap)
    
def initialize_icons():
    """在QApplication已创建后初始化所有图标"""
    global ICON_CACHE
    ICON_CACHE = {
        "app": get_icon_from_base64(APP_ICON),
        "refresh": get_icon_from_base64(REFRESH_ICON),
        "delete": get_icon_from_base64(DELETE_ICON),
        "save": get_icon_from_base64(SAVE_ICON),
        "folder": get_icon_from_base64(FOLDER_ICON),
        "file": get_icon_from_base64(FILE_ICON),
        "progress": get_icon_from_base64(PROGRESS_ICON),
        "edit": get_icon_from_base64(EDIT_ICON),
        "theme": get_icon_from_base64(THEME_ICON),
        "help": get_icon_from_base64(HELP_ICON),
        "about": get_icon_from_base64(ABOUT_ICON),
        "search_dark": get_icon_from_base64(SEARCH_DARK_ICON),
        "search_light": get_icon_from_base64(SEARCH_LIGHT_ICON)
    } 