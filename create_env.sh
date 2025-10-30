#!/bin/bash
# Helper script to create .env file for AskDB

echo "🔧 AskDB - Google Cloud SQL Configuration Helper"
echo "================================================="
echo ""

# Prompt for Cloud SQL details
read -p "Enter your Cloud SQL Public IP: " DB_HOST
read -p "Enter your MySQL root password: " DB_PASSWORD
read -p "Enter your database name [default: crmdb]: " DB_NAME
DB_NAME=${DB_NAME:-crmdb}

# Create .env file
cat > .env << EOF
# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=askdb_project
LANGCHAIN_API_KEY=your_langchain_api_key_here

# Google Cloud SQL Configuration
DB_USER=root
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=3306
DB_NAME=$DB_NAME
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "📝 Configuration:"
echo "   DB_HOST: $DB_HOST"
echo "   DB_USER: root"
echo "   DB_NAME: $DB_NAME"
echo ""
echo "🧪 Testing connection..."
echo ""

# Test connection
python -c "from untitled0 import db; print('✅ Database connection successful!')" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your database is connected!"
    echo ""
    echo "▶️  Start the application with: python code1.py"
else
    echo ""
    echo "❌ Connection failed. Please check:"
    echo "   1. Your Cloud SQL Public IP is correct"
    echo "   2. Your IP address is in authorized networks"
    echo "   3. Your password is correct"
    echo "   4. The database '$DB_NAME' exists"
fi

