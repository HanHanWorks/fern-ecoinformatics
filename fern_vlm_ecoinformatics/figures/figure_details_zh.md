# 论文图片 v2 详细说明与论文数据对照

更新时间：2026-05-14  
适用稿件：`paper_analysis/manuscript_drafts/ecological_informatics_initial_draft_mixed.md`  
图件目录：`paper_analysis/manuscript_figures_v2/`  
导出目录：`paper_analysis/manuscript_figures_v2/paper_ready_jpg/`

本文档用于统一论文插图的设计逻辑、图注写法、数据来源和结果解释口径。当前图组不是模型排行榜，而是服务于论文主线：**general-purpose VLMs can extract non-random family-level signal for fern images, but their ecological-informatics use is limited by class imbalance, prompt/order sensitivity, external source shift, open-set risk, confidence unreliability, and genus/species-level failure.**

## 统一命名与写作口径

### 模型命名

论文正文和图注中建议统一使用以下模型名称：

| 图中/正文统一名称 | 说明 | 接入方式写法 |
|---|---|---|
| `Qwen3.5-397B-A17B` | 原运行记录中可能出现 `Qwen3.5 Plus / 397B`、`qwen3.5-plus`、`qwen3.5-397b-a17b` 或 `Qwen/Qwen3.5-397B-A17B`，论文中统一写为 `Qwen3.5-397B-A17B`。 | DashScope-compatible API |
| `Qwen3.5-35B-A3B` | 原运行记录中可能出现 `Qwen3.5-35B-A3B / qwen3.5-flash`、`qwen3.5-flash`、`qwen3.5-flash-2026-02-23` 或 `Qwen/Qwen3.5-35B-A3B`，论文中统一写为 `Qwen3.5-35B-A3B`。 | DashScope-compatible API |
| `Qwen3.5-27B` | 用于比较同参数量级 dense 架构与 MoE 架构差异。 | ModelScope-compatible API |
| `Gemini 3.1 Flash Lite` | Google 轻量级多模态模型。 | Google AI Studio OpenAI-compatible API |
| `mimo-v2.5` | 作为前期流程验证和五模型主结果之一。 | Mimo-compatible API |

### 数据集与实验命名

| 术语 | 本文档统一含义 |
|---|---|
| local dataset | 本地 155 张 research-only 蕨类图像，覆盖 30 个项目候选科。 |
| direct30_full155 | 30 科闭集 family-level direct prompt，n = 155。 |
| taxonomy_full155 | 30 科闭集 taxonomy-structured prompt，n = 155。 |
| taxonomy_l3 | L3 子集 taxonomy prompt，n = 55。 |
| species_l4 | 水龙骨科 39 物种闭集 species-level 任务，n = 39。 |
| text-masked subset | 从本地图像构建的 60 张文本遮蔽图像，用于检验页面文字/标签线索风险。 |
| external validation | 外部验证集，90 张图像，30 科 × 每科 3 张，来源为 iNaturalist n = 72 和 GBIF n = 18。 |
| open-set experiment | 开放集/拒识实验，120 张图像，包括 60 张 in-scope positive 和 60 张 out-of-scope negative。 |

### 图件总体排版风格

本轮 v2 图组应采用偏期刊论文风格的克制排版：

- 颜色以深灰、浅灰、低饱和蓝绿和少量风险红/橙为主，避免看起来像 dashboard 或商业信息图。
- 每张图保留明确 panel label，例如 `A.`, `B.`, `C.`。
- 数值优先直接标注在图内，减少读者反复查表。
- 对小样本结果必须在说明中标注“descriptive rather than inferential”，尤其是外部验证按 family、GBIF/iNaturalist source 的比较。
- 所有涉及模型高低比较的文字避免写成绝对排名；主表述应为“models exceeded trivial baselines but leading estimates overlapped or clustered within a moderate band”。

## Figure 1 v2. Ecological-informatics workflow audit

### 文件

- HTML：`figure_01_workflow_v2.html`
- 公开版素材：不嵌入本地原始图像，使用 schematic image-evidence placeholder；本地图像不随 GitHub 仓库公开
- 建议导出名：`figure_01_workflow_v2.jpg`

### 论文位置

建议放在 Introduction 末尾或 Methods 开头。它的作用是把论文从“模型性能榜单”转成“生态信息学流程审计”：图像进入生态数据流程，VLM 只作为候选生成、拒识和置信度提示组件，最终仍需校准、异常处理和专家复核。

### 图面结构

Fig1 分为三层：

第一层是输入证据：

- `155 local research-only images`
- `60 text-masked images`
- `90 external images`
- 左侧使用本地 text-masked contact sheet 作为内部草稿视觉素材。

第二层是工作流：

- `1. Source audit`
- `2. VLM inference`
- `3. Reliability gates`
- `4a. Expert review`
- `4b. Database status`
- 另有一条风险分支：`Flag or reject`

第三层是审计模块：

- Closed-set capability：best family accuracy 60.6%
- Robustness checks：60 masked images；order consistency 78.3%-95.0%
- External validation：33.3%-43.3%
- Deployment risk：open-set negative rejection 73.3%-91.7%

### 图中关键数据

| 指标 | 数值 | 来源 |
|---|---:|---|
| 本地主实验图像数 | 155 | local dataset / `master_model_task_summary.csv` |
| 候选科数 | 30 | direct30 design |
| 文本遮蔽子集 | 60 | `text_masked_dataset` / paired masking experiment |
| 外部验证集 | 90 | `external_validation/manifest.csv` |
| best direct30 family accuracy | 60.6% | `Qwen3.5-397B-A17B`, direct30_full155 |
| random top-1 baseline | 3.3% | `baseline_comparison.csv` |
| majority-family baseline | 27.7% | `baseline_comparison.csv` |
| external validation accuracy range | 33.3%-43.3% | `external_validation_summary.csv` |
| open-set negative rejection range | 73.3%-91.7% | `open_set_rejection_summary.csv` |
| candidate-order consistency range | 78.3%-95.0% | `order_prediction_consistency.csv` |

### 图注建议

**Figure 1. Workflow for auditing general-purpose VLMs in fern identification within an ecological-informatics data pipeline.** The workflow treats the VLM as an assistive component for candidate-family generation, top-3 suggestion, self-reported confidence, and open-set rejection. Image inputs first pass through source and scope checks, then model inference, invalid-output handling, uncertainty/rejection gates, and human taxonomic review before a record can be treated as verified. The lower evidence cards summarize the experiments used in this study: local 30-family closed-set classification, text-masked and candidate-order robustness checks, iNaturalist/GBIF external validation, open-set rejection, and confidence/error auditing.

### 注意事项

- Fig1 当前包含本地 research-only 图像缩略素材。正文投稿前如果没有图像展示许可，建议替换为抽象化图片框、公开授权外部图像，或只保留示意性占位。
- 这张图要强调 “human-in-the-loop” 和 “auditable workflow”，不要让读者误解为模型可以直接进入数据库。

## Figure 2 v2. Closed-set family accuracy relative to trivial baselines

### 文件

- HTML：`figure_02_main_performance_forest_v2.html`
- JPG：`paper_ready_jpg/figure_02_main_performance_forest_v2.jpg`
- SVG：`paper_ready_jpg/figure_02_main_performance_forest_v2.svg`

### 今日修改要求对应情况

Fig2 今天已经按“更偏期刊风格”的要求重新优化了 SVG 排版和配色。当前设计不再使用每个模型一种高饱和色的模型榜单风格，而是改成：

- top-1 点和 Wilson 95% CI 使用统一深灰色；
- top-3 点使用统一空心圆和浅灰描边；
- majority-family baseline 使用低饱和棕色虚线；
- random top-1 和 random top-3 使用灰色虚线；
- 右侧结果拆成两列：`Top-1 estimate [95% CI]` 和 `Top-3`；
- 每个模型行使用极浅灰背景交替分层，增强打印阅读性；
- 不再让 top-3 空心圆和右侧数字挤在同一位置。

这张图是全文最重要的主结果图之一，建议放在 Results 3.1。

### 图面结构

Fig2 是 forest-plot style 主结果图：

- 横轴：Family accuracy (%)
- 纵轴：五个 VLM
- 实心点：top-1 family accuracy
- 横线：Wilson 95% confidence interval
- 空心点：top-3 family accuracy
- 三条 baseline：
  - random top-1 = 3.3%
  - random top-3 = 10.0%
  - majority-family baseline = 27.7%

### 图中关键数据

| 模型 | n | top-1 family accuracy | Wilson 95% CI | top-3 family accuracy | invalid rate |
|---|---:|---:|---:|---:|---:|
| mimo-v2.5 | 155 | 51.0% | 43.2%-58.7% | 58.1% | 0.6% |
| Qwen3.5-35B-A3B | 155 | 56.8% | 48.9%-64.3% | 70.3% | 0.0% |
| Qwen3.5-27B | 155 | 57.4% | 49.5%-64.9% | 69.0% | 0.0% |
| Gemini 3.1 Flash Lite | 155 | 59.4% | 51.5%-66.8% | 70.3% | 0.0% |
| Qwen3.5-397B-A17B | 155 | 60.6% | 52.8%-68.0% | 71.0% | 0.6% |

Baseline：

| baseline | 数值 | 说明 |
|---|---:|---|
| Random 30-family top-1 | 3.3% | 1 / 30 |
| Random 30-family top-3 | 10.0% | 3 / 30 |
| Majority-family baseline | 27.7% | 始终预测本地数据中最大科 `鳞毛蕨科`，43 / 155 |

### 论文解读口径

建议正文这样写：

- 所有 VLM 都显著高于 random baseline 和 majority-family baseline，说明模型确实提取到非随机的蕨类 family-level 视觉/上下文信号。
- 最高点估计为 Qwen3.5-397B-A17B 的 60.6%，但 Gemini 3.1 Flash Lite 为 59.4%，Qwen3.5-27B 为 57.4%，Qwen3.5-35B-A3B 为 56.8%，领先模型之间差距较小。
- 对领先模型不要写“绝对更优”，应结合 McNemar / bootstrap 表述为差异有限或不稳定。
- top-3 accuracy 明显高于 top-1 accuracy，提示模型更适合做 candidate generation，而不是自动确定分类结果。

### 图注建议

**Figure 2. Family-level closed-set performance of five general-purpose VLMs on the local 30-family dataset (n = 155).** Solid points indicate top-1 family accuracy, hollow points indicate top-3 family accuracy, and horizontal lines show Wilson 95% confidence intervals. Trivial baselines are shown for comparison: random top-1, 3.3%; random top-3, 10.0%; and majority-family baseline, 27.7%. All evaluated VLMs exceeded these baselines, but leading point estimates clustered in a moderate range, with the best top-1 estimate reaching 60.6% for Qwen3.5-397B-A17B and top-3 accuracy reaching 71.0%.

### 数据来源

- `paper_analysis/tables/master_model_task_summary.csv`
- `paper_analysis/tables/baseline_comparison.csv`
- `paper_analysis/tables/pairwise_mcnemar_bootstrap.csv`

## Figure 3 v2. Class imbalance and family-level heterogeneity

### 文件

- HTML：`figure_03_imbalance_heatmap_v2.html`
- JPG：`paper_ready_jpg/figure_03_imbalance_heatmap_v2.jpg`
- SVG：`paper_ready_jpg/figure_03_imbalance_heatmap_v2.svg`

### 论文位置

建议放在 Results 3.2，用于回应审稿人可能提出的核心问题：micro accuracy 60.6% 是否被大科样本膨胀？这张图是支撑 macro/balanced accuracy 的关键图。

### 图面结构

Fig3 为三面板：

Panel A：Micro versus macro family accuracy  
展示每个模型 direct30_full155 的 pooled micro accuracy 与 macro family accuracy 的差距。

Panel B：Family-size distribution  
展示本地数据集强类别不均衡。最大两科：

- Dryopteridaceae / 鳞毛蕨科：n = 43
- Polypodiaceae / 水龙骨科：n = 39

两者合计 82 / 155，占 52.9%。

Panel C：Rare, medium, and common family performance  
展示 rare、medium、common 三组 family macro recall，说明模型对小科识别不稳定。

### 图中关键数据

Direct30 full-set micro 与 macro：

| 模型 | micro family accuracy | macro family accuracy | balanced accuracy | rare macro | medium macro | common macro |
|---|---:|---:|---:|---:|---:|---:|
| mimo-v2.5 | 51.0% | 24.8% | 24.8% | 26.5% | 7.3% | 47.1% |
| Qwen3.5-35B-A3B | 56.8% | 29.5% | 29.5% | 26.5% | 20.8% | 53.9% |
| Qwen3.5-27B | 57.4% | 30.0% | 30.0% | 26.5% | 24.0% | 51.5% |
| Qwen3.5-397B-A17B | 60.6% | 34.1% | 34.1% | 32.4% | 22.9% | 58.2% |
| Gemini 3.1 Flash Lite | 59.4% | 35.8% | 35.8% | 29.4% | 38.5% | 53.4% |

Family-size distribution:

| family | n | 说明 |
|---|---:|---|
| Dryopteridaceae / 鳞毛蕨科 | 43 | 最大科，也是 majority baseline 来源 |
| Polypodiaceae / 水龙骨科 | 39 | 第二大科 |
| Lycopodiaceae / 石松科 | 7 | 中等大小科 |
| Blechnaceae / 乌毛蕨科 | 7 | 中等大小科 |
| Pteridaceae / 凤尾蕨科 | 5 | 中等大小科 |
| Small families, n = 1-4 | 54 total | 多个小科共同组成 |

### 论文解读口径

建议正文重点写：

- direct30 micro accuracy 最高达到 60.6%，但 macro/balanced accuracy 只有 24.8%-35.8%。
- 这说明 family-level 性能并不均匀，micro accuracy 会受到大科样本数量影响。
- 不能把 60.6% 解读成“对 30 个科都达到 60% 以上识别能力”。
- Fig3 是把论文从简单 accuracy 报告推进到 ecological informatics 可靠性审计的关键证据。

### 图注建议

**Figure 3. Class imbalance and family-level heterogeneity in the local evaluation set.** Panel A compares pooled micro accuracy with macro family accuracy for the direct 30-family task. Although pooled family accuracy reached 51.0%-60.6%, macro family accuracy dropped to 24.8%-35.8%. Panel B shows the family-size distribution, in which Dryopteridaceae (n = 43) and Polypodiaceae (n = 39) together contributed 82 of 155 records. Panel C summarizes rare-, medium-, and common-family macro recall, showing that family-level usefulness was uneven across the taxonomic label space.

### 数据来源

- `paper_analysis/supplementary_experiments/tables/macro_balanced_summary.csv`
- `paper_analysis/supplementary_experiments/tables/per_family_performance.csv`
- `ferns_dataset/species_data.json`

## Figure 4 v2. Text masking and candidate-order robustness

### 文件

- HTML：`figure_04_robustness_slope_strip_v2.html`
- JPG：`paper_ready_jpg/figure_04_robustness_slope_strip_v2.jpg`
- SVG：`paper_ready_jpg/figure_04_robustness_slope_strip_v2.svg`

### 论文位置

建议放在 Results 3.5，用于支撑 robustness 叙事。它连接两个问题：

1. 模型是否依赖页面文字/标签线索？
2. 同一批候选科仅改变排列顺序，预测是否稳定？

### 图面结构

Panel A：Paired direct30 accuracy before and after text masking  
三核心模型在 60 张 paired image 上进行原图 vs text-masked 比较。

Panel B：Candidate-order accuracy ranges across shuffled seeds  
三核心模型在 3 个 shuffled candidate-order seeds 下的 accuracy range。

Panel C：Prediction-change burden under candidate-order shuffling  
展示相对于 baseline candidate order，有多少样本改变预测，以及 mean prediction entropy。

### 图中关键数据

Panel A direct30 text masking：

| 模型 | paired n | original acc | masked acc | masked - original | McNemar exact p |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-35B-A3B | 60 | 45.0% | 46.7% | +1.7% | 1.000 |
| Qwen3.5-397B-A17B | 60 | 45.0% | 48.3% | +3.3% | 0.688 |
| Gemini 3.1 Flash Lite | 60 | 46.7% | 45.0% | -1.7% | 1.000 |

Panel B candidate-order shuffled seeds：

| 模型 | seed accuracy range | top-3 range | invalid range |
|---|---:|---:|---:|
| Qwen3.5-35B-A3B | 38.3%-41.7% | 50.0%-55.0% | 3.3%-10.0% |
| Qwen3.5-397B-A17B | 43.3%-50.0% | 55.0%-61.7% | 0.0%-3.3% |
| Gemini 3.1 Flash Lite | 45.0%-48.3% | 51.7%-55.0% | 0.0% |

Panel C prediction change：

| 模型 | changed prediction count | baseline consistency range | mean entropy shown in figure |
|---|---:|---:|---:|
| Qwen3.5-35B-A3B | 15 / 60 | 78.3%-83.3% | 0.263 |
| Qwen3.5-397B-A17B | 13 / 60 | 83.3%-88.3% | 0.232 |
| Gemini 3.1 Flash Lite | 8 / 60 | 90.0%-95.0% | 0.145 |

### 论文解读口径

对 text masking 必须谨慎：

- 可以写：在当前 n = 60 的样本量下，McNemar 检验未检测到文本遮蔽对 direct30 accuracy 的显著影响。
- 不建议写：模型不依赖文本。
- 更稳妥表述：This does not exclude smaller or context-specific text-cue effects because the paired subset has limited power.

对 candidate-order：

- 这部分更适合支撑“closed-set prompt 不是完全稳定的分类器”。
- 同一张图、同一候选列表，仅候选顺序改变，就能导致 8-15 / 60 张图预测改变。
- 这对生态数据流程意味着应记录 prompt version、candidate order 和 model ID。

### 图注建议

**Figure 4. Robustness to text masking and candidate-order perturbation.** Panel A compares paired direct30 predictions on the same 60 images before and after visible page text was masked. At the current sample size, McNemar tests did not detect a significant masking effect, but this does not exclude smaller effects outside the detectable range. Panel B summarizes seed-level accuracy variation when the 30 candidate families were randomly reordered for the three core models. Panel C reports sample-level prediction-change burden and mean prediction entropy across shuffled candidate orders, showing that 8-15 of 60 images changed predicted family depending on candidate order.

### 数据来源

- `paper_analysis/text_masked_experiments/tables/masked_vs_original_paired.csv`
- `paper_analysis/supplementary_experiments/tables/order_robustness_summary.csv`
- `paper_analysis/supplementary_experiments/tables/order_prediction_consistency.csv`
- `paper_analysis/supplementary_experiments/tables/order_prediction_entropy.csv`

## Figure 5 v2. External validation

### 文件

- HTML：`figure_05_external_validation_dumbbell_v2.html`
- JPG：`paper_ready_jpg/figure_05_external_validation_dumbbell_v2.jpg`
- SVG：`paper_ready_jpg/figure_05_external_validation_dumbbell_v2.svg`

### 论文位置

建议放在 Results 3.7。Fig5 是最能支撑 Ecological Informatics 投稿定位的结果图，因为它展示了从本地 reference-derived dataset 到真实 biodiversity-platform images 的 source shift。

### 图面结构

Panel A：Local direct30 versus external validation  
用 dumbbell / paired line 形式展示三核心模型从本地 direct30 到 external validation 的准确率下降。

Panel B：Source-specific external accuracy  
分别展示 GBIF 与 iNaturalist 的表现。GBIF 只有 n = 18，因此图中说明应明确这是 descriptive comparison。

Panel C：Descriptive family-level external extremes  
列出外部验证中表现较高和较低的 family。每个 family 有 3 张图 × 3 个模型 = 9 个 model-image evaluations。

### 图中关键数据

Panel A overall external：

| 模型 | local direct30 | external validation | absolute drop |
|---|---:|---:|---:|
| Qwen3.5-35B-A3B | 56.8% | 33.3% | -23.5 percentage points |
| Qwen3.5-397B-A17B | 60.6% | 43.3% | -17.3 percentage points |
| Gemini 3.1 Flash Lite | 59.4% | 41.1% | -18.3 percentage points |

Panel B source-specific external accuracy：

| 模型 | GBIF n | GBIF acc, 95% CI | iNaturalist n | iNaturalist acc, 95% CI |
|---|---:|---:|---:|---:|
| Qwen3.5-35B-A3B | 18 | 16.7%, 5.8%-39.2% | 72 | 37.5%, 27.2%-49.0% |
| Qwen3.5-397B-A17B | 18 | 33.3%, 16.3%-56.3% | 72 | 45.8%, 34.8%-57.3% |
| Gemini 3.1 Flash Lite | 18 | 61.1%, 38.6%-79.7% | 72 | 36.1%, 26.0%-47.6% |

Panel C external family extremes：

Higher-performing families, each across 9 model-image evaluations:

| family | correct / 9 |
|---|---:|
| Marsileaceae | 9 / 9 |
| Hymenophyllaceae | 9 / 9 |
| Lycopodiaceae | 9 / 9 |
| Psilotaceae | 9 / 9 |
| Gleicheniaceae | 8 / 9 |
| Polypodiaceae | 8 / 9 |

Lower-performing families:

| family | correct / 9 |
|---|---:|
| Tectariaceae | 0 / 9 |
| Marattiaceae | 0 / 9 |
| Arthropteridaceae | 0 / 9 |
| Osmundaceae | 0 / 9 |
| Didymochlaenaceae | 0 / 9 |
| Hypodematiaceae | 0 / 9 |
| Athyriaceae | 0 / 9 |

### 论文解读口径

建议正文突出：

- 外部验证准确率只有 33.3%-43.3%，明显低于本地主实验 56.8%-60.6% 的核心模型表现。
- 这是论文生态信息学意义最强的证据：VLM 在 curated local/reference-derived dataset 上的中等能力不能直接外推到异质化生物多样性图像流。
- GBIF vs iNaturalist 的比较需要报告 95% CI，并强调 GBIF n = 18 较小，不能过度解释 Gemini 在 GBIF 子集上的 61.1%。
- 每科只有 3 张外部图像，因此 family-level extremes 只能作为失败模式探索，不作为逐科显著性判断。

### 图注建议

**Figure 5. External validation on 90 biodiversity-platform images from iNaturalist (n = 72) and GBIF (n = 18).** Panel A shows the drop from local direct30 performance to external family accuracy for the three core models. Panel B reports source-specific accuracies with Wilson 95% confidence intervals; source differences are descriptive because the GBIF subset is small. Panel C summarizes high-performing and low-performing external families across nine model-image evaluations per family. External family accuracy fell to 33.3%-43.3%, emphasizing cross-source generalization risk in ecological-informatics deployment.

### 数据来源

- `paper_analysis/supplementary_experiments/tables/external_validation_summary.csv`
- `paper_analysis/supplementary_experiments/tables/external_validation_by_source.csv`
- `paper_analysis/supplementary_experiments/tables/external_validation_per_family.csv`
- `paper_analysis/supplementary_experiments/datasets/external_validation/manifest.csv`

## Figure 6 v2. Open-set rejection

### 文件

- HTML：`figure_06_open_set_tilematrix_v2.html`
- JPG：`paper_ready_jpg/figure_06_open_set_tilematrix_v2.jpg`
- SVG：`paper_ready_jpg/figure_06_open_set_tilematrix_v2.svg`

### 论文位置

建议放在 Results 3.8 或 Discussion 前的 deployment-risk 小节。Fig6 直接回应生态信息学部署场景：真实数据流中不可能保证所有图像都属于候选 30 科，模型是否能拒识 out-of-scope 样本？

### 图面结构

Panel A：Overall deployment metrics  
并列展示 negative rejection accuracy 与 positive family accuracy。

Panel B：Negative-group rejection matrix  
展示四类 negative group：

- candidate-out fern
- bryophyte_liverwort
- angiosperm
- gymnosperm_cycad

每组 n = 15。

Panel C：High-confidence false positives  
展示 out-of-scope negative 被错误分配到候选科且 confidence >= 0.8 的数量。

### 图中关键数据

Panel A overall open-set：

| 模型 | negative rejection accuracy, 95% CI | false positive rate | positive retention accuracy | positive family accuracy, 95% CI | high-conf false positives |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-35B-A3B | 73.3%, 61.0%-82.9% | 20.0% | 96.7% | 45.0%, 33.1%-57.5% | 12 |
| Qwen3.5-397B-A17B | 91.7%, 81.9%-96.4% | 8.3% | 96.7% | 46.7%, 34.6%-59.1% | 5 |
| Gemini 3.1 Flash Lite | 90.0%, 79.9%-95.3% | 10.0% | 93.3% | 40.0%, 28.6%-52.6% | 5 |

Panel B negative-group rejection：

| 模型 | candidate-out fern | bryophyte/liverwort | angiosperm | gymnosperm/cycad |
|---|---:|---:|---:|---:|
| Qwen3.5-35B-A3B | 13.3%, FP 9 / 15 | 80.0%, FP 3 / 15 | 100.0%, FP 0 / 15 | 100.0%, FP 0 / 15 |
| Qwen3.5-397B-A17B | 73.3%, FP 4 / 15 | 93.3%, FP 1 / 15 | 100.0%, FP 0 / 15 | 100.0%, FP 0 / 15 |
| Gemini 3.1 Flash Lite | 86.7%, FP 2 / 15 | 73.3%, FP 4 / 15 | 100.0%, FP 0 / 15 | 100.0%, FP 0 / 15 |

主要 false-positive families：

| 模型 | candidate-out fern 主要误判科 |
|---|---|
| Qwen3.5-35B-A3B | Selaginellaceae / 卷柏科, Lycopodiaceae / 石松科, Hymenophyllaceae / 膜蕨科 |
| Qwen3.5-397B-A17B | Lycopodiaceae / 石松科, Dryopteridaceae / 鳞毛蕨科 |
| Gemini 3.1 Flash Lite | Gleicheniaceae / 里白科, Lycopodiaceae / 石松科 |

### 论文解读口径

建议正文写：

- open-set prompt 能显著改善 obvious out-of-scope 类别的拒识，例如 angiosperm 和 gymnosperm/cycad 在三模型中均达到 100.0% rejection。
- 但 candidate-out fern 是最重要、也最贴近真实部署的风险组，因为这些样本视觉上接近候选空间。
- Qwen3.5-35B-A3B 在 candidate-out fern 上只有 13.3% rejection，说明模型容易把候选外的 fern-like/lycophyte-like 样本强行归入候选科。
- 高置信 false positives 是生态数据流程中的高风险错误，因为它们可能绕过人工复核阈值。

### 图注建议

**Figure 6. Open-set rejection performance on 120 images, including 60 in-scope positives and 60 out-of-scope negatives.** Panel A compares negative rejection accuracy with retained positive family accuracy under the open-set prompt. Panel B breaks rejection performance down by negative group, including candidate-out ferns, bryophyte/liverwort images, angiosperms, and gymnosperm/cycad images. Panel C highlights high-confidence false positives. Although overall negative rejection reached 73.3%-91.7%, visually similar out-of-scope fern-like images remained the dominant deployment risk.

### 数据来源

- `paper_analysis/supplementary_experiments/tables/open_set_rejection_summary.csv`
- `paper_analysis/supplementary_experiments/tables/open_set_by_negative_group.csv`
- `paper_analysis/supplementary_experiments/tables/open_set_false_positive_cases.csv`
- `paper_analysis/supplementary_experiments/datasets/open_set/manifest.csv`

## Figure 7 v2. Taxonomic rank collapse

### 文件

- HTML：`figure_07_taxonomic_rank_ladder_v2.html`
- JPG：`paper_ready_jpg/figure_07_taxonomic_rank_ladder_v2.jpg`
- SVG：`paper_ready_jpg/figure_07_taxonomic_rank_ladder_v2.svg`

### 论文位置

建议放在 Results 3.4 或 species/genus failure 小节。Fig7 说明：即便模型在 species_l4 prompt 下经常保持 family 正确，fine-grained species/genus identification 仍然失败。

### 图面结构

Fig7 是 rank-collapse ladder：

- 横轴：accuracy (%)
- 每个模型一行
- 最右侧大点：species prompt 下 family-level correctness
- 中间近 0 的点：genus accuracy
- 最左侧近 0 的点：species exact-match accuracy

### 图中关键数据

species_l4 subset：n = 39

| 模型 | family accuracy under species prompt | genus accuracy | genus top-3 accuracy | species accuracy | family-correct but genus-wrong cases | genus invalid count |
|---|---:|---:|---:|---:|---:|---:|
| mimo-v2.5 | 100.0% | 5.1% | 5.1% | 2.6% | 37 | 1 |
| Qwen3.5-27B | 100.0% | 7.7% | 7.7% | 2.6% | 36 | 0 |
| Qwen3.5-35B-A3B | 97.4% | 7.7% | 7.7% | 2.6% | 35 | 2 |
| Qwen3.5-397B-A17B | 97.4% | 7.7% | 7.7% | 2.6% | 35 | 0 |
| Gemini 3.1 Flash Lite | 97.4% | 7.7% | 10.3% | 0.0% | 35 | 2 |

### 论文解读口径

建议正文强调：

- species_l4 不是说明模型真的具备 species-level 识别能力，恰恰相反，它说明 fine-grained 分类边界非常明显。
- family accuracy under species prompt 为 97.4%-100.0%，但 genus accuracy 只有 5.1%-7.7%，species accuracy 只有 0.0%-2.6%。
- 这说明模型可能知道“这大概属于水龙骨科/fern-like group”，但无法可靠解析属种级别形态特征。
- 对生态信息学数据库而言，species-level occurrence records 不能由这些 general-purpose VLM 自动生成。

### 图注建议

**Figure 7. Rank-collapse ladder for the species_l4 subset (n = 39).** Family correctness under the species-level prompt remained high at 97.4%-100.0%, but collapsing predictions from species to genus did not rescue fine-grained performance. Genus accuracy remained only 5.1%-7.7%, genus top-3 accuracy reached at most 10.3%, and species exact-match accuracy remained 0.0%-2.6%. These results indicate a severe fine-grained identification boundary even when family-level information was preserved.

### 数据来源

- `paper_analysis/tables/master_model_task_summary.csv`
- `paper_analysis/supplementary_experiments/tables/genus_level_summary.csv`
- `paper_analysis/supplementary_experiments/tables/species_to_genus_error_cases.csv`

Figure 8. Confidence reliability and error taxonomy

Placement suggestion: Results 3.9, or immediately before the Discussion subsection on deployment risk / calibration.

Figure structure

Panel A – Mean confidence versus observed family accuracy
This panel illustrates the discrepancy between model-reported confidence and the actual observed accuracy across models. Each point represents a model’s mean confidence versus its measured family-level accuracy on the direct30_full155 dataset.

Panel B – High-confidence error rate
High-confidence predictions are defined as those with self-reported confidence ≥ 0.8. This panel shows both the proportion and raw counts of predictions that were incorrect despite high confidence.

Panel C – Error taxonomy matrix
This matrix categorizes model errors for a subset of representative models (to avoid figure clutter). Error types are not mutually exclusive; counts indicate how many errors fall into each category. Categories include:

Same L1 group: errors where the prediction is in the same first-level taxonomic group as the true label.
High-confidence error: incorrect predictions with confidence ≥ 0.8.
Page/text cue: errors likely influenced by text on source pages.
Dominant family: errors biased toward the most common family in the dataset.
Broad group: errors at a coarser taxonomic resolution.
Invalid: predictions that are taxonomically invalid.
Missing morphology: errors due to missing or ambiguous diagnostic features.
Key data

Panel A/B – Confidence reliability (direct30_full155)

Model	n with confidence	Observed accuracy	Mean confidence	ECE	High-conf error count	High-conf error rate
mimo-v2.5	141	54.6%	0.891	0.345	48	34.0%
Qwen3.5-35B-A3B	155	56.8%	0.911	0.344	55	35.5%
Qwen3.5-27B	155	57.4%	0.945	0.374	62	40.0%
Gemini 3.1 Flash Lite	155	59.4%	0.950	0.356	56	36.1%
Qwen3.5-397B-A17B	154	61.0%	0.959	0.348	55	35.7%

Panel C – Error taxonomy counts (subset of models)

Model	Same L1 group	High-conf error	Page/text cue	Dominant family	Broad group	Invalid	Missing morphology
mimo-v2.5	67	48	38	45	8	1	7
Qwen3.5-35B-A3B	59	55	39	25	8	0	0
Qwen3.5-397B-A17B	55	55	39	28	5	1	1

Note: The full error-type table also includes Qwen3.5-27B and Gemini 3.1 Flash Lite. Confidence refers to the self-reported field in the model’s JSON output, not a calibrated API probability.

Interpretation
Confidence vs. accuracy mismatch: Mean model confidence (0.891–0.959) substantially overestimates observed accuracy (54.6–61.0%).
High-confidence errors: 34–40% of predictions with confidence ≥ 0.8 are incorrect. Therefore, using confidence as an automatic acceptance threshold is not viable.
Error patterns:
Same-L1-group confusion and dominant-family attraction suggest that models capture broad patterns but fail on fine-grained, diagnostic morphological traits.
Page/text cues highlight the potential influence of extraneous text, suggesting that source images must be audited for textual contamination.

Takeaway: Reported confidence cannot be interpreted as a reliable probability for acceptance. Models show high confidence even when fundamentally uncertain, and errors cluster along predictable taxonomic biases or visual/textual confounders.

### 图注建议

**Figure 8. Confidence reliability and error taxonomy for the direct 30-family task.** Panel A compares self-reported model confidence with observed family accuracy for rows containing confidence values. Panel B shows the rate of high-confidence errors using a confidence threshold of at least 0.8. Panel C summarizes dominant error categories, including same-L1-group confusion, dominant-family attraction, page/text cue risk, broad-group confusion, invalid outputs, and missing key morphology. Across models with confidence fields, mean self-reported confidence remained high (0.891-0.959) despite observed family accuracy of only 54.6%-61.0%, indicating that reported confidence should not be used as an automatic acceptance rule without task-specific calibration and human review.

### 数据来源

- `paper_analysis/supplementary_experiments/tables/confidence_calibration_summary.csv`
- `paper_analysis/supplementary_experiments/tables/confidence_bins.csv`
- `paper_analysis/supplementary_experiments/tables/high_confidence_errors.csv`
- `paper_analysis/supplementary_experiments/tables/error_taxonomy_summary.csv`
- `paper_analysis/supplementary_experiments/tables/error_taxonomy_cases.csv`

## 建议的论文插图排序

建议正文中使用 8 张主图的顺序如下：

| 顺序 | 图 | 主要回答的问题 | 论文功能 |
|---:|---|---|---|
| 1 | Fig1 workflow | 这篇文章到底不是榜单，而是什么？ | 建立 ecological-informatics audit 框架 |
| 2 | Fig2 main performance | VLM 对本地 30 科蕨类图像是否有 family-level 能力？ | 主结果，显示优于 baseline 但能力有限 |
| 3 | Fig3 imbalance | 60.6% 是否被大科样本膨胀？ | 回应 class imbalance 与 macro/balanced accuracy |
| 4 | Fig7 species/genus | family-level 能力能否下推到属种？ | 说明 fine-grained taxonomy failure |
| 5 | Fig4 robustness | 文本遮蔽和候选顺序是否影响结果？ | 说明 prompt/data-context 稳定性问题 |
| 6 | Fig5 external | 外部数据泛化如何？ | 核心 ecological-informatics stress test |
| 7 | Fig6 open-set | 模型能否拒绝候选外图像？ | 部署风险与拒识能力 |
| 8 | Fig8 confidence/error | confidence 能不能作为自动接收依据？ | 可靠性、校准和错误类型总结 |

如果期刊版面有限，建议正文保留 Fig1-Fig6，将 Fig7-Fig8 放入 Supplementary 或合并为一张 reliability boundary figure。但从 Ecological Informatics 叙事完整性看，Fig7 和 Fig8 都很有价值。

## 需要与正文保持一致的关键句

下面这些句子可作为正文或图注附近的安全表述：

1. The evaluated VLMs performed clearly above random and majority-family baselines, but the best closed-set family accuracy remained moderate at 60.6%.
2. Macro and balanced accuracies were substantially lower than pooled micro accuracy, indicating that performance was not uniform across the 30 families.
3. At the current n = 60 paired subset, McNemar tests did not detect a significant text-masking effect; however, the experiment has limited power and does not exclude smaller text-cue effects.
4. Candidate-order perturbation changed predicted families for 8-15 of 60 images across the three core models, showing that closed-set prompting is not fully stable.
5. External validation accuracy dropped to 33.3%-43.3%, making cross-source generalization a central deployment limitation.
6. Open-set negative rejection reached 73.3%-91.7%, but visually similar candidate-out fern-like negatives remained the most relevant deployment risk.
7. Species-level accuracy remained 0.0%-2.6%, and genus accuracy remained 5.1%-7.7%, showing that family-level signal did not translate into reliable fine-grained identification.
8. Self-reported confidence was not calibrated: mean confidence reached 0.891-0.959 while observed family accuracy remained 54.6%-61.0% among rows with confidence fields.

## 最终检查清单

投稿前建议逐项检查：

- Fig2 中模型名称必须是 `Qwen3.5-397B-A17B` 和 `Qwen3.5-35B-A3B`，不要再出现 `Plus / 397B` 或 `qwen3.5-flash` 作为正文模型名。
- Fig5 的 GBIF / iNaturalist source-specific accuracy 必须带 95% CI，且注明 GBIF n = 18。
- Fig4 text masking 不能写成“模型不依赖文本”，只能写“当前样本量下未检测到显著影响”。
- Fig3 必须在正文中报告 macro/balanced accuracy，避免只展示 micro accuracy。
- Fig6 必须突出 candidate-out fern，而不是只看整体 negative rejection。
- Fig8 必须写明 confidence 是 self-reported output，不是 calibrated class probability。
- Fig1 若使用本地图片缩略素材，必须先确认版权/展示许可；否则改为示意图或授权图片。
- 所有图注中的结果数字应与以下表格一致：
  - `paper_analysis/tables/master_model_task_summary.csv`
  - `paper_analysis/tables/baseline_comparison.csv`
  - `paper_analysis/supplementary_experiments/tables/macro_balanced_summary.csv`
  - `paper_analysis/text_masked_experiments/tables/masked_vs_original_paired.csv`
  - `paper_analysis/supplementary_experiments/tables/order_robustness_summary.csv`
  - `paper_analysis/supplementary_experiments/tables/external_validation_summary.csv`
  - `paper_analysis/supplementary_experiments/tables/external_validation_by_source.csv`
  - `paper_analysis/supplementary_experiments/tables/open_set_rejection_summary.csv`
  - `paper_analysis/supplementary_experiments/tables/open_set_by_negative_group.csv`
  - `paper_analysis/supplementary_experiments/tables/genus_level_summary.csv`
  - `paper_analysis/supplementary_experiments/tables/confidence_calibration_summary.csv`
  - `paper_analysis/supplementary_experiments/tables/error_taxonomy_summary.csv`
