#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

PKG=$(ls -1t dist/k7_*_amd64.deb 2>/dev/null | head -n1 || true)
BIN="dist/k7"

# Check if uninstall was requested
if [[ "${1:-}" == "uninstall" ]]; then
  echo "Uninstalling k7..."
  if dpkg -l k7 >/dev/null 2>&1; then
    echo "Removing k7 package..."
    dpkg -r k7
  elif [ -f "/usr/local/bin/k7" ]; then
    echo "Removing k7 binary from /usr/local/bin..."
    rm -f /usr/local/bin/k7
  else
    echo "k7 not found (not installed or already removed)"
  fi
  hash -r
  echo "k7 uninstalled"
  exit 0
fi

# ... existing install code ...
if [ -n "$PKG" ] && [ -f "$PKG" ]; then
  echo "Installing $PKG..."
  dpkg -i "$PKG" || { apt-get -y -f install && dpkg -i "$PKG"; }
  hash -r
  echo "Installed. Try: k7 --help"
elif [ -f "$BIN" ]; then
  echo "No .deb found; installing binary to /usr/local/bin..."
  install -m 0755 "$BIN" /usr/local/bin/k7
  hash -r
  echo "Installed. Try: k7 --help"
else
  echo "Nothing to install. Run src/k7/cli/build.sh first, or 'make install' from the root of the repo."
  exit 1
fi