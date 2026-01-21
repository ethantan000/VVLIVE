#!/bin/bash
# VVLIVE Installation Script

echo "Installing VVLIVE..."

# Backend
echo "Installing backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..

# Frontend
echo "Installing frontend..."
cd frontend
npm install
cd ..

echo "Installation complete!"
echo "Configure backend/.env before running"