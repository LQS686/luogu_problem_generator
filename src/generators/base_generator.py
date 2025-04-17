"""
基础题目生成器类，定义生成器接口
"""
import os
import json
import re
import zipfile
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

from ..utils.api_utils import call_api


class BaseProblemGenerator(ABC):
    """基础题目生成器抽象类"""
    
    def __init__(self):
        self.problem_description = ""
        self.current_problem_dir = ""
        self.test_cases_dir = ""
        self.problem_name = ""
        self.test_cases_count = 10  # 默认测试点数量
        
    @abstractmethod
    def format_problem(self) -> Dict[str, Any]:
        """
        格式化题目描述，生成完整的题目
        返回包含题目信息的字典，至少应包含:
        {
            "title": "题目标题",
            "description": "完整的题目描述",
            "difficulty": 0-5 的难度等级,
            "time_limit": 时间限制(ms),
            "memory_limit": 内存限制(MB)
        }
        """
        pass
        
    @abstractmethod
    def generate_test_cases(self) -> List[Tuple[str, str]]:
        """
        生成测试数据
        返回(输入, 输出)元组的列表
        """
        pass
    
    def parse_api_response(self, response: str) -> Dict[str, Any]:
        """
        解析API返回的JSON响应
        """
        try:
            # 尝试直接解析整个响应
            problem_data = json.loads(response)
        except json.JSONDecodeError:
            # 如果失败，尝试从文本中提取JSON部分
            match = re.search(r'({[\s\S]*})', response)
            if match:
                json_str = match.group(1)
                problem_data = json.loads(json_str)
            else:
                raise ValueError("无法从API响应中提取有效的JSON数据")
        return problem_data
    
    def process_description(self, problem_data: Dict[str, Any]) -> str:
        """
        处理描述，合并相关字段，优化格式使其更加美观
        """
        # 确保标题作为描述的第一行，使用更加美观的标题格式
        title = problem_data.get("title", "未命名题目")
        description = f"# {title}\n\n"
        
        # 主体描述，确保段落之间有适当的空行
        main_desc = problem_data.get('description', '')
        # 如果描述中已有标题部分，移除它，避免重复
        if main_desc.startswith(f"# {title}") or main_desc.startswith(f"#{title}"):
            # 找到第一个换行符后的内容
            main_desc = main_desc[main_desc.find('\n')+1:].strip()
        description += main_desc
        
        # 优化标题格式，确保所有标题前后都有空行
        sections = []
        
        # 处理输入格式部分
        if ("## 输入格式" not in description and "输入格式" not in description) and "input_format" in problem_data:
            input_format = problem_data.get('input_format', '').strip()
            if input_format:
                sections.append(f"## 输入格式\n\n{input_format}")
        
        # 处理输出格式部分
        if ("## 输出格式" not in description and "输出格式" not in description) and "output_format" in problem_data:
            output_format = problem_data.get('output_format', '').strip()
            if output_format:
                sections.append(f"## 输出格式\n\n{output_format}")
        
        # 处理样例部分
        if ("## 样例" not in description and "## 示例" not in description and 
                "样例" not in description and "示例" not in description) and "samples" in problem_data:
            samples = problem_data.get('samples', [{}])
            if samples:
                sample_section = "## 样例\n\n"
                for i, sample in enumerate(samples, 1):
                    if len(samples) > 1:
                        sample_section += f"### 样例 {i}\n\n"
                    
                    sample_input = sample.get('input', '').strip()
                    sample_output = sample.get('output', '').strip()
                    
                    sample_section += f"#### 输入\n```\n{sample_input}\n```\n\n"
                    sample_section += f"#### 输出\n```\n{sample_output}\n```\n\n"
                    
                    # 如果有样例解释，添加它
                    if 'explanation' in sample and sample['explanation']:
                        explanation = sample['explanation'].strip()
                        sample_section += f"#### 解释\n{explanation}\n\n"
                
                sections.append(sample_section.strip())
        
        # 处理提示部分
        if "## 提示" not in description and "提示" not in description and "hints" in problem_data and problem_data["hints"]:
            hints = problem_data.get('hints', '').strip()
            if hints:
                sections.append(f"## 提示\n\n{hints}")
        
        # 将所有部分组合起来，确保它们之间有足够的空行
        if sections:
            description += "\n\n" + "\n\n".join(sections)
        
        # 优化数学公式的显示（确保$符号周围有适当的空格）
        description = re.sub(r'(?<!\s)\$', ' $', description)  # 在$前添加空格（如果没有）
        description = re.sub(r'\$(?!\s)', '$ ', description)  # 在$后添加空格（如果没有）
        
        # 确保所有段落之间有空行
        description = re.sub(r'\n{3,}', '\n\n', description)  # 将多个空行替换为两个空行
        
        # 为列表项增加适当的间距
        description = re.sub(r'(\n\d+\..*?)(\n\d+\.)', r'\1\n\2', description)
        
        return description
    
    def extract_sample_data(self, description: str) -> Tuple[str, str, str, str]:
        """
        从题目描述中提取输入输出格式和样例
        """
        input_format = ""
        output_format = ""
        samples = ""
        
        # 提取输入格式 - 匹配更多可能的格式化方式
        input_match = re.search(r'##\s+输入格式\s*([\s\S]*?)(?=##\s+|$)', description)
        if input_match:
            input_format = input_match.group(1).strip()
            
        # 提取输出格式
        output_match = re.search(r'##\s+输出格式\s*([\s\S]*?)(?=##\s+|$)', description)
        if output_match:
            output_format = output_match.group(1).strip()
            
        # 提取样例 - 处理可能的多个样例
        samples_section = ""
        samples_match = re.search(r'##\s+样例(?:\s*\d*)?(?:\s*\d)?\s*([\s\S]*?)(?=##\s+|$)', description)
        if not samples_match:
            samples_match = re.search(r'##\s+示例(?:\s*\d*)?(?:\s*\d)?\s*([\s\S]*?)(?=##\s+|$)', description)
            
        if samples_match:
            samples_section = samples_match.group(1).strip()
        
        # 如果找到了样例部分，解析所有的输入/输出对
        if samples_section:
            # 处理多个样例的情况
            sample_pairs = []
            
            # 查找所有 "输入" 和 "输出" 模式
            input_blocks = re.findall(r'(?:###\s+样例\s+\d+\s*\n)?\s*####?\s+输入\s*\n```\s*([\s\S]*?)```', samples_section)
            output_blocks = re.findall(r'####?\s+输出\s*\n```\s*([\s\S]*?)```', samples_section)
            explanation_blocks = re.findall(r'####?\s+解释\s*\n([\s\S]*?)(?=####?\s+|$)', samples_section)
            
            # 确保找到的输入和输出块数量相同
            min_blocks = min(len(input_blocks), len(output_blocks))
            
            for i in range(min_blocks):
                sample_input = input_blocks[i].strip()
                sample_output = output_blocks[i].strip()
                sample_explanation = ""
                if i < len(explanation_blocks):
                    sample_explanation = explanation_blocks[i].strip()
                    
                sample_pair = f"输入:\n{sample_input}\n\n输出:\n{sample_output}"
                if sample_explanation:
                    sample_pair += f"\n\n解释:\n{sample_explanation}"
                    
                sample_pairs.append(sample_pair)
            
            # 将所有样例组合在一起
            if sample_pairs:
                samples = "\n\n".join(sample_pairs)
        
        # 如果上面的方法没有找到样例，尝试更简单的模式匹配
        if not samples:
            # 寻找最基本的样例格式
            basic_match = re.search(r'###\s+输入[\s\S]*?```([\s\S]*?)```[\s\S]*?###\s+输出[\s\S]*?```([\s\S]*?)```', description)
            if basic_match:
                sample_input = basic_match.group(1).strip()
                sample_output = basic_match.group(2).strip()
                samples = f"输入:\n{sample_input}\n\n输出:\n{sample_output}"
        
        title = self.problem_name.replace("_", " ")
        
        return title, input_format, output_format, samples
        
    def save_problem_description(self, problem_data: Optional[Dict[str, Any]] = None) -> str:
        """
        保存题目描述到文件
        如果提供了problem_data，则使用提供的数据，否则调用format_problem
        """
        if problem_data is None:
            problem_data = self.format_problem()
            
        if not problem_data:
            raise ValueError("题目格式化失败")
            
        # 提取题目名称和描述
        title = problem_data.get("title", "未命名题目")
        description = problem_data.get("description", "")
        
        # 创建题目目录
        base_dir = "problems"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        # 创建以题目名称命名的子目录
        self.problem_name = title.replace(" ", "_")
        self.current_problem_dir = os.path.join(base_dir, self.problem_name)
        if not os.path.exists(self.current_problem_dir):
            os.makedirs(self.current_problem_dir)
            
        # 创建测试数据目录
        self.test_cases_dir = os.path.join(self.current_problem_dir, "test_cases")
        if not os.path.exists(self.test_cases_dir):
            os.makedirs(self.test_cases_dir)
            
        # 保存题目文件 - 使用self.problem_name代替title，确保与后续查找一致
        problem_file = os.path.join(self.current_problem_dir, f"{self.problem_name}.txt")
        with open(problem_file, "w", encoding="utf-8") as f:
            f.write(description)
            
        # 保存题目元数据
        metadata = {
            "title": title,
            "difficulty": problem_data.get("difficulty", 0),
            "time_limit": problem_data.get("time_limit", 1000),
            "memory_limit": problem_data.get("memory_limit", 128),
            "has_subtasks": problem_data.get("has_subtasks", False),
        }
        
        # 如果有子任务信息，保存子任务数据
        if "subtasks" in problem_data:
            metadata["subtasks"] = problem_data["subtasks"]
        
        metadata_file = os.path.join(self.current_problem_dir, "metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        return problem_file
        
    def save_test_cases(self, test_cases: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        保存测试数据到文件
        返回保存的文件路径列表
        """
        if not test_cases:
            raise ValueError("测试数据为空")
            
        if not self.test_cases_dir:
            raise ValueError("测试数据目录未初始化")
            
        saved_files = []
        
        for i, (input_data, output_data) in enumerate(test_cases, 1):
            # 使用两位数格式的编号，如01, 02, 03...
            case_id = f"{i:02d}"
            
            # 保存输入数据
            input_file = os.path.join(self.test_cases_dir, f"{case_id}.in")
            with open(input_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(input_data.strip())
                
            # 保存输出数据
            output_file = os.path.join(self.test_cases_dir, f"{case_id}.out")
            with open(output_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(output_data.strip())
                
            saved_files.append((input_file, output_file))
            
        return saved_files
        
    def create_zip_package(self) -> str:
        """
        将测试数据打包为zip文件
        返回zip文件路径
        """
        if not self.problem_name or not self.current_problem_dir or not self.test_cases_dir:
            raise ValueError("题目尚未初始化")
            
        zip_file = os.path.join(self.current_problem_dir, f"{self.problem_name}_test_cases.zip")
        
        with zipfile.ZipFile(zip_file, "w") as zipf:
            for file_name in os.listdir(self.test_cases_dir):
                file_path = os.path.join(self.test_cases_dir, file_name)
                if os.path.isfile(file_path):
                    zipf.write(file_path, arcname=file_name)
                    
        return zip_file 