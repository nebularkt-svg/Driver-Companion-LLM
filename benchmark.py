# benchmark.py
import time
import json
from datetime import datetime
from typing import List, Dict

from prompt_builder import build_messages
from llm_client import call_online, call_local, ONLINE_MODELS, LOCAL_MODELS

TEST_CASES = [
    {"emotion": "angry",    "speech": "What is that driver doing!",      "trigger": "speech"},
    {"emotion": "angry",    "speech": None,                               "trigger": "emotion_intervention"},
    {"emotion": "sad",      "speech": "Today was really rough",           "trigger": "speech"},
    {"emotion": "sad",      "speech": None,                               "trigger": "emotion_intervention"},
    {"emotion": "fear",     "speech": "That turn came out of nowhere",    "trigger": "speech"},
    {"emotion": "fear",     "speech": None,                               "trigger": "emotion_intervention"},
    {"emotion": "happy",    "speech": "Great day today!",                 "trigger": "speech"},
    {"emotion": "happy",    "speech": None,                               "trigger": "companionship"},
    {"emotion": "neutral",  "speech": "What time is it?",                 "trigger": "speech"},
    {"emotion": "neutral",  "speech": None,                               "trigger": "companionship"},
    {"emotion": "disgust",  "speech": "This road has been under construction forever!", "trigger": "speech"},
    {"emotion": "surprise", "speech": None,                               "trigger": "emotion_intervention"},
]

BENCHMARK_ONLINE_MODELS = list(ONLINE_MODELS.keys())
INCLUDE_LOCAL = False


def run_benchmark(
    save_to: str = "benchmark_results.json",
    models: List[str] = None,
    cases: List[Dict] = None,
) -> List[Dict]:
    models  = models or BENCHMARK_ONLINE_MODELS
    cases   = cases  or TEST_CASES
    results = []
    total   = len(models) * len(cases)
    done    = 0

    print(f"\n{'='*55}")
    print(f"Benchmark: {len(models)} models x {len(cases)} cases = {total} calls")
    print(f"{'='*55}\n")

    for model_key in models:
        is_local = model_key in LOCAL_MODELS

        if is_local and not INCLUDE_LOCAL:
            print(f"[Skip] {model_key} (local model, INCLUDE_LOCAL=False)")
            continue

        for case in cases:
            done += 1
            has_speech = "yes" if case["speech"] else "no"
            print(f"[{done}/{total}] {model_key} | emotion={case['emotion']} | speech={has_speech}")

            messages = build_messages(
                emotion=case["emotion"],
                speech_text=case["speech"],
                trigger_reason=case["trigger"],
            )

            start    = time.time()
            error    = None
            response = None

            try:
                if is_local:
                    response = call_local(messages, model_key)
                else:
                    response = call_online(messages, model_key)
            except Exception as e:
                error = str(e)
                print(f"  x Error: {error}")

            latency_ms = (time.time() - start) * 1000

            result = {
                "model":       model_key,
                "emotion":     case["emotion"],
                "has_speech":  case["speech"] is not None,
                "speech_text": case["speech"],
                "trigger":     case["trigger"],
                "response":    response,
                "latency_ms":  round(latency_ms, 1),
                "char_count":  len(response) if response else 0,
                "error":       error,
            }
            results.append(result)

            if response:
                print(f"  -> {response[:70]}{'...' if len(response) > 70 else ''}")
                print(f"  {latency_ms:.0f}ms\n")

    output = {
        "run_at":  datetime.now().isoformat(),
        "models":  models,
        "results": results,
        "summary": _summarize(results),
    }

    with open(save_to, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {save_to}")
    _print_summary(output["summary"])
    return results


def _summarize(results: List[Dict]) -> Dict:
    from collections import defaultdict
    stats = defaultdict(lambda: {"latencies": [], "errors": 0, "total": 0})

    for r in results:
        m = r["model"]
        stats[m]["total"] += 1
        if r["error"]:
            stats[m]["errors"] += 1
        else:
            stats[m]["latencies"].append(r["latency_ms"])

    summary = {}
    for model, s in stats.items():
        lats = s["latencies"]
        summary[model] = {
            "total":       s["total"],
            "success":     s["total"] - s["errors"],
            "error_count": s["errors"],
            "avg_latency": round(sum(lats) / len(lats), 1) if lats else None,
            "min_latency": round(min(lats), 1) if lats else None,
            "max_latency": round(max(lats), 1) if lats else None,
        }
    return summary


def _print_summary(summary: Dict):
    print(f"\n{'='*55}")
    print("Benchmark Summary")
    print(f"{'='*55}")
    print(f"{'Model':<20} {'OK':<6} {'Avg':>10} {'Min':>10} {'Max':>10}")
    print("-" * 58)
    for model, s in summary.items():
        avg = f"{s['avg_latency']}ms" if s['avg_latency'] else "N/A"
        mn  = f"{s['min_latency']}ms" if s['min_latency'] else "N/A"
        mx  = f"{s['max_latency']}ms" if s['max_latency'] else "N/A"
        print(f"{model:<20} {s['success']}/{s['total']:<4} {avg:>10} {mn:>10} {mx:>10}")
