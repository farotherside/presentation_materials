# Northern Australia Cyclones Animation

An interactive browser tool that animates tropical cyclone tracks approaching
the north Australian coast (Exmouth to Thursday Island) from 1980 to 2026,
rendered on a live Mapbox basemap and exportable as a WebM video for use in
Keynote or other presentation software.

## Files

- **`cyclone_render.html`** — the main tool; one self-contained HTML file,
  open directly in Chrome (no server needed)
- **`storm_tracks_1980.json`** — pre-processed IBTrACS storm data: 247 storms
  from 1980–2026 that passed within 100 nautical miles of the north Australian
  coast, stored as day-offsets from 1980-01-01 with Saffir-Simpson category
  per observation
- **`generate_cyclone_video.py`** — Python script for high-quality MP4
  rendering via cartopy + ESRI satellite tiles + ffmpeg (alternative to the
  in-browser WebM export; useful for maximum resolution output)

## Using the browser tool

1. Open `cyclone_render.html` in **Chrome** (other browsers work but Chrome
   gives the best WebM recording quality)
2. Paste a **Mapbox public token** into the token field and press Enter — the
   map will load
3. Choose a basemap style (Standard Satellite works well for presentations)
4. Adjust animation settings in the sidebar:
   - **Season window** — default Nov–Apr; storms outside this window are hidden
   - **Year range** — filter to a specific decade or era
   - **Category filter** — show only Cat 2+ etc.
   - **Track draw rate** — slow down how fast each track is drawn in
   - **Dwell** — how many days a track holds at full brightness before fading
   - **Fade duration** — how long tracks take to fade out (up to 180 days)
5. Press **▶ Preview** to watch the animation, drag the scrubber to any point
6. Set output dimensions and press **⏺ Record WebM** to capture a video file

## Track colour key

| Colour | Intensity |
|--------|-----------|
| Green `#88cc66` | Tropical storm |
| Yellow `#ffe040` | Category 1 (64–82 kt) |
| Orange `#ff8820` | Category 2 (83–95 kt) |
| Red `#ff2a1a` | Category 3 Severe (≥96 kt) |
| Purple `#cc40ff` | Category 4 Intense (≥113 kt) |

Track lines change colour along their length as the storm's intensity changes,
with a smooth gradient at each transition.

## Using the Python MP4 generator

```bash
pip install cartopy matplotlib pillow numpy
brew install ffmpeg   # macOS; use apt install ffmpeg on Ubuntu

python generate_cyclone_video.py --help
python generate_cyclone_video.py --fps 30 --days-per-frame 3
```

The script renders each frame to PNG, then encodes with ffmpeg using settings
optimised for Keynote compatibility (`-pix_fmt yuv420p -movflags +faststart`).

## Data source

Storm tracks derived from the **IBTrACS v04r01** global best-track dataset
(NOAA/NCEI). Filtered to storms with at least one observation within 100
nautical miles of the north Australian coastline (Exmouth to Thursday Island,
including the Gulf of Carpentaria).
