#!/usr/bin/env bash
# Downloads model.pkl and vectorizer.pkl from the wikimod GitHub Release.
# Skips download if files already exist.

set -euo pipefail

REPO="naeema-scopes/wikimod"
TAG="v0.1.0-model"
MODEL_DIR="$(dirname "$0")/../app/ml"

mkdir -p "$MODEL_DIR"

download_asset() {
    local filename="$1"
    local dest="$MODEL_DIR/$filename"

    if [ -f "$dest" ]; then
        echo "[download_model] $filename already exists, skipping."
        return 0
    fi

    echo "[download_model] Downloading $filename from GitHub Release $TAG..."
    local url="https://github.com/$REPO/releases/download/$TAG/$filename"
    curl -L -o "$dest" "$url" --fail --silent --show-error
    echo "[download_model] Downloaded $filename successfully."
}

download_asset "model.pkl"
download_asset "vectorizer.pkl"
download_asset "metrics.json"

echo "[download_model] All model artifacts are ready."
