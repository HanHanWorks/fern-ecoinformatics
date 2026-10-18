# Abstract（骨架，数字已按 numbers_reference.md 填入）

> 状态：草稿。**符合 EI 硬性要求：摘要 ≤250 词**（来源：Elsevier EI Guide for Authors，`elsevier.com/journals/ecological-informatics/1574-9541/guide-for-authors`）。
> 写作时可以改写句子，但**不要动数字**——每个数字的出处见
> `../numbers_reference.md`。
>
> **2026-10-14 修订**：迁移落差由 13.4–50.0 pp 改为 **8.6–48.1 pp**
> （改用与 Tab 4 相同的同子集基线，见 `numbers_reference.md` §3）；
> 关键词已重排（去掉刊名与标题重复词）。注意标题里**不要写 902**——
> 902 只是 test split，基准是 5,969 张（见 `framework_v5.md` §1）。
>
> **2026-10-14 二次修订**：初稿 313 词（超 EI 的 250 词上限 25%），且 7 句、
> 句均长 44.7 词（最长 58），与全稿其余部分的密度标准（17–23 词）不一致。
> 已按 250 词上限重写：见下方实测词数。**所有数字一字未动。**

---

Automated species identification is increasingly proposed for ecological
monitoring, yet its evaluation protocols routinely mix herbarium sheets with
field photographs, ignore geographic provenance, and leave the accuracy of
general-purpose vision–language models (VLMs) unaudited for text leakage. We
present a fern benchmark of 5,969 images covering 152 species in 30 families
from iNaturalist and GBIF, including iDigBio-digitised herbarium sheets. Every
image records its image domain, data source and, after normalising 1,468 raw
locality strings, country. It adds 700 open-set negatives in eight groups. Biology-pretrained features with a frozen trunk and a linear head
at 336 px are the best recipe, at **91.4 ± 0.7%** over three seeds. That is
**+7.1 ± 1.0 pp** over DINOv2 in a paired comparison robust to seed variance,
while a hierarchical head *hurts* (−6.0 pp). Under this recipe, transferring
across image domain or source costs **8.6–48.1 pp**, and leave-one-region-out
geographic holdouts cost **3.6–39.8 pp**. The largest losses fall where test
species have the least out-of-region training support (Spearman ρ = 0.48,
seven countries). Two independent VLMs reach only 24–32% on
a closed-set version of the task. OCR auditing shows the herbarium accuracy
comes largely from reading labels: after removing images whose species name
is machine-readable, open-ended accuracy falls to **8.3–10.9%**. The specialist
model is *under*-confident (ECE 0.195) while Pl@ntNet is *over*-confident (ECE
0.090). Accepting only the most confident 25% of images yields 100% accuracy at
100× lower latency than any VLM.

**Keywords**: herbarium specimens; distribution shift; geographic holdout;
BioCLIP; vision–language models; label leakage; open-set recognition

> 关键词说明（2026-10-14 二次修订）：EI 要求 **1–7 个**，初稿有 9 个，已删至 7 个。
> 删掉的是 `selective prediction` 与 `automated plant identification`——
> 前者是 §10 的部署结论、后者过于泛化，二者都可作为备选换回。
> 另：初稿曾把刊名 `Ecological Informatics` 列入（Elsevier 不建议）。
> 若最终改用"Biology-pretrained features…"那条结论式标题，
> 可考虑把 `vision–language models` 换成 `calibration`。

---

## 摘要里每个数字的出处核对表

| 数字 | 出处 |
|---|---|
| 5,969 / 152 / 30 | `numbers_reference.md` §1（注意：不是 6,237，那是采集总量） |
| 1,468 个原始国别字符串 | `numbers_reference.md` §1（归一化后 80 个取值，5.5% 未解析） |
| 700 / 8 组 | 同上 |
| 91.4±0.7% | §2.1（3 seeds 均值） |
| +7.1±1.0 pp | §6（3 seeds 配对差） |
| −6.0 pp（层次头） | §6 |
| 8.6–48.1 pp | §3（**同子集 in-domain 基线**；旧 13.4–50.0 已作废） |
| 3.6–39.8 pp | §4 |
| ρ = 0.48（n = 7 国） | §4（弱正相关，不显著） |
| 24–32%（VLM 闭集） | §5 |
| 8.3–10.9%（剔除泄漏） | §5 + §9 |
| ECE 0.195 / 0.090 | §7 |
| 25% → 100%，100× 延迟差 | §7 |
