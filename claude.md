# AnySpecs CLI 项目概览

## 项目基本信息

**项目名称**: AnySpecs CLI
**版本**: 0.0.2
**描述**: AI助手聊天记录的统一导出工具
**作者**: AnySpecs Team (me@timerring.com)
**许可证**: MIT
**主页**: https://github.com/anyspecs/anyspecs-cli

## 项目目标

AnySpecs CLI 是一个统一的命令行工具，用于从多个AI助手导出聊天记录。目标是提供一个通用的解决方案来备份、分析和共享AI对话历史。

### 座右铭

**"Code is cheap, Show me Any Specs."**

## 支持的AI助手

1. **Cursor AI** - 从本地SQLite数据库提取聊天记录
2. **Claude Code** - 从JSONL历史文件提取聊天记录
3. **Kiro Records** - 从 `.kiro` 目录提取markdown文档

## 核心功能

- ✅ **多源支持**: 支持Cursor AI、Claude Code、Kiro Records
- ✅ **多格式导出**: Markdown、HTML、JSON格式
- ✅ **项目级过滤**: 基于项目或当前目录的会话过滤
- ✅ **会话管理**: 列出、过滤、导出特定会话
- ✅ **默认导出目录**: 所有导出文件保存到 `.anyspecs/` 目录
- ✅ **AI智能压缩**: 支持多种AI服务压缩聊天记录为.specs格式
- 🚧 **终端历史和文件差异**: 导出终端历史和文件差异记录 (WIP)
- 🚧 **服务器上传分享**: 上传导出文件到远程服务器 (WIP)

## 技术架构

### 包结构

```
anyspecs-cli/
├── anyspecs/                 # 主包
│   ├── __init__.py          # 包初始化
│   ├── cli.py               # CLI接口 (主入口)
│   ├── config.py           # 配置管理
│   ├── core/               # 核心功能
│   │   ├── extractors.py   # 基础提取器类
│   │   ├── formatters.py   # 导出格式化器
│   │   └── ai_processor.py # AI压缩处理器
│   ├── exporters/          # 源特定提取器
│   │   ├── cursor.py       # Cursor AI提取器
│   │   ├── claude.py       # Claude Code提取器
│   │   └── kiro.py         # Kiro Records提取器
│   ├── ai_clients/         # AI服务客户端
│   │   ├── base_client.py  # 基础AI客户端接口
│   │   ├── aihubmix_client.py # Aihubmix客户端
│   │   ├── kimi_client.py  # Kimi客户端
│   │   └── minimax_client.py # MiniMax客户端
│   ├── config/             # 配置文件
│   │   └── prompts.py      # AI提示词配置
│   └── utils/              # 实用工具
│       ├── logging.py      # 日志配置
│       ├── paths.py        # 路径工具
│       ├── specs_formatter.py # .specs文件处理器
│       └── upload.py       # 上传功能
├── assets/                 # 资源文件
│   ├── headerDark.svg     # 深色主题头图
│   └── headerLight.svg    # 浅色主题头图
└── pyproject.toml         # 包配置
```

### 技术栈

**语言**: Python 3.8+
**构建系统**: setuptools
**依赖管理**: pip/pyproject.toml
**代码质量**: black, flake8, mypy, ruff
**测试**: pytest

### 核心依赖

- `requests>=2.25.0` - HTTP请求处理
- `python-dateutil>=2.8.0` - 日期时间处理
- `openai>=1.0.0` - OpenAI客户端库（用于Aihubmix和Kimi）

### 开发依赖

- 代码格式化: black, isort
- 代码检查: flake8, ruff, mypy
- 测试: pytest, pytest-cov
- 预提交钩子: pre-commit

## 核心组件分析

### 1. CLI入口 (`cli.py`)

- **类**: `AnySpecsCLI` - 主CLI控制器
- **命令**: `list`, `export`, `compress`
- **特性**:
  - 支持多源聚合（cursor, claude, kiro, all）
  - 项目级过滤和会话管理
  - 批量导出和单文件导出
  - AI智能压缩功能
  - 服务器上传功能
  - 详细的错误处理和用户友好输出

### 2. 配置管理 (`config.py`)

- **类**: `Config` - 配置管理器
- **配置文件**: `~/.anyspecs/config.json`
- **特性**:
  - 默认配置合并
  - 点符号路径访问 (`config.get('export.default_format')`)
  - AI相关配置管理（API密钥、模型设置）
  - 自动配置目录创建

### 3. 基础提取器 (`core/extractors.py`)

- **抽象类**: `BaseExtractor` - 所有提取器的基类
- **核心方法**:
  - `extract_chats()` - 提取聊天数据
  - `list_sessions()` - 列出可用会话
  - `format_chat_for_export()` - 标准化导出格式

### 4. 源特定提取器

#### Cursor提取器 (`exporters/cursor.py`)

- 从SQLite数据库提取聊天记录
- 支持工作区特定对话和全局聊天存储
- 处理Composer数据和bubble对话

#### Claude提取器 (`exporters/claude.py`)

- 从JSONL历史文件提取聊天记录
- 支持用户消息、AI响应、工具调用
- 会话元数据和项目上下文

#### Kiro提取器 (`exporters/kiro.py`)

- 从 `.kiro` 目录提取markdown文档
- 文件元数据（名称、修改时间）
- 自动项目摘要检测

### 5. AI压缩系统

#### AI处理器 (`core/ai_processor.py`)
- **类**: `AIProcessor` - AI压缩核心处理器
- **功能**:
  - 文件扫描和筛选
  - 批量压缩处理
  - 错误处理和重试
  - 进度跟踪和状态反馈

#### AI客户端架构 (`ai_clients/`)
- **基类**: `BaseAIClient` - 统一的AI服务接口
- **支持的服务**:
  - **Aihubmix**: 基于OpenAI客户端，支持GPT系列模型
  - **Kimi**: 月之暗面API，支持moonshot系列模型
  - **MiniMax**: 海量模型API，支持abab系列模型
  - **PPIO**: 派欧云GPU容器实例，支持deepseek系列模型

#### 提示词系统 (`config/prompts.py`)
- **智能提示词**: 基于TypeScript参考实现的专业压缩提示词
- **上下文工程**: 确保压缩后能完美还原对话上下文
- **可选字段**: 根据内容类型动态选择包含的字段

#### .specs文件格式处理器 (`utils/specs_formatter.py`)
- **.specs格式**: 标准化的聊天记录压缩格式
- **字段验证**: 确保生成的.specs文件符合规范
- **文件管理**: 智能文件命名和保存逻辑

### 6. 配置管理系统 (`config/ai_config.py`)

#### AI配置管理器 (`AIConfigManager`)
- **配置文件**: `~/.anyspecs/ai_config.json` - 主配置文件
- **环境变量**: `.env` - 项目级环境变量文件
- **核心功能**:
  - 首次交互式配置设置
  - 自动保存配置到JSON和.env文件
  - 智能配置加载和合并
  - 多级配置优先级管理

#### 配置优先级系统
1. **命令行参数** (最高优先级)
   - `--provider`, `--api-key`, `--model`等
   - 临时覆盖已保存的配置
2. **.env文件** (中等优先级)
   - `ANYSPECS_AI_PROVIDER`, `ANYSPECS_AI_API_KEY`等
   - 项目级配置，便于团队共享
3. **配置文件** (最低优先级)
   - `~/.anyspecs/ai_config.json`
   - 用户级默认配置

#### 支持的环境变量
- `ANYSPECS_AI_PROVIDER` - AI提供商 (aihubmix/kimi/minimax/ppio)
- `ANYSPECS_AI_API_KEY` - API密钥
- `ANYSPECS_AI_MODEL` - 模型名称
- `ANYSPECS_AI_GROUP_ID` - MiniMax专用Group ID
- `ANYSPECS_AI_TEMPERATURE` - 温度参数
- `ANYSPECS_AI_MAX_TOKENS` - 最大令牌数

#### 配置管理命令
- `anyspecs setup <provider>` - 配置特定AI提供商
- `anyspecs setup --list` - 列出已配置的提供商
- `anyspecs setup --reset` - 重置所有配置

## 使用方式

### 安装

```bash
pip install anyspecs
```

### 命令示例

```bash
# 列出所有聊天会话
anyspecs list

# 导出当前项目的会话到Markdown
anyspecs export

# 导出所有项目的会话到HTML
anyspecs export --all-projects --format html

# 导出特定会话
anyspecs export --session-id abc123 --format json

# 导出Claude会话
anyspecs export --source claude --format markdown

# AI智能压缩聊天记录
anyspecs compress --provider aihubmix --api-key YOUR_API_KEY



# 使用Kimi压缩
anyspecs compress --provider kimi --api-key YOUR_KIMI_KEY --model kimi-k2-0711-preview

# 使用MiniMax压缩（需要先配置group_id）
anyspecs setup minimax  # 首次配置，会要求输入API key和Group ID
anyspecs compress --provider minimax

# 指定输入输出目录
anyspecs compress --provider aihubmix --input .anyspecs --output .compressed --api-key YOUR_KEY

# 干运行模式（预览要处理的文件）
anyspecs compress --dry-run --verbose

# 使用环境变量
export ANYSPECS_AI_API_KEY=your_api_key
anyspecs compress --provider kimi

# 首次配置工作流
anyspecs setup aihubmix  # 交互式配置API密钥和模型
anyspecs compress        # 自动使用已配置的设置

# 配置管理
anyspecs setup --list   # 查看已配置的提供商
anyspecs setup --reset  # 重置所有配置
```

### 配置文件示例

**.env文件**:
```bash
# AnySpecs AI Configuration
ANYSPECS_AI_PROVIDER="aihubmix"
ANYSPECS_AI_API_KEY="your_api_key_here"
ANYSPECS_AI_MODEL="gpt-4o-mini"
```

**ai_config.json文件**:
```json
{
  "default_provider": "aihubmix",
  "providers": {
    "aihubmix": {
      "api_key": "your_api_key_here",
      "model": "gpt-4o-mini",
      "base_url": "https://aihubmix.com/v1",
      "temperature": 0.3,
      "max_tokens": 10000
    }
  }
}
```

## 开发工作流

### 代码质量

- **格式化**: Black (line-length: 88)
- **排序**: isort (兼容black配置)
- **检查**: flake8 + ruff (现代linter)
- **类型检查**: mypy (严格模式)
- **测试**: pytest + coverage

### 测试配置

- 最小覆盖率要求
- 单元测试和集成测试标记
- HTML/XML覆盖率报告

## 项目状态

**当前版本**: 0.0.2
**开发状态**: 活跃开发中

### v0.0.2+ 更新 (最新)

- ✅ Kiro Records支持
- ✅ 默认导出目录 (`.anyspecs/`)
- ✅ 工作区过滤 (Cursor)
- ✅ **AI智能压缩**: 完整的多提供商AI压缩系统
- ✅ **四大AI服务**: Aihubmix、Kimi、MiniMax、PPIO完整支持
- ✅ **.specs格式**: 标准化的压缩聊天记录格式
- ✅ **智能提示词**: 专业的上下文工程压缩算法
- ✅ **配置管理系统**: 完整的首次配置和自动加载功能
- ✅ **.env文件支持**: 自动保存配置到环境变量文件
- ✅ **配置优先级**: 命令行 > .env文件 > 配置文件的优先级系统

### 待开发功能 (WIP)

- 终端历史和文件差异导出
- 服务器上传和分享

## 设计哲学

1. **统一接口**: 为不同AI助手提供一致的导出体验
2. **灵活过滤**: 支持项目、会话、源级别的精细过滤
3. **多格式输出**: 适应不同使用场景的导出需求
4. **组织化存储**: 默认 `.anyspecs/` 目录保持项目整洁
5. **扩展性**: 通过插件化架构支持更多AI助手
6. **AI智能化**: 通过AI压缩实现聊天记录的智能归纳和上下文保持
7. **配置自动化**: 首次配置后自动保存，后续使用无需重复设置

## 技术亮点

- **模块化设计**: 清晰的提取器-格式化器分离
- **错误恢复**: 优雅的错误处理和降级策略
- **智能配置管理**: 多级优先级配置系统，支持.env文件和自动加载
- **现代Python**: 类型提示、现代工具链、测试覆盖
- **CLI用户体验**: 丰富的命令行选项和用户反馈
- **零重复配置**: 首次设置后自动保存到环境变量，提升开发效率

## 总结

AnySpecs CLI 是一个设计良好、架构清晰的Python命令行工具，专注于AI助手聊天记录的统一管理和导出。项目采用现代Python开发实践，具有良好的扩展性和维护性，为AI对话历史的备份和分析提供了优雅的解决方案。
