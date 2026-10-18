# 3. Construction Pipeline

The benchmark is not a convenience sample. Three properties had to hold at once: both visual regimes of fern imagery are represented in quantity, every image carries enough provenance to define a distribution shift, and no individual plant can appear on both sides of an evaluation. Figure 2 shows the pipeline; Table 1 summarises its output.

## 3.1 Sources and queries

Candidate taxa were taken from a reference atlas of Chinese higher plants (ferns, volumes 1–2), which supplied 155 species with Chinese and Latin names; the family treatment follows PPG I (2016). Occurrence records were then retrieved from two public sources, chosen because they carry different kinds of evidence rather than different amounts of it.

iNaturalist supplied research-grade observations, that is, records at least two identifiers have agreed on: photographs of living plants, taken opportunistically in the field. GBIF (GBIF Secretariat, 2023) supplied museum and aggregate records, a large fraction digitised herbarium sheets. The two sources differ not only in who made the image but in the physical object photographed, which is what makes them useful here.

Records were retained only when the occurrence matched one of the candidate species and the image was retrievable: 6,237 images covering 152 of the 155 candidate species in 30 families, with 1–120 images per species; three candidate species yielded no usable records and were dropped.

## 3.2 Licence layering and the redistribution split

Redistribution, not access, was the binding constraint. Each record was classified by its licence into redistributable (CC0, public domain, CC-BY, CC-BY-SA) or restricted (the non-commercial variants and everything else). Before balancing, 1,465 of the 6,237 images were redistributable, or 23%; because the cap described below prefers openly licensed images when it has a choice, the share rises slightly in the working set, to 1,432 of 5,969 images, or 24%. The remaining 4,537 images may be used for research and reported on, but cannot be republished by us. This asymmetry is stated here because it determines what the paper can hand to a reader; its consequences are set out in Section 12, and it is a general property of benchmark work built on citizen-science and museum records rather than a peculiarity of ferns.

## 3.3 Balancing the working set

The collected pool was strongly imbalanced, with a long tail of species represented by a handful of images and a few species by more than a hundred. Following common practice in fine-grained recognition benchmarks (Van Horn et al., 2018), the pool was capped at 60 images per species, which removed 268 over-cap images and left 5,969 images, between 1 and 60 per species. The working set contains 4,300 field photographs and 1,669 herbarium sheets, so specimens make up 28.0% of it. Two details of the cap matter for later results: images were drawn round-robin across the two image domains, so capping does not silently collapse the domain balance (specimen share 27.8% before, 28.0% after), and preferentially retaining openly licensed images raises the redistributable share from 23% to 24%.

## 3.4 Annotation axes

Three provenance axes were recorded for every image, and they are what make the shifts in Sections 5 and 6 measurable rather than anecdotal.

**Image domain.** Each image was assigned to `field` or `specimen` from the machine-readable `basisOfRecord` field of the source record, not by manual inspection: preserved, living and material-sample records map to `specimen`, human and machine observations to `field`. Deriving the axis this way keeps the herbarium-versus-field contrast reproducible and independent of our own judgement.

**Data source.** Each image retains its originating platform, iNaturalist or GBIF, which after balancing contributes 3,157 and 2,812 images respectively.

**Country.** The country field of the source records is free text, mixing ISO-2 codes, iNaturalist place strings, Chinese addresses, Russian locality names and English-language addresses — 1,468 distinct values in the training split alone. A normalisation step maps these to ISO-2 codes using ordered rules; everything unrecognised becomes `UNK`. The benchmark carries 80 countries plus 330 images with unknown country (5.5%), and the raw values are retained alongside the normalised column so the mapping can be audited.

## 3.5 Group-aware splits and evaluation subsets

Images were split into training, validation and test sets stratified by species, and *group-aware*: images sharing an observation or occurrence group are kept together, so a photographed individual, a duplicate sheet of the same gathering, or a set of frames from one observation never straddles two splits, which prevents a model from being credited for recognising an individual it saw during training.

The result is 4,185 training, 882 validation and 902 test images, covering 152, 150 and 150 species respectively; the intersection of the three splits is empty at the level of image identifier, file hash and group key. The two species that appear in the training split alone are those with the fewest images overall, discussed in Section 8.

Seven evaluation subsets are defined over the test split without moving or removing any image: by provenance, field only (640 images), specimen only (262), iNaturalist only (476) and GBIF only (426); by species frequency, 870 images for species with at least 30 balanced images and 32 for the rest. Sections 5 and 6 use these subsets to isolate each shift axis.

## 3.6 Fern-like negatives

A closed-set benchmark cannot evaluate rejection, and a deployment pipeline will encounter images that are not ferns at all. We therefore collected 700 additional images that a fern identifier should refuse to classify, drawn from the same sources and carrying the same manifest fields as the positives, so one pipeline can read both; they are used for evaluation only and never enter training.

The negatives are organised into eight groups, each defined by a taxon lookup rather than by hand-labelling, which keeps the group label auditable: three bracket the target taxa (horsetails *Equisetum*, lycopods outside the benchmark's 155 species *Selaginella*, and liverworts and mosses Marchantiophyta); two are the visually hardest case, plants whose fronds converge on fern morphology but which are not ferns (cycads *Cycas* and palms Arecaceae); one is ordinary flowering plants (*Rosa*, *Trifolium*, *Plantago*), which serves as an easy floor; and two cover taxa photographed in the same habitats (Agaricales fungi, *Pinaceae* conifers). Group sizes are 70 each, except the flowering-plant group, which has 210 across its three genera. All negatives are research-grade records, normalised to RGB JPEG with a short side of at least 240 px, de-duplicated by SHA-1 hash, and released with unique identifiers. Section 9 reports rejection performance on this set; per-group rates accompany the aggregate, which should not be read as an estimate for a deployment population.
