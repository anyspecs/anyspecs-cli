<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/headerDark.svg" />
    <img src="assets/headerLight.svg" alt="AnySpecs CLI" />
  </picture>

***Code is cheap, Show me Any Specs.***
  
[:page_facing_up: English Version](https://github.com/anyspecs/anyspecs-cli/blob/main/README.md) |
[:gear: 快速上手](#quick-start) |
[:thinking: 报告问题](https://github.com/anyspecs/anyspecs-cli/issues/new/choose)

</div>

AnySpecs CLI 是一个统一的命令行工具，用于从多个 AI 助手导出聊天记录。它目前支持 **Cursor AI**、**Claude Code** 和 **Kiro**，并支持多种导出格式，包括 Markdown、HTML 和 JSON。

## ✨ 功能特性

- **多源支持**: 从 Cursor AI、Claude Code 和 Kiro Records 导出（预计支持更多）。
- **多种导出格式**: 支持 Markdown、HTML 和 JSON。
- **项目与工作区过滤**: 按项目或当前目录导出聊天会话。
- **灵活的会话管理**: 列表、筛选和导出特定的聊天会话。
- **默认导出目录**: 所有导出的文件默认保存到 `.anyspecs/` 目录，以便于整理。
- **AI 总结**: 将聊天记录总结为单个文件 (开发中)。
- **服务器上传与分享**: 上传导出的文件到远程服务器 (开发中)。

## 📦 安装

### 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/anyspecs/anyspecs-cli.git
cd anyspecs-cli

# 以开发模式安装
pip install -e .

# 或者普通安装
pip install .
```

### 使用 pip 安装

```bash
pip install anyspecs
```

## 🚀 快速上手

### 列出当前工作区的所有聊天会话

```bash
# 列出所有来源的当前工作区的聊天会话
anyspecs list

# 仅列出当前工作区的 Cursor/Claude/Kiro 会话
anyspecs list --source cursor/claude/kiro

# 显示详细信息
anyspecs list --verbose
```

### 导出聊天会话

```bash
# 导出当前项目的会话为 Markdown (默认到 .anyspecs/ 目录)
anyspecs export

# 导出所有项目的会话为 HTML (默认到 .anyspecs/ 目录)
anyspecs export --all-projects --format html

# 导出指定的会话
anyspecs export --session-id abc123 --format json

# 仅导出 Claude 的会話
anyspecs export --source claude --format markdown

# 仅导出 Kiro 的记录
anyspecs export --source kiro --format html

# 导出到自定义输出路径
anyspecs export --output ./exports --format html

# 导出并上传到服务器 (开发中)
anyspecs export --format json --upload --server https://myserver.com --username user --password pass
```

## 🔌 支持的来源

### Cursor AI

从 Cursor 的本地 SQLite 数据库中提取聊天记录，包括：
- 特定于工作区的对话
- 全局聊天存储
- 编辑器中的对话和气泡对话
- 项目上下文和元数据

### Claude Code

从 Claude Code 的 JSONL 历史文件中提取聊天记录，包括：
- 用户消息和 AI 回复
- 工具调用和结果
- 会话元数据
- 项目上下文

### Kiro Records

从 `.kiro` 目录中提取和合并 Markdown 文档，包括：
- 文件元数据 (名称、修改时间)
- 自动项目摘要检测

## 📁 包结构

```
anyspecs-cli/
├── anyspecs/
│   ├── __init__.py          # 主包
│   ├── cli.py               # CLI 界面
│   ├── config.py           # 配置管理
│   ├── core/               # 核心功能
│   │   ├── extractors.py   # 提取器基类
│   │   └── formatters.py   # 导出格式化器
│   ├── exporters/          # 特定来源的提取器
│   │   ├── cursor.py       # Cursor AI 提取器
│   │   └── claude.py       # Claude Code 提取器
│   │   └── kiro.py         # Kiro Records 提取器
│   └── utils/              # 工具模块
│       ├── logging.py      # 日志配置
│       ├── paths.py        # 路径工具
│       └── upload.py       # 上传功能
├── setup.py               # 包安装文件
├── requirements.txt       # 依赖项
└── README.md             # 本文档
```

## 🤝 贡献

欢迎任何形式的贡献！请随时提交拉取请求 (Pull Request)。

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/anyspecs/anyspecs-cli.git
cd anyspecs-cli

# 以开发模式安装并包含开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 格式化代码
black anyspecs/

# 类型检查
mypy anyspecs/
```

## 📄 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## 📜 更新日志

### v0.0.2
- **Kiro Records 支持**: 提取并导出 `.kiro` 目录中的文件。
- **默认导出目录**: 所有导出的文件默认保存到 `.anyspecs/` 目录。
- **工作区过滤**: `list` 命令现在只显示当前工作区的 Cursor 会话。

### v0.0.1
- 初始版本发布。
- 支持 Cursor AI 和 Claude Code。
- 多种导出格式 (Markdown, HTML, JSON)。
- 上传功能。
- 基于项目的筛选。
- 组织良好的包结构。

## 💬 支持

如果您遇到任何问题或有任何疑问，请：

1.  查看 [文档](https://github.com/anyspecs/anyspecs-cli/wiki) (如果存在)。
2.  搜索 [现有的问题](https://github.com/anyspecs/anyspecs-cli/issues)。
3.  创建一个 [新的问题](https://github.com/anyspecs/anyspecs-cli/issues/new)。 