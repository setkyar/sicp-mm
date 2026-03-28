#!/bin/bash
# Translate all SICP XHTML files to Burmese
# Uses two Gemini models in parallel

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_DIR/source-en/html"
OUTPUT_DIR="$PROJECT_DIR/html"

MODEL1="google-antigravity/gemini-3-flash"
MODEL2="google-gemini-cli/gemini-3-flash-preview"

# Create output directory and copy static assets
mkdir -p "$OUTPUT_DIR"
cp -r "$SOURCE_DIR/css" "$OUTPUT_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/js" "$OUTPUT_DIR/" 2>/dev/null || true
cp -r "$SOURCE_DIR/fig" "$OUTPUT_DIR/" 2>/dev/null || true

# Files that don't need translation (just copy)
SKIP_FILES="Term-Index.xhtml Exercises.xhtml Figures.xhtml References.xhtml index.xhtml"

# Files for Model 1 (google-antigravity/gemini-3-flash)
# Front matter + Chapters 1-2 sections
MODEL1_FILES=(
    "Dedication.xhtml"
    "Foreword.xhtml"
    "Preface.xhtml"
    "Preface-1e.xhtml"
    "Acknowledgments.xhtml"
    "Chapter-1.xhtml"
    "1_002e1.xhtml"
    "1_002e2.xhtml"
    "1_002e3.xhtml"
    "Chapter-2.xhtml"
    "2_002e1.xhtml"
    "2_002e2.xhtml"
    "2_002e3.xhtml"
    "2_002e4.xhtml"
    "2_002e5.xhtml"
)

# Files for Model 2 (google-gemini-cli/gemini-3-flash-preview)
# Chapters 3-5 sections + back matter
MODEL2_FILES=(
    "Chapter-3.xhtml"
    "3_002e1.xhtml"
    "3_002e2.xhtml"
    "3_002e3.xhtml"
    "3_002e4.xhtml"
    "3_002e5.xhtml"
    "Chapter-4.xhtml"
    "4_002e1.xhtml"
    "4_002e2.xhtml"
    "4_002e3.xhtml"
    "4_002e4.xhtml"
    "Chapter-5.xhtml"
    "5_002e1.xhtml"
    "5_002e2.xhtml"
    "5_002e3.xhtml"
    "5_002e4.xhtml"
    "5_002e5.xhtml"
    "UTF.xhtml"
    "Colophon.xhtml"
)

# Copy files that don't need translation
for f in $SKIP_FILES; do
    if [ -f "$SOURCE_DIR/$f" ]; then
        echo "Copying $f (no translation needed)"
        cp "$SOURCE_DIR/$f" "$OUTPUT_DIR/$f"
    fi
done

# Function to translate a batch of files
translate_batch() {
    local model="$1"
    shift
    local files=("$@")
    
    for f in "${files[@]}"; do
        if [ -f "$OUTPUT_DIR/$f" ]; then
            echo "SKIP (already exists): $f"
            continue
        fi
        
        echo "=========================================="
        echo "Translating: $f with $model"
        echo "=========================================="
        
        python3 "$SCRIPT_DIR/translate_file.py" \
            "$SOURCE_DIR/$f" \
            "$OUTPUT_DIR/$f" \
            "$model"
        
        # Commit after each file
        cd "$PROJECT_DIR"
        git add "html/$f"
        git commit -m "Translate $f to Burmese (Myanmar)

Translated using $model
Source: sarabander/sicp" || true
        
        echo "Committed: $f"
        echo ""
    done
}

echo "Starting SICP Burmese translation..."
echo "Model 1: $MODEL1"
echo "Model 2: $MODEL2"
echo ""

# Run Model 1 files
echo "=== MODEL 1 BATCH ==="
translate_batch "$MODEL1" "${MODEL1_FILES[@]}"

# Run Model 2 files
echo "=== MODEL 2 BATCH ==="
translate_batch "$MODEL2" "${MODEL2_FILES[@]}"

echo ""
echo "=== Translation complete! ==="
echo "Output in: $OUTPUT_DIR"
