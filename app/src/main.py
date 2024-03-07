from fastapi import FastAPI
import uvicorn
# from methods import login, search
app = FastAPI()

@app.get('/')
def login():
    return login()

@app.get('/search')
def search():
    return search()

@app.post('/add_accounts')
def add_accounts():
    return 

if __name__ == "__main__":
