"""
简单题目生成器 - 生成不带子任务的题目
"""
import os
import json
import random
from typing import Dict, List, Tuple, Any

from .base_generator import BaseProblemGenerator
from ..utils.api_utils import call_api


class SimpleProblemGenerator(BaseProblemGenerator):
    """简单题目生成器类"""
    
    def __init__(self):
        super().__init__()
        
    def format_problem(self) -> Dict[str, Any]:
        """
        格式化题目描述，生成完整的题目
        """
        if not self.problem_description:
            raise ValueError("题目描述不能为空")
            
        prompt = f"""
请根据以下描述，创建一个完整的算法竞赛题目，风格应符合信息学奥林匹克竞赛(OI)的标准规范，必须包含以下部分：

1. 题目名称（简短明确，专业）
2. 题目描述（简洁准确地阐述问题，使用标准数学符号如$n$、$a_i$等，避免冗余描述）
3. 输入格式（清晰简洁地描述输入的结构）
4. 输出格式（清晰简洁地描述输出的要求）
5. 样例（提供有代表性的输入输出样例）
6. 数据范围与提示（使用规范的数学符号描述数据范围，如$1 \\leq n \\leq 10^5$，必要时分档说明不同测试点的约束）

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
    "hints": "数据范围与提示（使用规范的数学符号表示）",
    "difficulty": 难度等级(1-5之间的整数，1最简单，5最难),
    "time_limit": 时间限制(毫秒),
    "memory_limit": 内存限制(MB)
}}

确保：
1. 使用专业、简洁的语言，避免不必要的修饰
2. 题目描述应当直接切入主题，无需多余的背景故事
3. 使用标准的数学符号表示变量和约束
4. 输入输出格式描述应当简明扼要
5. 数据范围必须使用规范的数学表示法，分档说明测试点的约束
6. 整体风格应符合标准OI题目，如"数楼梯"、"选数"等经典题目的风格
"""
        
        try:
            # 调用API获取完整题目
            response = call_api(prompt)
            
            # 使用基类中的方法解析返回的JSON
            problem_data = self.parse_api_response(response)
            
            # 确保必要字段存在
            required_fields = ["title", "description", "difficulty"]
            for field in required_fields:
                if field not in problem_data:
                    raise ValueError(f"生成的题目缺少必要字段: {field}")
            
            # 设置默认值
            if "time_limit" not in problem_data:
                problem_data["time_limit"] = 1000
            if "memory_limit" not in problem_data:
                problem_data["memory_limit"] = 128
                
            # 使用基类方法处理描述，合并相关字段
            problem_data["description"] = self.process_description(problem_data)
            
            return problem_data
            
        except Exception as e:
            raise RuntimeError(f"格式化题目失败: {str(e)}")
            
    def generate_test_cases(self) -> List[Tuple[str, str]]:
        """
        生成测试数据
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
        
        # 构建生成测试数据的提示
        prompt = f"""
我需要为以下算法题目生成{self.test_cases_count}组测试数据，每组包含输入和对应的正确输出。

题目名称: {title}

题目描述:
{description}

输入格式:
{input_format}

输出格式:
{output_format}

样例数据:
{samples}

请为这个题目生成{self.test_cases_count}组有效的测试数据，包括基础测试用例和边界情况。
测试数据应该能够全面测试解答的正确性。
对于每一组测试数据，提供输入和期望的输出。

请按照以下JSON格式返回结果:
{{
    "test_cases": [
        {{
            "input": "测试输入1",
            "output": "期望输出1"
        }},
        {{
            "input": "测试输入2",
            "output": "期望输出2"
        }},
        ... 更多测试用例
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
                input_data = case.get("input", "").strip()
                output_data = case.get("output", "").strip()
                if input_data and output_data:  # 确保输入和输出都不为空
                    formatted_test_cases.append((input_data, output_data))
            
            # 保存测试用例到文件
            if formatted_test_cases:
                self.save_test_cases(formatted_test_cases)
                
            return formatted_test_cases
            
        except Exception as e:
            raise RuntimeError(f"生成测试数据失败: {str(e)}")