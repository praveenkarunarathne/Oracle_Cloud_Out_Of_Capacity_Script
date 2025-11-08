#!/bin/bash

# ===========================
# Oracle Cloud Bot Downloader
# ===========================

# Base URL
BASE_URL="https://raw.githubusercontent.com/praveenkarunarathne/Oracle_Cloud_Out_Of_Capacity_Script/refs/heads/main"

# Ask user for version
echo "Select the version to download:"
echo "1) Amd 1 RAM 1 CPU"
echo "2) Ampere 24 RAM 4 CPU"
read -p "Enter your choice (1 or 2): " choice

# Download common files
echo "Downloading .env and config..."
wget -q "${BASE_URL}/.env"
wget -q "${BASE_URL}/config"

# Download bot.py based on user choice
if [ "$choice" == "1" ]; then
    echo "Downloading AMD version..."
    wget -q "${BASE_URL}/Amd%201%20ram%201%20cpu/bot.py"
elif [ "$choice" == "2" ]; then
    echo "Downloading Ampere version..."
    wget -q "${BASE_URL}/Ampere%2024%20ram%204%20cpu/bot.py"
else
    echo "Invalid choice. Please run the script again and select 1 or 2."
    exit 1
fi

# Confirmation
echo "✅ Download completed successfully!"
