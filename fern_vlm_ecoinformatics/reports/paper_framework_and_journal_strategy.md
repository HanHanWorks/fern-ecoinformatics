# 论文框架与目标期刊策略

## 一、论文定位

### 推荐定位

本文建议定位为：

**植物分类学与生物多样性信息学视角下的通用视觉语言模型能力边界评估。**

不建议写成纯大模型 benchmark，也不建议写成“某模型性能最佳”的模型竞赛式论文。当前结果真正有价值的地方是：在蕨类植物这一细粒度、专业门槛高、形态证据依赖强的类群上，系统证明通用视觉语言模型只能达到中等科级识别能力，而在种级鉴定上几乎失效。

### 中心论点

通用视觉语言模型已经能够利用部分图像线索和页面文字线索完成一定程度的蕨类科级闭集分类，但其分类学推理能力、闭集约束遵循能力和细粒度种级鉴定能力仍明显不足。因此，当前 VLM 更适合作为植物数字化资料的辅助筛查工具，而不能替代专家鉴定。

## 二、建议英文标题

优先推荐：

**Can General-Purpose Vision-Language Models Identify Ferns? A Taxonomic Evaluation from Family to Species Level**

备选：

1. **Assessing the Limits of Vision-Language Models for Fern Identification: A Closed-Set Evaluation from Family to Species Level**
2. **Vision-Language Models for Fern Classification: Moderate Family-Level Performance but Failure in Species-Level Identification**
3. **From Family-Level Screening to Species-Level Failure: Evaluating Vision-Language Models for Fern Taxonomic Identification**

## 三、论文结构

### Abstract

建议按四句逻辑写：

1. 背景：VLM 正在被用于生物多样性识别和植物图像理解，但其在专业植物分类学任务中的可靠性仍不清楚。
2. 方法：构建蕨类植物闭集评估，覆盖 30 科科级识别、分类学提示识别、L3 子集和水龙骨科 39 种种级识别，比较 5 个 VLM。
3. 结果：科级准确率最高约 60%，分类学提示没有带来稳定提升，种级准确率接近 0%-2.6%，模型间多数差异不显著。
4. 结论：当前通用 VLM 可作为粗筛工具，但不能可靠承担专业蕨类鉴定。

### 1. Introduction

建议分 5 段：

1. **植物鉴定与生物多样性监测需求**
   - 植物图像识别对数字植物志、生物多样性调查、公众科学和保护生物学有价值。
   - 蕨类植物具有细粒度形态差异，专业鉴定依赖孢子囊群、鳞片、叶脉、根状茎等细节。

2. **VLM 的兴起与应用潜力**
   - GPT/Gemini/Qwen/Mimo 等通用 VLM 具备图像理解和自然语言推理能力。
   - 但多数公开评测集中在通用视觉问答、自然图像或粗粒度识别，专业分类学证据不足。

3. **现有植物 AI 鉴定研究的缺口**
   - 传统植物识别多依赖专用 CNN/ViT、标注图片和大规模训练集。
   - 通用 VLM 是否能零样本/低样本完成专业植物分类，尤其是从科级到种级，尚缺系统评估。

4. **研究问题**
   - RQ1: VLM 在蕨类 30 科闭集识别中能达到什么水平？
   - RQ2: 分类学提示是否改善科级识别？
   - RQ3: 模型规模/模型家族是否带来稳定收益？
   - RQ4: VLM 在水龙骨科种级识别中为何失败？
   - RQ5: 错误模式是否具有分类学解释？

5. **贡献**
   - 提供一个蕨类分类学场景下的 VLM 系统评估。
   - 比较 5 个模型和 4 类任务。
   - 统一报告 invalid、置信区间、McNemar 和 bootstrap 结果。
   - 总结 VLM 在植物分类学应用中的能力边界。

### 2. Materials and Methods

建议小节：

2.1 Dataset and taxonomic scope  
说明数据来源、155 个样本、30 个候选科、水龙骨科 39 种、图像来自植物图鉴/数据集。

2.2 Task design  
四组任务：

- `direct30_full155`: 30 科闭集直接识别。
- `taxonomy_l3`: L3 子集分类学提示。
- `taxonomy_full155`: 全量分类学提示。
- `species_l4`: 水龙骨科 39 种种级闭集。

2.3 Vision-language models  
5 个模型：

- mimo-v2.5
- Qwen3.5 Plus / 397B
- Qwen3.5-27B
- Qwen3.5-35B-A3B
- Gemini 3.1 Flash Lite

2.4 Prompting protocol  
说明固定候选列表、JSON 输出、top-3、置信度、闭集约束。

2.5 Output validation and invalid handling  
明确所有空输出、候选外输出、null、无法解析输出统一记为 invalid，并纳入 invalid rate。

2.6 Statistical analysis  
指标：

- Family accuracy
- Top-3 family accuracy
- Species accuracy
- Invalid rate
- 95% Wilson CI
- McNemar exact test
- Bootstrap paired accuracy difference CI

### 3. Results

建议小节：

3.1 Overall family-level performance  
报告 master table。重点：最高约 60%，不是高可靠识别。

3.2 Effect of taxonomic prompting  
比较 direct30 与 taxonomy_full。当前结果显示 taxonomy prompt 不稳定，不一定提升。

3.3 Model comparison and significance  
强调 Qwen/Gemini 主流模型差异小，多数无显著差异；mimo 明显弱。

3.4 Species-level failure  
种级准确率 0%-2.6%，说明从科级到种级出现性能断崖。

3.5 Invalid outputs and closed-set compliance  
报告少量 invalid，说明闭集约束仍不完全可靠。

3.6 Error patterns  
围绕高频混淆展开：

- 鳞毛蕨科 -> 叉蕨科
- 乌毛蕨科 -> 鳞毛蕨科
- 叉蕨科 -> 水龙骨科
- 骨碎补科 -> 水龙骨科

### 4. Discussion

建议小节：

4.1 What VLMs can do  
能做粗粒度科级筛查，尤其对图像/文字线索明显的类群较有效。

4.2 What VLMs cannot do  
不能稳定提取和解释蕨类关键分类性状；不能可靠完成种级鉴定。

4.3 Why taxonomic prompting did not solve the problem  
提示词提供候选框架，但不能弥补图像证据不足、模型形态学知识不足和细粒度类群混淆。

4.4 Implications for digital floras and biodiversity informatics  
VLM 可用于预筛、标注辅助、低风险候选建议；不能作为自动鉴定终端。

4.5 Limitations  
样本规模有限；图像来自图鉴页面；模型版本和 API 输出会变化；没有专家多轮交互；没有训练专用模型。

4.6 Future work  
扩大类群和图片来源；加入专家标注；对比专用植物识别模型；结合 OCR、形态结构检测和分类树推理。

### 5. Conclusion

推荐结论：

五个通用 VLM 在蕨类科级闭集分类中表现为中等准确率，但在种级鉴定中近乎失败。分类学提示和更大模型并未带来稳定突破。当前 VLM 在植物分类学中的合理角色是辅助筛查，而不是替代专家鉴定。

## 四、目标期刊评估

### 期刊选择原则

本稿最适合投向以下交叉方向：

- plant computational methods
- biodiversity informatics
- ecological informatics
- plant image analysis / AI application
- digital flora / taxonomic informatics

不建议首投纯 AI benchmark 期刊，因为目前数据集规模和方法创新不足以支撑通用 AI benchmark 论文。

## 五、推荐期刊排序

### 1. in silico Plants

**推荐等级：首选**

理由：

- Scope 明确欢迎 computational and data-driven approaches in plant sciences。
- 明确包括 artificial intelligence、machine learning、generative models、image capture/analysis、phenotyping 等技术方向。
- 你的文章可以包装为“data-driven evaluation of VLMs for plant taxonomic identification”。
- 相比 Plant Methods / Ecological Informatics，对“植物科学中的计算方法应用与评估”更贴切。

风险：

- 需要强调这是一个有植物科学问题驱动的评估，而不是简单模型调用。
- 需要把数据、代码、提示词和统计分析整理得可复现。

建议投稿类型：

- Original Research
- 或 computational/data-driven plant science article

### 2. Ecological Informatics

**推荐等级：冲刺首选 / 偏高目标**

理由：

- Scope 覆盖 computational ecology、ecological data science、biogeography、image-based monitoring、machine/deep learning 和 biodiversity 相关定量工具。
- 如果论文强调“VLM 对生物多样性数字化监测和植物分类信息化的能力边界”，匹配度高。
- 期刊影响力较高，适合作为冲刺。

风险：

- 期刊可能更偏生态数据科学和方法创新。
- 你的稿件需要把“蕨类图像分类”提升到 biodiversity informatics / ecological monitoring 的问题，而不是单一植物图鉴测试。

建议投稿类型：

- Research Article

### 3. Applications in Plant Sciences

**推荐等级：稳妥植物期刊方向**

理由：

- 面向植物科学中新技术、工具、协议和实际应用。
- Botanical Society of America 背景，与植物分类学、系统学和方法应用更接近。
- 如果把本文写成“VLM 作为植物分类辅助工具的评估协议和应用研究”，匹配度不错。

风险：

- 期刊可能更喜欢新工具、协议、软件或资源，而不仅是评估。
- 建议补充可复现工作流、prompt protocol、数据整理脚本，增强“Application Article”属性。

### 4. Plant Methods

**推荐等级：可投但需要强化方法创新**

理由：

- Scope 是 plant sciences 中的 technological innovation、techniques、tools 和 methodology。
- 如果强调“一个可复现的 VLM evaluation workflow for plant taxonomic identification”，可以尝试。

风险：

- 目前稿件主要是评估，不是新方法。
- 需要补一个更明确的方法学贡献，例如 standardized closed-set VLM evaluation protocol、invalid-output handling、taxonomy-aware evaluation framework。

### 5. Frontiers in Plant Science - Plant Bioinformatics / Technical Advances

**推荐等级：备选**

理由：

- 影响力和可见度较高，接受 Original Research、Methods、Technology and Code。
- 若投 Plant Bioinformatics，需要强调计算工具、数据分析和植物科学意义。

风险：

- Plant Bioinformatics section 偏 omics 和生物信息学，纯图像分类学评估可能有 scope 风险。
- 可以考虑更合适的 section 或 Research Topic，而不是直接投 Plant Bioinformatics。

## 六、不建议作为首投

### Plant Phenomics

期刊很强，但更偏 plant phenotyping、sensor systems、data analytics、crop/plant phenomics。你的任务是分类学鉴定与数字植物志评估，不是典型 phenomics。除非大幅改写为植物表型图像理解，否则不建议首投。

### Computers and Electronics in Agriculture

影响力很高，但 scope 明确强调农业生产中的计算机、电子、AI、机器视觉和创新系统。你的数据来自蕨类图鉴/分类学资料，不是农业生产场景；且该刊对 novelty 和 investigator-developed tools 要求高。不建议首投。

### BMC Plant Biology

范围广、重视研究 soundness，但更偏植物生物学机制、形态、生理、发育、基因组、互作等。本文主要是 VLM 评估，植物生物学机制贡献不足。可作为后备，但不是最佳。

## 七、最终投稿建议

### 最推荐路线

1. **首投：in silico Plants**
2. **如果想冲高：Ecological Informatics**
3. **如果想更植物分类/应用稳妥：Applications in Plant Sciences**
4. **如果补强方法框架：Plant Methods**

### 我建议你的实际策略

如果你目标是“较稳的 SCI 二区/植物交叉期刊”：

**首选 in silico Plants。**

如果你希望论文影响力更高、愿意承担 desk rejection 风险：

**先投 Ecological Informatics。**

如果你的导师更看重植物学和分类学读者：

**投 Applications in Plant Sciences。**

## 八、针对首选期刊的写法调整

### 若投 in silico Plants

标题关键词：

- vision-language models
- plant taxonomic identification
- data-driven evaluation
- fern classification

摘要强调：

- computational plant science
- AI evaluation
- reproducible benchmark
- model limitations in plant taxonomy

Discussion 强调：

- 未来如何结合 OCR、形态特征检测、分类树推理、专家知识库。

### 若投 Ecological Informatics

标题关键词：

- biodiversity informatics
- digital flora
- ecological monitoring
- vision-language models

摘要强调：

- biodiversity monitoring
- image-based species monitoring
- limitations of general-purpose AI
- uncertainty and invalid outputs

Discussion 强调：

- VLM 对生态监测和物种记录质量控制的风险。

### 若投 Applications in Plant Sciences

标题关键词：

- taxonomic workflow
- plant identification tools
- botanical image analysis
- applications of VLMs

摘要强调：

- practical evaluation protocol
- botanical use case
- reproducible prompts and scripts
- implications for herbarium/digital flora workflows

Discussion 强调：

- 专家工作流辅助，而非替代专家。

## 九、下一步写作行动

1. 先按 **in silico Plants** 风格写第一版。
2. Methods 写得非常可复现：数据、任务、prompt、模型、invalid 规则、统计检验。
3. Results 不夸模型，突出“moderate family-level performance + species-level failure”。
4. Discussion 用植物分类学语言解释错误，不要只写 AI 指标。
5. 最后根据目标期刊再微调 Introduction 和 Discussion。
