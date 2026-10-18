# 6. Geographic Shift

The second assumption is that geographic provenance is exchangeable: that a species' test images arise under the same conditions as its training images, so that recognising a species is equivalent to recognising it anywhere. This section tests that assumption directly by removing a region from training and evaluating on it.

## 6.1 Leave-one-region-out protocol

Eight holdouts were run. For each, the model was trained on the whole training split except images from the held-out region. Both the validation and test sets were then restricted to that region and, as in Section 5, to species the model had seen during training. The recipe is the one fixed in Section 4, at 336 px and 15 epochs.

Two properties make the result interpretable: the comparison column is the same full model scored on the identical test subset, so the difference is the effect of having seen the region rather than a difference between models; and the held-out regions are not mutually exclusive — the China-region row aggregates Mainland China with Taiwan, China, Hong Kong, China and Macao, China, and overlaps two other rows, so the eight values are eight measurements of one phenomenon, not eight independent countries.

The geographic annotation is derived, as described in Section 3.4. Of the 330 images whose country could not be established, 131 carry no location information at all and the remainder use formats the normaliser does not cover. All are excluded from the geographic analysis, so every number in this section rests on the remaining 5,639 images.

## 6.2 Results across the holdouts

Table 4 and Figure 5 report the results. Every holdout reduces accuracy, and the spread is wide: from −3.6 pp for Vietnam to −39.8 pp for Taiwan, China.

The pattern separates the holdouts into two groups: Taiwan, China (−39.8, from 0.9590 to 0.5615) and the China region (−32.7) lose most; Mainland China (−20.5), Japan (−15.3) and Thailand (−12.9) lose moderately; the United States (−6.4), Russia (−5.6) and Vietnam (−3.6) lose little. Both groups are geographically Asian, so the separation is not between continents — what distinguishes them is how much of each species' training support lies elsewhere, which is the subject of the next subsection.

## 6.3 Association with out-of-region training support

For each holdout we computed the share of its test images whose species has five or fewer training images outside the held-out region. This share ranges from 0.49 (Taiwan, China, and the China region) to 0.00 (Japan, the United States, Vietnam). It tracks the size of the drop. The two holdouts with the thinnest out-of-region support lose 39.8 and 32.7 pp; the three with complete support lose 15.3 pp or less.

Across the seven country-level holdouts the association is positive but weak: Spearman ρ = 0.48 (n = 7, p ≈ 0.28). Including the China-region aggregate raises it to 0.63 (n = 8, p ≈ 0.09). Neither is significant at conventional levels. Figure 5C plots the eight points with the fitted trend.

Two deviations are visible in that plot and are worth stating rather than smoothing over. Russia has a thin-support share of 0.15 but loses only 5.6 pp, and Japan has complete support yet loses 15.3 pp; with 54 and 59 test images respectively, both are noisy estimates, but they show that out-of-region support is not the only term. The image-domain composition of each country's test set also differs, from 2% specimens for Taiwan, China to 81% for Thailand, and the domain axis carries its own cost of up to 48 pp (Section 5), so the holdout drops contain a domain component this analysis does not separate.

The hypothesis we started with is the one we cannot report: if geographic loss were driven by species unique to a region, holdouts covering more such species should lose more, but because the split is stratified by species no species is confined to a single country and every species occurs in at least two. The first explanation we tested was therefore refuted by the design of the benchmark itself.

What these results support operationally is taken up in Section 10.
