# GPX Map Render

A single-page browser tool for turning GPX track files into animated map clips
suitable for conference talks, presentations, social posts, or any context
that wants a moving track on a beautiful basemap. Ships with the FarOtherSide
circumnavigation voyage built in (84 legs, ~43,700 nm) and can load any other
GPX file you point at it.

The whole tool is a single HTML file (`render.html`) and a folder of track
data (`geojson/`, for the built-in voyage). No build step, no Node, no Python
required to use it. Drop it in a folder, open `render.html` in Chrome, paste a
free Mapbox token, and you're rendering.


## Table of contents

- [Quick start](#quick-start)
- [Features](#features)
- [Workflow](#workflow)
- [Sidebar reference](#sidebar-reference)
- [Loading a different GPX file](#loading-a-different-gpx-file)
- [Multi-leg combined animations](#multi-leg-combined-animations)
- [Speed running-average and update rate](#speed-running-average-and-update-rate)
- [Output resolution and aspect ratio](#output-resolution-and-aspect-ratio)
- [Recording vs. PNG stills](#recording-vs-png-stills)
- [Converting WebM to MP4](#converting-webm-to-mp4)
- [File structure](#file-structure)
- [Troubleshooting](#troubleshooting)
- [How it works under the hood](#how-it-works-under-the-hood)


## Quick start

1. **Get a Mapbox token (one-time, ~3 minutes).** Sign up at
   https://mapbox.com — the free tier covers tens of thousands of map loads
   per month, more than enough for this. In your account dashboard, copy your
   default public token. It starts with `pk.`.

2. **Open `render.html` in Chrome.** Double-click it from Finder, or serve the
   folder with `python3 -m http.server` and visit http://localhost:8000/.
   Chrome is recommended — Safari's MediaRecorder support is patchy and may
   produce broken `.webm` files.

3. **Paste your Mapbox token** into the field at the top of the sidebar.
   The map appears and the leg list populates with the 84 legs of the
   FarOtherSide voyage.

4. **Click a leg.** The map zooms to fit. Adjust per-leg controls (duration,
   camera, overlays). Hit **Preview** to animate without saving. Hit **Record**
   to save a `.webm` file. Hit **Save PNG** for a high-res still.

5. **(Optional) Load your own GPX.** In the *Data source* section, click
   *Load GPX file…* and pick any `.gpx` file. Each `<trk>` element becomes a
   leg in the list.


## Features

- **Single-file deployment.** One HTML file plus optional track-data folder.
- **In-browser GPX parsing.** Drop any `.gpx` file in, no preprocessing.
- **84-leg FarOtherSide voyage built in.** All legs of the circumnavigation,
  with metadata (distance, duration, bbox) inlined.
- **16 basemap options** across dark/light/satellite, including Mapbox
  Standard's lighting presets (day, dawn, dusk, night).
- **Track color picker** with 9 presets, including International Orange
  (`#FF4F00`).
- **Three camera modes** — static wide (default, most readable), follow-boat
  (cinematic, more disorienting), and keyframe zoom (zooms in mid-leg, pulls
  back at the end — good for landfalls and capes).
- **Per-leg trim controls** to clip the start/end of a track before recording.
- **Waypoint rendering.** Reads `<wpt>` elements; eight icon shapes, color
  picker with International Orange and 8 other presets, label and visibility
  toggles.
- **Overlays.** Date, cumulative distance, current speed — each toggleable
  per leg. Drawn at the chosen output resolution so they stay crisp in 4K.
- **Speed as a running average** with adjustable smoothing window (0–25% of
  the track) and on-screen update-rate throttle (realtime to once every 5
  seconds of animation time).
- **Multi-leg combined animations.** Shift-click any two legs to combine the
  contiguous range into a single animated track.
- **Custom output resolution.** 1080p, 1440p, 4K UHD, 720p, square, vertical,
  Cinema 2K (2.39:1), or any custom size. Selectable FPS (24/30/60) and
  bitrate (6–48 Mbps).
- **Per-leg settings persistence.** Every leg's duration, camera, trim,
  overlays remembered in `localStorage`, scoped per source file so different
  GPX files don't collide.
- **PNG stills** at any output resolution — handy for slide backgrounds.


## Workflow

A typical session for prepping a conference talk:

1. Open `render.html`. Paste the Mapbox token (it's remembered after the
   first time).
2. Browse the leg list. Search by name if the GPX is large.
3. For each clip you want:
   - Click the leg.
   - Adjust the duration (the renderer suggests one based on distance —
     longer crossings get more screen time by default).
   - Pick a camera mode. Static wide is the safest default. Follow-boat is
     dramatic but can be disorienting on a big screen. Keyframe zoom adds a
     subtle push-in around the midpoint and pulls back at the end — great
     for landfalls.
   - Toggle overlays. For ocean crossings, *distance* is the overlay that
     conveys scale best — watching "847 nm" tick up over 30 seconds is the
     moment.
   - Optionally trim the start/end with the sliders if the track has extra
     miles you don't want to render.
   - Hit **Preview** until you like it.
   - Hit **Record** to save a `.webm`.
4. For each slide, save a PNG still as a slide background — then drop the
   matching `.webm` on top, set to play on click.


## Sidebar reference

### 1. Mapbox token

Your `pk.…` public token. Persisted in `localStorage` between sessions.

### 2. Data source

Either the built-in FarOtherSide voyage or a custom GPX file you load.

- **Load GPX file…** — opens a file picker. The chosen GPX is parsed
  in-browser; each `<trk>` becomes a leg, `<wpt>` elements become waypoints.
  The parsed result is cached in IndexedDB so a page reload restores it
  without re-picking the file.
- **Default** — discards a loaded custom GPX and reverts to the built-in
  FarOtherSide voyage.
- **Title** — text shown under the date in the overlay (defaults to
  "FAROTHERSIDE" or, for a loaded GPX, the file's `<metadata><name>` element
  uppercased, or the filename).

### 3. Pick a leg

Searchable list. Each row shows the leg id, the leg name, total nautical
miles, the year, the configured duration, and the camera mode.

- **Click a leg** to load its track and zoom the map to it.
- **Shift-click another leg** to combine the contiguous range — see
  [Multi-leg combined animations](#multi-leg-combined-animations).
- **The Combined banner** appears above the list when a range is active.
  Click *Clear* to drop the range and return to single-leg mode.

### 4. Map style & track

- **Basemap** — 16 options grouped by mood:
  - *Dark / night*: Navigation Night, Dark monochrome, Standard 3D · Dusk,
    Standard 3D · Night, Standard Satellite · Dusk, Standard Satellite ·
    Night.
  - *Light / day*: Light monochrome, Navigation Day, Streets, Outdoors /
    terrain, Standard 3D · Day, Standard 3D · Dawn.
  - *Satellite*: Satellite imagery (raw), Satellite + streets, Standard
    Satellite · Day, Standard Satellite · Dawn.
- **Track color** — color picker plus a preset dropdown. The presets are:
  Gold (default), International Orange `#FF4F00`, Coral red, Teal, Lavender,
  Sea green, Amber, White, Black.
- **Line weight** — 1.0 to 6.0 in 0.5 steps.

### 5. Waypoints

Reads `<wpt>` elements from the loaded GPX.

- **Show** — master toggle for waypoint visibility.
- **Labels** — toggle for the text label below each waypoint icon.
- **Icon** — eight shapes: Circle, Square, Diamond, Triangle, Star, Cross,
  Pin (teardrop), Anchor. Drawn fresh as a canvas image so they recolor
  cleanly.
- **Wpt color** — color picker with the same 9 presets as the track color
  (International Orange is the default).
- **Size** — 6–40 px slider.

### 6. Output resolution

- **Preset** — 1080p (1920×1080), 4K UHD (3840×2160), 720p, 1440p, square
  (1080×1080), vertical (1080×1920), Cinema 2K (2048×858), custom.
- **Size** — explicit width × height (auto-switches preset to "custom" if
  you edit either field).
- **FPS** — 30 (default), 60, or 24 (cinema).
- **Bitrate** — 6 / 12 / 24 / 48 Mbps. 12 is a reasonable default for 1080p;
  bump to 24+ for 4K.

### 7. Per-leg controls

- **Duration** — animation length in seconds. Default scales with leg
  distance (longer crossings → longer animations) within a 12–60s band.
- **Camera** — Static wide / Follow boat / Keyframe zoom.
- **Follow zoom** — only shown for follow-boat mode; zoom level 1–14
  (default 5).
- **Trim start / Trim end** — percentage sliders. The animation literally
  stops at the trimmed boundary; the trim is interpolated so the visual end
  is clean rather than landing on the nearest track point.
- **Show trim on map** — paints the trimmed segment statically so you can
  verify what'll be recorded.
- **Reset** — resets trim to the full track.
- **Overlays** — date / distance / speed checkboxes. Each toggle persists.
- **Overlay size** — global multiplier (0.5×–2.0×) on the size of all
  overlay text and the corner spacing. Affects the on-screen preview
  instantly (via a CSS variable) and the recorded canvas output (read at
  draw time). Default 1.0× matches the historical behaviour. Use a higher
  value for large auditorium displays or low-contrast basemaps; lower for
  understated overlays on busy maps.
- **Speed smooth** — window size for the running-average speed, as % of the
  leg's track points (0–25%). 0% is effectively instantaneous; 3% is the
  default and removes most jitter; 25% is heavy smoothing where the value
  changes slowly across the animation. See
  [Speed running-average and update rate](#speed-running-average-and-update-rate).
- **Speed update** — how often the on-screen speed value refreshes, in
  animation-time seconds (0–5). Realtime updates every frame; 5s freezes the
  value for 5 seconds at a time.

### 8. Preview / Record

- **Preview** — animates without recording. Use this while dialing in
  settings.
- **Record** — runs the animation while capturing the composite canvas to a
  `.webm` file. Filename: `leg_NN_WxH.webm` for single legs, `legs_F-T_WxH.webm`
  for combined ranges. Click again to abort mid-record. Before the recorder
  starts, the renderer pre-walks the camera through the path the animation
  will take so all the basemap tiles get fetched and cached — this prevents
  "white square" tile-loading artifacts from showing up in the recorded
  video. The first record on a fresh leg takes 3–10 seconds of prewarm; once
  the browser has cached the tiles, subsequent recordings of the same leg
  prewarm essentially instantly.
- **Stop** — interrupts whatever is currently playing. Stops a Preview in
  place. Stops a Record and finalises the `.webm` with whatever has been
  captured so far (the file is still saved, just shorter than a full run).
- **Save PNG** — captures the current map state at the configured output
  resolution as `.png`.


## Loading a different GPX file

The built-in voyage is just the default — you can drop in any GPX file:

1. In the sidebar, **Section 2 (Data source)**, click **Load GPX file…**.
2. Pick a `.gpx` file. The renderer parses it in-browser (no upload, no
   server).
3. Each `<trk>` element becomes a leg in the sidebar list. All `<trkseg>`
   points within a `<trk>` are concatenated. Waypoints (`<wpt>`) become map
   waypoints — the same icon/color/size controls apply.
4. Tracks denser than ~3,000 points are evenly downsampled (start and end
   points preserved) so the animation stays smooth.
5. Per-leg metadata (distance, duration, bbox, average speed) is computed
   from the coordinates and timestamps.
6. The parsed GPX is saved to your browser's IndexedDB, so a page reload
   restores it automatically. Click **Default** to switch back to the
   built-in FarOtherSide voyage.
7. Per-leg settings are namespaced by source — switching between FarOtherSide
   and a custom GPX doesn't trample either side's saved configurations.

Notes and limits:

- Time-based overlays (date, speed) require `<time>` elements on the
  trackpoints. Tracks without timestamps still render fine, but the date
  overlay stays blank and speed reads 0.
- Multi-track GPX files (e.g. one `<trk>` per day of a trip) work best — each
  `<trk>` is a separately selectable leg.
- The renderer expects standard GPX 1.1. Most consumer GPS apps and chart
  plotters export this.


## Multi-leg combined animations

Shift-click a second leg in the list to combine the contiguous range into a
single virtual leg.

- The Combined banner appears above the leg list with the leg count, total
  nautical miles, current duration, and camera mode.
- In-range rows get a subtle highlight.
- All the existing per-leg controls (duration, camera, trim, overlays, speed
  smoothing/update) operate on the combined track unchanged.
- The animation walks through the legs in id order; the line is continuous if
  the leg endpoints share a port (as they typically do).
- Gaps in time between legs (e.g. months at anchor) are silently dropped from
  the cumulative-time count, so the running-average speed reads correctly
  across leg boundaries instead of spiking when a 60-day pause shows up as a
  single segment.
- Recording filename: `legs_F-T_WxH.webm` (e.g. `legs_3-7_1920x1080.webm`)
  instead of `leg_NN_WxH.webm`.
- Settings for combined ranges are stored under their range key (`combined:3-7`),
  so different ranges keep separate settings.

To extend an existing range, shift-click another leg outside it — the renderer
keeps the anchor opposite to where you clicked. To drop the range and return
to single-leg mode, click any single leg without Shift, or hit *Clear* in the
banner.


## Speed running-average and update rate

Instantaneous speed (nm-per-hour over a single segment of the track) is
jittery — it jumps around with every gybe, current change, or GPS noise
hiccup. The renderer instead shows a running average, and lets you control
how aggressive the smoothing is.

- **Speed smooth (0–25%)** — the window for the running average, as a
  percentage of the leg's total track points. At 0% the value reads from a
  single segment (effectively instantaneous). The default 3% smooths over the
  most recent ~3% of points, which is usually enough to remove visible
  twitching. At 25% the value changes slowly through the animation.
- **Speed update (0–5s)** — how often the displayed value actually refreshes
  on screen, measured in animation-time seconds. "realtime" updates every
  frame; 1s freezes the value for a full second between updates; 5s changes
  it only four times during a 20-second animation. This is independent of the
  smoothing — it just controls how often you see the new value.

Implementation: cumulative-distance and cumulative-time arrays are
precomputed, so each frame's window query is O(1) regardless of the smoothing
percentage. Even the 17,000-point ocean-crossing legs render at 60 fps with
heavy smoothing turned on. Segments with unrealistically long time deltas
(more than 6 hours, e.g. a boat at anchor between two timestamps) are clamped
to 0 hours so they don't pollute the average.

Both sliders are read once at the start of each Preview/Record run — change a
slider and hit Preview/Record again to apply.


## Output resolution and aspect ratio

The renderer captures the live Mapbox canvas and composites it onto a
target-resolution canvas with object-fit "cover" semantics — the output
aspect ratio is honored even if the on-screen map is a different shape.

- **1080p** is fine for most presentation needs and most conference AV.
- **4K UHD** works, but with a caveat: the map canvas reflects the live
  on-screen Mapbox canvas size, so if the browser window's map area is
  smaller than 3840 wide, the map pixels get upscaled (smooth, not
  pixel-sharp). For maximum native 4K detail, resize the Chrome window so
  the map panel itself is at least 3840 wide before recording (fullscreen +
  narrow sidebar gets you there on most monitors).
- The overlays (date, distance, speed, project title) are drawn fresh at the
  chosen resolution, so the text stays crisp at any output size.
- **Vertical** (1080×1920) is good for phone-first social posts.
- **Cinema 2K** (2.39:1) gives that letterboxed widescreen film look — great
  for dramatic crossings.


## Recording vs. PNG stills

- **Record** captures a `.webm` (VP9) at the chosen resolution, FPS, and
  bitrate. The composite frame loop runs alongside the animation; when the
  animation finishes, the recorder holds the final frame for ~1 second
  before stopping, so the video ends on a settled state rather than mid-line.
- **Save PNG** captures one frame at the chosen output resolution. Useful for
  slide backgrounds, handouts, and social-post images.

Modern presentation software (Keynote, PowerPoint 2019+, Google Slides) plays
`.webm` natively, so MP4 conversion is usually optional. If you do need MP4,
see the next section.


## Converting WebM to MP4

If your AV system or workflow requires MP4, use `ffmpeg`:

```bash
ffmpeg -i leg_11_1920x1080.webm -c:v libx264 -pix_fmt yuv420p -crf 18 leg_11.mp4
```

Install `ffmpeg` on macOS:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg
```

To batch-convert every WebM in the current folder:

```bash
for f in leg_*.webm; do
  ffmpeg -i "$f" -c:v libx264 -pix_fmt yuv420p -crf 18 "${f%.webm}.mp4"
done
```

`-crf 18` is a good visually-lossless default. Use `-crf 23` for smaller
files at slightly lower quality.


## File structure

```
gpx_map_render/
├── README.md            (this file)
├── render.html          the renderer — open in Chrome
├── geojson/             built-in FarOtherSide track data (84 files)
│   ├── leg_01.geojson
│   ├── leg_02.geojson
│   └── ...
├── legs_index.json      parsed metadata for the 84 FarOtherSide legs (reference;
│                        the renderer has it inlined into render.html)
├── parse_gpx.py         script that originally produced the FarOtherSide JSON
│                        and GeoJSON from the master GPX. Kept for archival
│                        purposes; you don't need it for normal use — the
│                        renderer parses GPX in-browser now.
└── leg_picker.html      legacy two-page workflow, no longer needed
```

Everything except `render.html` is optional for arbitrary GPX work — if you're
only using your own GPX files, the `geojson/` folder and the various
FarOtherSide-specific files can be ignored.


## Troubleshooting

**"GeoJSON not available" when I click a built-in leg.**
The renderer tries to `fetch()` the per-leg geojson from `./geojson/`. If you
opened `render.html` via `file://` (double-click from Finder), Chrome's
security model blocks direct fetches of local files. Two fixes:

- *Easy:* serve the folder with a tiny local web server, e.g.
  `python3 -m http.server` in this folder, then visit
  http://localhost:8000/render.html.
- *No-server:* the renderer shows an "Import geojson folder (one-time)" button
  below the leg list. Click it, navigate into the `geojson/` folder, Cmd-A to
  select all 84 files, and open them. The files get cached in Chrome's
  IndexedDB and load instantly forever after (until you clear browser data).

**Record button is disabled / has a "no" icon.**
Pick a leg from the list first — the button is disabled until a leg is
selected. Hover for a tooltip.

**Speed reads 0 throughout the animation.**
Your GPX trackpoints don't have `<time>` elements, so the renderer can't
compute speed. The date overlay will also stay blank. This is normal for some
hiking apps and is harmless.

**The animation jumps geographically between two legs in a combined range.**
The two legs don't share a port. The renderer doesn't add a connecting line
or interpolation — the boat just "teleports" to the start of the next leg.
For voyages where every leg starts where the previous one ended (the typical
case), this is invisible.

**The recorded WebM looks blurry / pixelated at 4K.**
Resize your Chrome window so the map panel is at least 3840 px wide before
recording, or accept the upscale. The overlays will be sharp regardless.

**Safari produces broken `.webm` files.**
Use Chrome. Safari's MediaRecorder support has known issues.

**My custom GPX has 50,000 points and the animation is sluggish.**
The renderer downsamples each track to ~3,000 points on load, but rendering
many simultaneously dense legs can still strain the GPU. Try a lower output
resolution while previewing, then bump up for the final record.

**I want to start over fresh.**
The renderer stores its state in `localStorage` and IndexedDB (token,
per-leg settings, basemap, track color, loaded GPX, etc.). To reset:
DevTools → Application → Storage → Clear site data. Or use Chrome's
"Clear browsing data" for `localhost`/the file URL you're using.


## How it works under the hood

- **Mapbox GL JS v3.7.0**, loaded from the Mapbox CDN at the top of the file.
- **GPX parsing** uses the browser's native `DOMParser`. No external library.
- **Per-leg track data** is stored as GeoJSON `Feature` objects with a
  `times[]` array parallel to the `geometry.coordinates[]` array.
- **The track + boat layers** are added with `map.addSource`/`addLayer`. A
  glow layer (wider, blurred, low-opacity) sits under the main line; a halo
  + dot for the boat's current position.
- **Animation** uses `requestAnimationFrame` and walks the track by
  cumulative nautical-mile distance. The visible segment is rebuilt each
  frame as a `setData` call on the GeoJSON source.
- **Recording** uses `canvas.captureStream(fps)` plus `MediaRecorder` with
  VP9 codec preference. The Mapbox canvas is composited onto a target-size
  canvas (object-fit cover) each frame, with overlays drawn fresh.
- **Waypoint icons** are drawn to an off-screen canvas and registered with
  Mapbox via `addImage()`, so recoloring is just a re-register.
- **Per-leg settings** live in `localStorage` keyed by a source namespace
  (e.g. `farotherside-per-leg-settings::farotherside` or
  `farotherside-per-leg-settings::gpx::<filename>::<size>`).
- **The GeoJSON cache** uses IndexedDB with two stores: `legs` (per-leg
  geojson for the FarOtherSide voyage, keyed by numeric leg id) and `sources`
  (the active loaded-GPX bundle, keyed by `"active"`).


## License

See the repository root for license terms.
