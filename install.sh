#!/bin/bash

VENV_NAME="venv"

# Create a virtual environment
python3 -m venv "$VENV_NAME"

# Activate the virtual environment
source "$VENV_NAME/bin/activate"

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    # Install the requirements
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping installation."
fi

# Deactivate the virtual environment
deactivate

echo "Virtual environment '$VENV_NAME' created and requirements installed."

echo "Install and run gembot.service"

ln -s /var/www/gembot/gembot.service /etc/systemd/system/gembot.service

systemctl daemon-reload
