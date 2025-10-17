# 极简 Flow 引擎（仅演示串行执行，on/post/condition 未实现）
def node(prep=None, exec=None, post=None):
    return {
        "prep": prep or (lambda ctx, params: {}),
        "exec": exec or (lambda prep_result, params: prep_result),
        "post": post or (lambda ctx, prep_result, exec_result, params: "next")
    }

class Flow:
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
    return Flow()
