# 7. External Systems and the Text-Availability Assumption

The third assumption is that a reported accuracy reflects morphological identification. That assumption is hardest to test on a specialist classifier and easiest to test on models that read text, and general-purpose vision–language models can do both. This section evaluates three external systems on the same 902 test images, then tests the assumption with an independent reading of the labels.

## 7.1 A specialist identification API

Pl@ntNet was queried through its public identification service, using the full referential — the configuration a practitioner would use. It scores 0.2428 at species level (95% CI 0.215–0.272), 0.312 within the top three, 0.506 at genus level and 0.367 at family level. For 64.9% of test images the true species was not among its ten candidates; its species-level score is less than half its genus-level score.

Split by image domain, the failure is not uniform: 0.341 on field photographs against 0.004 on herbarium sheets — one sheet out of 262 right. The split by source is equally uneven: 0.368 on iNaturalist images and 0.103 on GBIF images.

Two of the 902 images returned HTTP 404 from the service, and repeated attempts reproduced the failure; re-encoding and resizing did not help, and a same-sized control image passes, so the trigger is the image content. Scaling the long side to 1024 px makes both images succeed. The evaluation therefore includes a fallback path that downscales and retries, and marks the affected records rather than merging them silently.

## 7.2 Two general-purpose vision–language models

Two models from independent families were evaluated: Qwen3.7-flash through its commercial API, and Qwen3-VL-8B-Instruct served locally (Bai et al., 2025). Table 5 places both alongside the specialist systems on the same images. Each saw the same 902 test images twice: in the open-ended task it was asked to name the species with no candidate list; in the closed-set task it was given the 152 species names and asked to choose one, making it directly comparable to the classifier of Section 4.

On the open-ended task the two models reach 0.1587 and 0.1364 at species level. On the closed-set task, where guessing has a 1-in-152 chance, they reach 0.3196 and 0.2417. Both are an order of magnitude below the specialist classifier's 0.9235 in the reference seed on the same images, and the paired differences are large and unambiguous: +60.3 pp against the better of the two on the closed-set task, and +80.8 to +83.5 pp against the open-ended runs once leaked images are removed (Section 7.5, Table 6).

The domain breakdown is what directed the rest of this section. Pl@ntNet failed on sheets and succeeded on field photographs; the language models did the opposite: Qwen3.7-flash reaches 0.069 on field photographs and 0.379 on herbarium sheets. The rest of this section tests the alternative explanation, that the models read the labels rather than identified the plants.

## 7.3 Text-leakage audit with an independent OCR pass

The assumption was tested with an instrument other than the models under test: every image was passed through an optical character recognition engine, and the recognised text was searched for the true species name. The two image domains separate cleanly: no field photograph yielded the species name as machine-readable text, and only 0.2% carried more than 40 characters of text at all, while among herbarium sheets 0.298 yielded the species name directly and 0.847 carried at least 40 characters of printed label text. Across the whole test set the name was available as text for 8.6% of images.

Accuracy follows that boundary: on the machine-readable subset Qwen3.7-flash reaches 0.688, while on the clean subset the same model reaches 0.250 on sheets and 0.069 on field photographs. The leaky subset is therefore three times easier than the clean one, and the advantage appears only where text exists. Removing every image whose species name is machine-readable gives the models' morphological accuracy as 0.1092 and 0.0825 on the open-ended task, and 0.2609 and 0.1833 on the closed-set task. The overall leakage rate of 8.6% is a lower bound, because optical character recognition reads printed labels far better than handwritten ones and the models can read both, so 10.9% is an upper bound rather than an estimate: the more leakage the audit missed, the lower the true morphological accuracy falls.

## 7.4 Calibration and selective prediction

A model whose confidence is trustworthy can be deployed with a rejection option; one whose confidence is not cannot. The two specialist systems differ in opposite directions. Our classifier is under-confident, with an expected calibration error of 0.195 over ten bins; its stated confidence sits below its observed accuracy in every bin, and its most confident bin is correct on every image in it. Pl@ntNet is systematically over-confident, with an expected calibration error of 0.090, and the gap widens as confidence rises: its most confident bin claims 0.943 and delivers 0.683. Thresholding Pl@ntNet's score at 0.5 raises its accuracy from 0.243 to 0.590 but covers only a quarter of the images, and 41% of those it accepts are wrong.

Accepting the classifier's most confident 25% of images gives 100% accuracy, accepting the most confident half keeps accuracy above 0.99, and accepting 85% still holds 0.967; Pl@ntNet's score supports no such policy. The full risk-coverage behaviour of both systems is shown in Figure 7, their reliability diagrams in Figure 6. Latency separates the systems by two orders of magnitude: the classifier runs at 22.6 ms per image on a single consumer-grade GPU, the external systems take 1.8 to 3.4 s. Full fine-tuning is the one configuration with a different calibration profile — better calibrated than the frozen probe (expected calibration error 0.095 against 0.195) but less accurate (Section 4) — so the frozen probe is the configuration reported above.

## 7.5 Paired significance

All systems saw the same images, so differences were tested with paired McNemar tests on the shared subset, with 95% confidence intervals from bootstrap resampling (Table 6). The classifier beats every external system on the same images: +68.0 pp over Pl@ntNet, +60.3 pp over the stronger of the two vision–language models on the closed-set task, and +80.8 to +83.5 pp over the open-ended runs with leaked images removed; all p < 1e-16. Pl@ntNet in turn beats the open-ended vision–language models by +8.4 pp (p = 1e-5). Within our own results, the pairs that matter are reported where they belong, with the three-seed evidence in Section 4; Table 6 lists the same comparisons from single-seed runs for completeness, and its footnote marks them as such.
