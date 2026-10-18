# 9. Open-Set Rejection

RQ4 asks whether the model's own confidence can be used to automate decisions, and the first of the two decisions is open-set rejection. A closed-set classifier assigns every image to one of 152 species, including images that contain no fern at all. In monitoring that is the common case rather than the exception, since a pipeline receives whatever the camera or the contributor supplies. This section asks whether the model can be made to abstain.

## 9.1 Negatives and the rejection score

The 700 negatives described in Section 3.6 are used as the positive class of the rejection problem: an image containing a horsetail, a moss, a cycad or a flowering plant should be refused. The rejection score is the maximum softmax probability of the closed-set classifier, which requires no additional training and no second model.

Section 3.6 also noted the limitation that governs how these numbers should be read. The negative groups are not a random sample of what a deployment would see; the flowering-plant group is deliberately easy, and the cycad and palm groups are deliberately hard. Aggregate figures therefore describe behaviour on this set, and per-group rates are what carry over.

## 9.2 Discrimination and per-group behaviour

Table 9 reports all seven trained models. The recipe of Section 4 reaches an AUROC of 0.9666, with a true-positive rate of 0.9302 at a 10% false-positive rate and 0.8426 at 5%. Its mean confidence is 0.728 on positives against 0.168 on negatives, so the score separates the two populations by a wide margin and without a second decision stage.

Two qualifications belong with that ranking. The single highest AUROC in the set is 0.9701, from the 224 px fully fine-tuned model, which is not the recipe used elsewhere in this paper. The frozen probe ties the 336 px fine-tuned model on AUROC and is clearly ahead of it at the operating point that matters, with a true-positive rate of 0.9302 against 0.8858 at a 10% false-positive rate. Rejection quality also tracks closed-set accuracy — BioCLIP 2 models at 0.96 to 0.97, DINOv2 models at 0.92 to 0.94, the hierarchical head last at 0.9236 — so closed-set accuracy, domain-transfer behaviour and rejection rank the seven models in the same order.

The per-group rates are more informative than the aggregate. At the 10% false-positive operating point the model rejects 0.971 of horsetails, 0.971 of fungi, 0.971 of conifers, 0.948 of flowering plants, 0.943 of palms, 0.871 of out-of-scope lycopods and 0.857 of mosses and liverworts. The cycad group is the outlier at 0.571, and it is the outlier in every model tested, ranging from 0.57 to 0.79 across all seven. Palm is second hardest. What the two hard groups share is pinnate foliage, which converges on fern morphology in a single photograph. The other six groups, which include taxa with no fern-like resemblance at all, are rejected at 0.85 or better.

Combining rejection with the selective policy of Section 7.4 gives a two-stage rule: reject anything whose maximum probability falls below the threshold, then accept the most confident fraction of what remains.
