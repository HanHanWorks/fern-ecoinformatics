# 5. Domain and Source Shift

The first assumption built into a mixed benchmark is that a herbarium sheet and a field photograph of the same species are interchangeable evidence. This section tests it by training on one image regime or source and testing on another, and by comparing each result against a baseline computed on the same images.

## 5.1 Transfer protocol and the subset-matched baseline

Four directions were run, each with the recipe fixed as in Section 4 and trained on the full training split restricted to one regime or source. The label space was rebuilt from the filtered training split, so the number of classes differs by direction: 90 for GBIF-trained models, 122 for iNaturalist-trained, 71 for specimen-trained and 137 for field-trained. Test sets were likewise restricted, and further restricted to species the model had seen during training, giving 128, 270, 156 and 210 images respectively.

A transfer result means nothing without a matched reference, because a class-restricted test subset is intrinsically harder than the full test split. The baseline used here is the full model of Section 4 scored on the identical subset of images — the same convention as the geographic holdouts of Section 6. Using the mixed-set accuracy instead would conflate the cost of the shift with the difficulty of the subset, and would overstate every drop.

One caveat belongs here. The transfer runs did not emit per-image predictions, so their baselines were recomputed from the main model's per-image records over reconstructed subsets; the reconstruction reproduces the exact test-set sizes recorded for each run, but on the smallest subset (128 images) a single image is worth 0.8 pp, and differences below about 1 pp should not be read as effects.

## 5.2 Cross-domain and cross-source results

Table 3 and Figure 4 report the four directions. All four lose accuracy, and the losses span an order of magnitude.

Training on digitised specimens and testing on field photographs costs −19.9 pp (0.6538 against an in-domain 0.8526). The reverse direction is the most damaging single result in the paper: training on field photographs and testing on specimens costs −48.1 pp (0.4238 against 0.9048).

The two source crossings behave similarly but less symmetrically: GBIF-trained to iNaturalist costs −8.6 pp (0.7891 against 0.8750), and the reverse costs −40.0 pp (0.5000 against 0.9000). Source and image domain are correlated, since most GBIF records in this corpus are sheets and most iNaturalist records are field photographs, so these two axes are not fully independent. Section 6 addresses the geographic axis, which is independent of both by construction.

## 5.3 Where the iNaturalist-to-GBIF cost comes from

The iNaturalist-to-GBIF direction can be decomposed because the GBIF test images carry both source and image-domain labels. Within that 270-image test set, the model scores 0.741 on the field photographs and 0.340 on the herbarium sheets. The cost is therefore not spread evenly across the source: it is concentrated in the sheet subpopulation.

## 5.4 Protocol correction

The transfer results reported here do not agree with an earlier run of the same experiments, and the reason matters for interpreting any transfer number.

In the original implementation the label space was taken from the unfiltered training split, so species removed by the domain or source filter retained their class indices and competed for every test image with randomly initialised weights — in the field-to-specimen direction, 81 of the 152 output classes were spurious. The effect was systematic rather than random: a class-restricted model had fewer real classes, a larger share of the output space was noise, and the collapse appeared far more severe than it is. Rebuilding the label space from the filtered split removes the defect, changing the four transfer accuracies from 0.2059, 0.3239, 0.3244 and 0.1500 to the values in Table 3.

Figure 4 retains the superseded values as separate markers, and a before-and-after comparison is given in the Supplementary Material.
