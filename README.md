# FarOtherSide presentation materials

Source materials, tools, and assets used to build the FarOtherSide
circumnavigation talk.

## Contents

### [`gpx_map_render/`](./gpx_map_render/)

A single-page browser tool that turns GPX files into animated map clips for
the talk. Ships with the full FarOtherSide voyage (84 legs, ~43,700 nm)
inlined as the default dataset, and can load arbitrary GPX files for use on
other voyages or trips. Open `gpx_map_render/render.html` in Chrome to use.

Includes:

- `render.html` — the renderer (one self-contained HTML file)
- `geojson/` — per-leg track data for the built-in FarOtherSide voyage
- `legs_index.json` — parsed metadata for the 84 legs
- `parse_gpx.py` — the script that originally produced the JSON/GeoJSON from
  the master GPX (archival; the renderer parses GPX in-browser now)

See [`gpx_map_render/README.md`](./gpx_map_render/README.md) for full user
documentation — features, sidebar reference, troubleshooting, etc.

### [`northern australia cyclones animation/`](./northern%20australia%20cyclones%20animation/)

An interactive browser tool that animates tropical cyclone tracks approaching
the north Australian coast (Exmouth to Thursday Island) from 1980 to 2026.
Renders on a live Mapbox satellite basemap; exports WebM video for Keynote.
Storm data (247 tracks, IBTrACS v04r01) is embedded in the HTML — open
`cyclone_render.html` in Chrome with a Mapbox token and it runs standalone.

Also includes a Python script (`generate_cyclone_video.py`) for high-quality
MP4 rendering via cartopy + ffmpeg.

See [`northern australia cyclones animation/README.md`](./northern%20australia%20cyclones%20animation/README.md)
for full documentation.
