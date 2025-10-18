"""
Examples demonstrating extended node types from engine.py

This shows how to use:
- Node (with retry)
- BatchNode (batch processing)
- AsyncNode (async operations)
- AsyncParallelBatchNode (parallel async batch)
- FlowNode (conditional flows)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time
from engine import (
    Node, BatchNode, FlowNode,
    AsyncNode, AsyncParallelBatchNode, AsyncFlow
)


# ============================================================================
# Example 1: Node with Retry Mechanism
# ============================================================================

class UnreliableAPINode(Node):
    """Simulates calling an unreliable API with retry"""

    def __init__(self):
        super().__init__(max_retries=3, wait=0.5)
        self.attempt = 0

    def prep(self, shared):
        return shared.get("query", "default query")

    def exec(self, prep_res):
        self.attempt += 1
        print(f"  Attempt {self.attempt}: Calling API with '{prep_res}'")

        # Simulate failure on first 2 attempts
        if self.attempt < 3:
            raise Exception("API temporarily unavailable")

        return {"status": "success", "data": f"Result for {prep_res}"}

    def post(self, shared, prep_res, exec_res):
        shared["api_result"] = exec_res
        print(f"  Success after {self.attempt} attempts")
        return "default"


def demo_retry():
    print("\n" + "=" * 80)
    print("Demo 1: Node with Retry Mechanism")
    print("=" * 80)

    node = UnreliableAPINode()
    shared = {"query": "get_user_data"}
    result = node.run(shared)

    print(f"\nFinal result: {shared['api_result']}")


# ============================================================================
# Example 2: BatchNode for Processing Multiple Items
# ============================================================================

class FileAnalyzerNode(BatchNode):
    """Analyze multiple files in batch"""

    def prep(self, shared):
        # Return list of files to process
        return shared.get("files", [])

    def exec(self, file_path):
        """Process single file"""
        print(f"  Analyzing: {file_path}")
        # Simulate file analysis
        time.sleep(0.1)
        return {
            "file": file_path,
            "lines": len(file_path) * 10,  # Fake metric
            "issues": 2
        }

    def post(self, shared, prep_res, exec_res):
        shared["analysis_results"] = exec_res
        return "default"


def demo_batch():
    print("\n" + "=" * 80)
    print("Demo 2: BatchNode Processing")
    print("=" * 80)

    node = FileAnalyzerNode()
    shared = {
        "files": ["src/main.py", "src/utils.py", "tests/test_main.py"]
    }
    node.run(shared)

    print(f"\nProcessed {len(shared['analysis_results'])} files")
    for result in shared["analysis_results"]:
        print(f"  {result['file']}: {result['lines']} lines, {result['issues']} issues")


# ============================================================================
# Example 3: Conditional Flow with FlowNode
# ============================================================================

class ValidateNode(Node):
    """Validate input data"""

    def prep(self, shared):
        return shared.get("data")

    def exec(self, data):
        print(f"  Validating: {data}")
        if isinstance(data, dict) and "value" in data:
            return "valid"
        return "invalid"

    def post(self, shared, prep_res, exec_res):
        print(f"  Validation result: {exec_res}")
        return exec_res  # Return "valid" or "invalid"


class ProcessValidNode(Node):
    """Process valid data"""

    def exec(self, prep_res):
        print("  Processing valid data...")
        return {"processed": True}

    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"


class HandleInvalidNode(Node):
    """Handle invalid data"""

    def exec(self, prep_res):
        print("  Handling invalid data...")
        return {"error": "Invalid input"}

    def post(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"


def demo_conditional_flow():
    print("\n" + "=" * 80)
    print("Demo 3: Conditional Flow")
    print("=" * 80)

    # Build flow with conditional branches
    validate = ValidateNode()
    process_valid = ProcessValidNode()
    handle_invalid = HandleInvalidNode()

    # Define transitions
    validate.next(process_valid, "valid")  # When "valid" returned
    validate.next(handle_invalid, "invalid")  # When "invalid" returned

    flow = FlowNode()
    flow.start(validate)

    # Test with valid data
    print("\nTest 1: Valid data")
    shared1 = {"data": {"value": 123}}
    flow.run(shared1)
    print(f"Result: {shared1['result']}")

    # Test with invalid data
    print("\nTest 2: Invalid data")
    shared2 = {"data": "invalid"}

    # Need fresh nodes for second run
    validate2 = ValidateNode()
    process_valid2 = ProcessValidNode()
    handle_invalid2 = HandleInvalidNode()
    validate2.next(process_valid2, "valid")
    validate2.next(handle_invalid2, "invalid")
    flow2 = FlowNode()
    flow2.start(validate2)

    flow2.run(shared2)
    print(f"Result: {shared2['result']}")


# ============================================================================
# Example 4: Async Node
# ============================================================================

class AsyncAPICallNode(AsyncNode):
    """Async API call with retry"""

    def __init__(self):
        super().__init__(max_retries=2, wait=0.5)

    async def prep_async(self, shared):
        return shared.get("endpoint", "/api/data")

    async def exec_async(self, endpoint):
        print(f"  Calling async API: {endpoint}")
        await asyncio.sleep(0.2)  # Simulate network delay
        return {"endpoint": endpoint, "data": "response data"}

    async def post_async(self, shared, prep_res, exec_res):
        shared["api_response"] = exec_res
        return "default"


async def demo_async():
    print("\n" + "=" * 80)
    print("Demo 4: Async Node")
    print("=" * 80)

    node = AsyncAPICallNode()
    shared = {"endpoint": "/api/users"}
    await node.run_async(shared)

    print(f"\nAPI Response: {shared['api_response']}")


# ============================================================================
# Example 5: Async Parallel Batch Processing
# ============================================================================

class AsyncFileDownloadNode(AsyncParallelBatchNode):
    """Download multiple files in parallel"""

    def __init__(self):
        super().__init__(max_retries=2, wait=0.5)

    async def prep_async(self, shared):
        return shared.get("urls", [])

    async def exec_async(self, url):
        """Download single file"""
        print(f"  Downloading: {url}")
        await asyncio.sleep(0.3)  # Simulate download time
        return {"url": url, "size": len(url) * 100}

    async def post_async(self, shared, prep_res, exec_res):
        shared["downloads"] = exec_res
        return "default"


async def demo_async_parallel_batch():
    print("\n" + "=" * 80)
    print("Demo 5: Async Parallel Batch Processing")
    print("=" * 80)

    node = AsyncFileDownloadNode()
    shared = {
        "urls": [
            "https://example.com/file1.zip",
            "https://example.com/file2.zip",
            "https://example.com/file3.zip",
            "https://example.com/file4.zip",
        ]
    }

    start = time.time()
    await node.run_async(shared)
    elapsed = time.time() - start

    print(f"\nDownloaded {len(shared['downloads'])} files in {elapsed:.2f}s")
    print("Note: Parallel execution is faster than sequential!")


# ============================================================================
# Example 6: Async Flow
# ============================================================================

class FetchDataNode(AsyncNode):
    """Fetch data asynchronously"""

    async def exec_async(self, prep_res):
        print("  Fetching data...")
        await asyncio.sleep(0.2)
        return {"count": 5}

    async def post_async(self, shared, prep_res, exec_res):
        shared["data_count"] = exec_res["count"]
        return "default"


class ProcessDataNode(AsyncNode):
    """Process fetched data"""

    async def prep_async(self, shared):
        return shared.get("data_count", 0)

    async def exec_async(self, count):
        print(f"  Processing {count} items...")
        await asyncio.sleep(0.2)
        return {"processed": count}

    async def post_async(self, shared, prep_res, exec_res):
        shared["result"] = exec_res
        return "default"


async def demo_async_flow():
    print("\n" + "=" * 80)
    print("Demo 6: Async Flow")
    print("=" * 80)

    fetch = FetchDataNode()
    process = ProcessDataNode()

    fetch >> process

    flow = AsyncFlow()
    flow.start(fetch)

    shared = {}
    await flow.run_async(shared)

    print(f"\nFinal result: {shared['result']}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Sync examples
    demo_retry()
    demo_batch()
    demo_conditional_flow()

    # Async examples
    print("\n" + "=" * 80)
    print("Running Async Examples")
    print("=" * 80)

    asyncio.run(demo_async())
    asyncio.run(demo_async_parallel_batch())
    asyncio.run(demo_async_flow())

    print("\n" + "=" * 80)
    print("All demos completed!")
    print("=" * 80)
