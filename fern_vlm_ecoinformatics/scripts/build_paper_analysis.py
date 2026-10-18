#!/usr/bin/env python3
"""Build unified paper-level tables from completed model experiments."""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_analysis"
TABLES = OUT / "tables"
REPORTS = OUT / "reports"
DATA = OUT / "data"
CONFIG = ROOT / "qwen35_35b_a3b_modelscope_pipeline" / "configs" / "canonical_taxonomy.json"


EXPERIMENTS = [
    {
        "model_id": "mimo_v2.5",
        "model_label": "mimo-v2.5",
        "provider": "Mimo",
        "task_files": {
            "direct30_full155": ROOT / "mimo_v25_sci2_pipeline/results/raw/mimo-v2.5_direct30_full155.json",
            "taxonomy_l3": ROOT / "mimo_v25_sci2_pipeline/results/raw/mimo-v2.5_taxonomy_prompt_l3.json",
            "taxonomy_full155": ROOT / "mimo_v25_sci2_pipeline/results/raw/mimo-v2.5_taxonomy_prompt_full155.json",
            "species_l4": ROOT / "mimo_v25_sci2_pipeline/results/raw/mimo-v2.5_species_closed_l4_polypodiaceae39.json",
        },
    },
    {
        "model_id": "qwen3.5_plus_397b",
        "model_label": "Qwen3.5 Plus / 397B",
        "provider": "DashScope + ModelScope",
        "task_files": {
            "direct30_full155": ROOT / "qwen35_plus_sci2_pipeline/results/raw/dashscope-2026__qwen3.5-plus-2026-02-15__direct30_full155.json",
            "taxonomy_l3": ROOT / "qwen35_plus_sci2_pipeline/results/raw/dashscope-2026__qwen3.5-plus-2026-02-15__taxonomy_prompt_l3.json",
            "taxonomy_full155": ROOT / "qwen35_plus_sci2_pipeline/results/raw/dashscope-alias__qwen3.5-plus__taxonomy_prompt_full155.json",
            "species_l4": ROOT / "qwen35_plus_sci2_pipeline/results/raw/modelscope-200calls__Qwen-Qwen3.5-397B-A17B__species_closed_l4_polypodiaceae39.json",
        },
    },
    {
        "model_id": "qwen3.5_27b",
        "model_label": "Qwen3.5-27B",
        "provider": "ModelScope",
        "task_files": {
            "direct30_full155": ROOT / "qwen35_27b_modelscope_pipeline/results/raw/modelscope-27b__Qwen-Qwen3.5-27B__direct30_full155.json",
            "taxonomy_l3": ROOT / "qwen35_27b_modelscope_pipeline/results/raw/modelscope-27b__Qwen-Qwen3.5-27B__taxonomy_prompt_l3.json",
            "taxonomy_full155": ROOT / "qwen35_27b_modelscope_pipeline/results/raw/modelscope-27b__Qwen-Qwen3.5-27B__taxonomy_prompt_full155.json",
            "species_l4": ROOT / "qwen35_27b_modelscope_pipeline/results/raw/modelscope-27b__Qwen-Qwen3.5-27B__species_closed_l4_polypodiaceae39.json",
        },
    },
    {
        "model_id": "qwen3.5_35b_a3b",
        "model_label": "Qwen3.5-35B-A3B",
        "provider": "ModelScope + DashScope",
        "task_files": {
            "direct30_full155": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__direct30_full155.json",
            "taxonomy_l3": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__taxonomy_prompt_l3.json",
            "taxonomy_full155": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__taxonomy_prompt_full155.json",
            "species_l4": ROOT / "qwen35_35b_a3b_modelscope_pipeline/results/raw/modelscope-35b-a3b__Qwen-Qwen3.5-35B-A3B__species_closed_l4_polypodiaceae39.json",
        },
    },
    {
        "model_id": "gemini_3.1_flash_lite",
        "model_label": "Gemini 3.1 Flash Lite",
        "provider": "Google",
        "task_files": {
            "direct30_full155": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__direct30_full155.json",
            "taxonomy_l3": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__taxonomy_prompt_l3.json",
            "taxonomy_full155": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__taxonomy_prompt_full155.json",
            "species_l4": ROOT / "gemini_3_1_flash_lite_pipeline/results/raw/google-gemini__gemini-3.1-flash-lite__species_closed_l4_polypodiaceae39.json",
        },
    },
]


TASK_LABELS = {
    "direct30_full155": "30-family direct closed-set",
    "taxonomy_l3": "30-family taxonomy prompt (L3 subset)",
    "taxonomy_full155": "30-family taxonomy prompt (full set)",
    "species_l4": "Polypodiaceae species closed-set",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0, center - half), min(1, center + half)


def binom_two_sided(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    comb = getattr(math, "comb", _comb)
    probs = [comb(n, i) * (0.5 ** n) for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= obs + 1e-15))


def _comb(n: int, k: int) -> int:
    k = min(k, n - k)
    if k < 0:
        return 0
    value = 1
    for i in range(1, k + 1):
        value = value * (n - k + i) // i
    return value


def bootstrap_diff_ci(a: list[int], b: list[int], reps: int = 5000, seed: int = 20260510) -> tuple[float, float, float]:
    n = len(a)
    if n == 0:
        return 0.0, 0.0, 0.0
    diff = sum(b) / n - sum(a) / n
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        idxs = [rng.randrange(n) for _ in range(n)]
        vals.append((sum(b[i] for i in idxs) - sum(a[i] for i in idxs)) / n)
    vals.sort()
    return diff, vals[int(0.025 * reps)], vals[int(0.975 * reps)]


def load_taxonomy():
    config = load_json(CONFIG)
    canonical = set(config["canonical_families"])
    aliases = config.get("aliases", {})
    return canonical, aliases


def norm_family(label: str, canonical: set[str], aliases: dict[str, str]) -> tuple[str, bool]:
    raw = str(label or "").strip()
    if raw in aliases:
        mapped = aliases[raw]
        return mapped, mapped in canonical
    if raw in canonical:
        return raw, True
    if not raw:
        return "INVALID_EMPTY", False
    compact = re.sub(r"^\s*\d+\s*[.、．)]\s*", "", raw).strip()
    if compact in canonical:
        return compact, True
    m = re.match(r"^([\u4e00-\u9fff]+科)\s*\([^)]*\)$", compact)
    if m:
        stripped = m.group(1)
        return stripped, stripped in canonical
    hits = [fam for fam in canonical if fam in compact]
    if len(hits) == 1:
        return hits[0], True
    return f"INVALID_OOV::{raw}", False


def row_success(row: dict, level: str) -> bool:
    if row.get("error"):
        return False
    if level == "family":
        return bool(str(row.get("predicted_family", "")).strip())
    return bool(str(row.get("predicted_species", "")).strip())


def standardize_row(row: dict, model: dict, task: str, canonical: set[str], aliases: dict[str, str]) -> dict:
    level = row.get("result_level") or ("species" if task == "species_l4" else "family")
    exp_family, exp_valid = norm_family(row.get("expected_family", ""), canonical, aliases)
    pred_family, pred_valid = norm_family(row.get("predicted_family", ""), canonical, aliases)
    top3_raw = row.get("top3_family", [])
    top3 = []
    if isinstance(top3_raw, list):
        for item in top3_raw:
            mapped, valid = norm_family(str(item), canonical, aliases)
            if valid and mapped not in top3:
                top3.append(mapped)
    valid_output = row_success(row, level)
    if level == "family":
        valid_output = valid_output and pred_valid
    else:
        valid_output = valid_output and bool(str(row.get("predicted_species", "")).strip())
    family_correct = bool(valid_output and exp_valid and pred_valid and exp_family == pred_family)
    family_top3_correct = bool(exp_valid and exp_family in top3)
    species_correct = bool(valid_output and row.get("predicted_species") == row.get("expected_species"))
    species_top3 = row.get("top3_species", [])
    species_top3_correct = bool(isinstance(species_top3, list) and row.get("expected_species") in species_top3)
    return {
        "model_id": model["model_id"],
        "model_label": model["model_label"],
        "provider": model["provider"],
        "task": task,
        "task_label": TASK_LABELS[task],
        "species_id": row.get("species_id", ""),
        "expected_family": row.get("expected_family", ""),
        "expected_family_std": exp_family,
        "predicted_family": row.get("predicted_family", ""),
        "predicted_family_std": pred_family,
        "expected_species": row.get("expected_species", ""),
        "predicted_species": row.get("predicted_species", ""),
        "valid_output": valid_output,
        "family_correct": family_correct,
        "family_top3_correct": family_top3_correct,
        "species_correct": species_correct,
        "species_top3_correct": species_top3_correct,
        "elapsed_seconds": float(row.get("elapsed_seconds") or 0),
        "estimated_tokens": int(row.get("estimated_tokens") or 0),
        "error": row.get("error", ""),
        "raw_response": row.get("raw_response", ""),
        "level": level,
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    family_k = sum(r["family_correct"] for r in rows)
    top3_k = sum(r["family_top3_correct"] for r in rows)
    species_k = sum(r["species_correct"] for r in rows)
    species_top3_k = sum(r["species_top3_correct"] for r in rows)
    valid_k = sum(r["valid_output"] for r in rows)
    lo, hi = wilson(family_k, n)
    sp_lo, sp_hi = wilson(species_k, n)
    return {
        "n": n,
        "family_correct": family_k,
        "family_acc": pct(family_k / n if n else 0),
        "family_acc_95ci": f"{pct(lo)}-{pct(hi)}",
        "family_top3_acc": pct(top3_k / n if n else 0),
        "species_correct": species_k,
        "species_acc": pct(species_k / n if n else 0),
        "species_acc_95ci": f"{pct(sp_lo)}-{pct(sp_hi)}",
        "species_top3_acc": pct(species_top3_k / n if n else 0),
        "invalid_count": n - valid_k,
        "invalid_rate": pct((n - valid_k) / n if n else 0),
        "estimated_tokens": sum(r["estimated_tokens"] for r in rows),
        "avg_time_s": f"{sum(r['elapsed_seconds'] for r in rows) / n:.1f}" if n else "0.0",
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    canonical, aliases = load_taxonomy()

    std_rows = []
    for model in EXPERIMENTS:
        for task, path in model["task_files"].items():
            data = load_json(path)
            for row in data:
                std_rows.append(standardize_row(row, model, task, canonical, aliases))

    with (DATA / "standardized_predictions.json").open("w", encoding="utf-8") as f:
        json.dump(std_rows, f, ensure_ascii=False, indent=2)

    master = []
    by_model_task = defaultdict(list)
    for row in std_rows:
        by_model_task[(row["model_id"], row["task"])].append(row)
    for model in EXPERIMENTS:
        for task in ["direct30_full155", "taxonomy_l3", "taxonomy_full155", "species_l4"]:
            rows = by_model_task[(model["model_id"], task)]
            s = summarize(rows)
            master.append({
                "model_id": model["model_id"],
                "model": model["model_label"],
                "provider": model["provider"],
                "task": task,
                "task_label": TASK_LABELS[task],
                **s,
            })
    write_csv(TABLES / "master_model_task_summary.csv", master, [
        "model_id", "model", "provider", "task", "task_label", "n",
        "family_correct", "family_acc", "family_acc_95ci", "family_top3_acc",
        "species_correct", "species_acc", "species_acc_95ci", "species_top3_acc",
        "invalid_count", "invalid_rate", "estimated_tokens", "avg_time_s",
    ])

    mcnemar_rows = []
    for task in ["direct30_full155", "taxonomy_l3", "taxonomy_full155", "species_l4"]:
        task_maps = {}
        for model in EXPERIMENTS:
            rows = by_model_task[(model["model_id"], task)]
            task_maps[model["model_id"]] = {r["species_id"]: int(r["family_correct"]) for r in rows}
        for a, b in combinations(EXPERIMENTS, 2):
            common = sorted(set(task_maps[a["model_id"]]) & set(task_maps[b["model_id"]]))
            av = [task_maps[a["model_id"]][sid] for sid in common]
            bv = [task_maps[b["model_id"]][sid] for sid in common]
            a_only = sum(1 for x, y in zip(av, bv) if x == 1 and y == 0)
            b_only = sum(1 for x, y in zip(av, bv) if x == 0 and y == 1)
            both = sum(1 for x, y in zip(av, bv) if x == 1 and y == 1)
            neither = sum(1 for x, y in zip(av, bv) if x == 0 and y == 0)
            diff, ci_lo, ci_hi = bootstrap_diff_ci(av, bv)
            mcnemar_rows.append({
                "task": task,
                "model_a": a["model_label"],
                "model_b": b["model_label"],
                "paired_n": len(common),
                "acc_a": pct(sum(av) / len(av) if av else 0),
                "acc_b": pct(sum(bv) / len(bv) if bv else 0),
                "both_correct": both,
                "a_only": a_only,
                "b_only": b_only,
                "neither_correct": neither,
                "mcnemar_exact_p": f"{binom_two_sided(min(a_only, b_only), a_only + b_only):.6f}",
                "bootstrap_diff_b_minus_a": pct(diff),
                "bootstrap_diff_95ci": f"{pct(ci_lo)}-{pct(ci_hi)}",
            })
    write_csv(TABLES / "pairwise_mcnemar_bootstrap.csv", mcnemar_rows, [
        "task", "model_a", "model_b", "paired_n", "acc_a", "acc_b",
        "both_correct", "a_only", "b_only", "neither_correct",
        "mcnemar_exact_p", "bootstrap_diff_b_minus_a", "bootstrap_diff_95ci",
    ])

    confusion_rows = []
    for (model_id, task), rows in by_model_task.items():
        model_label = next(m["model_label"] for m in EXPERIMENTS if m["model_id"] == model_id)
        c = Counter(
            (r["expected_family_std"], r["predicted_family_std"])
            for r in rows
            if r["valid_output"] and r["expected_family_std"] != r["predicted_family_std"]
        )
        for (expected, predicted), count in c.most_common(12):
            confusion_rows.append({
                "model_id": model_id,
                "model": model_label,
                "task": task,
                "expected_family": expected,
                "predicted_family": predicted,
                "count": count,
            })
    write_csv(TABLES / "top_family_confusions.csv", confusion_rows, [
        "model_id", "model", "task", "expected_family", "predicted_family", "count"
    ])

    invalid_rows = []
    for r in std_rows:
        if not r["valid_output"]:
            invalid_rows.append({
                "model": r["model_label"],
                "task": r["task"],
                "species_id": r["species_id"],
                "expected_family": r["expected_family"],
                "predicted_family": r["predicted_family"],
                "expected_species": r["expected_species"],
                "predicted_species": r["predicted_species"],
                "error": r["error"],
                "raw_response_head": r["raw_response"][:180],
            })
    write_csv(TABLES / "invalid_outputs_unified.csv", invalid_rows, [
        "model", "task", "species_id", "expected_family", "predicted_family",
        "expected_species", "predicted_species", "error", "raw_response_head",
    ])

    write_narrative(master, mcnemar_rows, confusion_rows, invalid_rows)


def top_model_for_task(master: list[dict], task: str, metric: str = "family_acc") -> list[dict]:
    rows = [r for r in master if r["task"] == task]
    return rows


def write_narrative(master: list[dict], mcnemar_rows: list[dict], confusion_rows: list[dict], invalid_rows: list[dict]) -> None:
    report = []
    report.append("# 论文分析脉络与当前证据链")
    report.append("")
    report.append("## 1. 可以支撑的核心结论")
    report.append("")
    report.append("当前结果更适合写成一篇系统评估型论文，而不是模型性能突破型论文。五个多模态大模型在 30 科闭集识别上的最佳科级准确率约为 60%，模型间差异较小；在水龙骨科 39 种闭集种级识别上，种级准确率整体接近 0%-2.6%。这说明通用 VLM 能利用部分图像和页面文字线索完成粗粒度科级判断，但尚不能可靠完成专业蕨类种级鉴定。")
    report.append("")
    report.append("建议主线：**通用多模态大模型在蕨类植物分类鉴定中的能力边界：科级闭集可用但不稳定，种级鉴定系统性失效。**")
    report.append("")
    report.append("## 2. Master Table 摘要")
    report.append("")
    report.append("| Model | Direct30 Family Acc | Taxonomy Full Family Acc | L3 Family Acc | Species Acc | Invalid Pattern |")
    report.append("|---|---:|---:|---:|---:|---|")
    by_model = defaultdict(dict)
    for row in master:
        by_model[row["model"]][row["task"]] = row
    for model, tasks in by_model.items():
        invalid = ", ".join(
            f"{task}:{tasks[task]['invalid_rate']}"
            for task in ["direct30_full155", "taxonomy_l3", "taxonomy_full155", "species_l4"]
        )
        report.append(
            f"| {model} | {tasks['direct30_full155']['family_acc']} | "
            f"{tasks['taxonomy_full155']['family_acc']} | {tasks['taxonomy_l3']['family_acc']} | "
            f"{tasks['species_l4']['species_acc']} | {invalid} |"
        )
    report.append("")
    report.append("完整表见 `paper_analysis/tables/master_model_task_summary.csv`。")
    report.append("")
    report.append("## 3. 显著性检验如何解释")
    report.append("")
    sig = [r for r in mcnemar_rows if float(r["mcnemar_exact_p"]) < 0.05]
    report.append(f"两两 McNemar 检验共生成 {len(mcnemar_rows)} 个比较，其中 p<0.05 的比较有 {len(sig)} 个。由于主要模型在 full 155 科级任务上的准确率集中在约 57%-61%，多数差异不应解释为显著优劣。论文中应使用保守表述：模型间总体表现接近，未观察到随模型规模单调提升的稳定趋势。")
    report.append("")
    report.append("建议在正文报告 full 155 direct 与 taxonomy 两个主任务的 McNemar p 值，并把完整两两比较放入附表。完整表见 `paper_analysis/tables/pairwise_mcnemar_bootstrap.csv`。")
    report.append("")
    report.append("## 4. 错误分析主线")
    report.append("")
    global_conf = Counter()
    for r in confusion_rows:
        global_conf[(r["expected_family"], r["predicted_family"])] += int(r["count"])
    report.append("跨模型高频混淆集中在以下方向：")
    for (expected, predicted), count in global_conf.most_common(10):
        report.append(f"- {expected} -> {predicted}: {count} 次")
    report.append("")
    report.append("可组织为三个错误机制：")
    report.append("- **优势类群吸附**：水龙骨科、鳞毛蕨科等样本较多或视觉特征明显的类群容易成为默认预测。")
    report.append("- **细粒度形态证据不足**：许多图像缺少孢子囊群、鳞片、叶脉等分类关键性状，模型只能凭叶形或页面文字猜测。")
    report.append("- **闭集约束不稳定**：少数模型会输出候选外科名、候选外物种或 null；这些已统一记为 invalid。")
    report.append("")
    report.append("## 5. 建议研究问题")
    report.append("")
    report.append("1. 通用 VLM 在专业蕨类图像分类中能达到怎样的科级闭集识别能力？")
    report.append("2. 分类学提示是否能显著提升科级识别，还是主要改变错误分布？")
    report.append("3. 模型规模或模型家族是否带来稳定收益？")
    report.append("4. 从科级到种级，性能断崖式下降的主要原因是什么？")
    report.append("5. 对生物多样性调查、植物志数字化和自动鉴定系统而言，这些模型目前适合承担什么角色？")
    report.append("")
    report.append("## 6. 论文结论口径")
    report.append("")
    report.append("推荐结论不要说“某某模型最好”，而是：")
    report.append("")
    report.append("> Across five contemporary VLMs, family-level closed-set fern classification reached only moderate accuracy, while species-level identification remained near chance. Taxonomic prompting did not consistently improve performance, suggesting that current general-purpose VLMs lack robust fine-grained botanical reasoning despite partial use of visual and textual cues.")
    report.append("")
    report.append("中文解释：五个模型能做一定程度的科级粗分类，但不能可靠做专业种级鉴定；提示词不是万能解法，模型规模也没有带来稳定提升。这个发现本身可以作为论文贡献。")
    report.append("")
    if invalid_rows:
        report.append("## 7. 数据清洗说明")
        report.append("")
        report.append(f"共发现 {len(invalid_rows)} 个无效输出或候选外输出，均已在统一分析中标注为 invalid，并纳入 invalid rate。详见 `paper_analysis/tables/invalid_outputs_unified.csv`。")
        report.append("")
    report.append("## 8. 下一步写作任务")
    report.append("")
    report.append("- 把 master table 精简成正文 Table 1。")
    report.append("- 把 McNemar/Bootstrap 结果做成附表，正文只解释关键比较。")
    report.append("- 写 Methods：数据集、闭集任务设计、提示词、模型调用、无效输出处理、统计检验。")
    report.append("- 写 Results：科级表现、提示词影响、种级失败、显著性检验、错误模式。")
    report.append("- 写 Discussion：为什么 VLM 失败、对植物分类学 AI 的启示、局限和未来方向。")
    (REPORTS / "paper_narrative_and_analysis.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
