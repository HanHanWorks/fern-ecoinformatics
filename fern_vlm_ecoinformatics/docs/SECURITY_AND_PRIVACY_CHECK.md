# Security and Privacy Check

Before publishing this repository, run:

```bash
rg -n "(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|ms-[0-9a-fA-F-]{20,}|tp-[A-Za-z0-9_-]{20,}|api_key\s*=\s*['\"][^'\"]{8,})" . || true
find . -type f \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.tif' -o -name '*.tiff' \) | sort
```

Expected result:

- No real API keys or credentials.
- Only planned figure files under `figures/paper_ready/`; no original local/reference-book images and no external image cache.
- No `results/raw`, `state`, `tmp`, or `logs` directories.

The current GitHub-ready package was built by copying a whitelist of files and generating public metadata manifests with local image paths removed.
