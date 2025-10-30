# AskDB - Quick Start Guide

## 🎉 Your Application is Running!

Your AskDB chatbot is now live and ready to use!

### Server Status

- ✅ Database: SQLite (askdb_local.db)
- ✅ LLM: Google Gemini 1.5 Pro
- ✅ Server: Running on http://127.0.0.1:5000
- ✅ API Endpoint: http://127.0.0.1:5000/api

## How to Use

### Test the API with curl:

```bash
curl -X POST http://localhost:5000/api \
  -H "Content-Type: application/json" \
  -d '{"question": "How many students are there?"}'
```

### Example Questions to Try:

1. "How many students are there?"
2. "List all programs"
3. "Show me all payments with status pending"
4. "What is the total order value?"
5. "Show me all open cases"
6. "List students in the Data Science Bootcamp"

### Test with Python:

```python
import requests

response = requests.post(
    'http://localhost:5000/api',
    json={'question': 'How many students are there?'}
)
print(response.json())
```

## Database Information

### Current Setup:

- **Type**: SQLite (Local)
- **File**: `askdb_local.db`
- **Tables**: programs, contacts, student_programs, orders, payments, cases, tasks
- **Sample Data**: 3 students, 3 programs, 3 orders, 3 payments

### To Switch to Google Cloud SQL:

Edit your `.env` file:

```bash
DB_TYPE=mysql
DB_USER=root1
DB_PASSWORD=7377
DB_HOST=34.69.7.128
DB_PORT=3306
DB_NAME=crmdata
```

## Next Steps

1. **Test the API** - Try the example questions above
2. **Build a Frontend** - Connect your React/Vue/Angular app to the API
3. **Add More Data** - Populate the database with real data
4. **Deploy** - Use Google Cloud Run or similar for production

## Troubleshooting

### If server is not responding:

```bash
# Check if server is running
ps aux | grep "python code1.py"

# Restart server
pkill -f "python code1.py"
python code1.py
```

### View logs:

The server output is shown in your terminal. Press Ctrl+C to stop the server.

## API Documentation

See `API.md` for complete API reference and examples.

---

**Need help?** Check the other documentation files:

- `README.md` - Overview and features
- `SETUP.md` - Installation guide
- `TECHNICAL.md` - Technical details
- `API.md` - Complete API reference
