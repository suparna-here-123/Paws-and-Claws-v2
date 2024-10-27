import mysql.connector
from random import randint
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Creating database connection
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='SuparnaSQL',
    database='susu'
)

# Creating an instance of the App
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return {"message" : "Home page"}


# ------------------------ PERSON/ FUNCTIONS ------------------------
def generate_PID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT p_id FROM people LIMIT 1")
    last_pid = int(cursor.fetchall()[0][0][1:])
    new_pid = 'P' + str(last_pid - 1)
    return new_pid

# To render user registration form
@app.get("/user/add", response_class=HTMLResponse)
async def registration_form(request: Request):
    return templates.TemplateResponse("userForm.html", {"request": request})

# To add user to DB
@app.post("/user/add/")
async def user_add(request : Request):
    form_data = await request.form()
    p_id = generate_PID()

    data = list(value for key, value in form_data.items())
    data.insert(0, p_id)
    data = tuple(data)

    cursor = db.cursor()
    sql = "INSERT INTO PEOPLE VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # This p_id will be used for login later
    return {"Message" : "Successfully added user!", "User ID" : p_id}

# To render user login form
@app.get("/user/login", response_class=HTMLResponse)
async def registration_form(request: Request):
    return templates.TemplateResponse("userLogin.html", {"request": request})

# To verify user from DB
@app.post("/user/login")
async def user_login(request : Request) :
    form_data = await request.form()
    id, pwd = (value for key, value in form_data.items())

    cursor = db.cursor()
    sql = "SELECT p_password FROM people WHERE p_id = %s"
    cursor.execute(sql, (id,))
    res = cursor.fetchall()
    if res[0][0] == pwd :
        return {"message" : "user verification SUCCESSFUL!"}
    return {"message" : "user verification FAILED"}
    
# @app.get("/user/homepage/{p_id}", response_class=HTMLResponse)
# async def registration_form(request: Request):
#     return templates.TemplateResponse("userHomePage.html", {"request": request})

    