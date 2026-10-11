"""Render a periodic breeze from the original, ring-attached Blender scene.

blender -b christine-sunlit-window.blend -P scripts/render_breeze_loop.py -- \
    --output <render-folder> --source-output <seamless.blend>

The 240 exported frames exclude the duplicate endpoint at frame 241.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--source-output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
args.output.mkdir(parents=True, exist_ok=True)
args.source_output.parent.mkdir(parents=True, exist_ok=True)

FRAME_COUNT = 240
POSE_FRAMES = list(range(75, 196, 15))
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = FRAME_COUNT
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.cycles.use_animated_seed = False
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'OPTIX'
scene.cycles.device = 'GPU'


def weights(time, phase=0):
    """Nonnegative periodic cubic B-spline: continuous position and velocity.

    Blend geometry, not rendered images, to retain one sharp fabric surface.
    Convex weights preserve the simulation's pinned curtain attachment points.
    """
    progress = ((time + phase) % 1) * len(POSE_FRAMES)
    index = math.floor(progress)
    t = progress - index
    local = ((1-t)**3/6, (3*t**3-6*t*t+4)/6,
             (-3*t**3+3*t*t+3*t+1)/6, t**3/6)
    result = np.zeros(len(POSE_FRAMES))
    for offset, weight in zip((-1, 0, 1, 2), local):
        result[(index + offset) % len(POSE_FRAMES)] += weight
    return result


def linear_cycle(keys):
    for layer in keys.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:
                        point.interpolation = 'LINEAR'
                    curve.modifiers.new('CYCLES')


checks = {'durationSeconds': FRAME_COUNT / 24, 'frames': FRAME_COUNT, 'curtains': {}}
for name, phase in [('Left curtain', .31), ('Right curtain', .43)]:
    obj = bpy.data.objects[name]
    keys = obj.data.shape_keys
    keys.animation_data_clear()
    for key in keys.key_blocks:
        key.value = 0
    poses = [keys.key_blocks[f'Cloth simulation {frame}'] for frame in POSE_FRAMES]
    coords = []
    for pose in poses:
        values = np.empty(len(pose.data) * 3, dtype=np.float32)
        pose.data.foreach_get('co', values)
        coords.append(values.reshape(-1, 3))
    coords = np.array(coords)
    positions = lambda t: np.einsum('i,ijk->jk', weights(t, phase), coords)
    eps = .00001
    start, end = positions(0), positions(1)
    velocity_before = (positions(0)-positions(-eps))/eps
    velocity_after = (positions(eps)-positions(0))/eps
    displacements = [float(np.max(np.linalg.norm(positions((i+1)/FRAME_COUNT)-positions(i/FRAME_COUNT), axis=1))) for i in range(FRAME_COUNT)]
    report = {
        'endpointMaxError': float(np.max(np.abs(start-end))),
        'velocityJoinMaxError': float(np.max(np.abs(velocity_before-velocity_after))),
        'seamStepMaxMeters': displacements[-1],
        'ordinaryStepMedianMeters': float(np.median(displacements)),
        'minimumFrameMovementMeters': min(displacements),
    }
    assert report['endpointMaxError'] < 1e-7
    assert report['velocityJoinMaxError'] < .01
    assert report['minimumFrameMovementMeters'] > .0001
    checks['curtains'][name] = report
    for frame in range(FRAME_COUNT + 1):
        for pose, value in zip(poses, weights(frame / FRAME_COUNT, phase)):
            pose.value = float(value)
            pose.keyframe_insert(data_path='value', frame=frame+1)
    linear_cycle(keys)

# Give each plant a closed cycle, sharing phases between a tree's branches/leaves.
for obj in bpy.data.objects:
    keys = getattr(obj.data, 'shape_keys', None)
    if not keys or 'Wind in the canopy' not in keys.key_blocks:
        continue
    keys.animation_data_clear()
    key = keys.key_blocks['Wind in the canopy']
    seed = int(obj.name.rsplit(' ', 1)[-1])
    phase = seed * 1.618
    for frame in range(FRAME_COUNT + 1):
        t = math.tau * frame / FRAME_COUNT
        key.value = .5 + .24*math.sin(t+phase) + .09*math.sin(2*t+phase*.7)
        key.keyframe_insert(data_path='value', frame=frame+1)
    linear_cycle(keys)

views = [
    ('desktop', bpy.data.objects['Window composition'], 1280, 800),
    ('mobile', bpy.data.objects['Portrait window composition'], 576, 768),
]
scene.camera = views[0][1]
scene.render.resolution_x, scene.render.resolution_y = 1280, 800
scene.frame_set(1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(args.source_output))
(args.output / 'loop-checks.json').write_text(json.dumps(checks, indent=2))
print('LOOP CHECKS', json.dumps(checks), flush=True)

# Render the join first so it can be inspected while the rest of the film renders.
order = list(dict.fromkeys([0, 1, 238, 239, 60, 120, 180] + list(range(FRAME_COUNT))))
for index in order:
    scene.frame_set(index+1)
    for view, camera, width, height in views:
        folder = args.output / f'{view}-frames'
        folder.mkdir(exist_ok=True)
        target = folder / f'{index:04}.png'
        if target.exists():
            continue
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = width, height
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
    print(f'RENDERED PAIR {index+1}/{FRAME_COUNT}', flush=True)

# High quality fallback images match the first frame to avoid an arrival jump.
scene.frame_set(1)
scene.cycles.samples = 96
for view, camera, width, height in views:
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = ((2000, 1250) if view == 'desktop' else (900, 1200))
    scene.render.filepath = str(args.output / f'{view}-poster.png')
    bpy.ops.render.render(write_still=True)
print('BREEZE RENDER COMPLETE', flush=True)
