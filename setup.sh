#!/bin/sh
# Prepare a local Python environment; install missing Linux system modules.
set -eu

cd "$(dirname "$0")"
PYTHON=${PYTHON:-python3}
WITH_GUI=${WITH_GUI:-1}
INSTALL_DEV=${INSTALL_DEV:-0}

install_system() {
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "Missing system packages: $*" >&2
        echo "Automatic installation supports Debian/Ubuntu Linux." >&2
        echo "Ask the administrator to install equivalent Python packages." >&2
        exit 1
    fi
    echo "Installing missing system packages: $*"
    if [ "$(id -u)" -eq 0 ]; then
        apt-get install -y "$@"
    elif command -v sudo >/dev/null 2>&1; then
        echo "System installation requires administrator rights (sudo)."
        sudo apt-get install -y "$@"
    else
        echo "Administrator rights are required: apt-get install $*" >&2
        exit 1
    fi
}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    install_system python3 python3-venv
fi

if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "Python 3.10 or newer is required. Set PYTHON to its executable." >&2
    exit 1
fi

if ! "$PYTHON" -c 'import venv, ensurepip' >/dev/null 2>&1; then
    install_system python3-venv
fi

if [ "$WITH_GUI" = 1 ]; then
    if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
        install_system python3-tk
    fi
    if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
        echo "Tkinter is still missing from $PYTHON." >&2
        echo "Use the system Python: make PYTHON=/usr/bin/python3" >&2
        exit 1
    fi
fi

if [ ! -x .venv/bin/python ]; then
    "$PYTHON" -m venv .venv
fi

if ! .venv/bin/python -c \
    'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "Existing .venv is incompatible. Remove or rename it and retry." >&2
    exit 1
fi

if [ "$WITH_GUI" = 1 ]; then
    if ! .venv/bin/python -c 'import tkinter' >/dev/null 2>&1; then
        echo "Existing .venv lacks Tkinter. Recreate it with system Python." >&2
        exit 1
    fi
fi

# The game has no pip dependencies. Only development tools need a download.
if [ "$INSTALL_DEV" = 1 ]; then
    .venv/bin/python -m pip install -r requirements-dev.txt
fi

chmod +x snake
.venv/bin/python -m compileall -q \
    agent.py environment.py interpreter.py main.py display.py ui.py menu.py \
    benchmark.py clean.py
echo "Ready. Start the game with: make run"
if [ "$WITH_GUI" = 0 ]; then
    echo "Graphics were skipped. Use -visual off for headless runs."
elif [ "$(uname -s)" = Linux ] && [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    echo "No graphical desktop detected. Use -visual off in this session."
fi
