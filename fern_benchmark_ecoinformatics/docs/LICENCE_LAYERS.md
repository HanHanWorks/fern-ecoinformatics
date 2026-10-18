# Licence layers

Three licences apply to this repository, and they attach to different things.
Mixing them up is the easiest mistake to make when reusing the data.

## The three layers

| Layer | What it covers | Licence |
|---|---|---|
| Code | `code/`, `tools/` | MIT (`LICENSE`) |
| Compilation and annotations | Manifests, splits, derived results, documentation, manuscript artefacts | CC BY 4.0 (`LICENSE-DATA.md`) |
| Images | `data/open_images/*.jpg` | The licence of each image, unchanged |

## The images

Every image keeps the licence its source platform recorded. This repository
does not relicense, relicense collectively, or sublicense any image, and the
CC BY 4.0 grant on the manifests does not extend to the image files.

Only permissively licensed images are redistributed at all — CC0, CC BY, or
CC BY-SA. Images under CC BY-NC or CC BY-NC-SA are not present.

| Licence | Images | Obligation when you redistribute |
|---|---:|---|
| CC0 | 743 | None. Attribution is welcome but not required. |
| CC BY | 618 | Credit the rights holder, link to the licence, indicate changes. |
| CC BY-SA | 71 | As CC BY, and derivatives must be released under the same licence. |

Attribution fields are in `data/open_images/LICENCES.csv` and in the
`license`, `rights_holder`, `occurrence_url` and `observation_url` columns of
the manifests. The `rights_holder` value is the photographer or institution
as named by the source platform.

**The CC BY-SA images carry a copyleft obligation.** If you build and
distribute a derivative image set that includes them, that derivative must be
released under CC BY-SA. Training a model on them does not, on the usual
reading, make the model a derivative work, but redistributing an image set
that contains them does constrain that image set's licence.

## The manifests and derived data

CC BY 4.0 covers the compilation of the manifests and the annotations this work
adds: the normalised country, the image-domain label, the licence class, the
split and evaluation-subset membership, and the group key. The underlying facts
in each row — the species name, the coordinates of the source record, the
source licence — are facts about the source record and are not created here.

## Platform terms

The images were obtained from iNaturalist and GBIF under their terms of use and
their API guidelines, which require a contact address in the request
User-Agent. Re-obtaining them means accepting those terms yourself. iNaturalist
observation pages and GBIF occurrence pages should be cited individually; the
manifest records the identifier and URL needed for each.

## Reusing the code

MIT places no conditions beyond keeping the copyright notice and the licence
text. The staging tools sanitise the working tree's absolute paths into
`FERN_ROOT` and `FERN_PYTHON` environment variables, so a clone runs against
whatever directory layout you provide.
