"""Run all three evaluation suites and print results (ASCII-safe)."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent

SEP = "=" * 60
SUB = "-" * 40


def run_tool_eval():
    """Tool Eval — mock mode."""
    print(SEP)
    print("SUITE 1/3: Tool Eval (mock mode)")
    print(SEP)

    from agentflow.eval.tool_eval.dataset import ToolEvalDataset
    from agentflow.eval.tool_eval.mock_runner import MockToolEvalRunner

    ds = ToolEvalDataset.load(str(_EVAL_DIR / "tool_eval" / "data" / "mock_tool_dataset.jsonl"))
    print(f"Loaded {len(ds)} samples")
    print(f"Stats: {ds.stats()}")

    runner = MockToolEvalRunner(ds)
    result = runner.run(verbose=True)

    summary = result["summary"]
    print(f"\n--- Tool Eval Results ---")
    print(f"Overall success_rate: {summary['success_rate']:.2%}")
    print(f"Action rates:")
    for action, rate in sorted(summary.get("action_rates", {}).items()):
        print(f"  {action}: {rate:.2%}")
    print(f"Error distribution: {summary.get('error_distribution', {})}")

    # Show mismatches
    mismatches = [s for s in runner.per_sample if not s.get("expected_match", True)]
    if mismatches:
        print(f"\nMismatches ({len(mismatches)}):")
        for m in mismatches[:15]:
            print(f"  [{m['sample_id']}] {m['tool']}.{m['action']} "
                  f"expected={m['expected_success']} actual={m['actual_success']}")
    else:
        print("No mismatches.")

    runner.save_results(str(_EVAL_DIR / "tool_eval" / "data" / "mock_tool_results.json"))
    print("Results saved.")
    return summary


def run_planner_eval():
    """Planner Eval."""
    print(f"\n{SEP}")
    print("SUITE 2/3: Planner Eval")
    print(SEP)

    from agentflow.eval.planner_eval.dataset import PlannerEvalDataset
    from agentflow.eval.planner_eval.runner import PlannerEvalRunner

    ds = PlannerEvalDataset.load(str(_EVAL_DIR / "planner_eval" / "data" / "planner_dataset.jsonl"))
    print(f"Loaded {len(ds)} samples")
    print(f"Stats: {ds.stats()}")

    runner = PlannerEvalRunner(ds)
    result = runner.run(verbose=True)

    summary = result["summary"]
    print(f"\n--- Planner Eval Results ---")
    for key, value in sorted(summary.items()):
        print(f"  {key}: {value:.4f}")

    runner.save_results(str(_EVAL_DIR / "planner_eval" / "data" / "planner_results.json"))
    print("Results saved.")
    return summary


def run_completion_eval():
    """Completion Eval."""
    print(f"\n{SEP}")
    print("SUITE 3/3: Completion Eval")
    print(SEP)

    from agentflow.eval.completion_eval.dataset import CompletionEvalDataset
    from agentflow.eval.completion_eval.runner import CompletionEvalRunner

    ds = CompletionEvalDataset.load(
        str(_EVAL_DIR / "completion_eval" / "data" / "completion_dataset.jsonl")
    )
    print(f"Loaded {len(ds)} samples")
    print(f"Stats: {ds.stats()}")

    runner = CompletionEvalRunner(ds)
    result = runner.run(max_turns=5, verbose=True)

    summary = result["summary"]
    print(f"\n--- Completion Eval Results ---")
    for key, value in sorted(summary.items()):
        print(f"  {key}: {value:.4f}")

    # Show per-sample summary
    print(f"\nPer-sample:")
    for s in runner.per_sample:
        status = "OK" if s.get("expected_match", False) else "MISMATCH"
        print(f"  [{status}] {s['sample_id']}: turns={s.get('turns_taken',0)} "
              f"tasks_done={s.get('tasks_done',0)}/{s.get('tasks_total',0)} "
              f"completed={s.get('goal_completed', False)} "
              f"expected_completed={s.get('expected_completed', False)}")

    runner.save_results(
        str(_EVAL_DIR / "completion_eval" / "data" / "completion_results.json")
    )
    print("Results saved.")
    return summary


def main():
    all_summaries = {}

    # 1. Tool Eval
    try:
        all_summaries["tool_eval"] = run_tool_eval()
    except Exception:
        print(f"FAILED: Tool Eval")
        traceback.print_exc()

    # 2. Planner Eval
    try:
        all_summaries["planner_eval"] = run_planner_eval()
    except Exception:
        print(f"FAILED: Planner Eval")
        traceback.print_exc()

    # 3. Completion Eval
    try:
        all_summaries["completion_eval"] = run_completion_eval()
    except Exception:
        print(f"FAILED: Completion Eval")
        traceback.print_exc()

    # Final summary
    print(f"\n{SEP}")
    print("FINAL SUMMARY")
    print(SEP)
    for suite_name, summary in all_summaries.items():
        print(f"{suite_name}:")
        if isinstance(summary, dict):
            for k, v in sorted(summary.items()):
                if isinstance(v, float):
                    print(f"  {k}: {v:.4f}")
                elif isinstance(v, dict):
                    print(f"  {k}: {len(v)} entries")
                else:
                    print(f"  {k}: {v}")
        print()


if __name__ == "__main__":
    main()
