# 2. Introduction

Ecological monitoring depends on identifying species correctly and repeatedly, and the supply of people able to do it has not kept pace with the demand for observations. Automated identification from images is therefore promoted as a component of biodiversity monitoring pipelines (Tuia et al., 2022; Wäldchen et al., 2018), and working systems exist for well-documented taxa such as birds and regional vascular-plant floras (Kahl et al., 2021; Mäder et al., 2021; Joly et al., 2014).

Ferns are a harder case. The group is large and taxonomically intricate (PPG I, 2016), its species span a wide range of habitats (Page, 2002), and its images come from two sources that look almost nothing alike: the herbarium sheet, photographed flat under controlled conditions by digitisation programmes, and the field photograph, contributed by a volunteer and showing a whole plant in natural light. When both regimes appear in its training data, a single model reaches 91.9% accuracy on herbarium sheets and 92.5% on field photographs. When the two are separated between training and test, accuracy falls to 42 to 65%. Withholding one region, Taiwan, China, costs 39.8 percentage points in a single step. Neither loss appears in the accuracy figure that a conventionally split benchmark reports, while monitoring programmes routinely extend into regions and imaging setups that were not represented during training.

The dominant response to this problem has been architectural: a backbone pretrained on general imagery (Radford et al., 2021; Ilharco et al., 2021) or on biological image–text data (Stevens et al., 2024; Gu et al., 2025), then fine-tuned on the target taxon (Kumar et al., 2012; Joly et al., 2014; Goëau et al., 2017) or frozen with a small head trained on top (Oquab et al., 2024); general-purpose vision–language models are now applied to plants the same way (Bai et al., 2025). Progress is reported as top-1 accuracy on a held-out portion of a pooled collection, split at random or stratified by species (Van Horn et al., 2018) — a number that builds in three assumptions, almost always left implicit. The first is that image domain is exchangeable: a herbarium sheet and a field photograph count as interchangeable evidence. The second is that geographic provenance is exchangeable: recognising a species is equivalent to recognising it anywhere. The third is that the measured accuracy reflects morphological identification rather than the printed text, although herbarium sheets carry printed labels bearing the species name. Each is falsifiable, and together they decide whether a benchmark number can estimate field performance. Figure 1 summarises the falsification framework: the two image regimes, the benchmark number that their separation collapses, the three assumptions behind that number, and the controlled tests that refuted each of them.

The literature supplies evidence against each assumption, but never tests one in isolation. Studies of plant identification apps disagree — high accuracy in a well-sampled European flora (Pärtel et al., 2021; Rzanny et al., 2024) against unreliability on toxic and edible species (Long et al., 2023) and sensitivity to framing and scorers (Campbell et al., 2023; Hart et al., 2023) — and the disagreement is hard to settle because images and protocol differ at once. Occurrence records are strongly biased in space and taxonomy (Meyer et al., 2016), and supplying geographic priors measurably changes fine-grained classification (Mac Aodha et al., 2019), yet geographic holdout is rarely used as an evaluation axis: the community's benchmark varies acquisition mode instead (Martellucci et al., 2025), and data scarcity itself has become the subject of a benchmark (Saputra et al., 2026). Reviews of herbarium analysis treat label text and open-set conditions as unsettled (Geng et al., 2020; Guo et al., 2025), and testing the text assumption requires reading labels with an instrument other than the model under test.

Producing the measurement is unattractive for practical rather than conceptual reasons: it calls for a nested design in which each axis is compared against a baseline from the same subset of images, for labelled negatives and per-image confidence, which botanical benchmarks do not normally carry, and for a data requirement few taxa satisfy — images in quantity in both visual regimes, per-image provenance, and licences permitting redistribution. Ferns meet the requirement only because digitised specimen records and volunteer observations are exposed through the same occurrence infrastructure (GBIF Secretariat, 2023), and even then most of the resulting images cannot be redistributed (Scheffers et al., 2012). Each piece is cheap in isolation; the combination is what has kept the question open.

We therefore ask four questions, which also determine the structure of the analysis that follows.

RQ1. Which pretraining source, adaptation mode, input resolution and output head give the best species-level identification on this benchmark, and does the ranking survive seed variance?

RQ2. How large are the accuracy losses when image domain, data source or geographic region are withheld, measured against baselines computed on the same images?

RQ3. How do a specialist identification API and two general-purpose vision–language models perform on the same images, and how much of their apparent accuracy on herbarium material depends on readable label text?

RQ4. Can the model's own confidence be used to automate decisions, in the sense of open-set rejection of non-fern images and selective prediction at controlled coverage?

Three of these close the assumptions above: RQ2 tests the first and second, RQ3 tests the third, and RQ1 establishes the instrument that makes all of them measurable. RQ4 asks a question the assumptions do not cover, because a monitoring workflow needs a decision rather than a label. We therefore treat the evaluation protocol, rather than the model, as the object of study, and use ferns to make it concrete: the benchmark assembles per-image annotations of image domain, source and country, splits by observation so that no occurrence straddles two splits, and pairs the positives with labelled fern-like negatives. Holding the model family fixed, we compare a frozen trunk against full fine-tuning, two input resolutions and a hierarchical head; the resulting recipe is statistically indistinguishable from fine-tuning across three seeds while training only a linear head, and we use it as a controlled instrument to test each assumption in turn. For RQ4, rejection is scored as a risk-coverage problem (Geifman & El-Yaniv, 2017) and calibration with the expected calibration error (Guo et al., 2017).

We summarise our contributions as follows.

(i) A fern identification benchmark of 5,969 images covering 152 species in 30 families, with per-image annotations of image domain, data source and country, split by observation into 4,185 training, 882 validation and 902 test images, and accompanied by 700 open-set negatives in eight groups (Section 3).

(ii) A controlled comparison of recipe choices, in which biology-pretrained features with a frozen trunk and a linear head at 336 px perform best at 91.4 ± 0.7% over three seeds, statistically indistinguishable from full fine-tuning and ahead of a general-purpose self-supervised backbone (RQ1; Section 4).

(iii) A test of the image-domain and geographic assumptions: crossing image domain or data source costs 8.6 to 48.1 percentage points, and holding out a region costs 3.6 to 39.8 percentage points, with the largest losses where species have the least out-of-region training support (RQ2; Sections 5 and 6).

(iv) A test of the text-availability assumption, and an audit of general-purpose vision–language models and a specialist API on the same images: closed-set accuracy is 24 to 32%, and open-ended accuracy after removing machine-readable names falls to 8.3 to 10.9% (RQ3; Sections 7 and 8).

(v) A deployment-oriented reading, in which the specialist model's confidence is conservative enough that accepting only the most confident quarter of images yields 100% accuracy, whereas the API's confidence is not (RQ4; Sections 9 and 10). Section 11 returns to the question with which this paper opened.

---

## References

Bai, S., Cai, Y., Chen, R., Chen, K., Chen, X., Cheng, Z., et al. (2025). Qwen3-VL technical report. *arXiv preprint*, arXiv:2511.21631.

Campbell, N., Peacock, J., & Bacon, K. L. (2023). A repeatable scoring system for assessing Smartphone applications ability to identify herbaceous plants. *PLOS ONE*, 18(4), e0283386.

Espitalier, V., Lombardo, J.-C., Goëau, H., Botella, C., Høye, T. T., Dyrmann, M., Bonnet, P., & Joly, A. (2025). Adapting a global plant identification model to detect invasive alien plant species in high-resolution road side images. *Ecological Informatics*, 89, 103129.

Garcin, C., Joly, A., Bonnet, P., Affouard, A., Lombardo, J.-C., Goëau, H., Herbaux, S., & Chouet, P. (2021). Pl@ntNet-300K: A plant image dataset with high label ambiguity and a long-tailed distribution. *Proceedings of the Neural Information Processing Systems Track on Datasets and Benchmarks*, 1.

GBIF Secretariat. (2023). *GBIF occurrence data and API documentation*. Global Biodiversity Information Facility.

Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks. *Advances in Neural Information Processing Systems*, 30, 4878–4887.

Geng, C., Huang, S.-J., & Chen, S. (2020). Recent advances in open set recognition: A survey. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 43(10), 3614–3631.

Goëau, H., Bonnet, P., & Joly, A. (2017). Plant identification based on noisy web data: The amazing performance of deep learning (LifeCLEF 2017). *CLEF 2017 Working Notes*.

Gu, J., Stevens, S., Campolongo, E. G., Thompson, M. J., Zhang, N., Wu, J., et al. (2025). BioCLIP 2: Emergent properties from scaling hierarchical contrastive learning. *Advances in Neural Information Processing Systems*, 38, 102778–102811.

Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. *Proceedings of the 34th International Conference on Machine Learning*, 1321–1330.

Guo, Y.-Y., Cai, H., Bramley, G. L. C., Atkins, H. J., Li, B., & Theodossiades, S. (2025). A review of artificial intelligence in herbarium specimen image analysis. *Artificial Intelligence Review*, 58, 402.

Hart, A. G., Bosley, H., Hooper, C., Perry, J., Sellors-Moore, J., Moore, O., & Goodenough, A. E. (2023). Assessing the accuracy of free automated plant identification applications. *People and Nature*, 5(3), 929–937.

Hussein, B. R., Malik, O. A., Ong, W.-H., & Slik, J. W. F. (2022). Applications of computer vision and machine learning techniques for digitized herbarium specimens: A systematic literature review. *Ecological Informatics*, 69, 101641.

Ilharco, G., Wortsman, M., Wightman, R., Gordon, C., Carlini, N., Taori, R., et al. (2021). *OpenCLIP*. Zenodo.

Joly, A., Goëau, H., Bonnet, P., Bakić, V., Barbe, J., Selmi, S., et al. (2014). Interactive plant identification based on social image data. *Ecological Informatics*, 23, 22–34.

Kahl, S., Wood, C. M., Eibl, M., & Klinck, H. (2021). BirdNET: A deep learning solution for avian diversity monitoring. *Ecological Informatics*, 61, 101236.

Kumar, N., Belhumeur, P. N., Biswas, A., Jacobs, D. W., Kress, W. J., Lopez, I. C., & Soares, J. V. (2012). Leafsnap: A computer vision system for automatic plant species identification. *Proceedings of the European Conference on Computer Vision*, 502–516.

Long, K., Townesmith, A., Overmiller, A., Applequist, W., Scalzo, A., Buchanan, P., & Bitter, C. C. (2023). Plant identification applications do not reliably identify toxic and edible plants in the American Midwest. *Clinical Toxicology*, 61(7), 524–528.

Mac Aodha, O., Cole, E., & Perona, P. (2019). Presence-only geographical priors for fine-grained image classification. *Proceedings of the IEEE/CVF International Conference on Computer Vision*, 9596–9606.

Martellucci, G., Goëau, H., Bonnet, P., Vinatier, F., & Joly, A. (2025). Overview of PlantCLEF 2025: Multi-species plant identification in vegetation quadrat images. *CLEF 2025 Working Notes*.

Mäder, P., Boho, D., Rzanny, M., Seeland, M., Wittich, H. C., Deggelmann, A., & Wäldchen, J. (2021). The Flora Incognita app: Interactive plant species identification. *Methods in Ecology and Evolution*, 12(7), 1335–1342.

Meyer, C., Weigelt, P., & Kreft, H. (2016). Multidimensional biases, gaps and uncertainties in global plant occurrence information. *Ecology Letters*, 19(8), 992–1006.

Oquab, M., Darcet, T., Moutakanni, T., Vo, H., Szafraniec, M., Khalidov, V., et al. (2024). DINOv2: Learning robust visual features without supervision. *Transactions on Machine Learning Research*.

Page, C. N. (2002). Ecological strategies in fern evolution: A neopteridological overview. *Review of Palaeobotany and Palynology*, 119(1–2), 1–33.

PPG I. (2016). A community-derived classification for extant lycophytes and ferns. *Journal of Systematics and Evolution*, 54(6), 563–603.

Pärtel, J., Pärtel, M., & Wäldchen, J. (2021). Plant image identification application demonstrates high accuracy in Northern Europe. *AoB PLANTS*, 13(4), plab050.

Radford, A., Kim, J. W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., et al. (2021). Learning transferable visual models from natural language supervision. *Proceedings of the 38th International Conference on Machine Learning*, 8748–8763.

Rzanny, M., Bebber, A., Wittich, H. C., Fritz, A., Boho, D., Mäder, P., & Wäldchen, J. (2024). More than rapid identification—Free plant identification apps can also be highly accurate. *People and Nature*, 6(6), 2178–2181.

Saputra, R., Apriyanti, D. H., Schuiteman, A., Metzger, K., Field, A., Nargar, K., & Edwards, W. (2026). Vision Transformers versus convolutional neural networks for fine-grained orchid genus identification in a species-rich, data-poor flora: A controlled benchmark on the Orchidaceae of New Guinea. *arXiv preprint*, arXiv:2609.24064.

Scheffers, B. R., Joppa, L. N., Pimm, S. L., & Laurance, W. F. (2012). What we know and don't know about Earth's missing biodiversity. *Trends in Ecology & Evolution*, 27(9), 501–510.

Stevens, S., Wu, J., Thompson, M. J., Campolongo, E. G., Song, C. H., Carlyn, D. E., et al. (2024). BioCLIP: A vision foundation model for the tree of life. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 19412–19424.

Tuia, D., Kellenberger, B., Beery, S., Costelloe, B. R., Zuffi, S., Risse, B., et al. (2022). Perspectives in machine learning for wildlife conservation. *Nature Communications*, 13, 792.

Van Horn, G., Mac Aodha, O., Song, Y., Cui, Y., Sun, C., Shepard, A., et al. (2018). The iNaturalist species classification and detection dataset. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition*, 8769–8778.

Wäldchen, J., Rzanny, M., Seeland, M., & Mäder, P. (2018). Automated plant species identification: Trends and future directions. *PLOS Computational Biology*, 14(4), e1005993.

Wang, H., Liu, W., Bocchieri, A., & Li, Y. (2023). Can multi-label classification networks know what they do not know? *Advances in Neural Information Processing Systems*, 36.

Yang, J., Zhou, K., Li, Y., & Liu, Z. (2024). Generalized out-of-distribution detection: A survey. *International Journal of Computer Vision*, 132(12), 5635–5662.
