# 04 — DLSS5-Feeder (DLSS 5 for games with NO DLSS)

**DLSS 5 neural rendering in games that ship without any DLSS — D3D11, D3D12, Vulkan, 32-bit, even DirectX 9.**

A game with no DLSS never calls DLSS, so the DLSS 5 add-on sits idle. **DLSS5-Feeder makes the
calls itself**: it builds a DLAA "contract" from what ReShade already has (frame + depth +
estimated motion vectors), runs a genuine DLSS evaluate, lets the DLSS 5 add-on hook it, and
copies the neural result back into the frame. All inside ReShade's effect chain.

```
game frame → ReShade effects → [motion vectors] → [DLSS5_Feed] → DLSS DLAA + DLSS 5 neural rendering
                                          depth + MV                  ↓
                                                  neural output written back → later effects → present
```

## Files in this folder

| File | Used by |
|---|---|
| `dlss5-feed.addon64` | **64-bit** games (D3D11/12/Vulkan) |
| `dlss5-feed.addon32` | **32-bit** games (and D3D9 via dgVoodoo2) |
| `DLSS5_Feed.fx` | both — goes into `reshade-shaders\Shaders\` |
| `feed-vk-layer.zip` | Vulkan games **only if the log tells you to** (interop hook fallback) |
| `host64\` | **32-bit games** — the complete 64-bit helper environment (see below) |

## Why 32-bit games need the `host64\` folder

NGX and the DLSS 5 add-on are **64-bit only**, and a 32-bit process can't load an x64 DLL.
So on a 32-bit game the feeder splits in two:

- `dlss5-feed.addon32` (in the game) creates cross-process shared GPU textures + fences on the
  game's device and spawns the helper.
- `host64\dlss5-feed-host64.exe` — a genuine 64-bit process that opens those shared resources on
  its **own** D3D12 device, runs the DLSS DLAA evaluate, and signals back. Every copy stays
  **GPU-to-GPU**; nothing crosses into system memory.
- Because the DLSS 5 add-on is itself a ReShade add-on, the host disguises itself as a game
  (hidden window + minimal D3D12 swapchain) so its own bundled ReShade (`host64\dxgi.dll`, 6.8.0
  add-on build) can load it. The helper's own settings panel lives in the "32-bit DLSS 5 Feeder"
  window — or right on the game's ReShade overlay page with an **Apply** button.
- If the host dies, the feed disables itself; the game keeps rendering normally.

`host64\` is pre-configured: helper exe, 64-bit ReShade, DLSS 5 add-on, `nvngx_dlssnr.dll`,
`nvngx_dlss*.dll`, Streamline set, and a **sanitized, pre-tuned `ReShade.ini`**
(neural uplift on, NR style 2, paper-white 9.437 — the pack owner's working values).

## Install — 64-bit game

1. Install **ReShade with add-on support** (reshade.me, full/unsigned build, Direct3D 10/11/12,
   tick "Enable loading of add-ons") against the game exe → `dxgi.dll` appears next to it.
2. Copy `dlss5-feed.addon64` next to the game exe; `DLSS5_Feed.fx` → `reshade-shaders\Shaders\`.
3. Copy `renodx-dlss5.addon64` + `nvngx_dlssnr.dll` + `nvngx_dlss.dll` next to the exe
   (from `02-DLSS5-Neural-Rendering\` and `01-Official-NVIDIA-DLLs\`).
4. **Motion vectors** (required): install **LumeniteFX Kernel** — github.com/umar-afzaal/LumeniteFX.
   Green Code ▸ Download ZIP → `Shaders\` (incl. `include\`) → `reshade-shaders\Shaders\`,
   `Textures\lumenite_bluenoise256.png` → `reshade-shaders\Textures\`.
   *(Nothing of any provider is bundled here — install from their repos.)*
5. ReShade overlay (Home) → select `DLSS5_Feed.fx` → **Preprocessor definitions** →
   `DLSS5_MV_PROVIDER = 3` (LumeniteFX Kernel) → reload effects.
6. Enable **LUMENITE: Kernel 2.0**, then **DLSS 5 Feed** below it, then enable neural rendering
   in the **DLSS 5 Neural Rendering** panel. Keep the game's MSAA/SSAA off.
7. Verify: `dlss5-feed.log` next to the exe shows `feature ready … DLAA` and `frame N delivered`.

## Install — 32-bit game (beta) ⭐

1. Install **32-bit ReShade** with add-on support (installer auto-detects; `dxgi.dll` ≈ 4.4 MB).
2. Copy **`dlss5-feed.addon32`** next to the game exe; `DLSS5_Feed.fx` → `reshade-shaders\Shaders\`.
3. Copy the **entire `host64\` folder** next to the game exe (nothing to configure).
4. Motion vectors + `DLSS5_MV_PROVIDER` — same as steps 4–5 above.
5. Enable **DLSS 5 Feed** in-game. The "32-bit DLSS 5 Feeder" window appears — set
   `host_window=0` on the add-on page once happy. Logs: `host64\dlss5-feed-host.log` and
   `host64\ReShade.log`.
6. **DirectX 9 games:** real D3D9 can't work (SM3 cap, no shared handles). Translate with
   **dgVoodoo2** first (dege.freeweb.hu): `MS\x86\D3D9.dll` + `dgVoodoo.conf` + `dgVoodooCpl.exe`
   next to the exe, `DisableAndPassThru=false`, `VRAM=1GB`, `OutputAPI=d3d11_fl11_0`, verify the
   watermark, then install the feeder normally (ReShade as `dxgi.dll`, **never** `d3d9.dll`).

## Install — Vulkan game

Same as 64-bit, but ReShade is a Vulkan **layer** (register the game exe in its installer; ensure
`AddonPath=.\` under `[ADDON]` in `ReShade.ini`). The add-on adds the interop extensions itself;
**only** if `dlss5-feed.log` reports missing interop entry points, unzip `feed-vk-layer.zip`
and launch via its `run-with-feed-layer.bat`.

## Motion-vector providers (choose ONE, enable above DLSS 5 Feed)

| Value | Provider | Enable technique |
|---|---|---|
| `0` | anything writing `texMotionVectors` (qUINT, dh_uber_motion) | its own |
| `1` | iMMERSE Launchpad (MartysMods) | `Launchpad` |
| `2` | VORT | `vort_Motion` |
| **`3`** | **LumeniteFX Kernel ← recommended** | `LUMENITE: Kernel 2.0` |
| `4` | LumeniteFX QuantMotion | `LUMENITE: QuantMotion` |

**Not DRME / ReshadeMotionEstimation** — it does not compile on ReShade 6.8 (silently writes
nothing; the feeder now detects this and says so in overlay + log).

## Troubleshooting (quick)

| Symptom | Fix |
|---|---|
| Image smears while moving | No vectors reaching DLSS: overlay "Motion vectors" section names the cause (provider not installed / disabled / failed to compile / wrong one enabled) |
| Warping around flames/transparents | Keep validation on; use provider 3; try `preset=5`/`6` in `dlss5-feed.cfg` |
| No `dlss5-feed.log` at all | ReShade arch mismatch: x64 `dxgi.dll` in a 32-bit game or vice versa |
| DLSS 5 panel stuck STANDBY | Built-in warm-up re-creates the feature after a few seconds |
| "ran out of video memory" (D3D9 path) | Raise `VRAM` in `dgVoodoo.conf` (1 GB; not 2 GB — 32-bit signed overflow) |
| Conflicts | Disable **NVIDIA Smooth Motion** and **OptiScaler** in the same game |

Logs: `dlss5-feed.log`, `ReShade.log`, `host64\dlss5-feed-host.log`, `host64\ReShade.log`.
Config: `dlss5-feed.cfg` (auto-created) — full key reference in the project's README.

## Proven working (pack owner's session)

**Saints Row: The Third (32-bit, D3D11)** — 2560×1440 DLAA, `feature ready … flags=66`,
99,000+ frames evaluated over a full play session, host window healthy throughout.
Upstream reports also: Metro 2033 Redux (64-bit D3D11), LOTR War in the North (64-bit D3D12),
Splinter Cell Blacklist (32-bit), BioShock Remastered (32-bit), Fable Anniversary (32-bit D3D9
via dgVoodoo2), DOOM 2016 (64-bit Vulkan).

## Source

github.com/jlrouzies-fr/DLSS5-Feeder — v0.6.0-beta.1 (2026-08-30). Beta software: temporal
quality of *estimated* motion vectors; HUD processed with the scene. Full documentation,
configuration reference and building instructions live in the project's README.
