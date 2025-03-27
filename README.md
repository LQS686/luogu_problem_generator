# 洛谷题目生成器

一个用于自动生成符合洛谷要求的算法竞赛题目和测试数据的工具。该工具采用PyQt6构建，具有现代化的用户界面和强大的生成能力。

## 功能特点

- **完整题目生成**：自动生成题目描述、输入输出格式、样例等内容
- **高质量测试数据**：根据题目要求生成多组测试数据
- **自定义测试点**：支持自定义生成的测试点数量
- **现代化界面**：使用PyQt6构建的美观界面，支持深色/浅色主题切换
- **内嵌SVG图标**：使用Base64编码的SVG图标，无需外部图标文件
- **命令行支持**：同时支持命令行和GUI两种使用方式
- **题目管理器**：内置题目管理器，可以方便地查看和编辑已生成的题目
- **文件管理**：统一的文件组织结构，自动打包测试数据
- **测试用例编辑**：支持在界面上直接编辑测试用例的输入和输出

## 安装说明

### 环境要求

- Python 3.8+
- PyQt6
- requests (API调用)
- 网络连接（用于API调用）

### 安装步骤

1. 克隆代码库:

```bash
git clone https://github.com/LQS686/luogu_problem_generator.git
cd luogu_problem_generator
```

2. 安装依赖:

```bash
pip install -r requirements.txt
```

3. 配置API密钥:

在项目根目录创建`.env`文件，添加以下内容：

```
DEEPSEEK_API_KEY=您的DeepSeek API密钥
```

## 使用说明

### GUI模式

```bash
python main.py

# 使用浅色主题启动
python main.py --theme light

# 使用深色主题启动
python main.py --theme dark
```

启动后，输入题目描述，设置测试点数量，点击"生成题目"按钮即可开始生成。

#### 主题配置

您可以通过以下三种方式设置应用主题：

1. **命令行参数**：使用 `--theme` 参数指定主题
   ```bash
   python main.py --theme light  # 使用浅色主题
   python main.py --theme dark   # 使用深色主题
   ```

2. **环境变量配置**：在 `.env` 文件中设置 `THEME` 变量
   ```
   THEME=light  # 浅色主题
   THEME=dark   # 深色主题（默认）
   ```

3. **应用内切换**：通过工具栏上的"切换主题"按钮，可以实时切换深色和浅色主题

#### 工具栏功能

- **清空**：清空输入和输出区域
- **题目管理**：打开题目管理器，可查看和编辑已生成的题目和测试数据
- **浏览题目**：直接打开题目文件夹，查看所有已生成的题目
- **切换主题**：在暗色和浅色主题间切换
- **模型设置**：配置DeepSeek API密钥，用于生成题目
- **帮助**：显示使用帮助信息
- **关于**：显示版本和版权信息
- **退出**：关闭应用程序

#### 题目管理器

题目管理器提供以下功能：

- **题目浏览**：查看所有已生成的题目
- **测试用例编辑**：编辑测试用例的输入和输出
- **测试用例搜索**：快速搜索和筛选测试用例
- **题目更新**：修改题目描述并保存更改
- **一键打包**：自动更新测试用例zip包

### 命令行模式

```bash
# 生成题目
python main.py --no-gui --description "设计一个计算斐波那契数列的题目"

# 指定测试点数量（默认为10）
python main.py --no-gui --description "设计一个字符串匹配题目" --test-cases 20

# 同时设置主题（GUI模式下有效）
python main.py --theme light --description "设计一个计算斐波那契数列的题目"
```

## 文件结构

生成的文件将保存在`problems`目录下，每个题目会创建一个独立的子目录，包含：

- `题目名称.txt`：题目描述文件
- `metadata.json`：题目元数据，包含难度、时间限制等信息
- `test_cases/`：测试数据目录
  - `001.in`、`001.out`等：测试输入输出文件
- `题目名称_test_cases.zip`：打包好的测试数据

## 界面预览

应用程序提供了一个现代化的用户界面，包含以下特点：
- 美观的深色/浅色主题
- 简洁直观的工具栏
- 分离的输出和日志视图
- 实时进度显示
- 卡片式布局
- 增强的视觉反馈

## 开发者说明

### 项目结构

```
luogu_problem_generator/
├── main.py                 # 程序入口点
├── requirements.txt        # 依赖管理
├── README.md               # 项目文档
├── assets/                 # 资源文件
│   ├── icons/              # 图标资源
│   └── styles/             # QSS样式表
│       ├── dark_theme.qss  # 深色主题
│       └── light_theme.qss # 浅色主题
├── problems/               # 生成的题目
└── src/                    # 源代码
    ├── models/             # 数据模型
    ├── generators/         # 生成器
    │   ├── base_generator.py    # 基础生成器
    │   └── simple_generator.py  # 简单题目生成器
    ├── utils/              # 工具函数
    │   ├── icons.py        # 图标资源
    │   └── api_utils.py    # API调用工具
    └── gui/                # 界面相关代码
        ├── main_window.py  # 主窗口
        └── widgets/        # 自定义控件
            └── problem_manager.py # 题目管理器
```

### 扩展功能

您可以通过修改以下文件来扩展功能：

- `src/generators/base_generator.py`：修改基础生成器逻辑
- `src/generators/simple_generator.py`：修改题目的生成逻辑
- `src/utils/api_utils.py`：调整API调用参数或更换模型
- `assets/styles/dark_theme.qss`：修改深色主题样式
- `assets/styles/light_theme.qss`：修改浅色主题样式
- `src/utils/icons.py`：添加或更改图标资源

## 自定义主题

应用程序支持完全自定义主题。默认提供了深色和浅色两种主题，您可以通过修改以下文件来自定义主题：

- `assets/styles/dark_theme.qss`：深色主题
- `assets/styles/light_theme.qss`：浅色主题

或者添加新的主题文件，并在 `src/gui/main_window.py` 中的 `toggle_theme` 方法中添加对新主题的支持。

## 许可证

MIT

## 贡献指南

欢迎提交Issues和Pull Requests来改进这个项目。在提交代码前，请确保：

1. 代码符合PEP 8规范
2. 添加了适当的测试
3. 更新了文档以反映您的更改

## 更新日志

### v2.2
- 简化了用户界面，移除了子任务功能
- 优化了代码结构，减少了复杂性
- 改进了API密钥验证流程
- 更新了帮助和关于信息

### v2.1
- 添加了浅色主题支持
- 优化了工具栏布局和功能
- 改进了图标加载机制，使用SVG图标
- 增强了题目管理器功能，支持测试用例搜索
- 添加了测试点数量自定义功能
- 优化了代码结构，减少冗余代码
- 修复了多处UI细节问题
- 添加了欢迎消息和使用提示

### v2.0
- 初始版本发布
- 深色主题支持
- 基本的题目生成功能
- 命令行和GUI模式支持

## 常见问题

**问：为什么生成的题目质量不高？**
答：题目质量与API模型有关，您可以尝试调整API调用参数或更换其他模型。

**问：如何获取DeepSeek API密钥？**
答：请访问DeepSeek官方网站注册并申请API密钥。

**问：支持哪些操作系统？**
答：支持Windows、macOS和Linux，只要安装了Python和必要的依赖。

**问：如何添加新的主题？**
答：在 `assets/styles/` 目录下创建新的.qss文件，然后修改 `main_window.py` 中的 `toggle_theme` 方法以支持新主题。

**问：如何更改默认主题？**
答：创建 `.env` 文件并设置 `THEME=light` 或 `THEME=dark`，或者在启动时使用 `--theme` 参数。

**问：主题设置优先级是怎样的？**
答：命令行参数 `--theme` 的优先级最高，其次是 `.env` 文件中的设置，最后是程序内部的默认值（深色主题）。

**问：如何设置生成的测试点数量？**
答：在GUI模式下，可以在主界面的"测试点数量"输入框中指定；在命令行模式下，可以使用 `--test-cases` 参数，例如 `--test-cases 20` 生成20个测试点。

**问：为什么图标加载出错？**
答：本应用使用内嵌的SVG图标，无需外部图标文件。如果图标加载出错，可能是QT版本不兼容，可尝试升级PyQt6到最新版本。 