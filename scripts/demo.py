"""Three real local demonstrations, without public posts or paid inference."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from veritas.cli import main


def demo():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir',type=Path,default=Path('data/demo'))
    args=p.parse_args()
    root=args.data_dir.resolve()
    if (root/'jobs').exists() and any((root/'jobs').iterdir()):
        print('Demo jobs already exist. Use replay or choose a new data directory.')
        return 2
    base=['--data-dir',str(root)]
    if main(base+['init']): return 1
    for name in ('job_demo_sum_correct','job_demo_sum_incorrect','job_demo_inaccessible'):
        path=Path(__file__).resolve().parents[1]/'examples'/f'{name}.json'
        if main(base+['verify',str(path)]): return 1
        if main(base+['replay',name]): return 1
        if main(['verify-attestation',str(root/'jobs'/name/'attestation.json')]): return 1
    return 0


if __name__=='__main__':
    raise SystemExit(demo())
