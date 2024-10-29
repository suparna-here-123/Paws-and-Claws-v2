import mysql.connector
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Creating database connection
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='30-nov-03',
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
    cursor.execute(f"SELECT p_id FROM people order by p_id asc LIMIT 1")
    last_pid = int(cursor.fetchall()[0][0][1:])
    new_pid = 'P' + str(last_pid - 1)
    cursor.close()
    return new_pid

def generate_PetID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT pet_id FROM pets order by p_id asc LIMIT 1")
    last_id = int(cursor.fetchall()[0][0][2:])
    new_id = 'PE' + str(last_id - 1)
    cursor.close()
    return new_id


# To render user registration form
@app.get("/user/add", response_class=HTMLResponse)
async def render_user_add(request: Request):
    return templates.TemplateResponse("userForm.html", {"request": request})

# To add user to DB
@app.post("/user/add")
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
async def render_user_login(request: Request):
    return templates.TemplateResponse("userLogin.html", {"request": request})

# To verify user from DB
@app.post("/user/login", response_class=RedirectResponse)
async def user_login(request : Request) :
    form_data = await request.form()
    p_id, pwd = (value for key, value in form_data.items())

    cursor = db.cursor()
    sql = "SELECT p_password FROM people WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    res = cursor.fetchall()
    cursor.close()

    if res[0][0] == pwd :
        # Default redirect makes POST request, changing status code match GET
        return RedirectResponse(url=f'/user/homepage/{p_id}', status_code=302)
    else :
        return templates.TemplateResponse("invalid.html", context={"request" : request})

# To view user/pet owner details and link to add pets
@app.get("/user/homepage/{p_id}", response_class=HTMLResponse)
async def user_homepage(request: Request, p_id:str):
    # Retrieving user details to display
    cursor = db.cursor()
    sql = f"SELECT * FROM people WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    res = cursor.fetchone()

    return templates.TemplateResponse("userHomePage.html", {"request": request, "res" : res})

# To render pet registration form for a user
@app.get("/pet/add", response_class=HTMLResponse)
async def render_pet_add(request: Request, p_id, endpoint):
    return templates.TemplateResponse("petForm.html", {"request": request, "p_id" : p_id, "endpoint" : endpoint})

# To actually add pet
@app.post("/pet/add")
async def pet_add(request : Request) :
    pet_id = generate_PetID()
    form_data = await request.form()
    data = (pet_id,) + tuple((value for key, value in form_data.items()))

    cursor = db.cursor()
    sql = 'INSERT INTO pets (pet_id, p_id, pet_name, pet_species, pet_breed, pet_gender, pet_dob) VALUES (%s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # Redirect to the vaccination form with the newly generated pet_id
    return RedirectResponse(url=f"/vaccination/add?pet_id={pet_id}&endpoint=/vaccination/add", status_code=302)

# To render all details of a user's pet
@app.get("/pet/view", response_class=HTMLResponse)
async def render_pet_add(request: Request, p_id):
    # Getting all pets of given user
    cursor = db.cursor()
    sql = "SELECT * FROM pets WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("petView.html", {"request": request,"res" : res})

# To delete a PET from user side
@app.get("/pet/delete")
async def pet_edit(request : Request, p_id, pet_id) :
    cursor = db.cursor()
    sql = 'DELETE FROM pets WHERE p_id = %s and pet_id = %s'
    cursor.execute(sql, (p_id, pet_id))
    db.commit()
    cursor.close()
    return {"Message" : "Successfully DELETED pet!"}

# -------------------------- VET FUNCTIONS --------------------------

def generate_VID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT v_id FROM vets order by v_id asc LIMIT 1")
    last_vid = int(cursor.fetchall()[0][0][1:])
    new_vid = 'V' + str(last_vid - 1)
    cursor.close()
    return new_vid

# To render vet registration form
@app.get("/vet/add", response_class=HTMLResponse)
async def render_vet_add(request: Request):
    return templates.TemplateResponse("vetForm.html", {"request": request})

# To add vet to DB
@app.post("/vet/add")
async def vet_add(request : Request):
    form_data = await request.form()
    v_id = generate_VID()
    data = list(value for key, value in form_data.items())
    data.insert(0, v_id)
    data = tuple(data)

    cursor = db.cursor()
    sql = "INSERT INTO vets VALUE (%s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # This v_id will be used for login later
    return {"Message" : "Successfully added vet!", "Vet ID" : v_id}

# To render vet login form
@app.get("/vet/login", response_class=HTMLResponse)
async def render_vet_login(request: Request):
    return templates.TemplateResponse("vetLogin.html", {"request": request})

# To verify vet from DB
@app.post("/vet/login", response_class=RedirectResponse)
async def vet_login(request : Request) :
    form_data = await request.form()
    print(form_data)
    v_id, pwd = (value for key, value in form_data.items())

    cursor = db.cursor()
    sql = "SELECT password FROM vets WHERE vet_id = %s"
    cursor.execute(sql, (v_id,))
    res = cursor.fetchall()
    cursor.close()

    if res[0][0] == pwd :
        # Default redirect makes POST request, changing status code match GET
        return RedirectResponse(url=f'/vet/homepage/{v_id}', status_code=302)
    else :
        return templates.TemplateResponse("invalid.html", context={"request" : request})
    
@app.get("/vet/homepage/{v_id}", response_class=HTMLResponse)
async def vet_homepage(request: Request, v_id: str):
    cursor = db.cursor()
    # Retrieve vet details
    cursor.execute("SELECT * FROM vets WHERE vet_id = %s", (v_id,))
    vet_details = cursor.fetchone()
    
    # Retrieve pets associated with the vet
    # cursor.execute("SELECT pet_id FROM pets WHERE vet_id = %s", (v_id,)) # need to see how to update the vet id to pets upon booking
    # pets = cursor.fetchall()
    
    cursor.close()
    return templates.TemplateResponse("vetHomePage.html", {"request": request, "res": vet_details}) #, "pets": pets


# -------------------------- VACCINATION FUNCTIONS --------------------------

# To render vaccination registration form
@app.get("/vaccination/add", response_class=HTMLResponse)
async def render_vac_add(request: Request, pet_id: str):
    return templates.TemplateResponse("vaccinationForm.html", {"request": request, "pet_id" : pet_id})

# To add vaccination to DB
@app.post("/vaccination/add")
async def vac_add(request : Request, pet_id: str):
    form_data = await request.form()
    data = list(value for key, value in form_data.items())
    data.insert(0, pet_id)
    data = tuple(data)

    cursor = db.cursor()
    sql = "INSERT INTO vaccinations VALUE (%s, %s, %s)"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # This p_id will be used for login later
    return {"Message" : "Successfully added vaccination!"}


# Clinic details will be added manually. From that, I need to source the admin id and check if the admin id is the same as the vet id.
# If yes, then the vet can view the clinic details. If not, then the vet cannot view the clinic details.
# All this should be displayed in the vet homepage itself.

# Also I think we need to add the admin id column to the clinics table in the database.

# now I need to start with apppointments. When an appointment is fixed, the vet id should be added to the pets table, so that I can view all the pets having appointments for the vet in the vet's homepage.
# In the vet's homepage, the vet should be able to see all the upcoming pets and their details, their vaccination history, the option to update their vaccination history, the option to book a new appointment, view clinic details if admin, change the time of existing appointments, and delete appointments.