import cProfile, os, pstats, sys
os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e01_controlled_sweeps as e, simp, taskspec
spec = e.track_specs("mbb_full")["center"][1][4]
S = simp.SIMP(taskspec.build(spec), simp.Settings(**e.SET))
pr = cProfile.Profile(); pr.enable(); r = S.optimize(); pr.disable()
print(f"iters={r['n_iter']} wall={r['wall_s']:.1f}s per-iter={1000*r['wall_s']/r['n_iter']:.0f}ms")
pstats.Stats(pr).sort_stats("tottime").print_stats(10)
