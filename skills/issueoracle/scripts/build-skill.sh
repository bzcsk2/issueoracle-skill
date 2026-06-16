#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$SKILL_DIR/../../dist"
mkdir -p "$DIST_DIR"

BUILD_DIR=$(mktemp -d)
trap 'rm -rf "$BUILD_DIR"' EXIT

rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.venv' --exclude='node_modules' --exclude='dist' \
  "$SKILL_DIR/" "$BUILD_DIR/"

cd "$BUILD_DIR" && tar czf "$DIST_DIR/issueoracle.skill" .
echo "Built: $DIST_DIR/issueoracle.skill"
