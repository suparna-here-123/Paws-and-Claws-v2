import mysql.connector
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
    cursor.execute(f"SELECT p_id FROM people order by p_id desc LIMIT 1")
    last_pid = int(cursor.fetchall()[0][0][1:])
    new_pid = 'P' + str(last_pid + 5)
    cursor.close()
    return new_pid

def generate_PetID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT pet_id FROM pets order by pet_id desc LIMIT 1")
    last_id = int(cursor.fetchall()[0][0][2:])
    new_id = 'PE' + str(last_id + 1)
    cursor.close()
    return new_id

def generate_ApptID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT appt_id FROM appointments order by appt_id desc LIMIT 1")
    last_id = int(cursor.fetchall()[0][0][1:])
    new_id = 'A' + str(last_id + 1)
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

    if res and res[0][0] == pwd :
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
async def render_pet_add(request: Request, p_id):
    return templates.TemplateResponse("petForm.html", {"request": request, "p_id" : p_id})

# To actually add pet
@app.post("/pet/add")
async def pet_add(request : Request) :
    pet_id = generate_PetID()
    form_data = await request.form()
    form_data = tuple(value for key, value in form_data.items())
    pets_data, vac_data = (pet_id,) + form_data[0 : 6], (pet_id,) + form_data[6:]

    cursor = db.cursor()
    pets_sql = 'INSERT INTO pets (pet_id, p_id, pet_name, pet_species, pet_breed, pet_gender, pet_dob) VALUES (%s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(pets_sql, pets_data)
    db.commit()

    vacs_sql = 'INSERT INTO vaccinations VALUES (%s, %s, %s)'
    cursor.execute(vacs_sql, vac_data)
    db.commit()

    cursor.close()
    return {"Message" : "Successfully added pet!"}

# To render all details of a user's pet
@app.get("/pet/view", response_class=HTMLResponse)
async def render_pet_add(request: Request, p_id):
    
    # Getting details of all pets of a user from PETS table
    cursor = db.cursor()
    sql = "SELECT * FROM pets WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    res = cursor.fetchall()

    return templates.TemplateResponse("petView.html", {"request": request,"res" : res})

# To view vaccination history of a pet (from user or vet side)
@app.get("/pet/vacc", response_class=HTMLResponse)
async def render_pet_vacc(request : Request, pet_id) :
    cursor = db.cursor()
    sql = "SELECT v.pet_id, p.pet_name, v.vac_name, v.vac_date\
           FROM vaccinations v JOIN pets p on v.pet_id = p.pet_id\
           WHERE v.pet_id = %s"
    
    cursor.execute(sql, (pet_id,))
    res = cursor.fetchall()

    return templates.TemplateResponse("petVaccs.html", {"request": request,"res" : res})

# To delete a PET from user side
@app.post("/pet/delete")
async def pet_delete(request : Request) :
    form_data = await request.form()
    data = tuple((value for key, value in form_data.items()))
    
    cursor = db.cursor()
    sql = 'DELETE FROM pets WHERE p_id = %s and pet_id = %s'
    cursor.execute(sql, data)
    db.commit()
    cursor.close()
    return {"Message" : "Successfully DELETED pet!"}

# To render user edit form
@app.get("/user/edit")
async def render_user_edit(request : Request, p_id) :
    return templates.TemplateResponse("userEdit.html", {"request": request, "p_id" : p_id})

# To actually edit the profile
@app.post("/user/edit")
async def user_edit(request : Request) :
    form_data = await request.form()
    form_data = tuple(value for key, value in form_data.items())
    p_id, data = form_data[0], form_data[1 : ]
    data += (p_id,)

    cursor = db.cursor()
    sql = "UPDATE people SET \
        p_firstName = %s, p_lastName = %s, p_phone = %s, \
        p_locality = %s, p_street = %s, p_houseNum = %s, p_password = %s\
        WHERE p_id = %s"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    return {"Message" : "Successfully updated user profile!"}

@app.post("/user/delete")
async def user_delete(request : Request) :
    p_id = (await request.form())["p_id"]
    cursor = db.cursor()
    sql = f"DELETE FROM people WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    db.commit()
    cursor.close()
    return {"Message" : "Successfully deleted profile!"}


# SHOULD DISPLAY AVAILABLE DOCTORS IN CLINICS NEARBY!!!
@app.get("/user/clinics")
async def render_user_clinics(request : Request, p_id, pet_id) :
    # Show all clinics in this locality
    sql = "SELECT * FROM clinics WHERE c_locality = \
           (SELECT p_locality FROM people WHERE p_id = %s)\
            ORDER BY c_opensAt"
    
    cursor = db.cursor()
    cursor.execute(sql, (p_id,))
    clinics = cursor.fetchall()
        
    return templates.TemplateResponse("userClinics.html", {"request": request, "p_id" : p_id, "pet_id" : pet_id, "clinics" : clinics})

@app.get("/user/vets")
async def render_user_vets(request : Request, c_id, pet_id) :
    sql = "SELECT * FROM vets v JOIN\
           (SELECT e.vet_id FROM employments e WHERE e.c_id = %s) as alias\
           ON v.vet_id = alias.vet_id"
    
    cursor = db.cursor()
    cursor.execute(sql, (c_id,))
    clinic_vets = cursor.fetchall()
    
    return templates.TemplateResponse("vetsView.html", {"request": request, "pet_id" : pet_id, "c_id" : c_id, "clinic_vets" : clinic_vets})

@app.post("/user/book")
async def user_book(request : Request, c_id, vet_id, pet_id) :
    form_data = await request.form()
    form_data = tuple(value for key, value in form_data.items())
    appt_id = generate_ApptID()

    data = (appt_id,) + (c_id, vet_id, pet_id) + form_data
    sql = 'INSERT INTO appointments VALUE (%s, %s, %s, %s, %s, %s)'
    cursor = db.cursor()
    cursor.execute(sql, data)
    db.commit()
    cursor.close()
    return {"Message" : "Successfully booked appointment"}
