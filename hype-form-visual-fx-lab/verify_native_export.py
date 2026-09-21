#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parent
html=(root/'index.html').read_text()
helper=(root/'mac_fast_export/native_export_helper.py').read_text()
checks={
'v35 version': 'v28.2.35' in html,
'engine selector': 'id="exportEngine"' in html,
'helper health': 'checkNativeHelperStatus' in html and '/health' in html,
'native path': 'async function exportNativeFastMp4' in html,
'locked frame path reused': re.search(r'exportNativeFastMp4[\s\S]*renderOfflineFrame\(',html) is not None,
'raw RGBA readback': 'getImageData(0,0,w,h)' in html,
'profiler phases': all(x in html for x in ['renderMs','readbackMs','feedMs','finalizeMs']),
'browser fallback': "if(engine==='browser')return exportVideo()" in html,
'helper missing auto fallback': "Protected Browser Exportへ自動Fallbackします。');return exportVideo()" in html,
'native failure auto fallback': "if(!succeeded){setStatus('Mac Fast Export failed. Protected Browser Exportへ切り替えます。');return exportVideo();}" in html,
'helper loopback bind': 'HOST = "127.0.0.1"' in helper,
'helper token auth': 'X-Hype-Token' in helper and 'TOKEN = secrets.token_urlsafe' in helper,
'helper validates order': 'Frame order mismatch' in helper,
'helper validates byte count': 'Invalid frame byte count' in helper,
'VideoToolbox preference': 'h264_videotoolbox' in helper,
'output owned by helper': 'Downloads" / "HYPE_FORM_EXPORTS' in helper,
'launcher present': (root/'START_MAC_FAST_EXPORT.command').exists(),
}
failed=[k for k,v in checks.items() if not v]
if failed:
    print('NATIVE EXPORT CONTRACT FAIL:',', '.join(failed));sys.exit(1)
print(f'NATIVE EXPORT CONTRACT PASS: {len(checks)} checks')