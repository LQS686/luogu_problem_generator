"""
问题模型类，用于表示洛谷题目及其属性
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any


class TestCase:
    """测试用例类"""
    def __init__(self, case_id: str, input_data: str = "", output_data: str = "",
                 score: int = 0, group: int = 0):
        self.case_id = case_id  # 测试点ID，如 "1"、"2.1" 等
        self.input_data = input_data  # 输入数据
        self.output_data = output_data  # 输出数据
        self.score = score  # 分值
        self.group = group  # 子任务组，0表示不属于子任务
        
    def save_to_files(self, directory: str) -> tuple:
        """保存测试用例到文件"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # 确保case_id是两位数格式，如01, 02等
        case_id_formatted = self.case_id.zfill(2) if self.case_id.isdigit() else self.case_id
            
        input_file = os.path.join(directory, f"{case_id_formatted}.in")
        output_file = os.path.join(directory, f"{case_id_formatted}.out")
        
        try:
            with open(input_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(self.input_data.strip())
                
            with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(self.output_data.strip())
                
            return (input_file, output_file)
        except Exception as e:
            raise IOError(f"保存测试用例文件时出错: {str(e)}")
    
    @classmethod
    def load_from_files(cls, directory: str, case_id: str) -> 'TestCase':
        """从文件加载测试用例"""
        # 支持不同的case_id格式（原始或格式化后的）
        case_id_formatted = case_id.zfill(2) if case_id.isdigit() else case_id
        
        input_file = os.path.join(directory, f"{case_id_formatted}.in")
        output_file = os.path.join(directory, f"{case_id_formatted}.out")
        
        # 如果找不到格式化的文件名，尝试原始的不带前导0的文件名
        if not (os.path.exists(input_file) and os.path.exists(output_file)) and case_id.isdigit():
            original_input_file = os.path.join(directory, f"{case_id}.in")
            original_output_file = os.path.join(directory, f"{case_id}.out")
            
            if os.path.exists(original_input_file) and os.path.exists(original_output_file):
                input_file = original_input_file
                output_file = original_output_file
        
        if not (os.path.exists(input_file) and os.path.exists(output_file)):
            raise FileNotFoundError(f"测试用例 {case_id} 的文件不存在")
            
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = f.read()
                
            with open(output_file, 'r', encoding='utf-8') as f:
                output_data = f.read()
                
            # 尝试从文件名解析子任务信息
            group = 0
            if '.' in case_id:
                try:
                    group = int(case_id.split('.')[0])
                except ValueError:
                    pass
                    
            return cls(case_id, input_data, output_data, group=group)
        except Exception as e:
            raise IOError(f"加载测试用例文件时出错: {str(e)}")


class SubTask:
    """子任务类"""
    def __init__(self, task_id: int, description: str = "", score: int = 0, test_cases: List[str] = None):
        self.task_id = task_id
        self.description = description
        self.score = score
        self.test_cases = test_cases or []  # 关联的测试用例ID列表


class Problem:
    """洛谷题目类"""
    def __init__(self, title: str = "", description: str = "", 
                 difficulty: int = 0, time_limit: int = 1000, 
                 memory_limit: int = 128, has_subtasks: bool = False):
        self.title = title  # 题目标题
        self.description = description  # 题目描述
        self.difficulty = difficulty  # 难度等级 (1-5)
        self.time_limit = time_limit  # 时间限制 (ms)
        self.memory_limit = memory_limit  # 内存限制 (MB)
        self.has_subtasks = has_subtasks  # 是否包含子任务
        self.test_cases: Dict[str, TestCase] = {}  # 测试用例字典
        self.subtasks: Dict[int, SubTask] = {}  # 子任务字典
        self.created_at = datetime.now()  # 创建时间
        self.modified_at = datetime.now()  # 修改时间
        self.directory = ""  # 题目目录
        
    def add_test_case(self, test_case: TestCase) -> None:
        """添加测试用例"""
        self.test_cases[test_case.case_id] = test_case
        self.modified_at = datetime.now()
        
    def add_subtask(self, subtask: SubTask) -> None:
        """添加子任务"""
        self.subtasks[subtask.task_id] = subtask
        self.modified_at = datetime.now()
        
    def save(self, base_dir: str = "problems") -> str:
        """保存题目到文件系统"""
        # 创建题目目录（如果没有标题，使用创建时间作为目录名）
        dir_name = self.title.replace(" ", "_") if self.title else f"problem_{int(self.created_at.timestamp())}"
        self.directory = os.path.join(base_dir, dir_name)
        
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            
        # 保存题目描述文件
        problem_file = os.path.join(self.directory, f"{self.title}.txt")
        with open(problem_file, 'w', encoding='utf-8') as f:
            f.write(self.description)
            
        # 创建测试数据目录
        test_cases_dir = os.path.join(self.directory, "test_cases")
        if not os.path.exists(test_cases_dir):
            os.makedirs(test_cases_dir)
            
        # 保存测试用例
        for case_id, test_case in self.test_cases.items():
            test_case.save_to_files(test_cases_dir)
            
        # 保存元数据
        metadata = {
            "title": self.title,
            "difficulty": self.difficulty,
            "time_limit": self.time_limit,
            "memory_limit": self.memory_limit,
            "has_subtasks": self.has_subtasks,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "test_cases": list(self.test_cases.keys())
        }
        
        # 保存子任务信息
        if self.has_subtasks:
            metadata["subtasks"] = {
                str(task_id): {
                    "description": subtask.description,
                    "score": subtask.score,
                    "test_cases": subtask.test_cases
                } for task_id, subtask in self.subtasks.items()
            }
            
        metadata_file = os.path.join(self.directory, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        # 创建测试数据压缩包
        self.create_test_cases_zip()
            
        return self.directory
        
    def create_test_cases_zip(self) -> str:
        """创建测试数据压缩包"""
        import zipfile
        
        # 检查测试数据目录是否存在
        test_cases_dir = os.path.join(self.directory, "test_cases")
        if not os.path.exists(test_cases_dir):
            raise FileNotFoundError(f"测试数据目录 {test_cases_dir} 不存在")
            
        # 检查测试数据目录中是否有文件
        files = [f for f in os.listdir(test_cases_dir) if os.path.isfile(os.path.join(test_cases_dir, f))]
        if not files:
            raise ValueError(f"测试数据目录 {test_cases_dir} 中没有文件")
            
        # 创建zip文件
        zip_file = os.path.join(self.directory, f"{self.title}_test_cases.zip")
        
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            for filename in files:
                file_path = os.path.join(test_cases_dir, filename)
                zipf.write(file_path, arcname=filename)
                    
        return zip_file
        
    def create_zip_package(self) -> str:
        """
        只创建zip包而不保存题目文件
        用于与生成器协作时避免重复保存文件
        """
        # 复用create_test_cases_zip方法避免重复代码
        return self.create_test_cases_zip()
        
    @classmethod
    def load(cls, problem_dir: str) -> 'Problem':
        """从文件系统加载题目"""
        if not os.path.exists(problem_dir) or not os.path.isdir(problem_dir):
            raise FileNotFoundError(f"题目目录 {problem_dir} 不存在")
            
        # 尝试加载元数据
        metadata_file = os.path.join(problem_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            problem = cls(
                title=metadata.get("title", ""),
                difficulty=metadata.get("difficulty", 0),
                time_limit=metadata.get("time_limit", 1000),
                memory_limit=metadata.get("memory_limit", 128),
                has_subtasks=metadata.get("has_subtasks", False)
            )
            
            # 设置创建和修改时间
            if "created_at" in metadata:
                problem.created_at = datetime.fromisoformat(metadata["created_at"])
            if "modified_at" in metadata:
                problem.modified_at = datetime.fromisoformat(metadata["modified_at"])
                
            # 加载子任务
            if problem.has_subtasks and "subtasks" in metadata:
                for task_id_str, subtask_data in metadata["subtasks"].items():
                    task_id = int(task_id_str)
                    subtask = SubTask(
                        task_id=task_id,
                        description=subtask_data.get("description", ""),
                        score=subtask_data.get("score", 0),
                        test_cases=subtask_data.get("test_cases", [])
                    )
                    problem.add_subtask(subtask)
        else:
            # 如果没有元数据，尝试从目录结构推断
            txt_files = [f for f in os.listdir(problem_dir) if f.endswith('.txt')]
            if not txt_files:
                raise FileNotFoundError(f"题目目录 {problem_dir} 中没有找到题目文件")
                
            title = txt_files[0].rsplit('.', 1)[0]
            problem = cls(title=title)
            
            # 读取题目描述
            with open(os.path.join(problem_dir, txt_files[0]), 'r', encoding='utf-8') as f:
                problem.description = f.read()
                
        # 加载测试用例
        test_cases_dir = os.path.join(problem_dir, "test_cases")
        if os.path.exists(test_cases_dir):
            in_files = [f for f in os.listdir(test_cases_dir) if f.endswith('.in')]
            for in_file in in_files:
                case_id = in_file.rsplit('.', 1)[0]
                test_case = TestCase.load_from_files(test_cases_dir, case_id)
                problem.add_test_case(test_case)
                
        # 设置题目目录
        problem.directory = problem_dir
        
        # 读取题目描述（如果元数据中没有）
        if not problem.description:
            txt_files = [f for f in os.listdir(problem_dir) if f.endswith('.txt')]
            if txt_files:
                with open(os.path.join(problem_dir, txt_files[0]), 'r', encoding='utf-8') as f:
                    problem.description = f.read()
                    
        return problem
        
    @staticmethod
    def list_problems(base_dir: str = "problems") -> List[Dict[str, Any]]:
        """列出所有题目"""
        if not os.path.exists(base_dir):
            return []
            
        problems = []
        for dir_name in os.listdir(base_dir):
            dir_path = os.path.join(base_dir, dir_name)
            if not os.path.isdir(dir_path):
                continue
                
            # 获取题目修改时间
            modified_time = os.path.getmtime(dir_path)
            
            # 尝试读取元数据
            metadata_file = os.path.join(dir_path, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                problems.append({
                    "id": dir_name,
                    "title": metadata.get("title", dir_name),
                    "difficulty": metadata.get("difficulty", 0),
                    "has_subtasks": metadata.get("has_subtasks", False),
                    "modified_at": modified_time,
                    "directory": dir_path
                })
            else:
                # 尝试从题目文件推断
                txt_files = [f for f in os.listdir(dir_path) if f.endswith('.txt')]
                if txt_files:
                    title = txt_files[0].rsplit('.', 1)[0]
                    problems.append({
                        "id": dir_name,
                        "title": title,
                        "difficulty": 0,
                        "has_subtasks": False,
                        "modified_at": modified_time,
                        "directory": dir_path
                    })
                else:
                    # 没有找到题目文件，但仍添加目录
                    problems.append({
                        "id": dir_name,
                        "title": dir_name,
                        "difficulty": 0,
                        "has_subtasks": False,
                        "modified_at": modified_time,
                        "directory": dir_path
                    })
                    
        # 按修改时间排序，最新的在前
        problems.sort(key=lambda x: x["modified_at"], reverse=True)
        return problems 