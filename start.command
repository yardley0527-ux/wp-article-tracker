#!/bin/bash
cd "$(dirname "$0")"
echo "啟動 Dashboard 伺服器..."
open http://localhost:8765
python3 -m http.server 8765
