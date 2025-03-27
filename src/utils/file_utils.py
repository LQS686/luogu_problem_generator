"""
文件操作工具模块 - 提供文件和目录处理函数
"""
import os
import shutil
import zipfile
from typing import List, Tuple, Optional


def ensure_dir(directory: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    参数:
        directory: 目录路径
        
    返回:
        创建或已存在的目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def clean_dir(directory: str) -> bool:
    """
    清空目录内容但保留目录本身
    
    参数:
        directory: 目录路径
        
    返回:
        操作是否成功
    """
    if not os.path.exists(directory):
        return False
        
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        return True
    except Exception as e:
        print(f"清空目录失败: {str(e)}")
        return False


def list_directories(parent_dir: str) -> List[str]:
    """
    列出给定目录下的所有子目录
    
    参数:
        parent_dir: 父目录路径
        
    返回:
        子目录名称列表
    """
    if not os.path.exists(parent_dir):
        return []
        
    return [d for d in os.listdir(parent_dir) 
            if os.path.isdir(os.path.join(parent_dir, d))]


def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    列出目录中的所有文件，可以按扩展名过滤
    
    参数:
        directory: 目录路径
        extensions: 文件扩展名列表，如 ['.txt', '.md']
        
    返回:
        符合条件的文件名列表
    """
    if not os.path.exists(directory):
        return []
        
    if extensions:
        return [f for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f)) and 
                any(f.endswith(ext) for ext in extensions)]
    else:
        return [f for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]


def read_file(file_path: str) -> str:
    """
    读取文本文件内容
    
    参数:
        file_path: 文件路径
        
    返回:
        文件内容字符串
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path: str, content: str) -> bool:
    """
    写入内容到文本文件
    
    参数:
        file_path: 文件路径
        content: 要写入的内容
        
    返回:
        操作是否成功
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文件失败: {str(e)}")
        return False


def create_zip(zip_file: str, source_dir: str, include_dir: bool = False) -> bool:
    """
    创建ZIP压缩文件
    
    参数:
        zip_file: 目标ZIP文件路径
        source_dir: 要压缩的源目录
        include_dir: 是否在ZIP中包含目录名
        
    返回:
        操作是否成功
    """
    if not os.path.exists(source_dir):
        return False
        
    try:
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if include_dir:
                        arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                    else:
                        arcname = os.path.relpath(file_path, source_dir)
                        
                    zipf.write(file_path, arcname=arcname)
        return True
    except Exception as e:
        print(f"创建ZIP文件失败: {str(e)}")
        return False


def extract_zip(zip_file: str, extract_dir: str) -> bool:
    """
    解压ZIP文件
    
    参数:
        zip_file: ZIP文件路径
        extract_dir: 解压目标目录
        
    返回:
        操作是否成功
    """
    if not os.path.exists(zip_file):
        return False
        
    try:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
            
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            zipf.extractall(extract_dir)
        return True
    except Exception as e:
        print(f"解压ZIP文件失败: {str(e)}")
        return False


def get_newest_file(directory: str, extensions: Optional[List[str]] = None) -> Optional[str]:
    """
    获取目录中最新的文件
    
    参数:
        directory: 目录路径
        extensions: 文件扩展名列表，如 ['.txt', '.md']
        
    返回:
        最新文件的路径，如果没有文件则返回None
    """
    if not os.path.exists(directory):
        return None
        
    files = list_files(directory, extensions)
    if not files:
        return None
        
    newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, newest_file) 