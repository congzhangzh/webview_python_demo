#!/bin/bash

# --- Configuration ---
# Directory to save libraries
LIBS_DIR="libs"

# Define URLs and their target filenames
declare -A DEPS=(
  ["https://unpkg.com/antd@5.12.8/dist/reset.css"]="reset.css"
  ["https://unpkg.com/antd@5.12.8/dist/antd.min.css"]="antd.min.css"
  ["https://unpkg.com/react@18.2.0/umd/react.development.js"]="react.development.js"
  ["https://unpkg.com/react-dom@18.2.0/umd/react-dom.development.js"]="react-dom.development.js"
  ["https://unpkg.com/dayjs@1.11.10/dayjs.min.js"]="dayjs.min.js"
  ["https://unpkg.com/dayjs@1.11.10/locale/zh-cn.js"]="zh-cn.js"
  ["https://unpkg.com/antd@5.12.8/dist/antd.min.js"]="antd.min.js"
  ["https://unpkg.com/@babel/standalone@7.23.0/babel.min.js"]="babel.min.js"
)

# --- Script Logic ---
echo "Starting download of offline dependencies..."

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed or not in PATH. Please install curl."
    exit 1
fi

# Create the libraries directory if it doesn't exist
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
  # Use curl: -L follows redirects, -sS shows errors but is silent on success,
  # --fail exits with error on server errors (like 404), -o specifies output file
  if curl -L -sS --fail -o "$target_path" "$url"; then
    echo "OK"
  else
    echo "FAILED! (Error code: $?)"
    # Optional: Remove partially downloaded file
    # rm -f "$target_path"
    # Consider adding a flag to stop on first error if needed
    # exit 1
  fi
}

# Iterate over dependencies and download them
error_count=0
for url in "${!DEPS[@]}"; do
  filename="${DEPS[$url]}"
  # Store original exit status check logic temporarily if needed
  download_file "$url" "$filename"
  if [ $? -ne 0 ]; then
     ((error_count++))
  fi
done


# Check for CURL errors during the loop if download_file doesn't exit
# Re-check files existence might be needed if not exiting on failure
final_error=0
for url in "${!DEPS[@]}"; do
    filename="${DEPS[$url]}"
    target_path="$LIBS_DIR/$filename"
    if [ ! -f "$target_path" ] || [ ! -s "$target_path" ]; then # Check if file exists and is not empty
        echo "Error: File '$filename' was not downloaded successfully or is empty."
        final_error=1
    fi
done

if [ $final_error -eq 0 ]; then
  echo "-------------------------------------"
  echo "All dependencies downloaded successfully to '$LIBS_DIR/'."
  echo "You can now open 'index.html' in your browser."
  echo "-------------------------------------"
else
   echo "-------------------------------------"
   echo "Warning: Some dependencies failed to download. Please check the output above."
   echo "-------------------------------------"
   exit 1 # Exit with error if any download failed
fi

exit 0
