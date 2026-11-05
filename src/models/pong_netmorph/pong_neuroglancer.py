#!/usr/bin/env python3
"""pong_neuroglancer.py: EM render -> Neuroglancer -> segmentation -> meshes for the Pong models.

Same acquisition/visualization pattern as xor_scnm/xor_scnm_acquisition_direct.py
(VSDA EM with GenerateSegmentation / GenerateMeshes, PrepareNeuroglancerDataset,
GetNeuroglancerDatasetURL), minus the experiments DB.

  -Model handwired   pong_handwired.build(sim)
  -Model g2          ModelLoad('johnjose-pong-g2') (Netmorph-grown; also -ModelName to override)
  -Model transplant  pong_transplant.build(sim, recipe, connectome)

Geometry exists in the sim right after build/ModelLoad, so no simulation is run.
Private stack only: port 8100.  -BBoxOnly prints the bounding box and voxel estimate.
"""
import os
import sys
import json
import time
import argparse

import nes_loop as NL
import BrainGenix.NES as NES

G2_MODEL = 'johnjose-pong-g2'


def parse(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('-Model', required=True, choices=['handwired', 'g2', 'transplant'])
    p.add_argument('-ModelName', default=G2_MODEL, help='g2: saved model name')
    p.add_argument('-Host', default='localhost')
    p.add_argument('-Port', default=8100, type=int)
    p.add_argument('-Recipe', default='transplant_recipe.json')
    p.add_argument('-Connectome', default='output/%s_connectome.json' % G2_MODEL)
    p.add_argument('-Resolution_um', default=0.5, type=float)
    p.add_argument('-SubdivideSize', default=1, type=int, help='divide the bounding box by this (as in xor_scnm)')
    p.add_argument('-NeuroglancerURLBase', default='http://localhost:8100')
    p.add_argument('-NoSegmentation', action='store_true')
    p.add_argument('-NoMeshes', action='store_true')
    p.add_argument('-NoNeuroglancer', action='store_true')
    p.add_argument('-BBoxOnly', action='store_true')
    p.add_argument('-Out', default='output')
    p.add_argument('-Seed', default=1, type=int)
    return p.parse_args(argv)


def main(argv=None):
    A = parse(argv)
    assert A.Port == 8100, 'this work uses the private stack on 8100 only'
    client = NL.connect(A.Host, A.Port)
    sim = NL.new_simulation(client, 'pong_ng_' + A.Model, seed=A.Seed)
    if A.Model == 'handwired':
        import pong_handwired as H
        H.build(sim)
    elif A.Model == 'g2':
        sim.ModelLoad(A.ModelName)
    else:
        import pong_transplant as T
        T.build(sim, json.load(open(A.Recipe)), json.load(open(A.Connectome)))
    print('model %s built/loaded, sim id %s' % (A.Model, sim.ID))

    bl, tr = sim.GetBoundingBox()
    sub = A.SubdivideSize
    bl = [c / sub for c in bl]
    tr = [c / sub for c in tr]
    ext = [t - b for b, t in zip(bl, tr)]
    vox = 1.0
    for e in ext:
        vox *= max(e, 0) / A.Resolution_um
    print('bbox_um', bl, tr, 'extent', ext, 'voxels %.3g' % vox)
    if A.BBoxOnly:
        return 0

    cfg = NES.VSDA.EM.Configuration()
    cfg.PixelResolution_nm = A.Resolution_um  # actually um
    cfg.ImageWidth_px = 512
    cfg.ImageHeight_px = 512
    cfg.SliceThickness_nm = 0.2  # actually um (as in xor_scnm)
    cfg.ScanRegionOverlap_percent = 0
    cfg.MicroscopeFOV_deg = 50
    cfg.NumPixelsPerVoxel_px = 1
    cfg.ImageNoiseIntensity = 130
    cfg.GuassianBlurSigma = 1.25
    cfg.BorderThickness_um = 0.3
    cfg.PostBlurNoisePasses = 1
    cfg.PreBlurNoisePasses = 0
    cfg.TearingEnabled = False
    cfg.RenderBorders = True
    cfg.GeneratePerlinNoise = True
    cfg.GenerateSegmentation = not A.NoSegmentation
    cfg.GenerateMeshes = not A.NoMeshes
    em = sim.AddVSDAEM(cfg)

    res = dict(model=A.Model, sim_id=sim.ID, resolution_um=A.Resolution_um, subdivide=sub,
               bbox_bl_um=bl, bbox_tr_um=tr, errors=[])
    t0 = time.time()
    try:
        em.DefineScanRegion(bl, tr, [0, 0, 0])
        em.QueueRenderOperation()
        em.WaitForRender()
    except Exception as e:
        res['errors'].append('render: %r' % e)
        print('ERROR render', repr(e))
    res['render_s'] = round(time.time() - t0, 1)
    print('render %.1f s' % res['render_s'])

    if not A.NoNeuroglancer and not res['errors']:
        t1 = time.time()
        try:
            em.PrepareNeuroglancerDataset()
            em.WaitForConversion()
            res['dataset'] = em.GetDatasetHandle()
            res['url'] = em.GetNeuroglancerDatasetURL(_ForceURLBase=A.NeuroglancerURLBase)
            print('Dataset Handle:', res['dataset'])
            print('URL:', res['url'])
        except Exception as e:
            res['errors'].append('neuroglancer/segmentation/meshes: %r' % e)
            print('ERROR neuroglancer', repr(e))
        res['neuroglancer_s'] = round(time.time() - t1, 1)
        print('neuroglancer conversion %.1f s' % res['neuroglancer_s'])
    os.makedirs(A.Out, exist_ok=True)
    json.dump(res, open(os.path.join(A.Out, 'ng_%s.json' % A.Model), 'w'), indent=1)
    print('RESULT', json.dumps(res))
    return 1 if res['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
