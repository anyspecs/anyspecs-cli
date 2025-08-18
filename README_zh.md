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

AnySpecs CLI 是一个统一的命令行工具，用于从多个 AI 助手导出聊天记录。它目前支持 **Cursor AI**、**Claude Code**、**Augment Code**、**Codex CLI** 和 **Kiro Records**，并支持多种导出格式，包括 Markdown、HTML 和 JSON。

## ✨ 功能特性

- **多源支持**: 从 Cursor、Claude、Augment、Codex、Kiro 等来源导出（持续增加）。
- **多种导出格式**: 支持 Markdown、HTML 和 JSON。
- **项目与工作区过滤**: 按项目或当前目录导出聊天会话。
- **灵活的会话管理**: 列表、筛选和导出特定的聊天会话。
- **默认导出目录**: 所有导出的文件默认保存到 `.anyspecs/` 目录，统一管理。
- **AI 总结**: 将聊天记录总结为结构化 `.specs` 文件。
- **上传分享**: 将导出的文件上传到远程服务器（AnySpecs Hub 或自建 ASAP）。
- **终端历史与文件变更**: 导出终端历史与文件 diff（开发中）。

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

# 仅列出当前工作区的 Cursor/Claude/Kiro/Augment/Codex 会话
anyspecs list --source cursor/claude/kiro/augment/codex/all

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

# 导出指定来源（默认 markdown）并自定义输出目录
anyspecs export --source claude/cursor/kiro/augment/codex --format markdown --output ./exports
```

### 配置（Setup）

```bash
# 配置指定的 AI 提供方
anyspecs setup [aihubmix/kimi/minimax/ppio/dify]
# 列出所有已配置的提供方
anyspecs setup --list
# 重置所有配置
anyspecs setup --reset
```

### 压缩（Compress）

```bash
# 更多参数参考 anyspecs compress --help
anyspecs compress [--input anyspecs.md] [--output anyspecs.specs] \
  [--provider aihubmix/kimi/minimax/ppio/dify] ...
```

### 上传分享你的 specs（Upload）

> 默认上传地址为官方 Hub `https://hub.anyspecs.cn/`，你也可以自建 [ASAP](https://github.com/anyspecs/ASAP)。

首次上传前，请在 `https://hub.anyspecs.cn/setting` 生成访问令牌，并导出到环境变量，例如：

```bash
export ANYSPECS_TOKEN="44xxxxxxxxxxxxxx7a82"

# 检查远端仓库
anyspecs upload --list
# 搜索特定仓库
anyspecs upload --search "My specs"
# 上传文件到远端
anyspecs upload --file anyspecs.specs
# 携带描述信息上传
anyspecs upload --file anyspecs.specs --description "My specs"
# 使用自定义服务器
anyspecs upload --url http://your-server:3000 --file anyspecs.specs
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

### v0.0.5
- 新增 Codex CLI 支持
- 新增 Dify 工作流压缩支持
- 新增上传到远程服务器（Hub/ASAP）

### v0.0.4
- 新增 Augment Code 支持
- 新增 `--version` 选项

### v0.0.3
- 新增 AI 总结支持（PPIO、MiniMax、Kimi）

### v0.0.2
- Kiro Records 支持；默认导出目录 `.anyspecs/`；工作区过滤优化

### v0.0.1
- 初始版本：支持 Cursor/Claude；支持 Markdown/HTML/JSON 导出

## 💬 支持

如果您遇到任何问题或有任何疑问，请：

1.  查看 [文档](https://github.com/anyspecs/anyspecs-cli/wiki) (如果存在)。
2.  搜索 [现有的问题](https://github.com/anyspecs/anyspecs-cli/issues)。
3.  创建一个 [新的问题](https://github.com/anyspecs/anyspecs-cli/issues/new)。 