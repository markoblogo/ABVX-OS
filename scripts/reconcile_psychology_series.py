"""Reconcile private Psychology Notebook IDs, editorial views and verified OS usage."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from abvx_harness.psychology_editorial import reconcile_series
from abvx_harness.harness import ValidationError

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--series-root',required=True,type=Path);p.add_argument('--write',action='store_true');a=p.parse_args()
 try:print(json.dumps(reconcile_series(ROOT,a.series_root,write=a.write),ensure_ascii=False,indent=2))
 except (ValidationError,OSError,ValueError,KeyError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
