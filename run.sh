#!/bin/bash
# Simple run script for Yaypan Toymix Bot

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the bot
python bot.py
