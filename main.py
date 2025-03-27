"""
洛谷出题工具 - 主程序入口点
"""
import os
import sys
import argparse
import importlib.util

# 确保所有源码目录在导入路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 检查外部依赖是否安装
def check_module(module_name):
    """检查模块是否已安装"""
    return importlib.util.find_spec(module_name) is not None

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("警告: python-dotenv模块未安装，无法从.env加载环境变量")
    # 手动实现简单的.env加载
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="洛谷出题工具")
    parser.add_argument("--no-gui", action="store_true", help="使用命令行模式而非GUI")
    parser.add_argument("--description", type=str, help="题目描述（仅命令行模式）")
    parser.add_argument("--theme", type=str, choices=["light", "dark"], default=None, 
                       help="设置界面主题 (light/dark)，默认为dark")
    parser.add_argument("--test-cases", type=int, default=10, 
                        help="生成的测试点数量，默认为10")
    return parser.parse_args()


def run_cli_mode(args):
    """运行命令行模式"""
    # 检查必要模块
    if not check_module('requests'):
        print("错误: requests模块未安装，CLI模式无法正常工作")
        print("请安装: pip install requests")
        return 1
    
    try:
        from src.generators.simple_generator import SimpleProblemGenerator
        
        # 获取题目描述
        description = args.description
        if not description:
            print("请输入题目描述:")
            description = input().strip()
            
        if not description:
            print("错误: 题目描述不能为空")
            return 1
            
        # 选择生成器
        generator = SimpleProblemGenerator()
        print("使用简单生成器")
            
        # 设置生成器参数
        generator.problem_description = description
        
        # 设置测试点数量
        if args.test_cases > 0:
            generator.test_cases_count = args.test_cases
            print(f"将生成 {args.test_cases} 个测试点")
        else:
            print("警告: 测试点数量必须大于0，使用默认值10")
            generator.test_cases_count = 10
        
        try:
            # 生成题目
            print("正在格式化题目...")
            problem_data = generator.format_problem()
            
            print(f"题目: {problem_data.get('title', '未命名题目')}")
            print(f"难度: {problem_data.get('difficulty', 0)}/5")
            
            # 生成测试数据
            print("正在生成测试数据...")
            test_cases = generator.generate_test_cases()
            
            print(f"生成了 {len(test_cases)} 个测试用例")
            print(f"文件保存在: {generator.current_problem_dir}")
            
            return 0
        except Exception as e:
            print(f"生成过程中出错: {str(e)}")
            return 1
    except Exception as e:
        print(f"初始化生成器失败: {str(e)}")
        return 1


def run_gui_mode():
    """运行GUI模式"""
    # 检查PyQt6安装
    if not check_module('PyQt6'):
        print("错误: PyQt6 模块未安装，GUI模式无法运行")
        print("请安装: pip install PyQt6")
        return 1
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # 读取环境变量中的主题设置，默认为dark
        theme = os.environ.get("THEME", "dark").lower()
        
        # 加载主题样式
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            if theme == "light":
                style_path = os.path.join(base_path, "assets", "styles", "light_theme.qss")
                theme_name = "浅色主题"
            else:
                style_path = os.path.join(base_path, "assets", "styles", "dark_theme.qss")
                theme_name = "暗色主题"
                
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    app.setStyleSheet(f.read())
                print(f"已加载{theme_name}: {style_path}")
            else:
                print(f"未找到主题文件: {style_path}")
        except Exception as e:
            print(f"加载主题出错: {str(e)}")
        
        window = MainWindow()
        # 设置主题状态以匹配加载的主题
        window.is_dark_theme = (theme != "light")
        window.show()
        
        return app.exec()
    except ImportError as e:
        missing_modules = []
        if not check_module('PyQt6'):
            missing_modules.append("PyQt6")
        if not check_module('requests'):
            missing_modules.append("requests")
            
        if missing_modules:
            print(f"错误: 缺少以下必要模块: {', '.join(missing_modules)}")
            print(f"请安装: pip install {' '.join(missing_modules)}")
        else:
            print(f"导入GUI模块失败: {str(e)}")
        return 1


def create_needed_directories():
    """创建必要的目录结构"""
    needed_dirs = [
        "problems",  # 题目保存目录
        "assets",    # 资源目录
        "assets/icons",  # 图标目录
        "assets/styles"  # 样式表目录
    ]
    
    for directory in needed_dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"创建目录 {directory} 失败: {str(e)}")


def check_requirements():
    """检查运行环境是否满足需求"""
    missing_modules = []
    
    # 检查必要模块
    if not check_module('requests'):
        missing_modules.append("requests")
    
    if not check_module('PyQt6'):
        missing_modules.append("PyQt6")
    
    if missing_modules:
        print("警告: 缺少以下模块，某些功能可能无法使用:")
        for module in missing_modules:
            print(f"  - {module}")
        print("可以使用以下命令安装全部依赖: pip install PyQt6 requests python-dotenv")
    
    # 检查API密钥设置
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("警告: 未设置 DEEPSEEK_API_KEY 环境变量，可能影响题目生成功能")
        print("您可以在 .env 文件中设置 DEEPSEEK_API_KEY=您的密钥")
            
    return True


def main():
    """主函数"""
    args = parse_args()
    
    # 创建必要的目录
    create_needed_directories()
    
    # 手动加载环境变量
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # 如果命令行指定了主题，则覆盖环境变量
    if args.theme:
        os.environ["THEME"] = args.theme
    
    # 检查环境需求
    check_requirements()
    
    # 根据不同模式运行程序
    if args.no_gui:
        return run_cli_mode(args)
    else:
        return run_gui_mode()


if __name__ == "__main__":
    sys.exit(main()) 