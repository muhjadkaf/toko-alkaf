#!/usr/bin/env bash
# Build Flutter Web dengan nomor build unik.
#
# Nomor build ditulis ke version.json dan dipakai theater sebagai query string
# pada asset (plate JPG + narasi MP3). Dengan begitu Opera/tablet/PC tidak
# perlu hard refresh saat build baru di-deploy.
set -euo pipefail

cd "$(dirname "$0")"
STAMP="$(date +%s)"
FLUTTER="${FLUTTER:-/home/mintbag/flutter-sdk/bin/flutter}"

"$FLUTTER" build web --release --no-wasm-dry-run --build-number="$STAMP"
echo "BUILD_NUMBER=$STAMP"
