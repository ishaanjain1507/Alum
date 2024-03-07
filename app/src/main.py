from fastapi import FastAPI
import uvicorn

from app.src.routers import dev_handler, user_handler
# from methods import login, search
app = FastAPI()

@app.get('/')
def login():
    return {}

@app.get('/search')
def search():
    return search()

@app.post('/add_accounts')
def add_accounts():
    return 

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)