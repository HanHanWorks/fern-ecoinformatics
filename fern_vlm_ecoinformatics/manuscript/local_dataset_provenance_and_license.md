# Local Dataset Provenance and License Note

This note documents the local research-only evaluation dataset used in the manuscript draft.

## Source and Scope

- Dataset name: 中国蕨类植物识别测试数据集.
- Version recorded in manifest: 3.0.
- Source recorded in manifest: 中国高等植物彩色图鉴 第1卷&第2卷.
- Total records: 155 species-level entries.
- Project families: 30 Chinese family labels with associated Latin family labels.
- Each record includes `species_id`, Chinese species name, Latin binomial, Chinese family label, Latin family label, morphology, distribution, habitat, and one local `image_refs` entry.

## Construction Workflow

The local dataset was constructed from digitized reference-book/PDF pages rather than obtained as a pre-existing machine-learning dataset. The working process was:

1. Convert relevant source pages into page-level images.
2. Extract candidate plant-photo regions from page layouts, preserving page number and image-box coordinates in file names such as `page_2_img_in_image_box_339_107_694_573.jpg`.
3. Parse the accompanying text into structured species-level fields: Chinese name, Latin binomial, family, Latin family, morphology, distribution, and habitat.
4. Link each species record to one representative local image reference.
5. Standardize family labels and aliases to the project canonical taxonomy used by the prompt builders and analysis scripts.
6. Export the linked image-text-taxonomy records as `species_data.json`, `species_data.md`, and `dataset_manifest.json`.

The working image directory contains 912 JPEG files: 797 cropped image-box files and 115 full-page images. The final evaluation set uses 155 selected image references, one for each species-level record.

## Image Context

- Full-page or page-context images: 115.
- Cropped plant-photo images: 40.
- Some full-page images may contain visible page text or labels. This risk was handled analytically through the 60-image text-masked robustness subset rather than by claiming that the original local set is text-free.

The difference between the working image directory and the final evaluation records is intentional: the extraction process produced multiple page and crop artifacts, but the benchmark selected one representative image reference per species-level record.

## Label Handling

- Labels were treated as source-standardized labels: species and family names were derived from the source reference and standardized to the project canonical taxonomy.
- The current manuscript should not claim independent expert re-identification or expert review of all labels unless such review is completed later.
- Synonym and family-name handling was performed through the project canonical taxonomy and alias normalization used in the analysis scripts.

## License and Redistribution

- The local images are used as a local research-only evaluation dataset.
- Original local images are not redistributed with the manuscript, repository, or supplementary materials.
- Releasable materials should be limited to metadata, non-sensitive manifests, prompts, scripts, raw/standardized model outputs where allowed, and derived result tables.
- External validation images retain their original GBIF/iNaturalist source URLs, license strings, and rights-holder metadata in the external manifest.

## Family Distribution

| Family | Latin family | n |
|---|---|---:|
| 鳞毛蕨科 | Dryopteridaceae | 43 |
| 水龙骨科 | Polypodiaceae | 39 |
| 石松科 | Lycopodiaceae | 7 |
| 乌毛蕨科 | Blechnaceae | 7 |
| 凤尾蕨科 | Pteridaceae | 5 |
| 瓶尔小草科 | Ophioglossaceae | 4 |
| 里白科 | Gleicheniaceae | 4 |
| 碗蕨科 | Dennstaedtiaceae | 4 |
| 球子蕨科 | Onocleaceae | 4 |
| 叉蕨科 | Tectariaceae | 4 |
| 紫萁科 | Osmundaceae | 3 |
| 膜蕨科 | Hymenophyllaceae | 3 |
| 骨碎补科 | Davalliaceae | 3 |
| 合囊蕨科 | Marattiaceae | 2 |
| 海金沙科 | Lygodiaceae | 2 |
| 冷蕨科 | Cystopteridaceae | 2 |
| 蹄盖蕨科 | Athyriaceae | 2 |
| 肿足蕨科 | Hypodematiaceae | 2 |
| 实蕨科 | Lomariopsidaceae | 2 |
| 肾蕨科 | Nephrolepidaceae | 2 |
| 禾叶蕨科 | Grammitidaceae | 2 |
| 松叶蕨科 | Psilotaceae | 1 |
| 蘋科 | Marsileaceae | 1 |
| 槐叶蘋科 | Salviniaceae | 1 |
| 铁角蕨科 | Aspleniaceae | 1 |
| 翼盖蕨科 | Didymochlaenaceae | 1 |
| 舌蕨科 | Dryopteridaceae | 1 |
| 藤蕨科 | Lomariopsidaceae | 1 |
| 爬树蕨科 | Arthropteridaceae | 1 |
| 睫毛蕨科 | Pleurosoriopsidaceae | 1 |
