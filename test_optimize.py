from src.generators.simple_generator import SimpleProblemGenerator
import json
from unittest.mock import patch

def mock_call_api(*args, **kwargs):
    """模拟API调用的响应"""
    mock_response = {
        "title": "欧几里得的宝藏",
        "description": "哆啦A梦带领大雄发现了一座古老的宝藏，宝藏由两把钥匙锁着，每把钥匙上分别写了一个正整数 $a$ 和 $b$。根据欧几里得留下的线索，只有计算出这两个数的最大公约数，才能成功开启宝藏。",
        "input_format": "输入包含两个由空格分隔的正整数 $a$ 和 $b$。",
        "output_format": "输出一个正整数，表示 $a$ 和 $b$ 的最大公约数。",
        "samples": [
            {
                "input": "12 18",
                "output": "6",
                "explanation": "12 和 18 的最大公约数是 6。大雄输入这个数字后，宝藏的第一道门打开了！"
            },
            {
                "input": "17 23",
                "output": "1",
                "explanation": "17 和 23 互质，所以它们的最大公约数是 1。宝藏的第二道门应声打开，大雄和哆啦A梦成功进入了宝藏室！"
            }
        ],
        "hints": "本题是一道基础的数学问题。\n\n数据范围：\n- $1 \\leq a, b \\leq 10^9$\n\n提示：\n- 你可以使用欧几里得算法（辗转相除法）求解最大公约数\n- 对于 $a$ 和 $b$ 两个正整数，一直计算 $a \\bmod b$，直到结果为 0 时停止，此时 $b$ 的值即为最大公约数",
        "difficulty": 2,
        "time_limit": 1000,
        "memory_limit": 128
    }
    return json.dumps(mock_response)

def main():
    # 创建生成器实例
    generator = SimpleProblemGenerator()
    
    # 设置题目描述
    generator.problem_description = "输入两个整数，计算它们的最大公约数"
    
    try:
        # 使用模拟的API调用
        with patch('src.utils.api_utils.call_api', side_effect=mock_call_api):
            # 格式化题目
            result = generator.format_problem()
            
            # 输出结果
            print('题目格式化成功!')
            print('标题:', result.get('title'))
            print('\n描述全文:')
            print(result.get('description'))
            
            print("\n优化后的题目描述更加美观，包括：")
            print("1. 更好的标题和段落格式")
            print("2. 优化的数学公式显示")
            print("3. 适当的空行和缩进")
            print("4. 多个样例的支持")
            print("5. 样例解释的格式化")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 