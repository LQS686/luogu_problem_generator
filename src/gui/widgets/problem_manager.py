"""
题目管理器对话框
"""
import os
import sys
import zipfile
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QTabWidget, QMessageBox, QFileDialog, QGroupBox,
    QTreeWidget, QTreeWidgetItem, QFrame, QScrollArea,
    QSpinBox, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QKeySequence, QShortcut

# 当模块处于开发中，使用相对导入
try:
    from ...models.problem import Problem, TestCase, SubTask
except ImportError:
    # 绝对导入作为后备
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from src.models.problem import Problem, TestCase, SubTask

try:
    # 尝试导入图标缓存
    from ...utils.icons import ICON_CACHE
    # 定义要使用的图标名称
    EDIT_ICON_NAME = "edit"
    DELETE_ICON_NAME = "delete"
    REFRESH_ICON_NAME = "refresh"
    SEARCH_ICON_NAME = "search_dark"  # 默认暗色主题搜索图标
except ImportError:
    # 导入失败时设置为None
    ICON_CACHE = None
    EDIT_ICON_NAME = ""
    DELETE_ICON_NAME = ""
    REFRESH_ICON_NAME = ""
    SEARCH_ICON_NAME = ""


class ProblemListItem(QListWidgetItem):
    """自定义题目列表项"""
    def __init__(self, problem_data: Dict[str, Any]):
        super().__init__(problem_data["title"])
        self.problem_data = problem_data
        self.setToolTip(f"路径: {problem_data['directory']}\n修改时间: {datetime.fromtimestamp(problem_data['modified_at']).strftime('%Y-%m-%d %H:%M:%S')}")


class TestCaseListItem(QListWidgetItem):
    """自定义测试用例列表项"""
    def __init__(self, case_id: str, group: int = 0):
        # 修改显示格式为xx.in/xx.out
        display_text = f"{case_id.zfill(2)}.in / {case_id.zfill(2)}.out"
        if group > 0:
            display_text = f"[组 {group}] {display_text}"
        super().__init__(display_text)
        self.case_id = case_id
        self.group = group
        self.setToolTip(f"测试点ID: {case_id}" + (f"\n所属子任务组: {group}" if group > 0 else ""))


class ProblemManagerDialog(QDialog):
    """题目管理器对话框"""
    def __init__(self, parent=None, initial_problem_dir: str = None):
        super().__init__(parent)
        self.setWindowTitle("题目管理器")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        
        # 当前加载的题目
        self.current_problem: Optional[Problem] = None
        
        # 当前编辑的测试用例ID
        self.current_test_case_id: Optional[str] = None
        
        # 初始化UI
        self.init_ui()
        
        # 添加快捷键
        self.setup_shortcuts()
        
        # 加载题目列表
        self.refresh_problem_list()
        
        # 如果指定了初始题目，加载它
        if initial_problem_dir:
            self.load_specific_problem(initial_problem_dir)
        # 否则加载第一个题目（如果有）
        elif self.problem_list.count() > 0:
            self.problem_list.setCurrentRow(0)
            self.load_problem_details()
            
    def init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 头部区域
        header_widget = QWidget()
        header_widget.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题标签
        title_label = QLabel("题目管理")
        title_label.setObjectName("cardTitle")
        title_font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # 添加提示文本
        tip_label = QLabel("在这里管理已生成的题目和测试数据")
        tip_label.setObjectName("tipLabel")
        header_layout.addWidget(tip_label)
        
        header_layout.addStretch()
        
        # 添加到主布局
        layout.addWidget(header_widget)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)
        
        # 左侧题目列表面板 (卡片式)
        left_panel = QWidget()
        left_panel.setObjectName("problemListCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        # 题目列表标签
        list_label = QLabel("题目列表")
        list_label.setObjectName("sectionTitle")
        left_layout.addWidget(list_label)
        
        # 题目列表
        self.problem_list = QListWidget()
        self.problem_list.setObjectName("modernList")
        self.problem_list.setMinimumWidth(200)
        self.problem_list.setAlternatingRowColors(True)
        self.problem_list.currentItemChanged.connect(self.load_problem_details)
        left_layout.addWidget(self.problem_list)
        
        # 题目列表操作按钮
        list_buttons_layout = QHBoxLayout()
        list_buttons_layout.setSpacing(8)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumWidth(80)
        self.refresh_button.clicked.connect(self.refresh_problem_list)
        # 尝试设置刷新图标
        if ICON_CACHE and REFRESH_ICON_NAME in ICON_CACHE:
            self.refresh_button.setIcon(ICON_CACHE[REFRESH_ICON_NAME])
        list_buttons_layout.addWidget(self.refresh_button)
        
        list_buttons_layout.addStretch()
        
        self.delete_button = QPushButton("删除题目")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setMinimumWidth(80)
        self.delete_button.clicked.connect(self.delete_problem)
        list_buttons_layout.addWidget(self.delete_button)
        
        left_layout.addLayout(list_buttons_layout)
        
        splitter.addWidget(left_panel)
        
        # 右侧题目详情面板 (卡片式)
        right_panel = QWidget()
        right_panel.setObjectName("problemDetailCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)
        
        # 题目详情标签
        detail_label = QLabel("题目详情")
        detail_label.setObjectName("sectionTitle")
        right_layout.addWidget(detail_label)
        
        # 标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("detailTabs")
        right_layout.addWidget(self.tab_widget)
        
        # 题目描述标签页
        desc_tab = QWidget()
        desc_layout = QVBoxLayout(desc_tab)
        desc_layout.setContentsMargins(10, 10, 10, 10)
        desc_layout.setSpacing(10)
        
        # 题目描述编辑器 - 纯文本编辑器，不渲染Markdown格式
        self.problem_editor = QTextEdit()
        self.problem_editor.setObjectName("problemDescriptionEdit")
        # 确保使用纯文本模式，不进行任何格式化处理
        self.problem_editor.setAcceptRichText(False)
        self.problem_editor.setFont(QFont("Consolas", 10))
        self.problem_editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        desc_layout.addWidget(self.problem_editor)
        
        self.tab_widget.addTab(desc_tab, "题目描述")
        
        # 测试数据标签页
        test_tab = QWidget()
        test_layout = QVBoxLayout(test_tab)
        test_layout.setContentsMargins(10, 10, 10, 10)
        test_layout.setSpacing(10)
        
        # 测试数据分割器
        test_splitter = QSplitter(Qt.Orientation.Vertical)
        test_splitter.setHandleWidth(1)
        test_splitter.setChildrenCollapsible(False)
        test_layout.addWidget(test_splitter)
        
        # 测试用例列表部分
        test_list_widget = QWidget()
        test_list_widget.setObjectName("testCaseListCard")
        test_list_layout = QVBoxLayout(test_list_widget)
        test_list_layout.setContentsMargins(10, 10, 10, 10)
        test_list_layout.setSpacing(8)
        
        test_list_label = QLabel("测试点列表")
        test_list_label.setObjectName("subsectionTitle")
        test_list_layout.addWidget(test_list_label)
        
        # 搜索框和工具栏
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.test_case_search = QLineEdit()
        self.test_case_search.setObjectName("searchBox")
        self.test_case_search.setPlaceholderText("搜索测试点...")
        self.test_case_search.textChanged.connect(self.filter_test_cases)
        self.test_case_search.setClearButtonEnabled(True)
        
        # 设置搜索图标
        if ICON_CACHE and SEARCH_ICON_NAME in ICON_CACHE:
            search_icon = ICON_CACHE[SEARCH_ICON_NAME]
            self.test_case_search.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        
        search_layout.addWidget(self.test_case_search)
        
        test_toolbar = QHBoxLayout()
        test_toolbar.setContentsMargins(0, 0, 0, 0)
        test_toolbar.setSpacing(8)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("smallButton")
        refresh_button.clicked.connect(self.refresh_problem_list)
        # 尝试设置刷新图标
        if ICON_CACHE and REFRESH_ICON_NAME in ICON_CACHE:
            refresh_button.setIcon(ICON_CACHE[REFRESH_ICON_NAME])
        refresh_button.setToolTip("刷新题目列表")
        test_toolbar.addWidget(refresh_button)
        
        search_layout.addLayout(test_toolbar)
        test_list_layout.addLayout(search_layout)
        
        self.test_case_list = QListWidget()
        self.test_case_list.setObjectName("testCaseList")
        self.test_case_list.setAlternatingRowColors(True)
        self.test_case_list.currentItemChanged.connect(self.load_test_case_details)
        test_list_layout.addWidget(self.test_case_list)
        
        test_splitter.addWidget(test_list_widget)
        
        # 测试用例编辑部分
        test_edit_widget = QWidget()
        test_edit_widget.setObjectName("testCaseEditCard")
        test_edit_layout = QVBoxLayout(test_edit_widget)
        test_edit_layout.setContentsMargins(10, 10, 10, 10)
        test_edit_layout.setSpacing(10)
        
        # 测试点编辑标题
        test_edit_label = QLabel("测试点编辑")
        test_edit_label.setObjectName("subsectionTitle")
        test_edit_layout.addWidget(test_edit_label)
        
        # 输入输出编辑框
        io_splitter = QSplitter(Qt.Orientation.Horizontal)
        io_splitter.setHandleWidth(1)
        io_splitter.setChildrenCollapsible(False)
        test_edit_layout.addWidget(io_splitter)
        
        # 输入数据组
        input_group = QGroupBox("输入数据")
        input_group.setObjectName("ioGroupBox")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(10, 15, 10, 10)
        
        self.input_editor = QTextEdit()
        self.input_editor.setObjectName("inputEditor")
        self.input_editor.setFont(QFont("Consolas", 10))
        self.input_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        input_layout.addWidget(self.input_editor)
        
        io_splitter.addWidget(input_group)
        
        # 输出数据组
        output_group = QGroupBox("输出数据")
        output_group.setObjectName("ioGroupBox")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        
        self.output_editor = QTextEdit()
        self.output_editor.setObjectName("outputEditor")
        self.output_editor.setFont(QFont("Consolas", 10))
        self.output_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        output_layout.addWidget(self.output_editor)
        
        io_splitter.addWidget(output_group)
        
        test_splitter.addWidget(test_edit_widget)
        
        # 设置分割比例
        test_splitter.setSizes([150, 550])
        
        self.tab_widget.addTab(test_tab, "测试数据")
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([250, 750])
        
        # 底部按钮区域
        bottom_widget = QWidget()
        bottom_widget.setObjectName("actionCard")
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(15, 10, 15, 10)
        
        # 左侧状态
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 底部按钮 - 移除更新打包文件按钮，合并两个功能
        self.save_button = QPushButton("保存修改")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setMinimumWidth(120)
        self.save_button.clicked.connect(self.save_problem_changes)
        bottom_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("defaultButton")
        self.close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_button)
        
        layout.addWidget(bottom_widget)
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+F 聚焦到搜索框
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search)
        
        # Esc 清空搜索框
        self.clear_search_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.clear_search_shortcut.activated.connect(self.clear_search)
    
    def focus_search(self):
        """聚焦到搜索框"""
        # 确保当前显示的是测试数据标签页
        self.tab_widget.setCurrentIndex(1)  # 假设测试数据是第二个标签页
        self.test_case_search.setFocus()
        self.test_case_search.selectAll()
    
    def clear_search(self):
        """清空搜索框"""
        if self.test_case_search.hasFocus():
            self.test_case_search.clear()
            self.status_label.setText("就绪")
            
    # 覆盖showEvent方法，在显示对话框时自动将焦点设置到测试点列表
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 如果有测试点，则聚焦到测试点列表
        if self.test_case_list.count() > 0:
            self.test_case_list.setFocus()
        # 如果显示的是测试数据标签页，则将tab切换到该页
        if self.current_problem and self.tab_widget.currentIndex() == 1:
            self.test_case_search.setFocus()
            
    def refresh_problem_list(self):
        """刷新题目列表"""
        # 保存当前选中的项目目录
        current_dir = None
        if self.problem_list.currentItem():
            item = self.problem_list.currentItem()
            if isinstance(item, ProblemListItem):
                current_dir = item.problem_data["directory"]
        
        # 清空列表
        self.problem_list.clear()
        
        # 加载题目列表
        problems = Problem.list_problems()
        
        if not problems:
            return
            
        # 添加到列表
        for problem_data in problems:
            item = ProblemListItem(problem_data)
            self.problem_list.addItem(item)
            
        # 恢复选择
        if current_dir:
            for i in range(self.problem_list.count()):
                item = self.problem_list.item(i)
                if isinstance(item, ProblemListItem) and item.problem_data["directory"] == current_dir:
                    self.problem_list.setCurrentRow(i)
                    break
        elif self.problem_list.count() > 0:
            self.problem_list.setCurrentRow(0)
            
    def load_specific_problem(self, problem_dir: str):
        """加载指定目录的题目"""
        for i in range(self.problem_list.count()):
            item = self.problem_list.item(i)
            if isinstance(item, ProblemListItem) and item.problem_data["directory"] == problem_dir:
                self.problem_list.setCurrentRow(i)
                return
                
        # 如果没有找到，尝试直接加载
        try:
            self.current_problem = Problem.load(problem_dir)
            self.update_ui_with_problem()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载题目失败: {str(e)}")
            
    def load_problem_details(self):
        """加载所选题目的详细信息"""
        # 清空当前编辑器
        self.problem_editor.clear()
        self.test_case_list.clear()
        self.input_editor.clear()
        self.output_editor.clear()
        
        # 清空搜索框
        if hasattr(self, 'test_case_search'):
            self.test_case_search.clear()
        
        # 获取所选题目
        item = self.problem_list.currentItem()
        if not item or not isinstance(item, ProblemListItem):
            return
            
        problem_dir = item.problem_data["directory"]
        
        try:
            # 加载题目
            self.current_problem = Problem.load(problem_dir)
            
            # 更新UI
            self.update_ui_with_problem()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载题目失败: {str(e)}")
            
    def update_ui_with_problem(self):
        """用题目数据更新UI"""
        if not self.current_problem:
            return
            
        # 更新题目描述
        self.problem_editor.setText(self.current_problem.description)
        
        # 清空搜索框
        if hasattr(self, 'test_case_search'):
            self.test_case_search.clear()
        
        # 更新测试用例列表
        self.test_case_list.clear()
        for case_id, test_case in self.current_problem.test_cases.items():
            item = TestCaseListItem(case_id, test_case.group)
            self.test_case_list.addItem(item)
            
        # 如果有测试用例，选择第一个
        if self.test_case_list.count() > 0:
            self.test_case_list.setCurrentRow(0)
            
    def load_test_case_details(self):
        """加载所选测试用例的详细信息"""
        # 先保存当前测试用例的修改（如果有）
        self.save_current_test_case()
        
        # 清空当前编辑器
        self.input_editor.clear()
        self.output_editor.clear()
        
        # 检查是否有选中的测试用例
        item = self.test_case_list.currentItem()
        if not item or not isinstance(item, TestCaseListItem) or not self.current_problem:
            self.current_test_case_id = None
            return
            
        case_id = item.case_id
        self.current_test_case_id = case_id
        
        # 检查测试用例是否存在
        if case_id not in self.current_problem.test_cases:
            self.current_test_case_id = None
            return
            
        test_case = self.current_problem.test_cases[case_id]
        
        # 更新编辑器
        self.input_editor.setText(test_case.input_data)
        self.output_editor.setText(test_case.output_data)
    
    def save_current_test_case(self):
        """临时保存当前测试用例的修改"""
        if not self.current_problem or not self.current_test_case_id:
            return
            
        # 检查测试用例是否存在
        if self.current_test_case_id not in self.current_problem.test_cases:
            return
            
        test_case = self.current_problem.test_cases[self.current_test_case_id]
        
        # 获取编辑器内容
        input_data = self.input_editor.toPlainText()
        output_data = self.output_editor.toPlainText()
        
        # 只有当内容有变化时才更新
        if test_case.input_data != input_data or test_case.output_data != output_data:
            test_case.input_data = input_data
            test_case.output_data = output_data
            self.status_label.setText(f"已临时保存测试点 {self.current_test_case_id} 的修改")
        
    def update_test_cases_zip(self):
        """更新测试用例的zip打包文件"""
        if not self.current_problem:
            self.status_label.setText("错误：没有加载题目")
            return False
            
        try:
            # 获取测试用例目录和目标zip文件路径
            test_cases_dir = os.path.join(self.current_problem.directory, "test_cases")
            zip_file = os.path.join(self.current_problem.directory, f"{self.current_problem.title}_test_cases.zip")
            
            # 检查测试用例目录是否存在
            if not os.path.exists(test_cases_dir) or not os.path.isdir(test_cases_dir):
                self.status_label.setText("错误：测试用例目录不存在")
                return False
                
            # 检查测试用例目录中是否有文件
            files = [f for f in os.listdir(test_cases_dir) if os.path.isfile(os.path.join(test_cases_dir, f))]
            if not files:
                self.status_label.setText("错误：测试用例目录为空")
                return False
                
            # 创建zip文件
            with zipfile.ZipFile(zip_file, "w") as zipf:
                for file_name in files:
                    file_path = os.path.join(test_cases_dir, file_name)
                    zipf.write(file_path, arcname=file_name)
                    
            self.status_label.setText(f"成功：已更新测试用例打包文件 ({len(files)} 个文件)")
            return True
            
        except Exception as e:
            self.status_label.setText(f"错误：{str(e)}")
            return False
            
    def save_problem_changes(self):
        """保存对题目和测试数据的修改"""
        if not self.current_problem:
            self.status_label.setText("错误：没有加载题目")
            return
            
        try:
            # 保存题目描述
            self.current_problem.description = self.problem_editor.toPlainText()
            
            # 保存当前测试用例修改
            self.save_current_test_case()
            
            # 保存题目
            self.current_problem.save()
            
            # 更新zip文件
            zip_result = self.update_test_cases_zip()
            
            if zip_result:
                self.status_label.setText("成功：已保存所有修改并更新打包文件")
            else:
                self.status_label.setText("警告：题目已保存，但更新打包文件失败")
            
        except Exception as e:
            self.status_label.setText(f"错误：保存失败：{str(e)}")
            
    def delete_problem(self):
        """删除选中的题目"""
        item = self.problem_list.currentItem()
        if not item or not isinstance(item, ProblemListItem):
            QMessageBox.information(self, "提示", "请先选择一个题目")
            return
            
        problem_dir = item.problem_data["directory"]
        problem_title = item.problem_data["title"]
        
        # 确认删除
        result = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除题目 {problem_title} 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # 删除目录
            shutil.rmtree(problem_dir)
            
            # 刷新列表
            self.refresh_problem_list()
            
            # 清空编辑器
            self.problem_editor.clear()
            self.test_case_list.clear()
            self.input_editor.clear()
            self.output_editor.clear()
            
            self.current_problem = None
            
            QMessageBox.information(self, "成功", "题目已删除")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除题目失败: {str(e)}")

    def filter_test_cases(self, text):
        """按序号搜索测试点"""
        if not text:
            # 如果搜索文本为空，显示所有测试点
            for i in range(self.test_case_list.count()):
                self.test_case_list.item(i).setHidden(False)
            self.status_label.setText("就绪")
            return
            
        # 搜索条件为测试点序号
        search_term = text.strip()
        
        # 所有可见测试点的计数
        visible_count = 0
        selected_item = None
        
        for i in range(self.test_case_list.count()):
            item = self.test_case_list.item(i)
            if isinstance(item, TestCaseListItem):
                # 从case_id中提取数字部分
                case_number = item.case_id.lstrip("0")
                
                # 如果搜索词匹配测试点序号的开头，则显示该测试点，否则隐藏
                if case_number.startswith(search_term) or search_term.startswith(case_number):
                    item.setHidden(False)
                    visible_count += 1
                    # 如果是精确匹配，直接选中该测试点
                    if case_number == search_term:
                        selected_item = item
                else:
                    item.setHidden(True)
        
        # 如果有精确匹配项，选中它
        if selected_item:
            self.test_case_list.setCurrentItem(selected_item)
            self.status_label.setText(f"找到精确匹配: 测试点 {selected_item.case_id}")
        else:
            # 更新状态标签显示搜索结果
            if visible_count == 0:
                self.status_label.setText(f"没有找到匹配的测试点: {text}")
            else:
                self.status_label.setText(f"显示 {visible_count} 个匹配的测试点")
                
    def closeEvent(self, event):
        """关闭事件，确保保存当前测试用例的修改"""
        # 保存当前测试用例的修改
        self.save_current_test_case()
        super().closeEvent(event) 