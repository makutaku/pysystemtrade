#!/bin/bash

# Function to check environment variables and issue warnings
check_env_var() {
  local var_name="$1"

  # Check if the variable is set
  if [ -z "${!var_name}" ]; then
    echo "Error: $var_name is not set. Please set this environment variable." >&2

    # Check if running as superuser and the variable is missing
    if [ "$(id -u)" -eq 0 ]; then
      echo "Notice: Running as superuser. If $var_name is set in your usual environment, consider using 'sudo -E' to preserve it." >&2
    fi

    exit 1
  fi
}

# Define the function to process each .env file
process_env_file() {
  local input_file="$1"
  local output_dir="$2"

  # Extract filename from the full path
  local filename=$(basename "$input_file")

  # Output file path
  local output_file="$output_dir/$filename"

  echo "Processing file: $input_file" >&2
  echo "Outputting to: $output_file" >&2

  # Interpolate variables into the output file from the specified environment file
  ./scripts/interpolate_vars.sh "$input_file" "$output_file" >&2
  if [ $? -ne 0 ]; then
    echo "Error: Failed to interpolate variables in $input_file" >&2
    exit 1
  fi

  echo "$output_file"
}

# Check for command-line argument and use it to override ENV if provided
if [ ! -z "$1" ]; then
  ENV="$1"
elif [ -z "$ENV" ]; then
  echo "Error: ENV variable is not set and no command-line argument provided."
  exit 1
fi

# Check both VAULT_ADDR and VAULT_TOKEN
check_env_var "VAULT_ADDR"
check_env_var "VAULT_TOKEN"

# Output directory for processed files
DEST_DIR_NAME="build"
DEST_DIR="./$DEST_DIR_NAME"

rm -rf "$DEST_DIR"
# Create output directory if it does not exist
mkdir -p "$DEST_DIR"

# Enable extended globbing
shopt -s extglob

# Copy all directories except the target directory
cp -r ./!(${DEST_DIR_NAME}) "${DEST_DIR}"

# Disable extended globbing
shopt -u extglob

echo "Build completed successfully"
