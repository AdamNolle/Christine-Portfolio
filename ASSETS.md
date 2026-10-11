# Scene and typography

The sunlit window was modeled and rendered in Blender for this website. Linen curtains were simulated with wind and collisions, pinned to individual rings on a supported curtain pole. The branch, leaf and fern geometry moves with the breeze. Separate desktop and portrait cameras provide responsive compositions.

The distant woodland and environmental lighting use [Forest Slope by Poly Haven](https://polyhaven.com/a/forest_slope), licensed [CC0](https://polyhaven.com/license). Foreground animated foliage, architecture, fabrics, grain and CN favicon are original work for this site.

The background film is decorative. It is muted, pausable, suspended outside the viewport, and replaced by a still for reduced-motion preferences or data-saving mode. The desktop and mobile films are selected by viewport width; mobile visitors load only the mobile film.

The breeze is a ten-second, 24 fps periodic animation. A closed cubic B-spline blends the original simulated curtain shapes with nonnegative weights, preserving the ring attachments and matching position and velocity across the loop. The two curtains and foliage have offset phases so they do not stop and reverse together. There is no reversed playback or image crossfade. The stills match the opening pose.

`scripts/render_breeze_loop.py` rebuilds the motion from the original ring-attached Blender source and saves a packed Blender file with the new animation. It renders frames 1–240; frame 241 is the matching endpoint and must not be encoded. Encode each numbered PNG sequence with FFmpeg using `-framerate 24 -frames:v 240 -c:v libx264 -preset slow -crf 15 -tune grain -x264-params ipratio=1:pbratio=1 -bf 0 -g 240 -pix_fmt yuv420p -movflags +faststart -an`. The higher texture quality and equal frame-type quantization reduce the compression change at the wrap.

Instrument Serif and Spectral are self-hosted. The Instrument Serif license is included with the fonts. Christine's supplied portrait is preserved.
