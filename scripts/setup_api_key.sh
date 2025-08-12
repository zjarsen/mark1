#!/bin/bash

# Easy API Key Setup Script
echo "🔑 TwitterAPI.io API Key Setup"
echo "=============================="
echo ""

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "📝 Creating .env file from template..."
    cp ../.env.example ../.env
    echo "✅ .env file created!"
    echo ""
fi

echo "📋 Instructions:"
echo "1. Open the .env file in your editor"
echo "2. Replace 'your_api_key_here' with your actual TwitterAPI.io API key"
echo "3. Save the file"
echo "4. Run: source .env"
echo "5. Test with: ./test_api_setup.sh"
echo ""
echo "🔧 Quick commands:"
echo "   nano ../.env          # Edit with nano"
echo "   code ../.env          # Edit with VS Code"
echo "   vi ../.env            # Edit with vi"
echo ""

# Offer to edit now
read -p "🎯 Would you like to edit the .env file now? (y/n): " edit_now
if [[ $edit_now =~ ^[Yy]$ ]]; then
    if command -v nano &> /dev/null; then
        echo "Opening .env with nano..."
        nano ../.env
    elif command -v vi &> /dev/null; then
        echo "Opening .env with vi..."
        vi ../.env
    else
        echo "Please manually edit the .env file and add your API key"
    fi
    
    echo ""
    echo "📥 Now load the environment variable:"
    echo "source ../.env"
    echo ""
    echo "🧪 Then test:"
    echo "./test_api_setup.sh"
fi