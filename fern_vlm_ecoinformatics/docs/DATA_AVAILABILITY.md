# Data Availability and Restrictions

## Local Fern Reference Images

The local 155-image fern evaluation set was derived from *Color Atlas of Higher Plants of China*, Volumes 1-2, and was used only as a research-only internal evaluation dataset. The original images and text-masked derivatives are not redistributed in this public repository.

This repository provides public taxonomic metadata and derived model-evaluation tables, but not the restricted image files.

## External Validation and Open-Set Images

External image files downloaded from iNaturalist/GBIF are not redistributed here. Public manifests include source URLs, record identifiers, license fields, rights-holder information, and source labels so that readers can inspect or reconstruct the external dataset subject to the original platforms' terms and license conditions.

## Raw API Responses

Raw provider API response files are excluded to avoid releasing unnecessary provider metadata or verbose model outputs. The public standardized prediction file retains normalized labels, correctness flags, timing/token fields, invalid-output indicators, and task/model identifiers needed for aggregate analysis.

## Re-running Experiments

Non-API analysis can be run from the derived tables and public prediction records. Full API re-runs require image files and user-supplied provider credentials through environment variables. No credentials are included in this repository.
