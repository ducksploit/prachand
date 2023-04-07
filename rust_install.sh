#!/bin/bash

# Download the Rustup installation script
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o rustup.sh

# Make the script executable
chmod +x rustup.sh

# Run the installation script with default options
./rustup.sh -y

# Add the Rustup binary directory to your PATH
source $HOME/.cargo/env

# Remove the installation script
rm rustup.sh

 