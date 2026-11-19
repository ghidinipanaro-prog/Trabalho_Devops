import os
from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return {"app": "devoops", "ambiente": os.getenv("APP_ENV", "local")}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(port=8000)
