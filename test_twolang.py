"""Test the two-language snake game request."""
import asyncio
import sys
sys.path.insert(0, 'g:/multi_agent')

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from agentflow.graph.workflow import build_workflow


async def test():
    wf = build_workflow()
    state = {
        "question": "创建两个文件一个用python实现一个用Java实现的贪吃蛇小游戏",
        "workflow": [],
        "history": [],
    }
    final = None

    async for event in wf.astream(state):
        for name, upd in event.items():
            if name == "reflector":
                res = upd.get("_reflection_result", "?")
                msg = upd.get("_reflection_message", "")[:60]
                print(f"[reflector] result={res} msg={msg}")
            elif name == "tool_executor":
                tr = upd.get("tool_results", [])
                for r in tr:
                    a = r.get("action", "?")
                    s = r.get("success")
                    print(f"[executor] action={a} success={s}")
            elif name == "planner":
                tq = upd.get("task_queue", [])
                todo = [t for t in tq if t.get("status") == "todo"]
                print(f"[planner] todo={len(todo)} total={len(tq)}")
                for t in todo:
                    inp = t.get("input", {})
                    c = inp.get("content", "")
                    print(f"  TODO: {t.get('task_id')} act={inp.get('action')} path={inp.get('path')} content_len={len(c)}")
            elif name == "memory":
                final = upd

    print("=" * 60)
    if final:
        ans = final.get("answer", "")
        print(f"Answer:\n{ans[:500]}")
    import os
    for root, dirs, files in os.walk("outputs"):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            print(f"  FILE: {fp} ({sz} bytes)")
            if sz < 200:
                with open(fp, "r", encoding="utf-8") as fh:
                    print(f"    CONTENT: {fh.read()[:80]}")


if __name__ == "__main__":
    asyncio.run(test())
