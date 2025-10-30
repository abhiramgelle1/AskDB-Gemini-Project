#!/bin/bash

echo "🔄 LangChain Account Update Helper"
echo "===================================="
echo ""
echo "This will update your LangChain/LangSmith credentials"
echo ""

# Get new credentials
read -p "Enter your new LangSmith API Key: " new_api_key
read -p "Enter your project name (default: askdb_project): " new_project
new_project=${new_project:-askdb_project}

# Backup current .env
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up current .env file"
fi

# Update .env file with new credentials
if [ -f .env ]; then
    # Update existing .env
    sed -i.bak "s/^LANGCHAIN_API_KEY=.*/LANGCHAIN_API_KEY=$new_api_key/" .env
    sed -i.bak "s/^LANGCHAIN_PROJECT=.*/LANGCHAIN_PROJECT=$new_project/" .env
    rm .env.bak
    echo "✅ Updated existing .env file"
else
    # Create new .env
    cat > .env << ENVEOF
# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# LangChain/LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=$new_project
LANGCHAIN_API_KEY=$new_api_key
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Database Configuration
DB_TYPE=sqlite
DB_HOST=localhost
DB_PORT=3306
DB_NAME=askdb_local.db
DB_USER=
DB_PASSWORD=
ENVEOF
    echo "✅ Created new .env file"
fi

echo ""
echo "🎉 LangChain credentials updated!"
echo ""
echo "New settings:"
echo "  Project: $new_project"
echo "  API Key: ${new_api_key:0:20}..."
echo ""
echo "📝 Next steps:"
echo "  1. Restart your server: pkill -f 'python code1.py' && python code1.py"
echo "  2. Visit https://smith.langchain.com to view traces"
echo ""
