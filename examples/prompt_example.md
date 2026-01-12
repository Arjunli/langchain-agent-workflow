# Prompt 管理使用示例

## 1. 创建 Prompt

```bash
curl -X POST "http://localhost:8000/api/prompts" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_custom_prompt",
    "name": "我的自定义 Prompt",
    "description": "一个自定义的 Prompt 模板",
    "content": "你是一个专业的助手。你的任务是：\n1. 理解用户需求：{user_input}\n2. 提供专业建议\n3. 使用工具完成任务\n\n可用工具：{tool_list}",
    "prompt_type": "template",
    "variables": ["user_input", "tool_list"],
    "category": "custom",
    "tags": ["custom", "assistant"],
    "is_default": false,
    "is_active": true
  }'
```

## 2. 列出所有 Prompt

```bash
# 列出所有 Prompt
curl "http://localhost:8000/api/prompts"

# 按分类筛选
curl "http://localhost:8000/api/prompts?category=workflow"

# 按标签筛选
curl "http://localhost:8000/api/prompts?tags=custom,assistant"

# 只列出启用的
curl "http://localhost:8000/api/prompts?active_only=true"
```

## 3. 获取 Prompt

```bash
curl "http://localhost:8000/api/prompts/my_custom_prompt"
```

## 4. 获取默认 Prompt

```bash
# 获取默认 Prompt（工作流类别）
curl "http://localhost:8000/api/prompts/default/workflow"

# 获取默认 Prompt（无分类）
curl "http://localhost:8000/api/prompts/default"
```

## 5. 更新 Prompt

```bash
curl -X PUT "http://localhost:8000/api/prompts/my_custom_prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的 Prompt 内容...",
    "is_default": true
  }'
```

## 6. 渲染 Prompt（测试变量替换）

```bash
curl -X POST "http://localhost:8000/api/prompts/my_custom_prompt/render" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "user_input": "用户的问题",
      "tool_list": "工具列表"
    }
  }'
```

## 7. 在聊天中使用自定义 Prompt

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行数据分析工作流",
    "prompt_id": "my_custom_prompt"
  }'
```

## 8. 搜索 Prompt

```bash
curl "http://localhost:8000/api/prompts/search/工作流"
```

## 9. 查看 Prompt 使用历史

```bash
curl "http://localhost:8000/api/prompts/my_custom_prompt/usage?limit=50"
```

## 10. 删除 Prompt

```bash
curl -X DELETE "http://localhost:8000/api/prompts/my_custom_prompt"
```

## Prompt 变量说明

Prompt 模板支持变量替换，常用变量包括：

- `{workflow_list}`: 可用工作流列表
- `{knowledge_instructions}`: 知识库工具说明
- `{user_input}`: 用户输入
- `{tool_list}`: 可用工具列表
- `{conversation_history}`: 对话历史

你可以在创建 Prompt 时定义自己的变量，然后在渲染时传入对应的值。

## 设置默认 Prompt

将 `is_default` 设置为 `true` 可以将 Prompt 设置为默认 Prompt。如果设置了默认 Prompt，Agent 会自动使用它（除非指定了其他 `prompt_id`）。

