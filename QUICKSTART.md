# AskDB – Quick start

**First time?** See [SETUP.md](SETUP.md).

**Already set up?**

```bash
python code1.py
```

Open http://127.0.0.1:5000 and ask questions about your ogms data.

**Test API:**
```bash
curl -X POST http://localhost:5000/api -H "Content-Type: application/json" -d "{\"question\": \"How many records are in the first table?\"}"
```
