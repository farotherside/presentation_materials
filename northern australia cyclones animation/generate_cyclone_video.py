"""
generate_cyclone_video.py
─────────────────────────────────────────────────────────────────────────────
Renders an animated MP4 of tropical cyclone tracks approaching the north
Australian coast (1980–2026) over an ESRI satellite basemap.

REQUIREMENTS
  pip install cartopy matplotlib pillow numpy
  brew install ffmpeg   (macOS)  |  apt install ffmpeg  (Ubuntu)

USAGE
  python generate_cyclone_video.py [options]

OPTIONS
  --output FILE        Output MP4 path (default: cyclones_north_australia.mp4)
  --fps N              Frames per second (default: 30)
  --days-per-frame N   Simulation days advanced per frame (default: 3)
                         3 d/frame @ 30fps ≈ 3m 10s for 1980–2026
                         6 d/frame @ 30fps ≈ 1m 35s
  --fade-days N        Days for a completed track to fade out (default: 20)
  --width PX           Output width in pixels (default: 1920)
  --height PX          Output height in pixels (default: 1080)
  --zoom N             Tile zoom level 1–8; higher = sharper but slower
                       download (default: 5)
  --cat-min N          Minimum Saffir-Simpson category to show: -1=all,
                       0=TS+, 1=Cat1+, 2=Cat2+, 3=Severe+ (default: -1)
  --trail-days N       Days of track history shown behind the storm head
                       (default: 999 = full track; set e.g. 15 for comet tail)
  --test-frame         Render only the first frame for a quick preview, then exit

NOTES
  • The ESRI World Imagery tile server is used by default (free, no API key).
  • The basemap is rendered once and cached; only storm tracks are re-drawn
    each frame, so rendering is fast.
  • Expect ~5–15 min rendering time for 1920×1080, depending on your machine.
  • The data file storm_tracks_1980.json must be in the same directory.
─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

# ── Config defaults ───────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
DATA_FILE  = SCRIPT_DIR / 'storm_tracks_1980.json'

MAP_EXTENT  = [108, 148, -31, -5]   # [lon_min, lon_max, lat_min, lat_max]
EPOCH       = datetime(1980, 1, 1)
MONTHS      = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']

# Category colours (RGB 0–1)
CAT_COLOR = {
    -1: (0.45, 0.50, 0.55),   # depression / unknown
     0: (0.52, 0.80, 0.40),   # tropical storm
     1: (1.00, 0.88, 0.25),   # cat 1
     2: (1.00, 0.53, 0.12),   # cat 2
     3: (1.00, 0.16, 0.10),   # cat 3 severe
     4: (0.80, 0.25, 1.00),   # cat 4 intense
}

def cat_color(cat, alpha=1.0):
    r, g, b = CAT_COLOR.get(cat, CAT_COLOR[-1])
    return (r, g, b, alpha)

# ── Data helpers ──────────────────────────────────────────────────────────────

def load_storms(path):
    with open(path) as f:
        storms = json.load(f)
    # Pre-compute per-storm max cat and time range
    for s in storms:
        pts = s['pts']
        s['t_start'] = pts[0][0]
        s['t_end']   = pts[-1][0]
        s['max_cat'] = max(p[3] for p in pts)
    storms.sort(key=lambda s: s['t_start'])
    return storms

def day_to_date(d):
    return EPOCH + timedelta(days=float(d))

def fmt_date(d):
    dt = day_to_date(d)
    return f"{MONTHS[dt.month-1].upper()} {dt.year}"

# ── Basemap ───────────────────────────────────────────────────────────────────

def build_basemap(fig_w_in, fig_h_in, dpi, zoom):
    """Render the satellite basemap into an RGBA array and return it."""
    print("  Downloading satellite tiles …", flush=True)

    esri_url = (
        'https://server.arcgisonline.com/ArcGIS/rest/services/'
        'World_Imagery/MapServer/tile/{z}/{y}/{x}'
    )
    tiles = cimgt.GoogleTiles(url=esri_url)

    fig_bm = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=dpi)
    ax_bm  = fig_bm.add_axes([0, 0, 1, 1], projection=tiles.crs)
    ax_bm.set_extent(MAP_EXTENT, crs=ccrs.PlateCarree())
    ax_bm.add_image(tiles, zoom)

    fig_bm.canvas.draw()
    # tostring_rgb removed in newer matplotlib; use buffer_rgba instead
    buf = np.frombuffer(fig_bm.canvas.buffer_rgba(), dtype=np.uint8)
    w_px = int(fig_w_in * dpi)
    h_px = int(fig_h_in * dpi)
    basemap_img = buf.reshape(h_px, w_px, 4)[..., :3]   # drop alpha → RGB
    plt.close(fig_bm)
    print("  Basemap ready.", flush=True)
    return basemap_img

# ── Frame renderer ────────────────────────────────────────────────────────────

def render_frame(ax, storms, current_day, fade_days, trail_days, cat_min, proj):
    """Draw all storm tracks onto ax for the given day."""
    ax.cla()
    ax.set_extent(MAP_EXTENT, crs=ccrs.PlateCarree())
    ax.axis('off')

    active_count = 0

    for storm in storms:
        if storm['t_start'] > current_day:
            break  # storms are sorted; nothing after this will be active

        if storm['t_end'] + fade_days < current_day:
            continue

        if cat_min > -2 and storm['max_cat'] < cat_min:
            continue

        pts = storm['pts']
        after_end  = max(0.0, current_day - storm['t_end'])
        fade_frac  = after_end / fade_days       # 0 = live, 1 = gone
        is_active  = (after_end == 0)
        base_alpha = 1.0 - fade_frac

        if is_active:
            active_count += 1

        # Gather visible points
        vis = [(p[1], p[2], p[0], p[3]) for p in pts if p[0] <= current_day]
        if len(vis) < 2:
            continue

        # Trail trim
        if trail_days < 999 and is_active:
            cutoff = current_day - trail_days
            vis = [(lo,la,t,c) for lo,la,t,c in vis if t >= cutoff]
            if len(vis) < 2:
                continue

        # Draw segments
        for i in range(1, len(vis)):
            lo0,la0,_,c0 = vis[i-1]
            lo1,la1,_,c1 = vis[i]
            cat = max(c0, c1)
            seg_alpha = base_alpha * (0.85 if is_active else 0.45)
            lw = 2.5 if is_active else 1.5
            ax.plot([lo0, lo1], [la0, la1],
                    color=cat_color(cat, seg_alpha),
                    linewidth=lw,
                    transform=ccrs.PlateCarree(),
                    solid_capstyle='round')

        # Storm-head glow
        if is_active:
            head_lo, head_la = vis[-1][0], vis[-1][1]
            head_cat = max(c for _,_,_,c in vis)
            r, g, b = CAT_COLOR.get(head_cat, CAT_COLOR[-1])
            ax.plot(head_lo, head_la, 'o',
                    color=(r, g, b),
                    markersize=7,
                    markeredgewidth=1.5,
                    markeredgecolor=(1,1,1,0.7),
                    transform=ccrs.PlateCarree(),
                    zorder=10)
            # Soft glow ring
            ax.plot(head_lo, head_la, 'o',
                    color=(r, g, b, 0.25),
                    markersize=18,
                    transform=ccrs.PlateCarree(),
                    zorder=9)

    return active_count

# ── Legend & HUD ──────────────────────────────────────────────────────────────

def add_legend(fig):
    legend_items = [
        Line2D([0],[0], color=CAT_COLOR[-1]+(1,), lw=2, label='Depression'),
        Line2D([0],[0], color=CAT_COLOR[0]+(1,),  lw=2, label='Tropical Storm'),
        Line2D([0],[0], color=CAT_COLOR[1]+(1,),  lw=2, label='Cat 1  (64–82 kt)'),
        Line2D([0],[0], color=CAT_COLOR[2]+(1,),  lw=2, label='Cat 2  (83–95 kt)'),
        Line2D([0],[0], color=CAT_COLOR[3]+(1,),  lw=2, label='Cat 3+ Severe  (≥96 kt)'),
        Line2D([0],[0], color=CAT_COLOR[4]+(1,),  lw=2, label='Cat 4+ Intense  (≥113 kt)'),
    ]
    leg = fig.legend(
        handles=legend_items,
        loc='lower left',
        bbox_to_anchor=(0.01, 0.01),
        framealpha=0.55,
        facecolor='#061018',
        edgecolor='#1a3050',
        labelcolor='#b0cce0',
        fontsize=9,
        handlelength=2.5,
    )
    return leg

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Render cyclone track MP4')
    parser.add_argument('--output',         default='cyclones_north_australia.mp4')
    parser.add_argument('--fps',            type=int,   default=30)
    parser.add_argument('--days-per-frame', type=float, default=3.0)
    parser.add_argument('--fade-days',      type=float, default=20.0)
    parser.add_argument('--trail-days',     type=float, default=999.0)
    parser.add_argument('--width',          type=int,   default=1920)
    parser.add_argument('--height',         type=int,   default=1080)
    parser.add_argument('--zoom',           type=int,   default=5)
    parser.add_argument('--cat-min',        type=int,   default=-1)
    parser.add_argument('--test-frame',     action='store_true')
    args = parser.parse_args()

    # ── Load data ─────────────────────────────────────────────────
    if not DATA_FILE.exists():
        sys.exit(f"ERROR: data file not found: {DATA_FILE}")
    storms = load_storms(DATA_FILE)
    max_day = max(s['t_end'] for s in storms) + args.fade_days + 10
    print(f"Loaded {len(storms)} storms, max_day={max_day:.0f}")

    # ── Figure setup ──────────────────────────────────────────────
    dpi      = args.width / (16/9 * (args.height / args.width * 16/9) * 9)
    # Simpler: fixed DPI so width×height matches
    dpi      = args.width / 16 * (9 / args.height * args.width / 9)
    # Just hardcode:
    FIG_W = args.width  / 100.0
    FIG_H = args.height / 100.0
    dpi   = 100

    proj  = ccrs.PlateCarree()

    # ── Basemap ───────────────────────────────────────────────────
    print("Building basemap …")
    basemap_img = build_basemap(FIG_W, FIG_H, dpi, args.zoom)

    # ── Frame output dir ──────────────────────────────────────────
    frames_dir = Path(args.output).stem + '_frames'
    os.makedirs(frames_dir, exist_ok=True)

    # ── Frame generation ──────────────────────────────────────────
    days = np.arange(0, max_day, args.days_per_frame)
    if args.test_frame:
        days = days[:1]

    print(f"Rendering {len(days)} frames …")

    for frame_idx, day in enumerate(days):
        if frame_idx % 100 == 0:
            pct = frame_idx / len(days) * 100
            print(f"  Frame {frame_idx}/{len(days)}  ({pct:.0f}%)  {fmt_date(day)}", flush=True)

        fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi, facecolor='black')
        ax_map = fig.add_axes([0, 0, 1, 1], projection=proj)
        ax_map.set_extent(MAP_EXTENT, crs=proj)

        # Paint cached basemap
        ax_map.imshow(basemap_img,
                      origin='upper',
                      extent=MAP_EXTENT,
                      transform=proj,
                      zorder=0)

        # Draw tracks
        active = render_frame(ax_map, storms, day,
                               args.fade_days, args.trail_days,
                               args.cat_min, proj)

        # Date HUD
        date_str = fmt_date(day)
        ax_map.text(0.985, 0.04, date_str,
                    transform=ax_map.transAxes,
                    ha='right', va='bottom',
                    fontsize=26, fontweight='bold',
                    color='white', alpha=0.85,
                    path_effects=[pe.withStroke(linewidth=4, foreground='black')])

        # Title
        ax_map.text(0.5, 0.975,
                    'TROPICAL CYCLONES · NORTH AUSTRALIAN COAST · 1980–2026',
                    transform=ax_map.transAxes,
                    ha='center', va='top',
                    fontsize=11, color='#88b8d8', alpha=0.9, fontweight='bold',
                    path_effects=[pe.withStroke(linewidth=3, foreground='black')])

        # Active count
        if active > 0:
            ax_map.text(0.015, 0.04,
                        f'Active storms: {active}',
                        transform=ax_map.transAxes,
                        ha='left', va='bottom',
                        fontsize=10, color='#ffe080', alpha=0.9,
                        path_effects=[pe.withStroke(linewidth=3, foreground='black')])

        # Legend (only first few frames so it's always visible)
        add_legend(fig)

        frame_path = f'{frames_dir}/frame_{frame_idx:05d}.png'
        fig.savefig(frame_path, dpi=dpi, bbox_inches=None, pad_inches=0,
                    facecolor='black')
        plt.close(fig)

    if args.test_frame:
        print(f"Test frame saved: {frames_dir}/frame_00000.png")
        return

    # ── Encode MP4 with ffmpeg ─────────────────────────────────────
    print(f"\nEncoding MP4 → {args.output} …")
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(args.fps),
        '-i', f'{frames_dir}/frame_%05d.png',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',                    # ~near-lossless; raise to 23 for smaller file
        '-pix_fmt', 'yuv420p',           # required for Keynote compatibility
        '-movflags', '+faststart',       # web-optimised; also needed for Keynote
        args.output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg STDERR:", result.stderr[-2000:])
        sys.exit("ffmpeg failed.")

    size_mb = os.path.getsize(args.output) / 1024**2
    duration = len(days) / args.fps
    print(f"\n✓ Done!  {args.output}  ({size_mb:.1f} MB, {duration:.0f}s @ {args.fps}fps)")
    print(f"  Frames kept in: {frames_dir}/")
    print(f"\nKeynote tip: Insert → Choose… and select the .mp4.")
    print("  It will loop by default — set playback to 'Play Once' in the inspector.")

if __name__ == '__main__':
    main()
