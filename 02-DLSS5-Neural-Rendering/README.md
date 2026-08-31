# 02 — DLSS 5 Neural Rendering (runtime + add-on)

**The heart of DLSS 5.** Two files, both needed together:

| File | Version | What it is |
|---|---|---|
| `nvngx_dlssnr.dll` | **310.8.0** | NVIDIA DLSS **Neural Rendering** runtime (DLSSNR). This is the early/community-circulated build, custom-compiled by the RenoDX author to add **RTX 40 and 50 series** support. |
| `renodx-dlss5.addon64` | **0.2026.827.2036** | The **DLSS 5 ReShade add-on** (RenoDX community). Hooks DLSS evaluate calls and injects the neural pass. |

## Where these files are needed

- **Manual DLSS5-Feeder 64-bit installs** (games with no DLSS): both files go **next to the game
  `.exe`** — the add-on refuses to start without the neural-rendering runtime beside it.
- **32-bit games via the Feeder**: identical copies already live inside
  `04-DLSS5-Feeder\host64\` — do **not** put these in the 32-bit game folder itself.
- **DLSS5-Swapper** (folder `03`) embeds its own copies — nothing to do.

## Notes

- This is **community-distributed, beta-grade** NVIDIA technology. DLSS 5 was announced at GTC
  (March 2026) with a full release planned for fall 2026 — expect newer official builds later.
- The add-on is built against **ReShade API 18**; ReShade ≥ 6.8 with add-on support required.
- GPU requirements: RTX 40/50 for the neural rendering features (per the RenoDX build).
- Fresh copies can be obtained from the **RenoDX Discord**, or auto-managed by **RHI**
  (github.com/RankFTW/RHI), which downloads and updates both files per game.
