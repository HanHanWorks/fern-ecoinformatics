# 论文分析脉络与当前证据链

## 1. 可以支撑的核心结论

当前结果更适合写成一篇系统评估型论文，而不是模型性能突破型论文。五个多模态大模型在 30 科闭集识别上的最佳科级准确率约为 60%，模型间差异较小；在水龙骨科 39 种闭集种级识别上，种级准确率整体接近 0%-2.6%。这说明通用 VLM 能利用部分图像和页面文字线索完成粗粒度科级判断，但尚不能可靠完成专业蕨类种级鉴定。

建议主线：**通用多模态大模型在蕨类植物分类鉴定中的能力边界：科级闭集可用但不稳定，种级鉴定系统性失效。**

## 2. Master Table 摘要

| Model | Direct30 Family Acc | Taxonomy Full Family Acc | L3 Family Acc | Species Acc | Invalid Pattern |
|---|---:|---:|---:|---:|---|
| mimo-v2.5 | 51.0% | 40.6% | 20.0% | 2.6% | direct30_full155:0.6%, taxonomy_l3:1.8%, taxonomy_full155:0.6%, species_l4:0.0% |
| Qwen3.5 Plus / 397B | 60.6% | 59.4% | 43.6% | 2.6% | direct30_full155:0.6%, taxonomy_l3:0.0%, taxonomy_full155:0.6%, species_l4:0.0% |
| Qwen3.5-27B | 57.4% | 59.4% | 36.4% | 2.6% | direct30_full155:0.0%, taxonomy_l3:0.0%, taxonomy_full155:0.0%, species_l4:0.0% |
| Qwen3.5-35B-A3B | 56.8% | 59.4% | 34.5% | 2.6% | direct30_full155:0.0%, taxonomy_l3:0.0%, taxonomy_full155:0.0%, species_l4:0.0% |
| Gemini 3.1 Flash Lite | 59.4% | 57.4% | 41.8% | 0.0% | direct30_full155:0.0%, taxonomy_l3:0.0%, taxonomy_full155:0.0%, species_l4:0.0% |

完整表见 `paper_analysis/tables/master_model_task_summary.csv`。

## 3. 显著性检验如何解释

两两 McNemar 检验共生成 40 个比较，其中 p<0.05 的比较有 12 个。由于主要模型在 full 155 科级任务上的准确率集中在约 57%-61%，多数差异不应解释为显著优劣。论文中应使用保守表述：模型间总体表现接近，未观察到随模型规模单调提升的稳定趋势。

建议在正文报告 full 155 direct 与 taxonomy 两个主任务的 McNemar p 值，并把完整两两比较放入附表。完整表见 `paper_analysis/tables/pairwise_mcnemar_bootstrap.csv`。

## 4. 错误分析主线

跨模型高频混淆集中在以下方向：
- 鳞毛蕨科 -> 叉蕨科: 62 次
- 乌毛蕨科 -> 鳞毛蕨科: 55 次
- 叉蕨科 -> 水龙骨科: 48 次
- 骨碎补科 -> 水龙骨科: 35 次
- 球子蕨科 -> 乌毛蕨科: 30 次
- 肿足蕨科 -> 鳞毛蕨科: 28 次
- 凤尾蕨科 -> 铁角蕨科: 23 次
- 紫萁科 -> 乌毛蕨科: 19 次
- 鳞毛蕨科 -> 藤蕨科: 12 次
- 凤尾蕨科 -> 乌毛蕨科: 10 次

可组织为三个错误机制：
- **优势类群吸附**：水龙骨科、鳞毛蕨科等样本较多或视觉特征明显的类群容易成为默认预测。
- **细粒度形态证据不足**：许多图像缺少孢子囊群、鳞片、叶脉等分类关键性状，模型只能凭叶形或页面文字猜测。
- **闭集约束不稳定**：少数模型会输出候选外科名、候选外物种或 null；这些已统一记为 invalid。

## 5. 建议研究问题

1. 通用 VLM 在专业蕨类图像分类中能达到怎样的科级闭集识别能力？
2. 分类学提示是否能显著提升科级识别，还是主要改变错误分布？
3. 模型规模或模型家族是否带来稳定收益？
4. 从科级到种级，性能断崖式下降的主要原因是什么？
5. 对生物多样性调查、植物志数字化和自动鉴定系统而言，这些模型目前适合承担什么角色？

## 6. 论文结论口径

推荐结论不要说“某某模型最好”，而是：

> Across five contemporary VLMs, family-level closed-set fern classification reached only moderate accuracy, while species-level identification remained near chance. Taxonomic prompting did not consistently improve performance, suggesting that current general-purpose VLMs lack robust fine-grained botanical reasoning despite partial use of visual and textual cues.

中文解释：五个模型能做一定程度的科级粗分类，但不能可靠做专业种级鉴定；提示词不是万能解法，模型规模也没有带来稳定提升。这个发现本身可以作为论文贡献。

## 7. 数据清洗说明

共发现 5 个无效输出或候选外输出，均已在统一分析中标注为 invalid，并纳入 invalid rate。详见 `paper_analysis/tables/invalid_outputs_unified.csv`。

## 8. 下一步写作任务

- 把 master table 精简成正文 Table 1。
- 把 McNemar/Bootstrap 结果做成附表，正文只解释关键比较。
- 写 Methods：数据集、闭集任务设计、提示词、模型调用、无效输出处理、统计检验。
- 写 Results：科级表现、提示词影响、种级失败、显著性检验、错误模式。
- 写 Discussion：为什么 VLM 失败、对植物分类学 AI 的启示、局限和未来方向。

## 9. 七项补强实验如何嵌入论文

新增补强实验位于 `paper_analysis/supplementary_experiments/`。当前最适合把论文主线调整为：

**通用 VLM 在蕨类植物自动鉴定中具备有限科级闭集识别能力，但其生态信息学部署受到类别不均衡、候选顺序敏感、外部泛化不足、open-set 拒识不稳定、置信度失准，以及属/种级细粒度失败的共同限制。**

七项补强实验对应论文段落：

- Macro / balanced / per-family：放在 Results 的“Class imbalance and family-level heterogeneity”，说明 micro accuracy 会高估能力，macro family accuracy 低得多。
- 错误类型分析：放在 Results 的“Failure modes”，把高频混淆写成优势类群吸附、同大类群混淆、关键形态证据缺失、候选外 invalid、高置信错误。
- 置信度校准：放在 Results 或 Discussion，强调模型给出的 confidence 不能直接作为实地调查或自动化流程的可靠性指标。
- 候选顺序稳健性：放在 Results 的“Prompt/candidate-order sensitivity”，说明闭集候选列表顺序会改变预测。
- Open-set 拒识：放在 Results 的“Open-set rejection”，用于支撑真实部署中必须具备拒识机制。三组核心模型均已完成 120/120。
- 外部验证集：放在 Results 的“Cross-source generalization”，说明 iNaturalist/GBIF 外部图像上的准确率明显低于主实验 full-set。
- Genus-level 层级分析：放在 Results 的“Species-to-genus failure cascade”，说明 species_l4 失败不是单纯 exact-match 太严格，折叠到 genus 后仍然很低。

补强实验当前关键结果：

- 候选顺序实验已完成 540/540 条 raw。三模型在 60 张 text-masked 图像上的 family accuracy 大致为 38.3%-50.0%，同一模型不同候选顺序也会波动。
- 外部验证集中，Qwen3.5 Plus/397B 完成 90/90，family accuracy 43.3%；Gemini 完成 90/90，family accuracy 41.1%；Qwen3.5-35B/qwen3.5-flash 完成 90/90，family accuracy 33.3%。三者 95% CI 明显重叠，模型间差异应保守解释。
- Open-set 中，Qwen3.5 Plus/397B 的 negative rejection accuracy 为 91.7%，false positive rate 8.3%，positive family accuracy 46.7%；Gemini 的 negative rejection accuracy 为 90.0%，false positive rate 10.0%，positive family accuracy 40.0%；Qwen3.5-35B/qwen3.5-flash 的 negative rejection accuracy 为 73.3%，false positive rate 20.0%，positive family accuracy 45.0%。
- 置信度校准显示多个模型存在明显 overconfidence：例如 Gemini direct30 mean confidence 0.950，但 high-confidence error rate 36.1%。
- Genus-level 分析显示五模型 genus accuracy 约 5.1%-7.7%，species accuracy 0%-2.6%，支持“种级/属级细粒度鉴定链条整体失败”的结论。

当前七项补强实验已经全部完成，可以稳定写入正文和附表。写作时仍应避免把小幅差异解释为绝对模型优劣，优先强调能力边界、风险结构和生态信息学部署限制。
