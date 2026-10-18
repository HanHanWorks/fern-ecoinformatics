# Strengthened Ecological Informatics narrative

新增补强实验把论文主线从模型排行推进到生态信息学可用性边界：

1. Macro/balanced accuracy 显著低于 micro accuracy，说明总体准确率受样本不均衡影响，稀有科识别更弱。
2. Confidence calibration 显示模型普遍过度自信，高置信错误比例高，实际部署时不能把置信度直接作为可靠性指标。
3. Genus-level 分析显示 species-level 失败不是单纯标签格式问题，而是属级/种级细粒度鉴定链条整体薄弱。
4. Candidate-order robustness 显示闭集候选顺序会改变部分样本预测，提示模型决策存在提示词表述敏感性。
5. External validation 和 open-set rejection 将论文推向真实生态信息学场景：跨来源泛化和拒识能力是当前 VLM 的关键风险点。

写作时建议采用保守表述：这些补强实验不是为了证明某个模型绝对最优，而是为了证明通用 VLM 在蕨类自动鉴定中的可用边界和风险结构。
