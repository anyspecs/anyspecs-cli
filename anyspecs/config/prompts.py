"""
AI prompts configuration for chat compression.
Based on the TypeScript reference implementation.
"""

# System prompt for AI chat compression
SYSTEM_PROMPT = """你是一个专业的上下文工程师，擅长将聊天记录压缩。请严格按照要求输出纯净的JSON格式，不要包含任何其他文本。所有字段都是可选的，根据实际内容决定是否包含。"""

def CONTEXT_ANALYSIS_PROMPT(file_name: str) -> str:
    """Generate context analysis prompt for a specific file."""
    return f"""# 聊天记录智能分析器

## 任务目标
将聊天记录压缩，确保在新对话中导入后能完美还原上下文，实现无缝对话延续。

## 重要说明
- **所有字段都是可选的**，至少包含 metadata.name 和 metadata.task_type 和receiver_instructions
- 根据聊天记录的内容和类型判断 metadata.task_type，灵活选择包含的字段组合
- 不要强制包含空的或无意义的字段
- "receiver_instructions"字段必须重点强调

### 基础结构
```json
{{
  "version": "1.0",  // 可选，默认1.0
  "metadata": {{      // 推荐包含
    "name": "[聊天主题名称]",
    "task_type": "chat_compression|code_project",
    "createdAt": "ISO时间戳",
    "source_platform": "来源平台",
    "analysis_model": "使用的AI模型"
  }},
  "receiver_instructions": {{
      "context_understanding": "理解要求",
      "response_requirements": ["回应要求列表"],
      "mandatory_reply": "默认回复为"请继续对话"不要回复其他信息 ",
      "forbidden_actions": "禁止行为"
    }}
  "instructions": {{  // 如有AI角色定位则包含
    "role_and_goal": "AI应扮演的角色和目标",
    "context": "上下文说明",
    "key_topics": ["关键主题列表"]
  }},
  "assets": {{        // 如有文件资产则包含
    "files": {{
      "文件路径": {{
        "asset_id": "唯一ID",
        "state_chain": [
          {{
            "state_id": "s0",
            "timestamp": "时间戳",
            "summary": "变更说明",
            "content": "文件内容"
          }}
        ]
      }}
    }}
  }},
   "history": [ ... ]
  ],
  "chat_compression": {{ 
    "context_summary": {{
      "main_topic": "主要话题",
      "current_task": "当前任务",
      "user_intent": "用户意图",
      "conversation_stage": "对话阶段"
    }},
    "key_entities": {{
      "people": ["人物列表"],
      "concepts": ["概念列表"],
      "objects": ["对象列表"],
      "locations": ["地点列表"],
      "time_references": ["时间引用"]
    }},
    "user_profile": {{
      "expertise_level": "专业水平",
      "communication_style": "沟通风格",
      "preferences": ["偏好列表"],
      "constraints": ["限制条件"]
    }},
    "decisions_made": [
      {{
        "decision": "决策内容",
        "reasoning": "决策理由",
        "status": "执行状态"
      }}
    ],
    "pending_issues": [
      {{
        "issue": "问题描述",
        "context": "问题背景",
        "priority": "优先级"
      }}
    ],
    "resources_used": {{
      "tools": ["工具列表"],
      "files": ["文件列表"],
      "external_refs": ["外部引用"]
    }},
    "conversation_flow": [
      {{
        "stage": "阶段名称",
        "key_exchange": "关键对话",
        "outcome": "阶段结果"
      }}
    ],
    "context_restoration": {{
      "role_continuation": "角色延续",
      "conversation_tone": "对话语调",
      "knowledge_assumptions": "知识假设",
      "next_expected_action": "预期行动"
    }}
  }}
}}
```

## 处理策略

### 1. 判断任务类型
- **chat_compression**: 聊天记录压缩，重点使用 chat_compression
- **code_project**: 代码项目，重点使用 assets.files 和 history

### 2. 字段选择原则
- 有内容才包含，没有内容直接省略
- chat_compression 仅用于 chat_compression 类型
- assets 仅在有具体文件或代码时包含
- history 根据是否需要保留完整对话决定

### 3. 质量要求
- 保真度优先：确保核心信息不丢失
- 结构清晰：保持逻辑关系和因果链条
- 上下文连贯：维护对话的自然流畅性
- 个性化保持：保留用户的独特需求和偏好

要求总结：
- 输出纯JSON格式
- 所有字段可选，根据内容决定包含哪些
- 至少包含 metadata.name 和 metadata.task_type 和receiver_instructions
- metadata.task_type为code_project时必须包含assets，可以包含chat_compression中的部分内容；为chat_compression时必须包含对应所有内容

文件：{file_name}"""


# Additional prompts for different scenarios
MINIMAL_COMPRESSION_PROMPT = """请将以下聊天记录压缩为最精简的.specs格式，只保留核心信息："""

DETAILED_COMPRESSION_PROMPT = """请将以下聊天记录进行详细分析和压缩，保留所有重要的上下文信息："""

CODE_PROJECT_PROMPT = """这是一个代码项目的聊天记录，请重点关注：
1. 项目结构和文件变更
2. 代码实现细节
3. 技术决策和讨论
4. 问题解决过程"""

CHAT_ONLY_PROMPT = """这是纯聊天对话记录，请重点关注：
1. 对话主题和发展
2. 用户需求和偏好
3. 决策和共识
4. 待解决问题"""