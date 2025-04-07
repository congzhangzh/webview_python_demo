#!/bin/bash

# --- Configuration ---
LIBS_DIR="libs"

# Define URLs (using jsDelivr CDN) and their target filenames
declare -A DEPS=(
  ["https://cdn.jsdelivr.net/npm/antd@5.12.8/dist/reset.css"]="reset.css"
  #["https://cdn.jsdelivr.net/npm/antd@5.12.8/dist/antd.min.css"]="antd.min.css" # Corrected CDN
  ["https://cdn.jsdelivr.net/npm/react@18.2.0/umd/react.development.js"]="react.development.js"
  ["https://cdn.jsdelivr.net/npm/react-dom@18.2.0/umd/react-dom.development.js"]="react-dom.development.js"
  ["https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js"]="dayjs.min.js"
  ["https://cdn.jsdelivr.net/npm/dayjs@1.11.10/locale/zh-cn.js"]="zh-cn.js"
  ["https://cdn.jsdelivr.net/npm/antd@5.12.8/dist/antd.min.js"]="antd.min.js"
  ["https://cdn.jsdelivr.net/npm/react@18.2.0/umd/react.production.min.js"]="react.production.min.js"
  ["https://cdn.jsdelivr.net/npm/react-dom@18.2.0/umd/react-dom.production.min.js"]="react-dom.production.min.js"
  ["https://cdn.jsdelivr.net/npm/@babel/standalone@7.23.0/babel.min.js"]="babel.min.js"
)

# --- Script Logic ---
echo "Starting download of offline dependencies (using jsDelivr)..."

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed or not in PATH. Please install curl."
    exit 1
fi

# Create the libraries directory
mkdir -p "$LIBS_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Could not create directory '$LIBS_DIR'."
    exit 1
fi
echo "Ensured library directory '$LIBS_DIR' exists."

# Function to download a single file
download_file() {
  local url="$1"
  local filename="$2"
  local target_path="$LIBS_DIR/$filename"

  echo -n "Downloading '$filename'... "
  # Use curl: -L follows redirects, -sS shows errors, --fail exits on server errors, -o output
  if curl -L -sS --fail -o "$target_path" "$url"; then
    echo "OK"
    return 0 # Indicate success
  else
    local exit_code=$?
    echo "FAILED! (curl exit code: $exit_code)"
    # Optionally remove potentially incomplete file
    rm -f "$target_path"
    return $exit_code # Indicate failure
  fi
}

# Iterate over dependencies and download them
error_count=0
for url in "${!DEPS[@]}"; do
  filename="${DEPS[$url]}"
  download_file "$url" "$filename"
  if [ $? -ne 0 ]; then
     ((error_count++))
     echo "Error encountered while downloading $filename from $url"
  fi
done

echo "-------------------------------------"
if [ $error_count -eq 0 ]; then
  echo "All dependencies downloaded successfully to '$LIBS_DIR/'."
  echo "You can now open 'index.html' in your browser."
  echo "-------------------------------------"
  exit 0
else
   echo "Warning: $error_count dependency download(s) failed. Please check the output above."
   echo "-------------------------------------"
   exit 1 # Exit with error if any download failed
fi
