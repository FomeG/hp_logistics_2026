#!/bin/bash

echo "Detecting Python..."

# Try python
if command -v python >/dev/null 2>&1; then
    PY="python"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
else
    echo "No Python installation detected!"
    echo "Please install Python before running this script."
    exit 1
fi

echo "Using interpreter: $PY"
echo "Upgrading pip..."
$PY -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "Failed to upgrade pip. Stopping..."
    exit 1
fi

echo "Pip upgraded successfully."
echo "------------------------------------"

echo "Installing root requirements..."
if [ -f "requirements.txt" ]; then
    $PY -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install root requirements"
        exit 1
    fi
    echo "Root requirements installed"
else
    echo "No requirements.txt found in root"
fi

echo
echo "Scanning modules folder..."

if [ ! -d "modules" ]; then
    echo "Modules folder not found"
    exit 0
fi

for m in modules/*; do
    if [ -d "$m" ] && [ -f "$m/requirements.txt" ]; then
        echo "Installing requirements for $m ..."
        $PY -m pip install -r "$m/requirements.txt"
        if [ $? -ne 0 ]; then
            echo "Failed to install requirements for $m"
        else
            echo "Completed $m"
        fi
    fi
done

echo
echo "All installations completed"
