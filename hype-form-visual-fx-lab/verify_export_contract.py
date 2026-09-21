#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys

EXPECTED={
'sourceTimeForMappedTimeline':'3c86e2485a74f143639e749af2cc1c80ad312f36f47b097b73dcede19f78339a',
'resolveProjectSourceTime':'8009074957a1f54b4ffede46f8d8e291c1a16942b931ad69dfd08a3f5047f219',
'waitForVideoSeek':'887ca950630a688114e1a1a03faf05c5f8eab1319d9c5d6e83e0b57b74319ee7',
'waitForExactVideoFrame':'c9ea8fe036e125d27aabd81e724b39d56ee6ba86d828aad442135af74d30aa9b',
'renderProjectFrame':'ba9bc7dc82e13041e83b7580e17aa6d0e4cdff77eb156df0b642ce320f4b263b',
'renderOfflineFrame':'a56fe0aeddf32d3dddad5d7920721334b5f9b5f42f18d44ba7fd9cdce31bec75',
'validateExportPreflight':'915ab3a348d4d9abca4e97d05239e0a33cdfa3750c8e33301878657cd8a542c5',
'validateExportFrameAudit':'340273154313f852e807b2d6cc5bb403cd74453abb6d4d8b45835cffb4a95af5',
'exportMp4FramePerfect':'17ba6a5f482d03681cd9436e91d951524d54738c43b9f289e38890bb934a51ac',
'exportWebmFallback':'4be8477b45fc4021554c3599afd59866387182e881ea5301092c9348ab790fd7',
'exportVideo':'2375acc98a8c4662b3c1f339f66f29c87e31bf4e1c2fa064e0acca26943d95f9',
'fxPixelScale':'92f61ed9ff92fe59c5ee4ea88382d37bf7a731d36de90baf6caabaab912e0f2c',
'typographyPixelScale':'8cad3324eee5a9c614275fdfc8edcf5e12a1a29da8cb808121f408b8d0f77d9a',
}

def extract(src,name):
    m=re.search(r'\b(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src)
    if not m: raise RuntimeError(f'missing {name}')
    i=src.find('{',m.end()); depth=0; quote=None; esc=False; line=False; block=False; j=i
    while j<len(src):
        c=src[j]; n=src[j+1] if j+1<len(src) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False; j+=1
        elif quote:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: quote=None
        else:
            if c in "'\"`": quote=c
            elif c=='/' and n=='/': line=True; j+=1
            elif c=='/' and n=='*': block=True; j+=1
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0:return src[m.start():j+1]
        j+=1
    raise RuntimeError(f'unterminated {name}')

src=Path(__file__).with_name('index.html').read_text()
failed=[]
for name,expected in EXPECTED.items():
    got=hashlib.sha256(extract(src,name).encode()).hexdigest()
    if got!=expected: failed.append((name,got,expected))
if failed:
    for name,got,exp in failed: print(f'FAIL {name}\n  got {got}\n  exp {exp}')
    sys.exit(1)
print(f'EXPORT CONTRACT PASS: {len(EXPECTED)} protected functions unchanged')