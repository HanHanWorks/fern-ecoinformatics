# Supplementary Prompts and Reproducibility Notes

This supplement records the model-access and prompt protocol used by the completed experiments. API keys are intentionally excluded and must not be stored in manuscript files.

## Model and API Settings

| Model label | Exact model IDs / aliases used | Provider route | Endpoint type | Temperature | Max output tokens | Image long-side limit | Fallback handling |
|---|---|---|---|---:|---|---|---|
| mimo-v2.5 | `mimo-v2.5` | Mimo API / existing completed pipeline | OpenAI-compatible or provider-compatible vision chat interface | 0.0 | 2200 in Mimo runner | not consistently recorded in raw rows | none recorded |
| Qwen3.5-397B-A17B | `qwen3.5-397b-a17b; qwen3.5-plus; qwen3.5-plus-2026-02-15; Qwen/Qwen3.5-397B-A17B` | DashScope | OpenAI-compatible /chat/completions | 0.0 | 900 in Qwen and supplementary runners | 2048 in main Qwen runner; 1536 in supplementary runner | DashScope aliases/fallbacks archived in state files |
| Qwen3.5-27B | `Qwen/Qwen3.5-27B` | DashScope | OpenAI-compatible /chat/completions | 0.0 | 900 | 2048 | archived model ID retained for traceability |
| Qwen3.5-35B-A3B | `qwen3.5-flash; qwen3.5-flash-2026-02-23; Qwen/Qwen3.5-35B-A3B` | DashScope | OpenAI-compatible /chat/completions | 0.0 | 900 | 2048 in main Qwen runner; 1536 in supplementary runner | DashScope aliases treated as the same model family in reporting |
| Gemini 3.1 Flash Lite | `gemini-3.1-flash-lite` | Google AI Studio | OpenAI-compatible /chat/completions | 0.0 | 900 in supplementary runner | 1536 in supplementary runner | none recorded |

All OpenAI-compatible calls used image-plus-text chat messages and requested structured JSON outputs. Each sample was written to raw result files immediately after completion, with state files recording completion count, next sample, status, and resume command. Empty outputs, unparsable outputs, and out-of-candidate outputs were retained and marked invalid rather than discarded.

## Direct 30-Family Closed-Set Prompt Template

```text
你是蕨类植物分类学专家。请只根据图片判断该植物属于以下 30 个候选科中的哪一个。

候选科：
1. <family_1>
...
30. <family_30>

要求：
- selected_option 必须严格等于候选科中文名之一。
- top3 给出最可能的前三个候选科，均必须来自候选列表。
- 不要输出候选外科名。
- 如果证据不足，也选择最可能科，并在 reasoning 中说明不确定原因。

只回复 JSON：
{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Taxonomy-Prompted 30-Family Template

```text
你是蕨类植物分类学专家。请进行 30 科闭集识别。

标准候选科及简要约束：
1. <family> (<latin_family>)；类群：<higher_group>；示例：<example_species>
...

观察重点：生活型、叶片分裂方式、叶片质地、叶柄/根状茎特征、孢子囊群位置和形状。

要求：
- selected_option 必须严格等于上述 30 个中文科名之一。
- top3 必须从上述 30 科中选择。
- 如果关键证据不可见，请说明缺失证据。
- 不要输出候选外科名。

只回复 JSON：
{
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "visible_features": ["可见特征1"],
  "missing_evidence": ["缺失证据1"],
  "reasoning": "简短理由"
}
```

## Species-Level Closed-Set Template

```text
你是蕨类植物分类学专家。请进行种级闭集识别：<task_title>

候选物种：
1. <Chinese species> (<Latin binomial>)；科：<family>；形态：<morphology excerpt>
...

要求：
- selected_species 必须严格等于候选物种中文名之一。
- top3_species 给出最可能的前三个候选物种中文名。
- selected_family 填写你认为的科名。
- 如果图片缺少关键证据，请在 reasoning 中说明。

只回复 JSON：
{
  "selected_species": "物种中文名",
  "top3_species": ["物种1", "物种2", "物种3"],
  "selected_family": "科名",
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Open-Set Rejection Template

```text
你是蕨类植物分类学专家。请判断图片是否属于下面 30 个候选蕨类科之一，或者不属于候选范围。

候选科：
1. <family_1>
...
30. <family_30>

允许的 decision：
- "in_scope"：图片确实属于上述 30 个候选科之一。
- "none_of_the_above"：图片不是蕨类，或属于候选列表之外的类群。
- "uncertain"：图片证据不足，无法可靠判断。

要求：
- 如果 decision 为 "in_scope"，selected_option 必须严格等于候选科中文名之一。
- 如果 decision 为 "none_of_the_above" 或 "uncertain"，selected_option 填空字符串。
- top3 只在 in_scope 时填写候选科；否则为空数组。
- 不要输出候选外科名作为 selected_option。

只回复 JSON：
{
  "decision": "in_scope",
  "selected_option": "科名",
  "top3": ["科名1", "科名2", "科名3"],
  "confidence": 0.8,
  "reasoning": "简短理由"
}
```

## Reproducibility Caveat

Several systems are API-based and may change over time. The manuscript should therefore describe this as a checkpointed evaluation instance: prompts, raw responses, standardized outputs, state files, model identifiers, and access routes were archived locally for reproducibility of the completed runs.
