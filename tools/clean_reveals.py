#!/usr/bin/env python3
# EXPERIMENTAL: works for simple cases (text inside a bubble, an icon on a plain background) but is NOT reliable
# for every frame (it can leak later elements into earlier frames). Review every output before using it.
"""Rebuild the "before" frames of a progressive reveal so the hidden element is removed cleanly.

Many AI reveal sequences (A -> B -> C, where each step pops in text or an icon) hide the upcoming element in the
earlier frame with a flat background-coloured box. That box also wipes out whatever was underneath (a speech-bubble
outline, a door edge), which looks cheap. This tool rebuilds each earlier frame from the next, complete one:

  for k = n-1 .. 1 (S_n = original final frame):
    M      = area that changes between original frame k and k+1 (the reveal region)
    keep   = existing artwork in S_k+1 that runs out of M (outlines, edges): always kept
    new    = everything else in M that is not plain background in S_k+1 (letters, icons)
    if original frame k still shows the kept artwork inside M  -> use the original frame there (it is clean)
    else                                                          -> S_k = S_k+1 with only `new` inpainted away

Usage: python3 tools/clean_reveals.py OUT_DIR frameA.png frameB.png [frameC.png ...]
Writes OUT_DIR/<name of each earlier frame> (the last frame is copied unchanged) and a debug mask per step.
"""
import os, sys
import cv2
import numpy as np
from scipy import ndimage as ndi


def _nonbg_unused(img, ref_mask):
    """Pixels clearly different from the local background colour (median of a ring around ref_mask)."""
    ring = ndi.binary_dilation(ref_mask, iterations=12) & ~ndi.binary_dilation(ref_mask, iterations=4)
    bg = np.median(img[ring], axis=0) if ring.any() else np.median(img.reshape(-1, 3), axis=0)
    return np.abs(img.astype(int) - bg).max(axis=2) > 28, bg


def artwork_classes(img):
    """Label map of line art / text / icons, measured against the LOCAL background (so white text on a dark night
    sky and black lines on cream paper both count), split by colour family so touching elements of different
    colours (a green tick on a brown door) stay separate: 0 = background, 1 = dark, 2 = light, 3.. = hue bins."""
    bg = cv2.medianBlur(img, 41).astype(int)
    dev = np.abs(img.astype(int) - bg).max(axis=2)
    art = dev > 38
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(int)
    f = img.astype(np.float32)
    lum = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    blum = 0.299 * bg[..., 0] + 0.587 * bg[..., 1] + 0.114 * bg[..., 2]
    cls = np.zeros(img.shape[:2], np.int32)
    colour = art & (hsv[..., 1] > 95) & (hsv[..., 2] > 70)
    cls[colour] = 3 + (hsv[..., 0][colour] // 15) * 2 + (hsv[..., 2][colour] > 170)
    cls[art & ~colour & (lum < blum)] = 1
    cls[art & ~colour & (lum >= blum)] = 2
    return cls


def components(cls):
    """Connected components of each colour class, numbered uniquely across classes."""
    lab = np.zeros(cls.shape, np.int32)
    nxt = 1
    for c in np.unique(cls):
        if c == 0:
            continue
        l, n = ndi.label(cls == c)
        lab[l > 0] = l[l > 0] + nxt - 1
        nxt += n
    return lab


def fill_flat(img, mask):
    """Fill each masked blob with the median colour of the plain surroundings (clean on flat fills, no smears)."""
    out = img.copy()
    l, n = ndi.label(mask)
    plain = artwork_classes(img) == 0
    for k in range(1, n + 1):
        blob = l == k
        ring = ndi.binary_dilation(blob, iterations=6) & ~ndi.binary_dilation(blob, iterations=2) & plain & ~mask
        if ring.sum() < 10:
            ring = ndi.binary_dilation(blob, iterations=10) & ~mask
        out[blob] = np.median(img[ring], axis=0).astype(np.uint8)
    # soften the seam by one pixel
    edge = ndi.binary_dilation(mask, iterations=1) & ~ndi.binary_erosion(mask, iterations=1)
    blur = cv2.GaussianBlur(out, (3, 3), 0)
    out[edge] = blur[edge]
    return out


def fill_lines(img, blob, vertical):
    """Rebuild straight structure through a hole: linear interpolation between the nearest clean pixels above and
    below each column (vertical=True) or left and right of each row."""
    out = img.copy().astype(np.float32)
    a = np.transpose(out, (1, 0, 2)) if vertical else out
    m = blob.T if vertical else blob
    for r in np.where(m.any(axis=1))[0]:
        xs = np.where(m[r])[0]
        lo, hi = xs.min() - 1, xs.max() + 1
        if lo < 0 or hi >= m.shape[1]:
            continue
        for x in xs:
            t = (x - lo) / (hi - lo)
            a[r, x] = a[r, lo] * (1 - t) + a[r, hi] * t
    return out.astype(np.uint8)


def fill_smart(img, mask):
    """Plain surroundings: flat fill (with a wider halo so anti-aliased letter edges go too).
    Straight lines passing through: rebuild them along their direction. Otherwise: inpaint."""
    out = img.copy()
    l, n = ndi.label(mask)
    gy, gx = np.gradient(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32))
    for k in range(1, n + 1):
        blob = l == k
        ring = ndi.binary_dilation(blob, iterations=5) & ~blob
        busy = np.abs(img[ring].astype(int) - np.median(img[ring], axis=0)).max(axis=1)
        if (busy > 40).mean() <= 0.08:
            wide = ndi.binary_dilation(blob, iterations=4)
            plain_col = np.median(img[ring], axis=0)
            near = ndi.binary_dilation(blob, iterations=9) & ~wide
            dev = np.abs(img.astype(int) - plain_col).max(axis=2)
            wide |= near & (dev > 5) & (dev < 90)          # faint anti-aliased traces, not real dark lines
            out[wide] = fill_flat(img, wide)[wide]
            continue
        ex, ey = np.abs(gx[ring]).sum(), np.abs(gy[ring]).sum()
        if ex > 1.6 * ey or ey > 1.6 * ex:          # mostly vertical (ex) or horizontal (ey) edges around
            out[blob] = fill_lines(img, blob, vertical=ex > ey)[blob]
        else:
            out[blob] = cv2.inpaint(img, (blob * 255).astype(np.uint8), 3, cv2.INPAINT_TELEA)[blob]
    return out


def step(orig_k, orig_k1, S_k1, fixed, debug=None):
    """Return (S_k, fixed, fallbacks): the earlier frame rebuilt from the complete later frame S_k1 by removing only
    the element that pops in, the mask of rebuilt pixels, and the number of regions left as the original."""
    diff_full = np.abs(orig_k.astype(int) - S_k1.astype(int)).max(axis=2)
    d = ndi.binary_opening(diff_full > 18, iterations=1)
    lab, n = ndi.label(ndi.binary_dilation(d, iterations=6))
    out = orig_k.copy()
    out[fixed] = S_k1[fixed]
    fixed = fixed.copy()
    cls = artwork_classes(S_k1)
    alab = components(cls)
    art = cls > 0
    dbg = np.zeros(d.shape, np.uint8)
    fallbacks = 0
    for c in range(1, n + 1):
        M = ndi.binary_fill_holes(lab == c)
        if M.sum() < 40:
            continue
        ring = ndi.binary_dilation(M, iterations=2) & ~M
        touching = np.unique(alab[ring & art])
        touching = touching[touching > 0]
        keep = np.isin(alab, touching) & M                 # existing artwork running out of the region: stays
        new = np.zeros_like(M)
        for comp in np.unique(alab[M & art]):
            if comp == 0 or comp in touching:
                continue
            cm = alab == comp
            if (cm & d).sum() >= 0.5 * cm.sum():
                new |= cm
        if new.sum() < 0.04 * (M & d).sum():
            out[M] = orig_k[M]                             # could not isolate the new element: keep original
            dbg[M] = 1
            fallbacks += 1
            continue
        new = ndi.binary_fill_holes(new)                   # a closed shape takes its inside with it (bubble fill)
        dark = cls == 1
        new |= dark & ndi.binary_dilation(new, iterations=5) & M & d   # its outline where it touches old lines
        new = ndi.binary_dilation(new, iterations=3) & (~keep | ndi.binary_dilation(new, iterations=1))
        out[M] = fill_smart(S_k1, new)[M]
        fixed |= M
        dbg[M] = 2
        dbg[new] = 3
    if debug is not None:
        vis = np.zeros(d.shape + (3,), np.uint8)
        vis[dbg == 1] = (80, 160, 80); vis[dbg == 2] = (80, 80, 200); vis[dbg == 3] = (255, 60, 60)
        cv2.imwrite(debug, cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    return out, fixed, fallbacks


def main():
    out_dir, files = sys.argv[1], sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    origs = [cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2RGB) for f in files]
    S = origs[-1]
    cv2.imwrite(os.path.join(out_dir, os.path.basename(files[-1])), cv2.cvtColor(S, cv2.COLOR_RGB2BGR))
    fixed = np.zeros(S.shape[:2], bool)
    for k in range(len(files) - 2, -1, -1):
        name = os.path.basename(files[k])
        S, fixed, fb = step(origs[k], origs[k + 1], S, fixed, debug=os.path.join(out_dir, "_mask_" + name))
        cv2.imwrite(os.path.join(out_dir, name), cv2.cvtColor(S, cv2.COLOR_RGB2BGR))
        print("cleaned", name, f"(fallback regions: {fb})" if fb else "")


if __name__ == "__main__":
    main()
