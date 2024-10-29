import mysql.connector
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root(request : Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
    return templates.TemplateResponse("message.html", {"request": request, "message" : f"You're In! Save your user ID : {p_id}"})

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
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Added Pet!"})

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
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Pet Deleted :("})

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

    return templates.TemplateResponse("message.html", {"request": request, "message" : "Profile Edited Successfully!"})

@app.post("/user/delete")
async def user_delete(request : Request) :
    p_id = (await request.form())["p_id"]
    cursor = db.cursor()
    sql = f"DELETE FROM people WHERE p_id = %s"
    cursor.execute(sql, (p_id,))
    db.commit()
    cursor.close()
    return templates.TemplateResponse("message.html", {"request": request, "message" : "We're sorry to see you leave :("})


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
    sql_1 = "SELECT * FROM vets v JOIN\
           (SELECT e.vet_id FROM employments e WHERE e.c_id = %s) as alias\
           ON v.vet_id = alias.vet_id"
    
    cursor = db.cursor()
    cursor.execute(sql_1, (c_id,))
    clinic_vets = cursor.fetchall()

    # Fetching timings of the clinic
    sql_2 = "SELECT c_opensAt, c_closesAt FROM clinics WHERE c_id = %s"
    cursor.execute(sql_2, (c_id,))
    timings = cursor.fetchall()             # time is return in datetime.timedelta(seconds = ,) format
    cursor.close()
    
    ft = []
    for open_close_tuple in timings:
        # Extract both opening and closing times
        opens_at, closes_at = open_close_tuple
        
        # Convert opening time to HH:MM
        open_hours, open_remainder = divmod(opens_at.seconds, 3600)
        open_minutes = open_remainder // 60
        formatted_open_time = f"{open_hours:02}:{open_minutes:02}"
        
        # Convert closing time to HH:MM
        close_hours, close_remainder = divmod(closes_at.seconds, 3600)
        close_minutes = close_remainder // 60
        formatted_close_time = f"{close_hours:02}:{close_minutes:02}"
        
        # Append the pair of formatted times
        ft.append((formatted_open_time, formatted_close_time))


    return templates.TemplateResponse("vetsView.html", {"request": request, "pet_id" : pet_id, "c_id" : c_id, "ft" : ft, "clinic_vets" : clinic_vets})

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

    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully booked appointment!"})

def convert(datetime_ele) :
    # Convert closing time to HH:MM
    hours, rem = divmod(datetime_ele.seconds, 3600)
    mins = rem // 60
    formatted = f"{hours:02}:{mins:02}"
    return formatted

@app.get("/user/upcoming")
async def user_upcoming(request : Request, p_id) :
    cursor = db.cursor()

    # Step 1 : Find all pets of this user
    sql_1 = "(SELECT pet_id FROM pets WHERE p_id = %s) AS alias_1"

    # Step 2 : Find all appointments with these pet IDs
    sql_2 = "SELECT appt_id, c_id, vet_id, a.pet_id, appt_time, appt_reason FROM appointments a JOIN " + sql_1 + " ON a.pet_id = alias_1.pet_id"
    cursor.execute(sql_2, (p_id,))
    appts = cursor.fetchall()
    f_appts = []
    for appt in appts :
        new = list(appt)
        new[4] = convert(new[4])
        f_appts.append(new)

    return templates.TemplateResponse("userAppts.html", {"request": request, \
                                                        "appts" : f_appts,\
                                                        "p_id" : p_id})

@app.get("/user/cancel")
async def user_cancel(request : Request, appt_id) :
    cursor = db.cursor()
    sql = "DELETE FROM appointments WHERE appt_id = %s"
    cursor.execute(sql, (appt_id,))
    db.commit()
    cursor.close()
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Cancelled Appointment"})
