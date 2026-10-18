# External validation report

更新时间：2026-05-12

## Dataset

外部验证集位于 `paper_analysis/supplementary_experiments/datasets/external_validation/manifest.csv`，共 90 张图像，覆盖 30 个候选科，每科 3 张。当前来源构成为 iNaturalist 72 张、GBIF 18 张；每条记录均保存了 source、record id、taxon、license、rights holder、image URL 与本地图片路径。

构建策略是优先使用项目 `ferns_dataset/species_data.json` 中的代表 species/genus 检索，而不是只按外部数据库的 family 粗拉，因此更贴近原始实验的中文科标签体系。

## Current results

完整表见 `paper_analysis/supplementary_experiments/tables/external_validation_summary.csv`。

| Model | Status | Completed | Family Acc | 95% CI | Top-3 | Macro/Balanced | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-35B-A3B / qwen3.5-flash | completed | 90/90 | 33.3% | 24.5%-43.6% | 44.4% | 33.3% | 4.4% |
| Gemini 3.1 Flash Lite | completed | 90/90 | 41.1% | 31.5%-51.4% | 56.7% | 41.1% | 0.0% |
| Qwen3.5 Plus / 397B | completed | 90/90 | 43.3% | 33.6%-53.6% | 60.0% | 43.3% | 0.0% |

Qwen3.5 Plus / 397B 的外部验证已经补齐，三组核心模型均为 completed。

## Interpretation

外部验证结果整体低于主实验 full-set direct30 的约 57%-61% 区间，说明模型在跨来源、跨拍摄条件图像上的泛化能力明显受限。这个结果对 Ecological Informatics 的写作非常关键：论文不应只写闭集排行榜，而应强调真实生态信息学部署中的跨来源泛化风险。

三组核心模型的外部集 family accuracy 为 33.3%-43.3%，整体明显低于主实验 full-set direct30 的约 57%-61% 区间。模型间配对检验见 `supplementary_pairwise_mcnemar_bootstrap.csv`：Qwen3.5 Plus / 397B 相比 Qwen3.5-35B/qwen3.5-flash 的差异为 10.0 个百分点，McNemar p=0.078354；与 Gemini 的差异为 -2.2 个百分点，p=0.845019。因此论文中应强调外部泛化下降，而不是把外部集写成明确模型排名。

## Reproduce

如需复现 Qwen3.5 Plus / 397B 外部验证：

```bash
DASHSCOPE_API_KEY='<DASHSCOPE_API_KEY>' MODELSCOPE_API_KEY='<MODELSCOPE_API_KEY>' python3 paper_analysis/supplementary_experiments/scripts/run_supplementary_vlm_experiments.py --experiments external --providers qwen397b --max-output-tokens 900 --max-image-side 1536
```

复现或新增模型后重新分析：

```bash
python3 paper_analysis/supplementary_experiments/scripts/analyze_supplementary_experiments.py
python3 paper_analysis/supplementary_experiments/scripts/validate_supplementary_outputs.py
```
