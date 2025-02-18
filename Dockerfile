FROM python:3.8\n\nWORKDIR /app\n\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\n\nCOPY . .\n\nEXPOSE 9009\n\nCMD ["python", "app.py"]
