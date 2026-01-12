# 知识库使用示例

## 1. 创建知识库

```bash
curl -X POST "http://localhost:8000/api/knowledge-bases" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_kb",
    "name": "我的知识库",
    "description": "这是一个示例知识库",
    "embedding_model": "text-embedding-ada-002",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }'
```

## 2. 添加文档

### 方式1: 直接添加文本内容

```bash
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc1",
    "content": "LangChain 是一个用于构建 LLM 应用的框架。它提供了多种工具和组件来简化开发过程。",
    "title": "LangChain 简介",
    "knowledge_base_id": "my_kb",
    "metadata": {
      "category": "技术文档",
      "author": "系统"
    }
  }'
```

### 方式2: 上传文件

```bash
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/documents/upload" \
  -F "file=@document.txt" \
  -F "title=文档标题"
```

## 3. 搜索文档

```bash
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "LangChain 是什么",
    "knowledge_base_id": "my_kb",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

## 4. 在聊天中使用知识库

Agent 会自动使用知识库工具来检索相关信息：

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "LangChain 是什么？请从知识库中查找相关信息"
  }'
```

Agent 会：
1. 自动调用 `list_knowledge_bases` 列出可用知识库
2. 调用 `search_knowledge_base` 检索相关信息
3. 结合检索结果回答用户问题

## 5. 列出所有知识库

```bash
curl "http://localhost:8000/api/knowledge-bases"
```

## 6. 删除文档

```bash
curl -X DELETE "http://localhost:8000/api/knowledge-bases/my_kb/documents/doc1"
```

## 7. 删除知识库

```bash
curl -X DELETE "http://localhost:8000/api/knowledge-bases/my_kb"
```

