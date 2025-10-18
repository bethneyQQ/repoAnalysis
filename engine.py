"""
Flow Engine - Extended with PocketFlow features
Supports: sync nodes, async nodes, batch processing, parallel execution, retry mechanism
"""
import asyncio
import warnings
import copy
import time


# ============================================================================
# Legacy API (backward compatible with existing code)
# ============================================================================

def node(prep=None, exec=None, post=None):
    """Legacy function-based node (backward compatible)"""
    return {
        "prep": prep or (lambda ctx, params: {}),
        "exec": exec or (lambda prep_result, params: prep_result),
        "post": post or (lambda ctx, prep_result, exec_result, params: "next")
    }


class Flow:
    """Legacy Flow class (backward compatible)"""
    def __init__(self):
        self.nodes = []

    def add(self, node_func, name, on=None, params=None):
        self.nodes.append({
            "name": name,
            "node": node_func,
            "on": on,
            "params": params or {}
        })
        return self

    def run(self, shared_store):
        for nfo in self.nodes:
            n = nfo["node"]
            p = nfo["params"]
            prep = n["prep"](shared_store, p)
            out = n["exec"](prep, p)
            _ = n["post"](shared_store, prep, out, p)
        return shared_store


def flow():
    """Legacy flow constructor (backward compatible)"""
    return Flow()


# ============================================================================
# Extended API - PocketFlow-style node types
# ============================================================================

class BaseNode:
    """Base class for all nodes"""

    def __init__(self):
        self.params = {}
        self.successors = {}

    def set_params(self, params):
        """Set node parameters"""
        self.params = params

    def next(self, node, action="default"):
        """Define next node based on action

        Example:
            node1.next(node2)  # default transition
            node1.next(node3, "error")  # error transition
        """
        if action in self.successors:
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node

    def prep(self, shared):
        """Preparation phase - extract data from shared context"""
        pass

    def exec(self, prep_res):
        """Execution phase - main logic"""
        pass

    def post(self, shared, prep_res, exec_res):
        """Post-processing phase - update shared context, return next action"""
        pass

    def _exec(self, prep_res):
        """Internal execution wrapper"""
        return self.exec(prep_res)

    def _run(self, shared):
        """Internal run logic"""
        p = self.prep(shared)
        e = self._exec(p)
        return self.post(shared, p, e)

    def run(self, shared):
        """Run this node standalone"""
        if self.successors:
            warnings.warn("Node won't run successors. Use Flow.")
        return self._run(shared)

    def __rshift__(self, other):
        """Shorthand for next(): node1 >> node2"""
        return self.next(other)

    def __sub__(self, action):
        """Shorthand for conditional: node1 - "error" >> node2"""
        if isinstance(action, str):
            return _ConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class _ConditionalTransition:
    """Helper for conditional transitions"""
    def __init__(self, src, action):
        self.src = src
        self.action = action

    def __rshift__(self, tgt):
        return self.src.next(tgt, self.action)


class Node(BaseNode):
    """Standard synchronous node with retry support

    Example:
        class MyNode(Node):
            def __init__(self):
                super().__init__(max_retries=3, wait=1)

            def prep(self, shared):
                return shared.get("input_data")

            def exec(self, prep_res):
                # Main logic here
                return process(prep_res)

            def post(self, shared, prep_res, exec_res):
                shared["output"] = exec_res
                return "default"
    """

    def __init__(self, max_retries=1, wait=0):
        super().__init__()
        self.max_retries = max_retries
        self.wait = wait

    def exec_fallback(self, prep_res, exc):
        """Fallback when all retries exhausted"""
        raise exc

    def _exec(self, prep_res):
        """Execute with retry logic"""
        for self.cur_retry in range(self.max_retries):
            try:
                return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0:
                    time.sleep(self.wait)


class BatchNode(Node):
    """Batch processing node (synchronous, sequential)

    Example:
        class ProcessFiles(BatchNode):
            def exec(self, file_path):
                # Process single file
                return analyze(file_path)

        node = ProcessFiles()
        result = node.run({"files": ["a.py", "b.py", "c.py"]})
    """

    def _exec(self, items):
        """Execute for each item in batch"""
        return [super(BatchNode, self)._exec(i) for i in (items or [])]


class FlowNode(BaseNode):
    """Flow control node - orchestrates multiple nodes

    Example:
        flow = FlowNode()
        flow.start(node1)
        node1 >> node2 >> node3
        result = flow.run(shared)
    """

    def __init__(self, start=None):
        super().__init__()
        self.start_node = start

    def start(self, start):
        """Set the starting node"""
        self.start_node = start
        return start

    def get_next_node(self, curr, action):
        """Get next node based on action"""
        nxt = curr.successors.get(action or "default")
        if not nxt and curr.successors:
            warnings.warn(
                f"Flow ends: '{action}' not found in {list(curr.successors)}"
            )
        return nxt

    def _orch(self, shared, params=None):
        """Orchestrate node execution"""
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None

        while curr:
            curr.set_params(p)
            last_action = curr._run(shared)
            curr = copy.copy(self.get_next_node(curr, last_action))

        return last_action

    def _run(self, shared):
        """Run the flow"""
        p = self.prep(shared)
        o = self._orch(shared)
        return self.post(shared, p, o)

    def post(self, shared, prep_res, exec_res):
        return exec_res


class BatchFlow(FlowNode):
    """Batch flow - run flow for each item in batch

    Example:
        flow = BatchFlow()
        flow.start(validate_node)
        validate_node >> process_node

        # Run flow for each file
        flow.run({"files": [{"path": "a.py"}, {"path": "b.py"}]})
    """

    def _run(self, shared):
        pr = self.prep(shared) or []
        for bp in pr:
            self._orch(shared, {**self.params, **bp})
        return self.post(shared, pr, None)


# ============================================================================
# Async Node Types
# ============================================================================

class AsyncNode(Node):
    """Asynchronous node with retry support

    Example:
        class CallLLM(AsyncNode):
            async def exec_async(self, prep_res):
                response = await openai_api.call(prep_res["prompt"])
                return response
    """

    async def prep_async(self, shared):
        """Async prep phase"""
        pass

    async def exec_async(self, prep_res):
        """Async execution phase"""
        pass

    async def exec_fallback_async(self, prep_res, exc):
        """Async fallback"""
        raise exc

    async def post_async(self, shared, prep_res, exec_res):
        """Async post phase"""
        pass

    async def _exec(self, prep_res):
        """Async execute with retry"""
        for self.cur_retry in range(self.max_retries):
            try:
                return await self.exec_async(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0:
                    await asyncio.sleep(self.wait)

    async def run_async(self, shared):
        """Run async node standalone"""
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(shared)

    async def _run_async(self, shared):
        """Internal async run"""
        p = await self.prep_async(shared)
        e = await self._exec(p)
        return await self.post_async(shared, p, e)

    def _run(self, shared):
        """Override sync run to raise error"""
        raise RuntimeError("Use run_async() for async nodes")


class AsyncBatchNode(AsyncNode, BatchNode):
    """Async batch node (sequential)

    Example:
        class FetchURLs(AsyncBatchNode):
            async def exec_async(self, url):
                return await fetch(url)
    """

    async def _exec(self, items):
        """Execute each item sequentially"""
        results = []
        for item in items:
            result = await super(AsyncBatchNode, self)._exec(item)
            results.append(result)
        return results


class AsyncParallelBatchNode(AsyncNode, BatchNode):
    """Async batch node (parallel execution)

    Example:
        class FetchURLsParallel(AsyncParallelBatchNode):
            async def exec_async(self, url):
                return await fetch(url)

        # Fetches all URLs in parallel
        node = FetchURLsParallel()
        results = await node.run_async({"urls": [...]})
    """

    async def _exec(self, items):
        """Execute all items in parallel"""
        tasks = [super(AsyncParallelBatchNode, self)._exec(i) for i in items]
        return await asyncio.gather(*tasks)


class AsyncFlow(FlowNode, AsyncNode):
    """Async flow control

    Example:
        flow = AsyncFlow()
        flow.start(fetch_node)
        fetch_node >> process_node >> save_node
        await flow.run_async(shared)
    """

    async def _orch_async(self, shared, params=None):
        """Async orchestration"""
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None

        while curr:
            curr.set_params(p)
            if isinstance(curr, AsyncNode):
                last_action = await curr._run_async(shared)
            else:
                last_action = curr._run(shared)
            curr = copy.copy(self.get_next_node(curr, last_action))

        return last_action

    async def _run_async(self, shared):
        """Run async flow"""
        p = await self.prep_async(shared)
        o = await self._orch_async(shared)
        return await self.post_async(shared, p, o)

    async def post_async(self, shared, prep_res, exec_res):
        return exec_res


class AsyncBatchFlow(AsyncFlow, BatchFlow):
    """Async batch flow (sequential)"""

    async def _run_async(self, shared):
        pr = await self.prep_async(shared) or []
        for bp in pr:
            await self._orch_async(shared, {**self.params, **bp})
        return await self.post_async(shared, pr, None)


class AsyncParallelBatchFlow(AsyncFlow, BatchFlow):
    """Async batch flow (parallel execution)

    Example:
        flow = AsyncParallelBatchFlow()
        flow.start(process_node)

        # Process all items in parallel
        await flow.run_async({"items": [...]})
    """

    async def _run_async(self, shared):
        pr = await self.prep_async(shared) or []
        tasks = [
            self._orch_async(shared, {**self.params, **bp})
            for bp in pr
        ]
        await asyncio.gather(*tasks)
        return await self.post_async(shared, pr, None)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Legacy API
    'node', 'flow', 'Flow',

    # Base classes
    'BaseNode', 'Node', 'FlowNode',

    # Sync batch
    'BatchNode', 'BatchFlow',

    # Async
    'AsyncNode', 'AsyncFlow',
    'AsyncBatchNode', 'AsyncParallelBatchNode',
    'AsyncBatchFlow', 'AsyncParallelBatchFlow',
]
