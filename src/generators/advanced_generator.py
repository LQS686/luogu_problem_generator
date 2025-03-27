"""
高级题目生成器 - 生成带子任务的题目
"""
import os
import json
import re
from typing import Dict, List, Tuple, Any

from .base_generator import BaseProblemGenerator
from ..utils.api_utils import call_api


class AdvancedProblemGenerator(BaseProblemGenerator):
    """高级题目生成器类，支持子任务"""
    
    def __init__(self):
        super().__init__()
        self.has_subtasks = True
        self.subtask_count = 3  # 默认子任务数量
        self.test_cases_per_subtask = 3  # 每个子任务的默认测试点数量
        
    def format_problem(self) -> Dict[str, Any]:
        """
        格式化题目描述，生成完整的带子任务的题目
        """
        if not self.problem_description:
            raise ValueError("题目描述不能为空")
            
        prompt = f"""
请根据以下描述，创建一个完整的带子任务的算法竞赛题目，风格应符合信息学奥林匹克竞赛(OI)的标准规范，必须包含以下部分：

1. 题目名称（简短明确，专业）
2. 题目描述（简洁准确地阐述问题，使用标准数学符号如$n$、$a_i$等，避免冗余描述）
3. 输入格式（清晰简洁地描述输入的结构）
4. 输出格式（清晰简洁地描述输出的要求）
5. 样例（提供有代表性的输入输出样例）
6. 子任务设置（{self.subtask_count}个子任务，难度递增，每个子任务有明确的约束和分值）
7. 数据范围与提示（使用规范的数学符号描述数据范围，分档说明不同子任务的约束）

用户描述: {self.problem_description}

请按照以下JSON格式返回结果:
{{
    "title": "题目名称",
    "description": "题目描述（简洁准确）",
    "input_format": "输入格式（简明扼要）",
    "output_format": "输出格式（简明扼要）",
    "samples": [
        {{"input": "样例输入1", "output": "样例输出1"}},
        {{"input": "样例输入2", "output": "样例输出2"}}
    ],
    "hints": "通用数据范围与提示",
    "difficulty": 难度等级(1-5之间的整数，1最简单，5最难),
    "time_limit": 时间限制(毫秒),
    "memory_limit": 内存限制(MB),
    "subtasks": [
        {{
            "id": 1,
            "score": 第一个子任务的分值,
            "description": "对于$20\\%$的数据，$n \\leq 10$",
            "test_cases": [1, 2, 3]  // 关联的测试用例编号
        }},
        {{
            "id": 2,
            "score": 第二个子任务的分值,
            "description": "对于$50\\%$的数据，$n \\leq 10^3$",
            "test_cases": [4, 5, 6]  // 关联的测试用例编号
        }},
        {{
            "id": 3,
            "score": 第三个子任务的分值,
            "description": "对于$100\\%$的数据，$n \\leq 10^5$",
            "test_cases": [7, 8, 9, 10]  // 关联的测试用例编号
        }}
    ]
}}

确保：
1. 使用专业、简洁的语言，避免不必要的修饰
2. 题目描述应当直接切入主题，无需多余的背景故事
3. 使用标准的数学符号表示变量和约束
4. 输入输出格式描述应当简明扼要
5. 数据范围必须使用规范的数学表示法，分档说明不同子任务的约束
6. 子任务约束应以"对于X%的数据"开头，符合OI习惯
7. 子任务的分值总和为100分
8. 整体风格应符合标准OI题目，如"数楼梯"、"选数"等经典题目的风格
"""
        
        try:
            # 调用API获取完整题目
            response = call_api(prompt)
            
            # 使用基类方法解析返回的JSON
            problem_data = self.parse_api_response(response)
            
            # 确保必要字段存在
            required_fields = ["title", "description", "difficulty", "subtasks"]
            for field in required_fields:
                if field not in problem_data:
                    raise ValueError(f"生成的题目缺少必要字段: {field}")
            
            # 设置默认值
            if "time_limit" not in problem_data:
                problem_data["time_limit"] = 1000
            if "memory_limit" not in problem_data:
                problem_data["memory_limit"] = 256
                
            # 确保子任务字段存在并符合要求
            subtasks = problem_data.get("subtasks", [])
            if not subtasks or len(subtasks) < 1:
                raise ValueError("生成的子任务为空")
                
            # 验证子任务分值总和是否为100
            total_score = sum(subtask.get("score", 0) for subtask in subtasks)
            if total_score != 100:
                # 调整分值，确保总和为100
                factor = 100 / total_score if total_score > 0 else 0
                for subtask in subtasks:
                    subtask["score"] = int(subtask.get("score", 0) * factor)
                
                # 处理剩余的误差
                remainder = 100 - sum(subtask.get("score", 0) for subtask in subtasks)
                if remainder != 0 and subtasks:
                    subtasks[-1]["score"] += remainder
            
            # 使用基类方法处理描述，合并相关字段
            description = self.process_description(problem_data)
            
            # 处理子任务描述
            if "子任务" not in description:
                description += "\n\n## 子任务\n"
                for i, subtask in enumerate(subtasks, 1):
                    st_desc = subtask.get("description", "")
                    st_score = subtask.get("score", 0)
                    description += f"\n{i}. 子任务 {i}（{st_score} 分）：{st_desc}"
            
            problem_data["description"] = description
            problem_data["has_subtasks"] = True
            
            return problem_data
            
        except Exception as e:
            raise RuntimeError(f"格式化题目失败: {str(e)}")
            
    def generate_test_cases(self) -> List[Tuple[str, str]]:
        """
        生成带子任务的测试数据
        返回(输入, 输出)元组的列表
        """
        if not self.problem_name:
            # 如果题目还没格式化，先格式化
            problem_data = self.format_problem()
            # 保存题目描述，这步会设置self.problem_name
            self.save_problem_description(problem_data)
            
        # 获取题目描述文件中的内容
        problem_file = os.path.join(self.current_problem_dir, f"{self.problem_name}.txt")
        if not os.path.exists(problem_file):
            raise ValueError(f"题目文件不存在: {problem_file}")
            
        with open(problem_file, "r", encoding="utf-8") as f:
            description = f.read()
            
        # 使用基类方法提取样例数据
        title, input_format, output_format, samples = self.extract_sample_data(description)
        
        # 读取元数据获取子任务数量
        metadata_file = os.path.join(self.current_problem_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                # 如果有子任务信息，获取子任务数量
                if "subtasks" in metadata:
                    self.subtask_count = len(metadata["subtasks"])
        
        # 计算每个子任务的测试点数量
        # 确保至少有一个测试点，并且总数与test_cases_count相符
        tests_per_subtask = max(1, self.test_cases_count // self.subtask_count)
        self.test_cases_per_subtask = tests_per_subtask
        
        # 提取子任务描述
        subtasks_match = re.search(r'## 子任务\s*([\s\S]*?)(?=## |$)', description)
        subtasks_desc = ""
        if subtasks_match:
            subtasks_desc = subtasks_match.group(1).strip()
        
        # 构建生成测试数据的提示
        prompt = f"""
我需要为以下带子任务的算法题目生成测试数据。
题目有{self.subtask_count}个子任务，每个子任务应生成{self.test_cases_per_subtask}组测试数据。

题目名称: {title}

题目描述:
{description}

输入格式:
{input_format}

输出格式:
{output_format}

样例数据:
{samples}

子任务设置:
{subtasks_desc}

请为每个子任务生成{self.test_cases_per_subtask}组测试数据，即总共{self.subtask_count * self.test_cases_per_subtask}组。
对于每一个子任务，测试数据应该满足该子任务的限制条件，并且难度应该符合子任务的要求。
对于每一组测试数据，提供输入和期望的输出。

请按照以下JSON格式返回结果:
{{
    "test_cases": [
        {{
            "subtask": 1,
            "input": "子任务1的测试输入1",
            "output": "期望输出1"
        }},
        {{
            "subtask": 1,
            "input": "子任务1的测试输入2",
            "output": "期望输出2"
        }},
        ... 更多子任务1的测试用例
        
        {{
            "subtask": 2,
            "input": "子任务2的测试输入1",
            "output": "期望输出1"
        }},
        ... 更多子任务的测试用例
    ]
}}

确保输入格式符合题目要求，输出是正确的解答。
"""
        
        try:
            # 调用API获取测试数据
            response = call_api(prompt)
            
            # 使用基类方法解析返回的JSON
            test_data = self.parse_api_response(response)
            
            # 提取测试用例
            test_cases = test_data.get("test_cases", [])
            if not test_cases:
                raise ValueError("API未返回有效的测试用例")
                
            # 转换为所需的格式
            formatted_test_cases = []
            for case in test_cases:
                case_id = case.get("id", "")
                input_data = case.get("input", "").strip()
                output_data = case.get("output", "").strip()
                
                if not case_id or not input_data or not output_data:
                    continue
                    
                # 保留原始ID格式作为子任务分组
                formatted_test_cases.append((input_data, output_data))
            
            # 保存测试用例到文件
            if formatted_test_cases:
                self.save_test_cases(formatted_test_cases)
                
            return formatted_test_cases
            
        except Exception as e:
            raise RuntimeError(f"生成测试数据失败: {str(e)}") 