# Engine Extended API - Node Types Reference

## Overview

engine.py 已扩展支持 PocketFlow 的完整 node 类型系统，包括：

- 同步节点（Node）
- 批处理节点（BatchNode）
- 异步节点（AsyncNode）
- 并行批处理节点（AsyncParallelBatchNode）
- 流程控制（FlowNode, AsyncFlow）
- 重试机制
- 条件分支

**向后兼容**: 所有现有代码继续使用 `flow()` 和函数式 node API。

---

## Node Types

### 1. BaseNode

所有节点的基类。

**方法:**
```python
class BaseNode:
    def prep(self, shared):
        """准备阶段 - 从 shared context 提取数据"""
        pass

    def exec(self, prep_res):
        """执行阶段 - 核心业务逻辑"""
        pass

    def post(self, shared, prep_res, exec_res):
        """后处理阶段 - 更新 shared context，返回下一个动作"""
        pass
```

**操作符:**
- `>>` - 定义默认后继节点: `node1 >> node2`
- `-` - 定义条件后继: `node1 - "error" >> error_handler`

---

### 2. Node - 同步节点（带重试）

标准同步节点，支持自动重试机制。

**特性:**
- `max_retries`: 最大重试次数（默认 1）
- `wait`: 重试间隔秒数（默认 0）
- `exec_fallback()`: 所有重试失败后的降级处理

**示例:**
```python
class CallExternalAPI(Node):
    def __init__(self):
        super().__init__(max_retries=3, wait=1.0)

    def prep(self, shared):
        return shared.get("api_request")

    def exec(self, request):
        # 主逻辑 - 自动重试
        response = call_api(request)
        if response.status != 200:
            raise Exception("API failed")
        return response.data

    def exec_fallback(self, prep_res, exc):
        # 降级处理
        return {"error": str(exc), "fallback": True}

    def post(self, shared, prep_res, exec_res):
        shared["api_response"] = exec_res
        return "default"

# 使用
node = CallExternalAPI()
result = node.run({"api_request": {...}})
```

---

### 3. BatchNode - 批处理节点（同步）

对列表中的每个项目执行相同操作（串行）。

**特性:**
- `exec()` 处理单个项目
- 自动遍历列表
- 支持重试机制（继承自 Node）

**示例:**
```python
class AnalyzeFiles(BatchNode):
    def __init__(self):
        super().__init__(max_retries=2, wait=0.5)

    def prep(self, shared):
        # 返回要处理的文件列表
        return shared.get("files", [])

    def exec(self, file_path):
        # 处理单个文件
        with open(file_path) as f:
            content = f.read()
        return analyze(content)

    def post(self, shared, prep_res, exec_res):
        # exec_res 是所有文件的结果列表
        shared["analysis_results"] = exec_res
        return "default"

# 使用
node = AnalyzeFiles()
node.run({"files": ["a.py", "b.py", "c.py"]})
# 结果: analysis_results = [result1, result2, result3]
```

---

### 4. FlowNode - 流程控制节点

编排多个节点，支持条件分支。

**特性:**
- `start()` 设置起始节点
- `next()` 定义节点间转换
- 根据 `post()` 返回值选择下一个节点

**示例 - 简单链式:**
```python
node1 = ProcessNode()
node2 = ValidateNode()
node3 = SaveNode()

node1 >> node2 >> node3  # 链式连接

flow = FlowNode()
flow.start(node1)
flow.run(shared)
```

**示例 - 条件分支:**
```python
validate = ValidateNode()  # post() 返回 "valid" 或 "invalid"
process = ProcessNode()
handle_error = ErrorNode()

# 定义转换
validate.next(process, "valid")
validate.next(handle_error, "invalid")

flow = FlowNode()
flow.start(validate)
flow.run(shared)
```

**使用运算符:**
```python
# 等价写法
validate - "valid" >> process
validate - "invalid" >> handle_error
```

---

### 5. BatchFlow - 批处理流程

对批次中的每个项目运行整个流程（串行）。

**示例:**
```python
# 为每个文件运行 validate -> process -> save 流程
validate = ValidateFileNode()
process = ProcessFileNode()
save = SaveResultNode()

validate >> process >> save

flow = BatchFlow()
flow.start(validate)

# prep() 应返回批次参数列表
class MyBatchFlow(BatchFlow):
    def prep(self, shared):
        # 为每个文件返回参数
        return [
            {"file": "a.py"},
            {"file": "b.py"},
            {"file": "c.py"}
        ]

flow.run(shared)
# 流程运行 3 次，每次处理一个文件
```

---

### 6. AsyncNode - 异步节点

异步版本的 Node，支持 async/await。

**方法:**
```python
class AsyncNode(Node):
    async def prep_async(self, shared):
        """异步准备"""
        pass

    async def exec_async(self, prep_res):
        """异步执行"""
        pass

    async def exec_fallback_async(self, prep_res, exc):
        """异步降级"""
        raise exc

    async def post_async(self, shared, prep_res, exec_res):
        """异步后处理"""
        pass
```

**示例:**
```python
class FetchFromAPI(AsyncNode):
    def __init__(self):
        super().__init__(max_retries=3, wait=1.0)

    async def prep_async(self, shared):
        return shared.get("url")

    async def exec_async(self, url):
        # 异步 HTTP 请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def post_async(self, shared, prep_res, exec_res):
        shared["data"] = exec_res
        return "default"

# 使用
node = FetchFromAPI()
result = await node.run_async({"url": "https://api.example.com"})
```

---

### 7. AsyncBatchNode - 异步批处理（串行）

异步处理批次中的每个项目，一个接一个。

**示例:**
```python
class FetchURLs(AsyncBatchNode):
    async def prep_async(self, shared):
        return shared.get("urls", [])

    async def exec_async(self, url):
        # 处理单个 URL
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()

    async def post_async(self, shared, prep_res, exec_res):
        shared["results"] = exec_res
        return "default"

# 使用
node = FetchURLs()
await node.run_async({"urls": ["url1", "url2", "url3"]})
# 串行执行: url1 -> url2 -> url3
```

---

### 8. AsyncParallelBatchNode - 异步批处理（并行）

异步并行处理批次中的所有项目。

**特性:**
- 使用 `asyncio.gather()` 并行执行
- 所有项目同时开始
- 等待所有项目完成

**示例:**
```python
class FetchURLsParallel(AsyncParallelBatchNode):
    async def exec_async(self, url):
        # 每个 URL 并行处理
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()

# 使用
node = FetchURLsParallel()
await node.run_async({"urls": ["url1", "url2", "url3"]})
# 并行执行: url1 + url2 + url3 同时开始
```

**性能对比:**
```python
# 串行: 3 个 URL，每个 1 秒 = 总共 3 秒
serial_node = AsyncBatchNode()

# 并行: 3 个 URL，每个 1 秒 = 总共 1 秒
parallel_node = AsyncParallelBatchNode()
```

---

### 9. AsyncFlow - 异步流程控制

异步版本的 FlowNode，支持混合同步/异步节点。

**特性:**
- 自动检测节点类型（AsyncNode vs Node）
- 异步节点使用 `await`
- 同步节点直接调用

**示例:**
```python
fetch = FetchDataNode()  # AsyncNode
process = ProcessDataNode()  # AsyncNode
save = SaveNode()  # 同步 Node

fetch >> process >> save

flow = AsyncFlow()
flow.start(fetch)
await flow.run_async(shared)
```

---

### 10. AsyncBatchFlow - 异步批处理流程（串行）

对批次中的每个项目异步运行流程（串行）。

**示例:**
```python
flow = AsyncBatchFlow()
flow.start(fetch_node)
fetch_node >> process_node >> save_node

# 为每个项目串行运行流程
await flow.run_async(shared)
```

---

### 11. AsyncParallelBatchFlow - 异步批处理流程（并行）

对批次中的所有项目并行运行流程。

**示例:**
```python
class ProcessItemsFlow(AsyncParallelBatchFlow):
    async def prep_async(self, shared):
        # 返回项目列表
        return [
            {"item_id": 1},
            {"item_id": 2},
            {"item_id": 3}
        ]

flow = ProcessItemsFlow()
flow.start(fetch_node)
fetch_node >> process_node >> save_node

# 3 个流程并行运行
await flow.run_async(shared)
```

---

## 向后兼容的 Legacy API

原有的函数式 API 完全保留，不影响现有代码。

```python
from engine import flow, node

# 旧的函数式 node
def my_node():
    def prep(ctx, params):
        return ctx.get("data")

    def exec(prep_res, params):
        return process(prep_res)

    def post(ctx, prep_res, exec_res, params):
        ctx["result"] = exec_res
        return "next"

    return prep, exec, post

# 旧的 Flow
f = flow()
f.add(my_node(), name="step1", params={})
f.add(another_node(), name="step2", params={})
result = f.run(shared_store)
```

---

## 使用场景对比

### 场景 1: 简单串行处理
**使用:** Legacy Flow API
```python
f = flow()
f.add(step1(), name="s1")
f.add(step2(), name="s2")
```

### 场景 2: 需要重试的 API 调用
**使用:** Node
```python
class APICall(Node):
    def __init__(self):
        super().__init__(max_retries=3, wait=1.0)
```

### 场景 3: 批量处理文件
**使用:** BatchNode
```python
class ProcessFiles(BatchNode):
    def exec(self, file_path):
        return analyze(file_path)
```

### 场景 4: 条件分支
**使用:** FlowNode
```python
validate - "success" >> process
validate - "error" >> handle_error
```

### 场景 5: 异步 API 调用
**使用:** AsyncNode
```python
class FetchData(AsyncNode):
    async def exec_async(self, prep_res):
        return await api.call()
```

### 场景 6: 并行下载
**使用:** AsyncParallelBatchNode
```python
class DownloadFiles(AsyncParallelBatchNode):
    async def exec_async(self, url):
        return await download(url)
```

---

## 完整示例

参考 `examples/example_extended_nodes.py` 获取所有 node 类型的完整示例。

运行示例:
```bash
python examples/example_extended_nodes.py
```

---

## 迁移指南

### 现有代码
**不需要修改** - 所有现有的 scenarios 和 nodes 继续正常工作。

### 新代码
可以选择使用新的类式 API 获得更多功能：

**从函数式迁移到类式:**
```python
# 旧方式
def my_node():
    def prep(ctx, params):
        return ctx.get("data")
    def exec(prep_res, params):
        return process(prep_res)
    def post(ctx, prep_res, exec_res, params):
        ctx["result"] = exec_res
        return "next"
    return prep, exec, post

# 新方式
class MyNode(Node):
    def prep(self, shared):
        return shared.get("data")

    def exec(self, prep_res):
        return process(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"
```

**优势:**
- 更清晰的结构
- 自动重试机制
- 类型提示支持
- 更好的 IDE 自动完成

---

## 总结

| Node Type | 同步/异步 | 批处理 | 并行 | 重试 | 适用场景 |
|-----------|----------|--------|------|------|----------|
| Node | 同步 | - | - | Yes | 基础同步操作 |
| BatchNode | 同步 | Yes | - | Yes | 批量处理文件 |
| FlowNode | 同步 | - | - | - | 条件分支流程 |
| BatchFlow | 同步 | Yes | - | - | 批量运行流程 |
| AsyncNode | 异步 | - | - | Yes | 异步 API 调用 |
| AsyncBatchNode | 异步 | Yes | - | Yes | 串行异步批处理 |
| AsyncParallelBatchNode | 异步 | Yes | Yes | Yes | 并行异步批处理 |
| AsyncFlow | 异步 | - | - | - | 异步流程控制 |
| AsyncBatchFlow | 异步 | Yes | - | - | 串行批量流程 |
| AsyncParallelBatchFlow | 异步 | Yes | Yes | - | 并行批量流程 |

选择合适的 node 类型以获得最佳性能和代码可读性。
