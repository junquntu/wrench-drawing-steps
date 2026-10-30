import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
os.makedirs('pv', exist_ok=True)
for t in [float(x) for x in sys.argv[1:]]:
    t0 = time.time()
    img = render.render(t)
    p = 'pv/t%06.1f.png' % t
    img.save(p)
    print(p, '%.2fs' % (time.time()-t0), flush=True)
