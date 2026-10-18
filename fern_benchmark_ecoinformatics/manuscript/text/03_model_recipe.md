# 4. Model and Recipe

The results follow the four research questions set out in Section 2, in the order in which they were posed. RQ1 comes first because it establishes the recipe that makes the remaining measurements comparable; RQ2 then tests the image-domain and geographic assumptions (Sections 5 and 6); RQ3 audits the external systems and the text-availability assumption (Sections 7 and 8); and RQ4 asks whether the model's own confidence can automate decisions (Section 9). Sections 5 and 6 attribute accuracy losses to the distribution of the data rather than to the model, and that attribution is only meaningful if the model is held fixed and reasonably well chosen. This section establishes the recipe used throughout, and reports how much of its ranking survives seed variance. Each section restates the question it answers; the interpretation of the measurements is taken up in Section 10.

## 4.1 Backbones and adaptation modes

Two pretrained visual backbones were compared under an identical protocol. BioCLIP 2 provides features pretrained on biological image–text data (Gu et al., 2025); DINOv2 provides features pretrained by self-supervision on general imagery (Oquab et al., 2024); the two are matched in architecture class, parameter count and input pipeline, so a difference between them is attributable to pretraining data. Two adaptation modes were used: in `linear` mode the trunk is frozen and only a LayerNorm projection and a linear classifier are trained; in `finetune` mode all parameters are updated. Both were evaluated because the literature does not settle which is preferable for fine-grained botanical tasks, and the answer sets the cost of redeploying the benchmark for a new taxon.

## 4.2 Training protocol

Input images were resized to 224 or 336 px. All runs used AdamW with weight decay 0.05, one warm-up epoch followed by cosine decay, label smoothing 0.1, gradient clipping at 1.0, mixed-precision arithmetic, and model selection on validation top-1 accuracy. Frozen-probe runs used 15 epochs, batch size 32 and a learning rate of 1e-3, except at 224 px, where the batch size was 64. The 336 px fine-tuned run used 12 epochs, batch size 16 and a learning rate of 2e-5. The reference seed is 20261010, and two further seeds were run for the key configurations. Every run saw the same 4,185 training and 902 test images, with 152 output classes.

## 4.3 Recipe comparison

Table 2 and Figure 3 report eleven configurations. The best recipe is a frozen BioCLIP 2 trunk with a linear head at 336 px. It scores 0.9235 in its best seed, or 0.9139 ± 0.0073 over three seeds (91.4 ± 0.7%). The same backbone at 224 px reaches 0.8980, so resolution is worth 2.5 pp (paired McNemar p = 0.005, single seed). Zero-shot BioCLIP 2, with no training at all, already reaches 0.6829 at species level, 0.8381 within the top three, and 0.290 at family level. Replacing biological pretraining with general self-supervision costs more than any other single change. DINOv2 reaches 0.8433 ± 0.0050 at 336 px. BioCLIP 2 is therefore ahead by +7.1 ± 1.0 pp in a paired comparison across three seeds, and the ordering is the same at 224 px.

Two recipe choices did not help, and both are reported rather than omitted: a hierarchical head with a family-level auxiliary loss produced 0.8614, 6.0 pp below the main recipe (paired McNemar p < 1e-16), though that configuration also differs in resolution and learning rate, so the difference is not a clean estimate of what a hierarchical head costs; and class-balanced sampling changed macro-averaged accuracy by 0.04 pp.

## 4.4 Seed variance and the frozen-versus-fine-tuned question

The fine-tuned 336 px configuration is the only variant close enough to the main recipe to need a careful comparison, and seed variance decides it. Across three seeds it reaches 0.9084 ± 0.0041, against 0.9139 ± 0.0073 for the frozen probe. Pairing by seed gives differences of +2.00, +0.44 and −0.78 pp, a mean of +0.55 ± 1.13 pp whose interval includes zero; in one seed the fine-tuned model is ahead. A single-seed paired test would have reported p = 0.025 in favour of the frozen probe, and that value does not survive the seed-level comparison, so it is not used as evidence here. The frozen probe is used for every result that follows, because it trains only a linear head, and its seed-to-seed standard deviation of 0.7 pp is smaller than the smallest shift effect reported later (3.6 pp), so the shifts that follow are not seed noise.

## 4.5 Reproducibility

Training is deterministic for the frozen-probe configuration: rerunning the reference seed reproduces its accuracy exactly. The fine-tuned configuration contains non-deterministic CUDA kernels (about ±0.22 pp per re-run), which three-seed means cover; where a comparison could not be repeated across seeds, the tables label it as a single-seed result.
