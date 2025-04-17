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
请根据以下描述，创建一个富有趣味性的算法竞赛题目，风格应既符合信息学奥林匹克竞赛(OI)的标准规范，又具有生动有趣的情景和角色设定。题目必须包含以下部分，使用良好的 Markdown 格式：

1. 题目名称（简短明确，富有创意）
2. 题目描述（通过有趣的情景和角色来描述算法问题，可以引入以下元素之一：
   - 经典动画/游戏角色（如哆啦A梦、马里奥、宝可梦等）
   - 历史/文学人物（如诸葛亮、哈利波特等）
   - 创意情景（如太空冒险、魔法学院、科技公司等）
   使用标准数学符号如 $n$、$a_i$ 等，并将它们融入到情景中）
3. 输入格式（清晰简洁地描述输入的结构）
4. 输出格式（清晰简洁地描述输出的要求）
5. 样例（至少提供2个有代表性的输入输出样例，可以在样例说明中继续延伸情景）
6. 数据范围与提示（使用规范的数学符号描述数据范围，如 $1 \\leq n \\leq 10^5$，必要时分档说明不同测试点的约束）

用户描述: {self.problem_description}

请按照以下JSON格式返回结果，确保输出良好的 Markdown 格式内容：
{{
    "title": "题目名称",
    "description": "题目描述（有趣的情景与角色，同时准确描述问题）",
    "input_format": "输入格式（简明扼要，使用规范的 Markdown 格式）",
    "output_format": "输出格式（简明扼要，使用规范的 Markdown 格式）",
    "samples": [
        {{
            "input": "样例输入1",
            "output": "样例输出1",
            "explanation": "样例解释1（详细解释样例，同时与情景呼应）"
        }},
        {{
            "input": "样例输入2",
            "output": "样例输出2",
            "explanation": "样例解释2（详细解释样例，同时与情景呼应）"
        }}
    ],
    "hints": "数据范围与提示（使用规范的数学符号表示，并提供解题思路）",
    "difficulty": 难度等级(1-5之间的整数，1最简单，5最难),
    "time_limit": 时间限制(毫秒),
    "memory_limit": 内存限制(MB)
}}

格式要求与规范：
1. 题目必须通过有趣的情景或角色来引入问题，使枯燥的算法问题变得生动有趣
2. 情景应当合理地融入问题描述，而不是简单地添加无关的背景故事
3. 使用标准的数学符号表示变量和约束，数学公式要用 $ 符号包裹，格式规范
4. 输入输出格式描述要使用清晰的 Markdown 格式，列表使用 - 或 1. 格式
5. 样例部分确保提供至少两个代表性样例，并附有详细解释
6. 数据范围必须使用规范的数学表示法，分档说明测试点的约束
7. 整体风格应既符合OI题目的严谨性，又具有生动有趣的叙述方式
8. 请确保所有字段中的 Markdown 格式正确，包括标题、列表、代码块等
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
                
            # 使用基类方法处理描述，合并相关字段并美化格式
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
我需要为以下算法题目生成{self.test_cases_count}组测试数据，每组包含输入和对应的正确输出。这个题目具有富有趣味性的情景设定。

题目名称: {title}

题目描述:
{description}

请为这个题目生成{self.test_cases_count}组有效的测试数据，包括以下类型：
1. 基础测试用例（简单情况，能快速验证算法正确性）
2. 边界情况测试（最大/最小值，特殊情况如0、负数、空集等）
3. 随机大规模测试（接近题目中描述的数据范围上限）
4. 具有陷阱的测试用例（可能导致常见错误的情况）
5. 能体现题目趣味性情景的特殊测试用例（与题目的角色或场景相关）

请确保测试数据具有以下特点：
- 测试数据应该由易到难，逐步增加难度和规模
- 每个测试用例都是有效的，符合题目输入格式的约束
- 输出必须是按照题目输出格式的正确结果
- 测试用例应该覆盖题目中描述的各种情况和边界条件
- 对于每个测试用例，提供一个简短的描述，说明该测试用例的目的和特点

请按照以下JSON格式返回结果:
{
    "test_cases": [
        {
            "input": "测试输入1",
            "output": "期望输出1",
            "description": "这是一个基础测试用例，用于验证简单情况下的正确性"
        },
        {
            "input": "测试输入2",
            "output": "期望输出2", 
            "description": "这是一个边界情况测试，测试最小值情况"
        },
        ... 更多测试用例
    ]
}

务必确保：
1. 每个测试用例的输入格式严格符合题目要求
2. 输出是基于给定输入的正确解答
3. 测试用例覆盖足够多的情况，能够充分测试算法的正确性
4. 包含与题目情景相关的有趣测试用例
5. 对于大规模数据，保证数据生成的随机性和多样性
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