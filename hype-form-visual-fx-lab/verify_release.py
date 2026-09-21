#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, tempfile
root=Path(__file__).resolve().parent
html=(root/'index.html').read_text()
# JS syntax
m=re.search(r'<script>(.*)</script>',html,re.S)
if not m: raise SystemExit('No application script found')
with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False) as f:
    f.write(m.group(1)); js=f.name
subprocess.run(['node','--check',js],check=True)
# Python helper syntax
subprocess.run([sys.executable,'-m','py_compile',str(root/'mac_fast_export/native_export_helper.py')],check=True)
subprocess.run([sys.executable,str(root/'verify_export_contract.py')],check=True)
subprocess.run([sys.executable,str(root/'verify_native_export.py')],check=True)
# Basic duplicate audit
ids=re.findall(r'\bid="([^"]+)"',html)
funcs=re.findall(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(',m.group(1))
if len(ids)!=len(set(ids)): raise SystemExit('Duplicate DOM IDs detected')
if len(funcs)!=len(set(funcs)): raise SystemExit('Duplicate named functions detected')
fx=re.findall(r"\{value:'([^']+)',label:",html)
print(f'STATIC AUDIT: DOM {len(ids)} unique / functions {len(funcs)} unique / FX definitions {len(fx)}')
print('RELEASE VERIFY PASS')