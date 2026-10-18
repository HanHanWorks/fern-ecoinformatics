# 8. Error Structure

RQ3 also asks how the systems fail, not only how often. This section compares the two systems by the structure of their mistakes rather than their rate: which species each system identifies at all, and how far each system's mistakes travel taxonomically.

## 8.1 Species-level coverage

Two species appear only once in the test split, *Huperzia nanchuanensis* and *H. sutchueniana*, so species-level counts are taken over the 148 species that have at least two test images; the accuracy figures still use all 902 images.

The classifier identifies all 148 species correctly at least once, and every one of them enters its top three at least once. Pl@ntNet never identifies 90 of the 148 (60.8%), and 86 (58.1%) never appear in its top three.

## 8.2 Error taxonomy: cross-genus versus cross-family

The classifier's errors are also taxonomically close, as Table 8 shows. Of its 902 predictions, 47 (5.2%) fall outside the true genus and 26 (2.9%) outside the true family. Pl@ntNet's errors are not close: 446 (49.4%) cross the genus boundary and 473 (52.4%) cross the family boundary. Its worst single direction moves 188 of the 273 test images of Dryopteridaceae into Polypodiaceae, a different family, which is 68.9% of that family's test images.

The contrast is best stated as a ratio. Pl@ntNet's errors are eighteen times more likely to cross a family boundary than the classifier's (52.4% against 2.9% of all images). Looked at within each system's own errors, 63% of the classifier's mistakes stay inside the correct family, whereas 69% of Pl@ntNet's leave it.

## 8.3 Per-family comparison

Table 7 gives family-level accuracy for the 28 families with at least five test images. The classifier falls below 0.60 on none of them, and its weakest family, Didymochlaenaceae, is represented by five images. Pl@ntNet scores exactly zero on eleven of the 28, and on those families the classifier ranges from 0.60 to 1.00.

The two systems do converge where Pl@ntNet's reference library is strong. On Polypodiaceae, its best-represented family, it reaches 0.799 against the classifier's 0.980; on Lycopodiaceae, 0.958 against 1.000. The gap is therefore not uniform. It is concentrated in the families where the API has no coverage at all.

Figure 8 shows the decomposition and the per-family comparison together.
