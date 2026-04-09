#!/usr/bin/env python3
"""
restore_graphivac_volume.py
────────────────────────────────────────────────────────────────────────────────
Restores the exact directory layout and file contents of the Docker volume
  si-mapper_graphivac_data
from a snapshot taken on 2026-03-30.

Works on Windows, macOS and Linux.  Requires only the Python 3 standard library.

Usage
─────
  # Write files to ./graphivac-data/ and stop (inspect before pushing):
  python restore_graphivac_volume.py

  # Also push the files into the live Docker volume:
  python restore_graphivac_volume.py --to-volume

  # Use a different volume name:
  python restore_graphivac_volume.py --to-volume --volume my_other_volume

  # Skip the local staging directory (write directly to the volume only):
  python restore_graphivac_volume.py --to-volume --no-local
"""

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Embedded file contents (base64-encoded to survive cross-platform copy/paste)
# Snapshot date: 2026-03-30
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_VOLUME = "si-mapper-2_graphivac_data"

# Binary Fressian databases ────────────────────────────────────────────────────

PROJECTS_DB_B64 = (
    "cAFpDFAtbUh6b0FTMUJYaHAEagxwcm9qZWN0LW5hbWVpBERlbW9qBm9yZy1pZGkGcHVibGljagpj"
    "cmVhdGVkLWF0WgAAAZ1AG2TBagtsYXN0LXVwZGF0ZVoAAAGdQBtkwQ=="
)

GRIDS_DB_B64 = (
    "cAJpDEctS3JRaWtBUERzTHAGagV0aXRsZWkIU3lzdGVtIEFqB2dyaWQtaWRpDEctS3JRaWtBUERz"
    "TGoKcHJvamVjdC1pZGkMUC1tSHpvQVMxQlhoagZvcmctaWRpBnB1YmxpY2oKY3JlYXRlZC1hdFoA"
    "AAGdQBuRmGoLbGFzdC11cGRhdGVaAAABnUAngKFpDEctV2dYN1ZXd0Ezb3AGagV0aXRsZWkIU3lz"
    "dGVtIEJqB2dyaWQtaWRpDEctV2dYN1ZXd0Ezb2oKcHJvamVjdC1pZGkMUC1tSHpvQVMxQlhoagZv"
    "cmctaWRpBnB1YmxpY2oKY3JlYXRlZC1hdFoAAAGdQBx252oLbGFzdC11cGRhdGVaAAABnUAcduc="
)

THEMES_DB_B64 = (
    "cAFpB2RlZmF1bHRwBWoGb3JnLWlkaQZwdWJsaWNqAmlkaQdkZWZhdWx0ag10aGVtZS12ZXJzaW9u"
    "ZAFqB3N5bWJvbHNwHmkScGlwZS52YWx2ZS50d28td2F5aRJwaXBlLnZhbHZlLnR3by13YXlpEGR1"
    "Y3Quc2Vuc29yLmZsb3dpEGR1Y3Quc2Vuc29yLmZsb3dpFHBpcGUudmFsdmUudGhyZWUtd2F5aRRw"
    "aXBlLnZhbHZlLnRocmVlLXdheWkUZHVjdC5zZW5zb3IuZW50aGFscHlpFGR1Y3Quc2Vuc29yLmVu"
    "dGhhbHB5aRRkdWN0LnNlbnNvci5odW1pZGl0eWkUZHVjdC5zZW5zb3IuaHVtaWRpdHlpFWR1Y3Qu"
    "c2Vuc29yLmxvdy1saW1pdGkVZHVjdC5zZW5zb3IubG93LWxpbWl0aRdyb29tLnNlbnNvci50ZW1w"
    "ZXJhdHVyZWkXcm9vbS5zZW5zb3IudGVtcGVyYXR1cmVpDnBpcGUuaGVhdC1wdW1waQ5waXBlLmhl"
    "YXQtcHVtcGkXcGlwZS5zZW5zb3IudGVtcGVyYXR1cmVpF3BpcGUuc2Vuc29yLnRlbXBlcmF0dXJl"
    "aQxzdGF0dXMuYWxhcm1pDHN0YXR1cy5hbGFybWkJYmFzaWMuZG90aQliYXNpYy5kb3RpEWR1Y3Qu"
    "Y29pbC5oZWF0aW5naRFkdWN0LmNvaWwuaGVhdGluZ2kIZHVjdC5mYW5pCGR1Y3QuZmFuaQtkdWN0"
    "LmZpbHRlcmkLZHVjdC5maWx0ZXJpC2Jhc2ljLmFycm93aQtiYXNpYy5hcnJvd2kXZHVjdC5zZW5z"
    "b3IudGVtcGVyYXR1cmVpF2R1Y3Quc2Vuc29yLnRlbXBlcmF0dXJlaRRkdWN0LnNlbnNvci5wcmVz"
    "c3VyZWkUZHVjdC5zZW5zb3IucHJlc3N1cmVpCXBpcGUucHVtcGkJcGlwZS5wdW1waRRyb29tLnNl"
    "bnNvci5odW1pZGl0eWkUcm9vbS5zZW5zb3IuaHVtaWRpdHlpDGVsZWN0cmljLnZmZGkMZWxlY3Ry"
    "aWMudmZkaQ1iYXNpYy51bmtub3duaQ1iYXNpYy51bmtub3duaQxzdGF0dXMuZmF1bHRpDHN0YXR1"
    "cy5mYXVsdGkLZHVjdC5kYW1wZXJpC2R1Y3QuZGFtcGVyaRFkdWN0LmNvaWwuY29vbGluZ2kRZHVj"
    "dC5jb2lsLmNvb2xpbmdpC3BpcGUuYm9pbGVyaQtwaXBlLmJvaWxlcmkSZHVjdC50aGVybWFsLXdo"
    "ZWVsaRJkdWN0LnRoZXJtYWwtd2hlZWxpG2R1Y3Quc2Vuc29yLnN0YXRpYy1wcmVzc3VyZWkbZHVj"
    "dC5zZW5zb3Iuc3RhdGljLXByZXNzdXJlaRZzdGF0dXMubWFudWFsLW92ZXJyaWRlaRZzdGF0dXMu"
    "bWFudWFsLW92ZXJyaWRlaQ9kdWN0Lmh1bWlkaWZpZXJpD2R1Y3QuaHVtaWRpZmllcmkVc3RhdHVz"
    "Lm91dC1vZi1zZXJ2aWNlaRVzdGF0dXMub3V0LW9mLXNlcnZpY2VqCnRoZW1lLW5hbWVpB0RlZmF1"
    "bHQ="
)

# EDN grid files (also base64-encoded to avoid multi-platform escaping issues) ─

GRID_A_EDN_B64 = (
    "ezp0aXRsZSAiU3lzdGVtIEEiLCA6Z3JpZC1pZCAiRy1LclFpa0FQRHNMIiwgOnByb2plY3QtaWQg"
    "IlAtbUh6b0FTMUJYaCIsIDpvcmctaWQgInB1YmxpYyIsIDpjcmVhdGVkLWF0ICNpbnN0ICIyMDI2"
    "LTAzLTMwVDE4OjU3OjIxLjgxNi0wMDowMCIsIDpsYXN0LXVwZGF0ZSAjaW5zdCAiMjAyNi0wMy0z"
    "MFQxOTowNToxMi40ODAtMDA6MDAiLCA6Y29tcHMgeyg6b2JqICJIQy0xIikgezpzeW1ib2wgImR1"
    "Y3QuY29pbC5oZWF0aW5nIiwgOm5hbWUgIkhDLTEiLCA6cG9zIFsyMyAxNF0sIDpjdXN0b20tZmll"
    "bGRzIHsiYmFjbmV0IiAie1wiMjUwMC5DTzlcIjoge1wib2JqZWN0LXR5cGVcIjogXCJsb29wXCIs"
    "IFwib2JqZWN0LWluc3RhbmNlXCI6IDksIFwibmFtZVwiOiBcIlBJRCBTRVJQLiBFTEVDLiAxQVwi"
    "LCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5pdFwiOiBcIlBlcmNlbnRhZ2VcIn0s"
    "IFwiMjUwMC5QRzE4XCI6IHtcIm5hbWVcIjogXCJDVFJMLlNFLjFBXCIsIFwib2JqZWN0LWluc3Rh"
    "bmNlXCI6IDE4LCBcInVuaXRcIjogXCJcIiwgXCJkZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBc"
    "Im9iamVjdC10eXBlXCI6IFwicHJvZ3JhbVwifSwgXCIyNTAwLkFWMjQ4XCI6IHtcIm9iamVjdC1p"
    "bnN0YW5jZVwiOiAyNDgsIFwibmFtZVwiOiBcIlBDLiBTRVJQLiBFTEVDLiAxQVwiLCBcImRldmlj"
    "ZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5pdFwiOiBcIkNlbHNpdXNcIiwgXCJvYmplY3QtdHlw"
    "ZVwiOiBcImFuYWxvZy12YWx1ZVwifSwgXCIyNTAwLkFPMTNcIjoge1wib2JqZWN0LXR5cGVcIjog"
    "XCJhbmFsb2ctb3V0cHV0XCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6"
    "IFwiUGVyY2VudGFnZVwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxMywgXCJuYW1lXCI6IFwiU0VS"
    "UC4gRUxFQ1QuIDFBXCJ9fSJ9fSwgKDpvYmogIk1JWC1EQU1QRVIiKSB7OnN5bWJvbCAiZHVjdC5k"
    "YW1wZXIiLCA6bmFtZSAiTUlYLURBTVBFUiIsIDpwb3MgWzEwIDEwXSwgOmN1c3RvbS1maWVsZHMg"
    "eyJiYWNuZXQiICJ7XCIyNTAwLlBHMTRcIjoge1wibmFtZVwiOiBcIkNUUkwgVk9MRVQgTUVMIDFB"
    "XCIsIFwib2JqZWN0LWluc3RhbmNlXCI6IDE0LCBcInVuaXRcIjogXCJcIiwgXCJkZXZpY2UtaWRl"
    "bnRpZmllclwiOiAyNTAwLCBcIm9iamVjdC10eXBlXCI6IFwicHJvZ3JhbVwifSwgXCIyNTAwLkFW"
    "MjUxXCI6IHtcIm9iamVjdC10eXBlXCI6IFwiYW5hbG9nLXZhbHVlXCIsIFwibmFtZVwiOiBcIlAu"
    "Qy4gVk9MRVQgTUVMIDFBXCIsIFwib2JqZWN0LWluc3RhbmNlXCI6IDI1MSwgXCJ1bml0XCI6IFwi"
    "Q2Vsc2l1c1wiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDB9LCBcIjI1MDAuQU8xMFwiOiB7"
    "XCJvYmplY3QtaW5zdGFuY2VcIjogMTAsIFwibmFtZVwiOiBcIlZPTEVUIE1FTC4gTm8uMUFcIiwg"
    "XCJkZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBcInVuaXRcIjogXCJQZXJjZW50YWdlXCIsIFwi"
    "b2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctb3V0cHV0XCJ9fSJ9fSwgKDpkdWN0ICJIRC0zIikgezpu"
    "MSB7OnBvcyBbNCAxNF19LCA6bjIgezpwb3MgWzI4IDE0XX19LCAoOm9iaiAiTUlYLVRFTVAtMSIp"
    "IHs6c3ltYm9sICJkdWN0LnNlbnNvci50ZW1wZXJhdHVyZSIsIDpuYW1lICJNSVgtVEVNUC0xIiwg"
    "OnBvcyBbMTUgMTRdLCA6Y3VzdG9tLWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQUkxNVwiOiB7"
    "XCJuYW1lXCI6IFwiVEVNUC4gTUVMLiBOby4xQVwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxNSwg"
    "XCJ1bml0XCI6IFwiQ2Vsc2l1c1wiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwib2Jq"
    "ZWN0LXR5cGVcIjogXCJhbmFsb2ctaW5wdXRcIn19In19LCAoOm9iaiAiUkVULUhVTS0xIikgezpz"
    "eW1ib2wgImR1Y3Quc2Vuc29yLmh1bWlkaXR5IiwgOm5hbWUgIlJFVC1IVU0tMSIsIDpwb3MgWzI1"
    "IDddLCA6Y3VzdG9tLWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQUkxNlwiOiB7XCJvYmplY3Qt"
    "dHlwZVwiOiBcImFuYWxvZy1pbnB1dFwiLCBcInVuaXRcIjogXCJQZXJjZW50YWdlXCIsIFwiZGV2"
    "aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJuYW1lXCI6IFwiSFVNSURJVEUgUkVULiBOby4xQVwi"
    "LCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxNn19In19LCAoOm9iaiAiRVZBQy1EQU1QRVIiKSB7OnN5"
    "bWJvbCAiZHVjdC5kYW1wZXIiLCA6bmFtZSAiRVZBQy1EQU1QRVIiLCA6cG9zIFsxMyAzXSwgOmN1"
    "c3RvbS1maWVsZHMgeyJiYWNuZXQiICJ7XCIyNTAwLkFPMTJcIjoge1wib2JqZWN0LXR5cGVcIjog"
    "XCJhbmFsb2ctb3V0cHV0XCIsIFwibmFtZVwiOiBcIlZPTEVUIEVWQUMuIE5vLjFFXCIsIFwib2Jq"
    "ZWN0LWluc3RhbmNlXCI6IDEyLCBcInVuaXRcIjogXCJQZXJjZW50YWdlXCIsIFwiZGV2aWNlLWlk"
    "ZW50aWZpZXJcIjogMjUwMH19In19LCAoOm9iaiAiVkZELTEtQSIpIHs6c3ltYm9sICJlbGVjdHJp"
    "Yy52ZmQiLCA6bmFtZSAiVkZELTEtQSIsIDpwb3MgWzIxIDE1XSwgOmN1c3RvbS1maWVsZHMgeyJi"
    "YWNuZXQiICJ7XCIyNTAwLkFPNlwiOiB7XCJvYmplY3QtdHlwZVwiOiBcImFuYWxvZy1vdXRwdXRc"
    "IiwgXCJ1bml0XCI6IFwiUGVyY2VudGFnZVwiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAs"
    "IFwibmFtZVwiOiBcIk1PRC4gRFJJVkUgQUxNIE5vLjFBXCIsIFwib2JqZWN0LWluc3RhbmNlXCI6"
    "IDZ9LCBcIjI1MDAuUEcxMlwiOiB7XCJvYmplY3QtaW5zdGFuY2VcIjogMTIsIFwibmFtZVwiOiBc"
    "IkNUUkwgTU9ELiBEUklWRSAxQVwiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5p"
    "dFwiOiBcIlwiLCBcIm9iamVjdC10eXBlXCI6IFwicHJvZ3JhbVwifX0ifX0sICg6b2JqICJSRVQt"
    "VEVNUC0xIikgezpzeW1ib2wgImR1Y3Quc2Vuc29yLnRlbXBlcmF0dXJlIiwgOm5hbWUgIlJFVC1U"
    "RU1QLTEiLCA6cG9zIFsyMyA3XSwgOmN1c3RvbS1maWVsZHMgeyJiYWNuZXQiICJ7XCIyNTAwLkFJ"
    "MTRcIjoge1wibmFtZVwiOiBcIlRFTVAuIFJFVE9VUiBOby4xQVwiLCBcIm9iamVjdC1pbnN0YW5j"
    "ZVwiOiAxNCwgXCJ1bml0XCI6IFwiQ2Vsc2l1c1wiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1"
    "MDAsIFwib2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctaW5wdXRcIn19In19LCAoOm9iaiAiMS1FIikg"
    "ezpzeW1ib2wgImR1Y3QuZmFuIiwgOm5hbWUgIjEtRSIsIDpwb3MgWzEwIDNdLCA6Y3VzdG9tLWZp"
    "ZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQlYxXCI6IHtcInVuaXRcIjogXCJPbi9PZmZcIiwgXCJk"
    "ZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBcIm5hbWVcIjogXCJTVEFUVVQgRElHIDFFXCIsIFwi"
    "b2JqZWN0LWluc3RhbmNlXCI6IDEsIFwib2JqZWN0LXR5cGVcIjogXCJiaW5hcnktdmFsdWVcIn0s"
    "IFwiMjUwMC5QRzE1XCI6IHtcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5pdFwiOiBc"
    "IlwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxNSwgXCJuYW1lXCI6IFwiQ1RSTCBFVkFDIE5vLjFF"
    "XCIsIFwib2JqZWN0LXR5cGVcIjogXCJwcm9ncmFtXCJ9LCBcIjI1MDAuQk8xMVwiOiB7XCJvYmpl"
    "Y3QtdHlwZVwiOiBcImJpbmFyeS1vdXRwdXRcIiwgXCJuYW1lXCI6IFwiQS9EIEVWQUMuIE5vLjFF"
    "XCIsIFwib2JqZWN0LWluc3RhbmNlXCI6IDExLCBcInVuaXRcIjogXCJPbi9PZmZcIiwgXCJkZXZp"
    "Y2UtaWRlbnRpZmllclwiOiAyNTAwfX0ifX0sICg6b2JqICJDQy0xIikgezpzeW1ib2wgImR1Y3Qu"
    "Y29pbC5jb29saW5nIiwgOm5hbWUgIkNDLTEiLCA6cG9zIFsxNyAxNF0sIDpjdXN0b20tZmllbGRz"
    "IHsiYmFjbmV0IiAie1wiMjUwMC5QRzEzXCI6IHtcIm9iamVjdC10eXBlXCI6IFwicHJvZ3JhbVwi"
    "LCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5pdFwiOiBcIlwiLCBcIm9iamVjdC1p"
    "bnN0YW5jZVwiOiAxMywgXCJuYW1lXCI6IFwiQ1RSTCBTRVJQIFJFRlIgMUFcIn0sIFwiMjUwMC5C"
    "VjE0N1wiOiB7XCJvYmplY3QtaW5zdGFuY2VcIjogMTQ3LCBcIm5hbWVcIjogXCJQRVJNLiBSRUYu"
    "IDFBXCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiT24vT2ZmXCIs"
    "IFwib2JqZWN0LXR5cGVcIjogXCJiaW5hcnktdmFsdWVcIn0sIFwiMjUwMC5BVjI1MlwiOiB7XCJ1"
    "bml0XCI6IFwiQ2Vsc2l1c1wiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwibmFtZVwi"
    "OiBcIlAuQy4gU0VSUCBSRUYgMUFcIiwgXCJvYmplY3QtaW5zdGFuY2VcIjogMjUyLCBcIm9iamVj"
    "dC10eXBlXCI6IFwiYW5hbG9nLXZhbHVlXCJ9LCBcIjI1MDAuQU85XCI6IHtcIm9iamVjdC1pbnN0"
    "YW5jZVwiOiA5LCBcIm5hbWVcIjogXCJTRVJQLiBSRUYuIE5vLjFBXCIsIFwiZGV2aWNlLWlkZW50"
    "aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiUGVyY2VudGFnZVwiLCBcIm9iamVjdC10eXBlXCI6"
    "IFwiYW5hbG9nLW91dHB1dFwifSwgXCIyNTAwLkJWMjUzXCI6IHtcIm5hbWVcIjogXCJQRVJNIFJF"
    "RlIgMUFcIiwgXCJvYmplY3QtaW5zdGFuY2VcIjogMjUzLCBcInVuaXRcIjogXCJPbi9PZmZcIiwg"
    "XCJkZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBcIm9iamVjdC10eXBlXCI6IFwiYmluYXJ5LXZh"
    "bHVlXCJ9fSJ9fSwgKDpvYmogIkZJTFRFUi0xIikgezpzeW1ib2wgImR1Y3QuZmlsdGVyIiwgOm5h"
    "bWUgIkZJTFRFUi0xIiwgOnBvcyBbMTMgMTRdfSwgKDpkdWN0ICJWRC0zIikgezpuMSB7OnBvcyBb"
    "OCAxOF19LCA6bjIgezpwb3MgWzggMTRdfX0sICg6ZHVjdCAiVkQtMiIpIHs6bjEgezpwb3MgWzEy"
    "IDEwXX0sIDpuMiB7OnBvcyBbMTIgMTRdfX0sICg6b2JqICJGUkVFWkVTVEFULTEiKSB7OnN5bWJv"
    "bCAiZHVjdC5zZW5zb3IubG93LWxpbWl0IiwgOm5hbWUgIkZSRUVaRVNUQVQtMSIsIDpwb3MgWzE5"
    "IDE0XSwgOmN1c3RvbS1maWVsZHMgeyJiYWNuZXQiICJ7XCIyNTAwLkJWMjU0XCI6IHtcImRldmlj"
    "ZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwidW5pdFwiOiBcIlwiLCBcIm9iamVjdC1pbnN0YW5jZVwi"
    "OiAyNTQsIFwibmFtZVwiOiBcIkFSUkVUIEJBUyBMSU0gR0VMIDFBXCIsIFwib2JqZWN0LXR5cGVc"
    "IjogXCJiaW5hcnktdmFsdWVcIn19In19LCAoOmR1Y3QgIlZELTEiKSB7Om4xIHs6cG9zIFs4IDdd"
    "fSwgOm4yIHs6cG9zIFs4IDEwXX19LCAoOmR1Y3QgIkhELTQiKSB7Om4xIHs6cG9zIFs0IDE4XX0s"
    "IDpuMiB7OnBvcyBbOCAxOF19fSwgKDpvYmogIlBBRi1VUFBFUi1EQU1QRVIiKSB7OnN5bWJvbCAi"
    "ZHVjdC5kYW1wZXIiLCA6bmFtZSAiUEFGLVVQUEVSLURBTVBFUiIsIDpwb3MgWzYgMTRdLCA6Y3Vz"
    "dG9tLWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQU80MlwiOiB7XCJ1bml0XCI6IFwiUGVyY2Vu"
    "dGFnZVwiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwibmFtZVwiOiBcIlZPTEVUIFAu"
    "QS5GLjFBXCIsIFwib2JqZWN0LWluc3RhbmNlXCI6IDQyLCBcIm9iamVjdC10eXBlXCI6IFwiYW5h"
    "bG9nLW91dHB1dFwifX0ifX0sICg6b2JqICJSQVYtREFNUEVSIikgezpzeW1ib2wgImR1Y3QuZGFt"
    "cGVyIiwgOm5hbWUgIlJBVi1EQU1QRVIiLCA6cG9zIFs2IDddfSwgKDpvYmogIlBBRi1MT1dFUi1E"
    "QU1QRVIiKSB7OnN5bWJvbCAiZHVjdC5kYW1wZXIiLCA6bmFtZSAiUEFGLUxPV0VSLURBTVBFUiIs"
    "IDpwb3MgWzYgMThdLCA6Y3VzdG9tLWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQU80MlwiOiB7"
    "XCJuYW1lXCI6IFwiVk9MRVQgUC5BLkYuMUFcIiwgXCJvYmplY3QtaW5zdGFuY2VcIjogNDIsIFwi"
    "dW5pdFwiOiBcIlBlcmNlbnRhZ2VcIiwgXCJkZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBcIm9i"
    "amVjdC10eXBlXCI6IFwiYW5hbG9nLW91dHB1dFwifX0ifX0sICg6b2JqICJWQUxWRS1DQy0xIikg"
    "ezpzeW1ib2wgInBpcGUudmFsdmUudGhyZWUtd2F5IiwgOm5hbWUgIlZBTFZFLUNDLTEiLCA6cG9z"
    "IFsxOCAxNF19LCAoOmR1Y3QgIkhELTEiKSB7Om4xIHs6cG9zIFs0IDNdfSwgOm4yIHs6cG9zIFsx"
    "NSAzXX19LCAoOm9iaiAiU1RBVElDLTEiKSB7OnN5bWJvbCAiZHVjdC5zZW5zb3Iuc3RhdGljLXBy"
    "ZXNzdXJlIiwgOm5hbWUgIlNUQVRJQy0xIiwgOnBvcyBbMjcgMTRdLCA6Y3VzdG9tLWZpZWxkcyB7"
    "ImJhY25ldCIgIntcIjI1MDAuQVYyNTBcIjoge1wiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwg"
    "XCJ1bml0XCI6IFwiaW5XQ1wiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAyNTAsIFwibmFtZVwiOiBc"
    "IlAuQy4gUFJFUyBTVEFUIDFBXCIsIFwib2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctdmFsdWVcIn0s"
    "IFwiMjUwMC5BSTE3XCI6IHtcIm9iamVjdC10eXBlXCI6IFwiYW5hbG9nLWlucHV0XCIsIFwidW5p"
    "dFwiOiBcImluV0NcIiwgXCJkZXZpY2UtaWRlbnRpZmllclwiOiAyNTAwLCBcIm5hbWVcIjogXCJQ"
    "UkVTLiBTVEFULiBOby4xQVwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxN319In19LCAoOm9iaiAi"
    "SFVNLTEiKSB7OnN5bWJvbCAiZHVjdC5odW1pZGlmaWVyIiwgOm5hbWUgIkhVTS0xIiwgOnBvcyBb"
    "MjUgMTRdLCA6Y3VzdG9tLWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuQUkxOVwiOiB7XCJvYmpl"
    "Y3QtdHlwZVwiOiBcImFuYWxvZy1pbnB1dFwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxOSwgXCJu"
    "YW1lXCI6IFwiU1RBVFVUIEhVTUkuIDFBXCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwg"
    "XCJ1bml0XCI6IFwiQW1wZXJlc1wifSwgXCIyNTAwLkFWMjQ5XCI6IHtcImRldmljZS1pZGVudGlm"
    "aWVyXCI6IDI1MDAsIFwidW5pdFwiOiBcIlBlcmNlbnRhZ2VcIiwgXCJvYmplY3QtaW5zdGFuY2Vc"
    "IjogMjQ5LCBcIm5hbWVcIjogXCJQLkMuIEhVTSAxQVwiLCBcIm9iamVjdC10eXBlXCI6IFwiYW5h"
    "bG9nLXZhbHVlXCJ9LCBcIjI1MDAuUEcxNlwiOiB7XCJvYmplY3QtdHlwZVwiOiBcInByb2dyYW1c"
    "IiwgXCJvYmplY3QtaW5zdGFuY2VcIjogMTYsIFwibmFtZVwiOiBcIkNUUkwgSFVNSUQuIDFBXCIs"
    "IFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiXCJ9LCBcIjI1MDAuQU80"
    "MFwiOiB7XCJvYmplY3QtaW5zdGFuY2VcIjogNDAsIFwibmFtZVwiOiBcIkhVTUlESUZJQ0FURVVS"
    "IDFBXCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiUGVyY2VudGFn"
    "ZVwiLCBcIm9iamVjdC10eXBlXCI6IFwiYW5hbG9nLW91dHB1dFwifX0ifX0sICg6b2JqICIxLUEi"
    "KSB7OnN5bWJvbCAiZHVjdC5mYW4iLCA6bmFtZSAiMS1BIiwgOnBvcyBbMjEgMTRdLCA6Y3VzdG9t"
    "LWZpZWxkcyB7ImJhY25ldCIgIntcIjI1MDAuUEcxMVwiOiB7XCJvYmplY3QtdHlwZVwiOiBcInBy"
    "b2dyYW1cIiwgXCJ1bml0XCI6IFwiXCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJu"
    "YW1lXCI6IFwiQ1RSTCBWRU5ULiBOby4xQVwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxMX0sIFwi"
    "MjUwMC5CVjI1NVwiOiB7XCJuYW1lXCI6IFwiU1RBVFVUIERJRyAxQVwiLCBcIm9iamVjdC1pbnN0"
    "YW5jZVwiOiAyNTUsIFwidW5pdFwiOiBcIk9uL09mZlwiLCBcImRldmljZS1pZGVudGlmaWVyXCI6"
    "IDI1MDAsIFwib2JqZWN0LXR5cGVcIjogXCJiaW5hcnktdmFsdWVcIn0sIFwiMjUwMC5CTzVcIjog"
    "e1widW5pdFwiOiBcIk9uL09mZlwiLCBcImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwibmFt"
    "ZVwiOiBcIkEvRCBWRU5ULiBBTE0uIE5vLjFBXCIsIFwib2JqZWN0LWluc3RhbmNlXCI6IDUsIFwi"
    "b2JqZWN0LXR5cGVcIjogXCJiaW5hcnktb3V0cHV0XCJ9LCBcIjI1MDAuQUk2XCI6IHtcIm9iamVj"
    "dC10eXBlXCI6IFwiYW5hbG9nLWlucHV0XCIsIFwidW5pdFwiOiBcIkFtcGVyZXNcIiwgXCJkZXZp"
    "Y2UtaWRlbnRpZmllclwiOiAyNTAwLCBcIm5hbWVcIjogXCJWSVRFU1NFIEFMSU0uIE5vLiAxQVwi"
    "LCBcIm9iamVjdC1pbnN0YW5jZVwiOiA2fSwgXCIyNTAwLkJJN1wiOiB7XCJuYW1lXCI6IFwiRkFV"
    "VEUgVkVOVC4gQUxJTS4gMUFcIiwgXCJvYmplY3QtaW5zdGFuY2VcIjogNywgXCJ1bml0XCI6IFwi"
    "XCIsIFwiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJvYmplY3QtdHlwZVwiOiBcImJpbmFy"
    "eS1pbnB1dFwifX0ifX0sICg6b2JqICJWRkQtMS1SIikgezpzeW1ib2wgImVsZWN0cmljLnZmZCIs"
    "IDpuYW1lICJWRkQtMS1SIiwgOnBvcyBbMTggOF0sIDpjdXN0b20tZmllbGRzIHsiYmFjbmV0IiAi"
    "e1wiMjUwMC5BTzhcIjoge1wib2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctb3V0cHV0XCIsIFwib2Jq"
    "ZWN0LWluc3RhbmNlXCI6IDgsIFwibmFtZVwiOiBcIk1PRC4gRFJJVkUgUkVUIE5vLjFSXCIsIFwi"
    "ZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiUGVyY2VudGFnZVwifX0ifX0s"
    "ICg6ZHVjdCAiSEQtMiIpIHs6bjEgezpwb3MgWzI2IDddfSwgOm4yIHs6cG9zIFs0IDddfX0sICg6"
    "ZHVjdCAiSEQtNSIpIHs6bjEgezpwb3MgWzggMTBdfSwgOm4yIHs6cG9zIFsxMiAxMF19fSwgKDpv"
    "YmogIkRQLTEiKSB7OnN5bWJvbCAiZHVjdC5zZW5zb3IucHJlc3N1cmUiLCA6bmFtZSAiRFAtMSIs"
    "IDpwb3MgWzEzIDE1XSwgOmN1c3RvbS1maWVsZHMgeyJiYWNuZXQiICJ7XCIyNTAwLkFJMThcIjog"
    "e1wib2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctaW5wdXRcIiwgXCJ1bml0XCI6IFwiaW5XQ1wiLCBc"
    "ImRldmljZS1pZGVudGlmaWVyXCI6IDI1MDAsIFwibmFtZVwiOiBcIlBSRVNTSU9OIEZJTFRSRSAx"
    "QVwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxOH19In19LCAoOm9iaiAiMS1SIikgezpzeW1ib2wg"
    "ImR1Y3QuZmFuIiwgOm5hbWUgIjEtUiIsIDpwb3MgWzE4IDddLCA6cm90IDE4MCwgOmN1c3RvbS1m"
    "aWVsZHMgeyJiYWNuZXQiICJ7XCIyNTAwLkJWMjU2XCI6IHtcIm9iamVjdC1pbnN0YW5jZVwiOiAy"
    "NTYsIFwibmFtZVwiOiBcIlNUQVRVVCBESUcgMVJcIiwgXCJkZXZpY2UtaWRlbnRpZmllclwiOiAy"
    "NTAwLCBcInVuaXRcIjogXCJPbi9PZmZcIiwgXCJvYmplY3QtdHlwZVwiOiBcImJpbmFyeS12YWx1"
    "ZVwifSwgXCIyNTAwLkFJMTFcIjoge1wiZGV2aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0"
    "XCI6IFwiQW1wZXJlc1wiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiAxMSwgXCJuYW1lXCI6IFwiVklU"
    "RVNTRSBSRVQuIE5vLjFBXCIsIFwib2JqZWN0LXR5cGVcIjogXCJhbmFsb2ctaW5wdXRcIn0sIFwi"
    "MjUwMC5CSTEyXCI6IHtcIm9iamVjdC10eXBlXCI6IFwiYmluYXJ5LWlucHV0XCIsIFwib2JqZWN0"
    "LWluc3RhbmNlXCI6IDEyLCBcIm5hbWVcIjogXCJGQVVURSBWRU5ULiBSRVQuIDFBXCIsIFwiZGV2"
    "aWNlLWlkZW50aWZpZXJcIjogMjUwMCwgXCJ1bml0XCI6IFwiXCJ9LCBcIjI1MDAuQk83XCI6IHtc"
    "Im9iamVjdC10eXBlXCI6IFwiYmluYXJ5LW91dHB1dFwiLCBcIm9iamVjdC1pbnN0YW5jZVwiOiA3"
    "LCBcIm5hbWVcIjogXCJBL0QgVkVOVC4gUkVULiBOby4xQVwiLCBcImRldmljZS1pZGVudGlmaWVy"
    "XCI6IDI1MDAsIFwidW5pdFwiOiBcIk9uL09mZlwifX0ifX19fQ=="
)

GRID_B_EDN_B64 = "ezp0aXRsZSAiU3lzdGVtIEIiLCA6Z3JpZC1pZCAiRy1XZ1g3Vld3QTNvIn0="

# ──────────────────────────────────────────────────────────────────────────────
# File manifest  {relative_path: (base64_string, is_binary)}
# ──────────────────────────────────────────────────────────────────────────────

FILES = {
    "orgs/public/themes.db": (THEMES_DB_B64, True),
    "orgs/public/projects/projects.db": (PROJECTS_DB_B64, True),
    "orgs/public/projects/P-mHzoAS1BXh/grids/grids.db": (GRIDS_DB_B64, True),
    "orgs/public/projects/P-mHzoAS1BXh/grids/G-KrQikAPDsL.edn": (GRID_A_EDN_B64, False),
    "orgs/public/projects/P-mHzoAS1BXh/grids/G-WgX7VWwA3o.edn": (GRID_B_EDN_B64, False),
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def write_files(root: Path) -> None:
    """Decode and write every file in the manifest under *root*."""
    for rel, (b64, is_binary) in FILES.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = base64.b64decode(b64)
        if is_binary:
            dest.write_bytes(raw)
        else:
            dest.write_text(raw.decode("utf-8"), encoding="utf-8")
        print(f"  wrote {dest}")


def docker_available() -> bool:
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def push_to_volume(staging: Path, volume: str) -> None:
    """
    Copy the staging directory tree into the Docker volume using a throwaway
    alpine container.  The container is removed automatically afterwards.
    """
    print(f"\nPushing files to Docker volume '{volume}' …")

    # Build a shell script that recreates the directory tree inside the container
    cmds = ["set -e"]
    for rel in FILES:
        cmds.append(f"mkdir -p /data/{Path(rel).parent.as_posix()}")
    cmds.append("echo 'directories created'")

    # We use `docker cp` which is simpler and doesn't require the image to be
    # writable; spin up a container first, copy, then remove.
    cid_result = subprocess.run(
        [
            "docker", "run", "--rm", "-d",
            "-v", f"{volume}:/data",
            "alpine", "sh", "-c", "sleep 600",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cid = cid_result.stdout.strip()
    print(f"  temporary container: {cid[:12]}")

    try:
        # Copy the entire staging tree into /data in one shot.
        # The trailing "/." tells docker cp to copy the *contents* of staging
        # rather than the directory itself, so files land at /data/orgs/…
        src = str(staging) + "/."
        subprocess.run(
            ["docker", "cp", src, f"{cid}:/data/"],
            check=True,
        )
        print(f"  copied all files into volume")
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  temporary container removed")

    print(f"\n✅  Volume '{volume}' restored successfully.")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore the si-mapper_graphivac_data Docker volume from the embedded snapshot."
    )
    parser.add_argument(
        "--to-volume",
        action="store_true",
        help="Push the restored files into the Docker volume after writing them locally.",
    )
    parser.add_argument(
        "--volume",
        default=DEFAULT_VOLUME,
        metavar="NAME",
        help=f"Docker volume name to restore into (default: {DEFAULT_VOLUME}).",
    )
    parser.add_argument(
        "--no-local",
        action="store_true",
        help="Do not keep a local copy; use a temporary directory that is cleaned up automatically. "
             "Implies --to-volume.",
    )
    parser.add_argument(
        "--output-dir",
        default="graphivac-data",
        metavar="DIR",
        help="Local directory to write the restored files into (default: ./graphivac-data).",
    )
    args = parser.parse_args()

    if args.no_local and not args.to_volume:
        args.to_volume = True  # --no-local implies we must push somewhere

    if args.to_volume and not docker_available():
        print("ERROR: Docker is not available or not running.", file=sys.stderr)
        sys.exit(1)

    if args.no_local:
        tmp = tempfile.mkdtemp(prefix="graphivac_restore_")
        staging = Path(tmp)
        try:
            print(f"Writing to temporary staging directory: {staging}")
            write_files(staging)
            push_to_volume(staging, args.volume)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        staging = Path(args.output_dir)
        print(f"Writing restored files to: {staging.resolve()}")
        write_files(staging)

        if args.to_volume:
            push_to_volume(staging, args.volume)
        else:
            print(
                f"\n✅  Files written to '{staging}'. "
                "Run with --to-volume to push them into Docker."
            )


if __name__ == "__main__":
    main()



