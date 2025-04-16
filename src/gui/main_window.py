"""
洛谷出题工具主窗口
"""
import os
import sys
import traceback
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QProgressBar, QStatusBar, QTabWidget,
    QCheckBox, QPushButton, QMessageBox, QFileDialog, QToolBar,
    QDockWidget, QApplication, QDialog, QLineEdit, QRadioButton
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QThread, QTimer, QPropertyAnimation
from PyQt6.QtGui import QAction, QIcon, QFont, QTextCursor, QIntValidator, QPalette, QColor

# 当模块处于开发中，使用相对导入
try:
    from ..models.problem import Problem, TestCase, SubTask
    from .widgets.problem_manager import ProblemManagerDialog
    from ..generators.base_generator import BaseProblemGenerator
except ImportError:
    # 绝对导入作为后备
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from src.models.problem import Problem, TestCase, SubTask
    from src.gui.widgets.problem_manager import ProblemManagerDialog
    from src.generators.base_generator import BaseProblemGenerator


class LogRedirector:
    """用于将标准输出重定向到QTextEdit控件"""
    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.buffer = ""
        
    def write(self, text):
        """写入文本"""
        self.buffer += text
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.text_edit.insertPlainText(text)
        
    def flush(self):
        pass


class GeneratorThread(QThread):
    """题目生成线程"""
    progress_update = pyqtSignal(str)
    generation_completed = pyqtSignal(Problem)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, generator: BaseProblemGenerator, description: str, has_subtasks: bool = False, test_cases_count: int = 10):
        super().__init__()
        self.generator = generator
        self.description = description
        self.has_subtasks = has_subtasks
        self.test_cases_count = test_cases_count
        
    def run(self):
        try:
            # 设置生成器参数
            self.generator.problem_description = self.description
            if hasattr(self.generator, 'has_subtasks'):
                self.generator.has_subtasks = self.has_subtasks
            if hasattr(self.generator, 'test_cases_count'):
                self.generator.test_cases_count = self.test_cases_count
                
            # 生成题目
            self.progress_update.emit("正在格式化题目...")
            problem_data = self.generator.format_problem()
            if not problem_data:
                self.generation_failed.emit("题目格式化失败")
                return
                
            # 生成测试数据
            self.progress_update.emit("正在生成测试数据...")
            test_cases = self.generator.generate_test_cases()
            if not test_cases:
                self.generation_failed.emit("测试数据生成失败")
                return
                
            # 创建Problem对象，使用生成器中已有的题目信息
            self.progress_update.emit("正在保存题目和测试数据...")
            problem_obj = Problem(
                title=problem_data.get("title", "未命名题目"),
                description=problem_data.get("description", ""),
                difficulty=problem_data.get("difficulty", 0),
                time_limit=problem_data.get("time_limit", 1000),
                memory_limit=problem_data.get("memory_limit", 128),
                has_subtasks=self.has_subtasks
            )
            
            # 设置题目目录为生成器已创建的目录
            if self.generator.current_problem_dir:
                problem_obj.directory = self.generator.current_problem_dir
                
            # 添加测试用例，使用生成器中test_cases_dir下已有的文件
            for i, (input_data, output_data) in enumerate(test_cases, 1):
                case_id = str(i)
                if self.has_subtasks and "." in case_id:
                    group = int(case_id.split(".")[0])
                else:
                    group = 0
                    
                test_case = TestCase(
                    case_id=case_id,
                    input_data=input_data,
                    output_data=output_data,
                    group=group
                )
                problem_obj.add_test_case(test_case)
                
            # 添加子任务信息
            if self.has_subtasks and "subtasks" in problem_data:
                for i, subtask_data in enumerate(problem_data["subtasks"], 1):
                    subtask = SubTask(
                        task_id=i,
                        description=subtask_data.get("description", ""),
                        score=subtask_data.get("score", 0),
                        test_cases=[str(tc_id) for tc_id in subtask_data.get("test_cases", [])]
                    )
                    problem_obj.add_subtask(subtask)
            
            # 创建zip包（不重新保存题目文件和测试数据文件，只打包）
            problem_obj.create_zip_package()
            
            self.progress_update.emit("生成完成!")
            self.generation_completed.emit(problem_obj)
            
        except Exception as e:
            error_msg = f"生成过程中出错: {str(e)}\n{traceback.format_exc()}"
            self.generation_failed.emit(error_msg)


class MimicGeneratorThread(QThread):
    """模仿出题线程"""
    progress_update = pyqtSignal(str)
    generation_completed = pyqtSignal(Problem)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, generator: BaseProblemGenerator, reference_description: str, test_cases_count: int = 10):
        super().__init__()
        self.generator = generator
        self.reference_description = reference_description
        self.test_cases_count = test_cases_count
        
    def run(self):
        try:
            # 设置生成器参数
            self.generator.test_cases_count = self.test_cases_count
                
            # 生成模仿题目
            self.progress_update.emit("正在分析参考题目...")
            problem_data = self.generator.mimic_problem(self.reference_description)
            if not problem_data:
                self.generation_failed.emit("模仿题目生成失败")
                return
                
            # 设置problem_description用于后续生成测试数据
            self.generator.problem_description = problem_data.get("description", "")
            
            # 生成测试数据
            self.progress_update.emit("正在生成测试数据...")
            test_cases = self.generator.generate_test_cases()
            if not test_cases:
                self.generation_failed.emit("测试数据生成失败")
                return
                
            # 创建Problem对象，使用生成器中已有的题目信息
            self.progress_update.emit("正在保存题目和测试数据...")
            problem_obj = Problem(
                title=problem_data.get("title", "未命名题目"),
                description=problem_data.get("description", ""),
                difficulty=problem_data.get("difficulty", 0),
                time_limit=problem_data.get("time_limit", 1000),
                memory_limit=problem_data.get("memory_limit", 128),
                has_subtasks=False  # 模仿生成不支持子任务
            )
            
            # 设置题目目录为生成器已创建的目录
            if self.generator.current_problem_dir:
                problem_obj.directory = self.generator.current_problem_dir
                
            # 添加测试用例
            for i, (input_data, output_data) in enumerate(test_cases, 1):
                case_id = str(i)
                test_case = TestCase(
                    case_id=case_id,
                    input_data=input_data,
                    output_data=output_data,
                    group=0
                )
                problem_obj.add_test_case(test_case)
            
            # 创建zip包
            problem_obj.create_zip_package()
            
            self.progress_update.emit("模仿题目生成完成!")
            self.generation_completed.emit(problem_obj)
            
        except Exception as e:
            error_msg = f"模仿生成过程中出错: {str(e)}\n{traceback.format_exc()}"
            self.generation_failed.emit(error_msg)


class ApiKeyDialog(QDialog):
    """API密钥配置对话框"""
    def __init__(self, parent=None, current_key=""):
        super().__init__(parent)
        self.setWindowTitle("配置模型API密钥")
        self.resize(500, 150)
        self.setModal(True)
        
        self.init_ui(current_key)
        
    def init_ui(self, current_key):
        layout = QVBoxLayout(self)
        
        # 说明标签
        label = QLabel("请输入DeepSeek API密钥，用于生成题目:")
        layout.addWidget(label)
        
        # API密钥输入框
        self.api_key_edit = QLineEdit(current_key)
        self.api_key_edit.setPlaceholderText("输入您的API密钥")
        layout.addWidget(self.api_key_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def get_api_key(self):
        return self.api_key_edit.text().strip()


class MainWindow(QMainWindow):
    """洛谷出题工具主窗口"""
    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle("洛谷出题工具")
        self.resize(1000, 800)
        self.setMinimumSize(800, 600)
        
        # 初始化API Key变量
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        # 结果处理变量
        self.current_problem = None
        
        # 主题设置
        self.is_dark_theme = True
        
        # 加载图标
        try:
            from ..utils.icons import get_icon_from_base64, APP_ICON, ICON_CACHE, initialize_icons
            # 初始化图标缓存
            initialize_icons()
            # 使用初始化的图标缓存
            if "app" in ICON_CACHE:
                self.setWindowIcon(ICON_CACHE["app"])
            else:
                # 如果缓存中没有，则加载应用图标
                app_icon = get_icon_from_base64(APP_ICON)
                self.setWindowIcon(app_icon)
        except ImportError as e:
            print(f"无法加载图标资源: {str(e)}")
        
        # 创建动作
        self.create_actions()
        
        # 创建工具栏（菜单栏功能已合并到工具栏）
        self.create_toolbars()
        
        # 设置主界面
        self.setup_ui()
        
        # 添加渐入动画
        self.fade_in_animation()
        
        # 显示欢迎信息
        self.show_welcome_message()
        
        # 移除菜单栏
        self.menuBar().setVisible(False)
        
    def setup_ui(self):
        """设置主UI布局"""
        # 中央部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局 - 减小整体边距
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 更合适的边距
        main_layout.setSpacing(8)  # 增加间距改善布局呼吸感
        
        # 创建分割器 - 更细的分隔线
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #3D3D3D;
                height: 1px;
            }
        """)
        main_layout.addWidget(splitter)
        
        # 顶部区域 - 输入区域
        top_widget = QWidget()
        top_widget.setObjectName("inputCard")
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(16, 16, 16, 12)  # 增加内边距
        top_layout.setSpacing(10)  # 增加元素间距
        
        # 题目类型选择标签
        generation_type_label = QLabel("选择生成模式:")
        top_layout.addWidget(generation_type_label)
        
        # 生成模式选择
        generation_type_layout = QHBoxLayout()
        generation_type_layout.setSpacing(10)
        
        # 常规生成模式（默认）
        self.normal_generation_radio = QRadioButton("常规生成")
        self.normal_generation_radio.setChecked(True)
        self.normal_generation_radio.toggled.connect(self.toggle_generation_mode)
        generation_type_layout.addWidget(self.normal_generation_radio)
        
        # 模仿出题模式
        self.mimic_generation_radio = QRadioButton("模仿出题")
        self.mimic_generation_radio.toggled.connect(self.toggle_generation_mode)
        generation_type_layout.addWidget(self.mimic_generation_radio)
        
        generation_type_layout.addStretch()
        top_layout.addLayout(generation_type_layout)
        
        # 描述标签
        self.description_label = QLabel("题目描述（输入您想要生成的题目类型、难度等要求）:")
        top_layout.addWidget(self.description_label)
        
        # 题目描述输入框
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(150)
        top_layout.addWidget(self.description_input)
        
        # 参考题目标签和输入框（初始隐藏，模仿模式下显示）
        self.reference_label = QLabel("参考题目（输入完整的题目描述，将生成类似题目）:")
        self.reference_label.setVisible(False)
        top_layout.addWidget(self.reference_label)
        
        self.reference_input = QTextEdit()
        self.reference_input.setMinimumHeight(150)
        self.reference_input.setVisible(False)
        top_layout.addWidget(self.reference_input)
        
        # 选项区域
        options_layout = QHBoxLayout()
        
        # 测试点数量
        test_cases_layout = QHBoxLayout()
        test_cases_label = QLabel("测试点数量:")
        test_cases_layout.addWidget(test_cases_label)
        
        self.test_cases_count = QLineEdit()
        self.test_cases_count.setValidator(QIntValidator(1, 100))
        self.test_cases_count.setText("10")
        self.test_cases_count.setMaximumWidth(50)
        test_cases_layout.addWidget(self.test_cases_count)
        
        options_layout.addLayout(test_cases_layout)
        options_layout.addStretch()
        
        # 生成按钮
        self.generate_button = QPushButton("生成题目")
        self.generate_button.setMinimumWidth(150)
        self.generate_button.clicked.connect(self.start_generation)
        options_layout.addWidget(self.generate_button)
        
        # 模仿生成按钮（初始隐藏）
        self.mimic_button = QPushButton("模仿生成")
        self.mimic_button.setMinimumWidth(150)
        self.mimic_button.clicked.connect(self.start_mimic_generation)
        self.mimic_button.setVisible(False)
        options_layout.addWidget(self.mimic_button)
        
        top_layout.addLayout(options_layout)
        splitter.addWidget(top_widget)
        
        # 底部区域 - 输出和日志
        bottom_widget = QWidget()
        bottom_widget.setObjectName("outputCard")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(16, 16, 16, 16)  # 增加内边距
        bottom_layout.setSpacing(10)  # 增加元素间距
        
        # 输出区域
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(12, 12, 12, 12)  # 增加内边距
        output_layout.setSpacing(10)  # 增加元素间距
        
        # 结果标签和工具栏
        result_header = QHBoxLayout()
        result_header.setSpacing(10)
        
        self.result_label = QLabel("生成结果")
        self.result_label.setObjectName("sectionTitle")
        self.result_label.setMinimumHeight(32)  # 增加高度
        result_header.addWidget(self.result_label)
        
        result_header.addStretch()
        
        output_layout.addLayout(result_header)
        
        # 结果文本框
        self.result_text = QTextEdit()
        self.result_text.setObjectName("resultText")
        self.result_text.setReadOnly(True)
        output_layout.addWidget(self.result_text)
        
        # 直接将输出widget添加到底部布局
        bottom_layout.addWidget(output_widget)
        
        # 添加底部组件到分割器
        splitter.addWidget(bottom_widget)
        
        # 设置分割比例 (40:60)
        splitter.setSizes([400, 600])
        
        # 底部状态栏
        status_bar = self.statusBar()
        status_bar.setObjectName("modernStatusBar")
        
        # 进度条 - 更现代的样式
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(2)  # 保持更细的进度条
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        status_bar.addPermanentWidget(self.progress_bar, 1)
        
        # 显示欢迎信息
        self.show_welcome_message()
        
    def create_actions(self):
        """创建动作"""
        # 导入图标资源
        try:
            from ..utils.icons import ICON_CACHE
            
            # 使用预加载的图标缓存
            refresh_icon = ICON_CACHE.get("refresh", QIcon())
            delete_icon = ICON_CACHE.get("delete", QIcon())
            save_icon = ICON_CACHE.get("save", QIcon())
            folder_icon = ICON_CACHE.get("folder", QIcon())
            file_icon = ICON_CACHE.get("file", QIcon())
            progress_icon = ICON_CACHE.get("progress", QIcon())
            edit_icon = ICON_CACHE.get("edit", QIcon())
            theme_icon = ICON_CACHE.get("theme", QIcon())
            help_icon = ICON_CACHE.get("help", QIcon())
            about_icon = ICON_CACHE.get("about", QIcon())
        except ImportError as e:
            # 如果无法导入图标，使用文本替代
            print(f"无法加载图标缓存: {str(e)}")
            refresh_icon = QIcon()
            delete_icon = QIcon()
            save_icon = QIcon()
            folder_icon = QIcon()
            file_icon = QIcon()
            progress_icon = QIcon()
            edit_icon = QIcon()
            theme_icon = QIcon()
            help_icon = QIcon()
            about_icon = QIcon()
            
        # 文件菜单
        self.config_action = QAction("模型设置", self)
        self.config_action.setStatusTip("配置DeepSeek API密钥")
        self.config_action.triggered.connect(self.configure_api_key)
        self.config_action.setIcon(edit_icon)
        
        self.clear_action = QAction("清空", self)
        self.clear_action.setStatusTip("清空所有输入和输出")
        self.clear_action.triggered.connect(self.clear_all)
        self.clear_action.setIcon(delete_icon)
        
        self.exit_action = QAction("退出", self)
        self.exit_action.setStatusTip("退出应用程序")
        self.exit_action.triggered.connect(self.close)
        
        # 题目管理
        self.problem_manager_action = QAction("题目管理", self)
        self.problem_manager_action.setStatusTip("管理题目和测试数据")
        self.problem_manager_action.triggered.connect(self.open_problem_manager)
        self.problem_manager_action.setIcon(edit_icon)
        
        self.open_problem_dir_action = QAction("浏览题目", self)
        self.open_problem_dir_action.setStatusTip("打开题目目录，浏览所有题目")
        self.open_problem_dir_action.triggered.connect(self.open_problems_dir)
        self.open_problem_dir_action.setIcon(folder_icon)
        
        # 视图菜单
        self.toggle_theme_action = QAction("切换主题", self)
        self.toggle_theme_action.setStatusTip("切换浅色/暗色主题")
        self.toggle_theme_action.triggered.connect(self.toggle_theme)
        self.toggle_theme_action.setIcon(theme_icon)
        
        # 帮助菜单
        self.help_action = QAction("帮助", self)
        self.help_action.setStatusTip("显示使用帮助")
        self.help_action.triggered.connect(self.show_help)
        self.help_action.setIcon(help_icon)
        
        self.about_action = QAction("关于", self)
        self.about_action.setStatusTip("显示版本和版权信息")
        self.about_action.triggered.connect(self.show_about)
        self.about_action.setIcon(about_icon)
        
        # 模仿题目生成
        self.mimic_action = QAction("模仿出题", self)
        self.mimic_action.triggered.connect(lambda: self.mimic_generation_radio.setChecked(True))
        if hasattr(self, 'icon_cache') and "copy" in self.icon_cache:
            self.mimic_action.setIcon(self.icon_cache["copy"])
        
    def create_toolbars(self):
        """创建工具栏，包含原菜单栏的所有功能"""
        # 主工具栏
        main_toolbar = QToolBar("主工具栏", self)
        main_toolbar.setIconSize(QSize(24, 24))  # 稍微减小图标尺寸
        main_toolbar.setObjectName("mainToolBar")
        main_toolbar.setMovable(False)  # 固定工具栏位置
        main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)  # 文字在图标下方
        main_toolbar.setStyleSheet("""
            QToolBar { 
                background-color: #2C2C2C; 
                border-bottom: 1px solid #3D3D3D; 
                padding: 4px;
                spacing: 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
                min-width: 70px;
            }
            QToolButton:hover {
                background-color: #3A3A3A;
                border: 1px solid #505050;
            }
            QToolButton:pressed {
                background-color: #505050;
            }
        """)
        self.addToolBar(main_toolbar)
        
        # 添加所有功能到工具栏
        # 文件操作
        self.clear_action.setText("清空")
        self.clear_action.setToolTip("清空所有输入和输出")
        main_toolbar.addAction(self.clear_action)
        
        main_toolbar.addSeparator()
        
        # 题目管理
        self.problem_manager_action.setText("题目管理")
        self.problem_manager_action.setToolTip("管理已生成的题目和测试数据")
        main_toolbar.addAction(self.problem_manager_action)
        
        self.open_problem_dir_action.setText("浏览题目")
        self.open_problem_dir_action.setToolTip("打开题目目录，浏览所有题目")
        main_toolbar.addAction(self.open_problem_dir_action)
        
        main_toolbar.addSeparator()
        
        # 视图操作
        self.toggle_theme_action.setText("切换主题")
        self.toggle_theme_action.setToolTip("切换浅色/暗色主题")
        main_toolbar.addAction(self.toggle_theme_action)
        
        # 设置操作 - 移动到这个位置
        self.config_action.setText("模型设置")
        self.config_action.setToolTip("配置DeepSeek API密钥")
        main_toolbar.addAction(self.config_action)
        
        main_toolbar.addSeparator()
        
        # 帮助
        self.help_action.setText("帮助")
        self.help_action.setToolTip("显示使用帮助")
        main_toolbar.addAction(self.help_action)
        
        self.about_action.setText("关于")
        self.about_action.setToolTip("显示版本和版权信息")
        main_toolbar.addAction(self.about_action)
        
        # 模仿题目生成
        self.mimic_action.setText("模仿出题")
        self.mimic_action.setToolTip("模仿出题")
        main_toolbar.addAction(self.mimic_action)
        
        # 增加退出按钮
        exit_button = QAction("退出", self)
        exit_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogCloseButton))
        exit_button.setToolTip("退出应用程序")
        exit_button.triggered.connect(self.close)
        main_toolbar.addAction(exit_button)
        
    def configure_api_key(self):
        """配置API密钥"""
        dialog = ApiKeyDialog(self, self.api_key)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            api_key = dialog.get_api_key()
            if not api_key:
                QMessageBox.warning(self, "警告", "API密钥不能为空")
                return
                
            self.api_key = api_key
            os.environ["DEEPSEEK_API_KEY"] = api_key
            
            # 尝试保存到.env文件
            try:
                with open('.env', 'w') as f:
                    f.write(f"DEEPSEEK_API_KEY={api_key}")
                QMessageBox.information(self, "成功", "模型API密钥已保存")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"保存API密钥到文件时出错: {str(e)}")
    
    def clear_all(self):
        """清空所有输入和输出"""
        self.description_input.clear()
        self.result_text.clear()
        self.statusBar().showMessage("已清空")
        self.current_problem = None
        
        # 添加欢迎消息
        welcome_msg = """
<h3>欢迎使用 洛谷测试数据生成器</h3>

<p>在上方输入题目描述，然后点击"生成题目"按钮开始生成</p>

<p><i>提示：详细的描述可以生成更准确的题目</i></p>
"""
        self.result_text.setHtml(welcome_msg)
        
    def start_generation(self):
        """开始生成题目"""
        # 获取题目描述
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "警告", "请输入题目描述")
            return
            
        # 获取测试点数量
        test_cases_count = 10  # 默认值
        try:
            test_cases_count = int(self.test_cases_count.text())
            if test_cases_count < 1:
                raise ValueError("测试点数量必须大于0")
        except ValueError as e:
            QMessageBox.warning(self, "警告", f"测试点数量设置错误: {str(e)}")
            return
            
        # 验证API密钥
        if not self.api_key:
            result = QMessageBox.question(
                self, "API密钥缺失", 
                "未设置API密钥，是否现在配置？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                self.configure_api_key()
                # 如果用户取消了配置，不继续生成
                if not self.api_key:
                    return
            else:
                return
                
        # 更新UI状态
        self.generate_button.setEnabled(False)
        self.result_text.clear()
        self.progress_bar.show()
        self.statusBar().showMessage("正在生成...")
        
        # 设置环境变量
        os.environ["DEEPSEEK_API_KEY"] = self.api_key
        
        # 创建并启动生成线程
        try:
            # 始终使用SimpleProblemGenerator，移除子任务判断
            try:
                from ..generators.simple_generator import SimpleProblemGenerator
                generator = SimpleProblemGenerator()
            except ImportError:
                # 绝对导入作为后备
                from src.generators.simple_generator import SimpleProblemGenerator
                generator = SimpleProblemGenerator()
            
            # 确保生成器有正确的API密钥和测试点数量
            if hasattr(generator, 'api_key'):
                generator.api_key = self.api_key
                
            if hasattr(generator, 'test_cases_count'):
                generator.test_cases_count = test_cases_count
                
            # 创建生成线程
            self.generator_thread = GeneratorThread(
                generator=generator,
                description=description,
                has_subtasks=False,  # 始终为False
                test_cases_count=test_cases_count
            )
            
            # 连接信号
            self.generator_thread.progress_update.connect(self.update_progress)
            self.generator_thread.generation_completed.connect(self.generation_completed)
            self.generator_thread.generation_failed.connect(self.generation_failed)
            
            # 启动线程
            self.generator_thread.start()
            
            # 将标准输出重定向到结果文本框
            sys.stdout = LogRedirector(self.result_text)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动生成器时出错: {str(e)}")
            self.finish_generation()
        
        # 禁用生成按钮，避免重复点击
        self.generate_button.setEnabled(False)
        
    def update_progress(self, message):
        """更新进度消息"""
        self.result_text.append(message)
        # 更新状态栏
        self.statusBar().showMessage(message)
        
        # 增加一个简单的视觉反馈
        QApplication.processEvents()
        
    def generation_completed(self, problem):
        """生成完成处理"""
        self.current_problem = problem
        self.result_text.append(f"洛谷出题工具执行完成！")
        self.result_text.append(f"生成的文件保存在: {problem.directory}")
        self.finish_generation()
        
        # 显示成功消息
        QMessageBox.information(
            self, "成功", 
            f"题目和测试数据生成成功！\n文件已保存到：{problem.directory}"
        )
        
    def generation_failed(self, error_message):
        """生成失败处理"""
        self.result_text.append(f"生成失败: {error_message}")
        self.finish_generation()
        
        # 设置状态栏为错误状态
        self.statusBar().setStyleSheet("QStatusBar { background-color: #CC3333; color: white; }")
        self.statusBar().showMessage("生成失败")
        
        # 2秒后恢复原样式
        QTimer.singleShot(2000, lambda: self.statusBar().setStyleSheet(""))
        
    def finish_generation(self):
        """完成生成，恢复UI状态"""
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        
        # 更新UI状态
        self.generate_button.setEnabled(True)
        self.progress_bar.hide()
        self.statusBar().showMessage("完成")
        
        # 添加一些动画效果
        def pulse_result():
            self.result_text.setStyleSheet("QTextEdit { border: 2px solid #0078D7; }")
            QTimer.singleShot(300, lambda: self.result_text.setStyleSheet(""))
            
        pulse_result()
        
    def open_problems_dir(self):
        """打开题目目录，浏览所有题目"""
        problems_dir = "problems"
        if not os.path.exists(problems_dir):
            os.makedirs(problems_dir)
            QMessageBox.information(self, "提示", "题目目录已创建，但还没有生成任何题目")
        
        os.startfile(problems_dir)
        
    def open_problem_manager(self):
        """打开题目管理器"""
        dialog = ProblemManagerDialog(self)
        dialog.exec()
            
    def show_help(self):
        """显示帮助信息"""
        help_text = """
洛谷出题工具使用说明：

基本操作：
1. 在顶部输入框中输入题目的大致描述
2. 设置测试点数量（默认为10）
3. 点击"生成题目"按钮开始生成题目和测试数据
4. 生成完成后，结果将显示在下方文本框中

生成的文件会保存在以下位置：
- problems/题目名称/ - 题目主目录
- problems/题目名称/题目名称.txt - 题目描述文件
- problems/题目名称/test_cases/ - 测试数据目录
- problems/题目名称/题目名称_test_cases.zip - 打包好的测试数据

工具栏功能：
- 清空：清空输入和输出区域
- 题目管理：打开题目管理器，可查看和编辑已生成的题目和测试数据
- 浏览题目：直接打开题目文件夹，查看所有已生成的题目
- 切换主题：在暗色和浅色主题间切换
- 模型设置：配置DeepSeek API密钥，用于生成题目
- 帮助：显示本帮助信息
- 关于：显示版本和版权信息
- 退出：关闭应用程序

使用提示：
- 提供更详细的题目描述可获得更精确的生成结果
- 您可以在题目管理器中编辑已生成的题目和测试数据
- 在首次使用前，请通过"模型设置"按钮配置您的API密钥

注意：生成过程可能需要一些时间，请耐心等待。生成过程中会显示进度信息。
"""
        QMessageBox.information(self, "使用说明", help_text)
            
    def show_about(self):
        """显示关于信息"""
        about_text = """
洛谷出题工具 v2.2

本工具用于生成符合洛谷要求的算法竞赛题目和测试数据。

主要特性：
- 自动生成完整题目描述和格式化内容
- 生成高质量的测试数据并自动打包
- 支持自定义测试点数量
- 符合洛谷题目上传格式要求
- 统一的文件组织结构便于管理
- 题目管理器支持查看和编辑题目内容
- 支持切换浅色/暗色主题
- 基于DeepSeek API的高质量内容生成
- 使用PyQt6构建的现代化界面

© 2023-2024 All Rights Reserved
"""
        QMessageBox.information(self, "关于", about_text)

    def toggle_theme(self):
        """切换浅色/暗色主题"""
        try:
            app = QApplication.instance()
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if self.is_dark_theme:
                # 切换到浅色主题
                light_style_path = os.path.join(base_path, "assets", "styles", "light_theme.qss")
                if os.path.exists(light_style_path):
                    with open(light_style_path, "r", encoding="utf-8") as f:
                        app.setStyleSheet(f.read())
                    self.is_dark_theme = False
                    self.statusBar().showMessage("已切换到浅色主题")
                else:
                    # 如果找不到浅色主题文件，则使用空样式表作为后备
                    app.setStyleSheet("")
                    self.is_dark_theme = False
                    self.statusBar().showMessage("浅色主题文件未找到，使用系统默认主题")
            else:
                # 切换到暗色主题
                dark_style_path = os.path.join(base_path, "assets", "styles", "dark_theme.qss")
                if os.path.exists(dark_style_path):
                    with open(dark_style_path, "r", encoding="utf-8") as f:
                        app.setStyleSheet(f.read())
                    self.is_dark_theme = True
                    self.statusBar().showMessage("已切换到暗色主题")
                else:
                    self.statusBar().showMessage("未找到暗色主题文件，无法切换到暗色主题")
        except Exception as e:
            self.statusBar().showMessage(f"切换主题失败: {str(e)}")
            print(f"切换主题时发生错误: {str(e)}")

    def fade_in_animation(self):
        """窗口渐入动画"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)  # 稍快的动画
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
        
    def show_welcome_message(self):
        """显示欢迎信息"""
        # 将标准输出重定向到结果文本框
        sys.stdout = LogRedirector(self.result_text)
        
        # 添加欢迎消息
        welcome_msg = """
<div style="text-align: center;">
<h2 style="color: #2196F3; margin-bottom: 15px;">欢迎使用 洛谷测试数据生成器</h2>

<p style="margin: 10px 0; font-size: 11pt;">在上方输入题目描述，然后点击"生成题目"按钮开始生成</p>

<p style="margin: 10px 0; font-style: italic; color: #757575;">提示：详细的描述可以生成更准确的题目</p>

<hr style="border: 0; border-top: 1px solid #E0E0E0; margin: 20px 0;">

<p style="margin: 10px 0;">工具栏中的按钮可以帮助您管理已生成的题目和测试数据</p>
</div>
"""
        self.result_text.setHtml(welcome_msg)
        
        # 添加一些示例提示在结果框中
        example_msg = """
<div style="padding: 10px;">
<h3 style="color: #2196F3; margin-bottom: 10px;">题目生成示例</h3>

<p>生成的题目将在这里显示，包括：</p>
<ul style="margin-left: 20px;">
  <li>题目标题和描述</li>
  <li>输入输出格式</li>
  <li>样例数据</li>
  <li>测试点信息</li>
</ul>

<p style="font-style: italic; color: #757575; margin-top: 15px;">输入详细的题目描述可获得更好的生成效果</p>
</div>
"""
        self.result_text.setHtml(example_msg)

    def toggle_generation_mode(self):
        """切换生成模式（常规/模仿）"""
        if self.normal_generation_radio.isChecked():
            # 常规模式
            self.description_label.setText("题目描述（输入您想要生成的题目类型、难度等要求）:")
            self.reference_label.setVisible(False)
            self.reference_input.setVisible(False)
            self.generate_button.setVisible(True)
            self.mimic_button.setVisible(False)
        else:
            # 模仿模式
            self.description_label.setText("新题目要求（可选，指定新题目的特定要求）:")
            self.reference_label.setVisible(True)
            self.reference_input.setVisible(True)
            self.generate_button.setVisible(False)
            self.mimic_button.setVisible(True)

    def start_mimic_generation(self):
        """开始模仿出题过程"""
        # 获取参考题目
        reference_description = self.reference_input.toPlainText().strip()
        if not reference_description:
            QMessageBox.warning(self, "错误", "请输入参考题目描述")
            return
            
        # 获取附加要求（可选）
        additional_requirements = self.description_input.toPlainText().strip()
        
        # 禁用按钮，防止重复点击
        self.mimic_button.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # 清空结果显示
        self.result_text.clear()
        
        # 添加附加要求到参考描述
        if additional_requirements:
            # 如果有附加要求，将其显示在日志中
            self.result_text.append(f"附加要求: {additional_requirements}\n")
            full_reference = f"{reference_description}\n\n附加要求：{additional_requirements}"
        else:
            full_reference = reference_description
        
        # 验证API密钥
        if not self.api_key:
            result = QMessageBox.question(
                self, "API密钥缺失", 
                "未设置API密钥，是否现在配置？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                self.configure_api_key()
                # 如果用户取消了配置，不继续生成
                if not self.api_key:
                    self.mimic_button.setEnabled(True)
                    return
            else:
                self.mimic_button.setEnabled(True)
                return
        
        # 创建生成器实例
        try:
            from ..generators.simple_generator import SimpleProblemGenerator
            generator = SimpleProblemGenerator()
        except ImportError:
            # 绝对导入作为后备
            from src.generators.simple_generator import SimpleProblemGenerator
            generator = SimpleProblemGenerator()
        
        # 设置API密钥
        from ..utils.api_utils import set_api_key
        set_api_key(self.api_key)
        
        # 获取测试点数量
        try:
            test_cases_count = int(self.test_cases_count.text())
        except ValueError:
            test_cases_count = 10
        
        # 创建并启动模仿生成线程
        self.mimic_thread = MimicGeneratorThread(
            generator=generator,
            reference_description=full_reference,
            test_cases_count=test_cases_count
        )
        self.mimic_thread.progress_update.connect(self.update_progress)
        self.mimic_thread.generation_completed.connect(self.generation_completed)
        self.mimic_thread.generation_failed.connect(self.generation_failed)
        self.mimic_thread.finished.connect(self.finish_generation)
        
        # 显示状态
        self.statusBar().showMessage("正在模仿生成题目...")
        
        # 启动线程
        self.mimic_thread.start()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 加载环境变量
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 