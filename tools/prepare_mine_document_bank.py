"""Compatibility entry point for the reviewed physical document/device banks.

The old flat explanatory SVG excerpts are no longer selected. Source pins,
original pixels and alpha geometry belong to prepare_mine_object_bank.py.
"""
from pathlib import Path
import subprocess
import sys

TASKS=('T1-MM-A03','T6-MM-A02','T6-MM-A03')
def main():
    owner=Path(__file__).with_name('prepare_mine_object_bank.py')
    for task in TASKS:
        subprocess.run([sys.executable,'-X','utf8',str(owner),'--task',task],check=True)
if __name__=='__main__':main()
