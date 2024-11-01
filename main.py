import mysql.connector
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root(request : Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
async def render_pet_add(request: Request, id: str):
    # Getting all pets where the given id matches either p_id or vet_id
    cursor = db.cursor()
    sql = "SELECT * FROM pets WHERE p_id = %s OR vet_id = %s"
    cursor.execute(sql, (id, id))
    res = cursor.fetchall()
    cursor.close()
    return templates.TemplateResponse("petView.html", {"request": request, "res": res})

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
    cursor.execute(f"SELECT vet_id FROM vets order by vet_id asc LIMIT 1")
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
    sql = "INSERT INTO vets VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # This v_id will be used for login later
    return templates.TemplateResponse("message.html", {"request": request, "message" : f"You're In! Save your vet ID : {v_id}"})

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

    cursor.execute("SELECT pet_id FROM pets")
    pets = cursor.fetchall()

    # Fetch admin_id if the vet is also an admin
    sql_admin = "SELECT admin_id FROM clinics WHERE admin_id = %s"
    cursor.execute(sql_admin, (v_id,))
    admin_record = cursor.fetchone()
    admin_id = admin_record[0] if admin_record else None
    
    cursor.close()
    return templates.TemplateResponse("vetHomePage.html", {"request": request, "details": vet_details, "pets": pets, "admin_id": admin_id})


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
    sql1= "delete from vaccinations where pet_id = %s"
    cursor.execute(sql1, (pet_id,))
    sql = "INSERT INTO vaccinations VALUE (%s, %s, %s)"
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    # This p_id will be used for login later
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Added the Vaccination!"})


# Clinic details will be added manually. From that, I need to source the admin id and check if the admin id is the same as the vet id.
# If yes, then the vet can view the clinic details. If not, then the vet cannot view the clinic details.
# All this should be displayed in the vet homepage itself.

# Also I think we need to add the admin id column to the clinics table in the database.

# now I need to start with apppointments. When an appointment is fixed, the vet id should be added to the pets table, so that I can view all the pets having appointments for the vet in the vet's homepage.
# In the vet's homepage, the vet should be able to see all the upcoming pets and their details, their vaccination history, the option to update their vaccination history, the option to book a new appointment, view clinic details if admin, change the time of existing appointments, and delete appointments.

# -------------------------- APPOINTMENT FUNCTIONS --------------------------

# To generate appointment ID
def generate_APPTID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT appt_id FROM appointments order by appt_id asc LIMIT 1")
    last_aid = int(cursor.fetchall()[0][0][1:])
    new_aid = 'A' + str(last_aid - 1)
    cursor.close()
    return new_aid

# To render appointment form for a vet
@app.get("/appointment/add", response_class=HTMLResponse)
async def render_appt_add(request: Request, vet_id: str):
    cursor = db.cursor()

    # Fetch clinic IDs with their opening and closing times
    clinic_sql = """
    SELECT employments.c_id, clinics.c_opensAt, clinics.c_closesAt
    FROM employments 
    JOIN clinics ON employments.c_id = clinics.c_id 
    WHERE vet_id = %s
    """
    cursor.execute(clinic_sql, (vet_id,))
    clinic_results = cursor.fetchall()
    
    # Check if clinic IDs were found
    if not clinic_results:
        cursor.close()
        raise HTTPException(status_code=404, detail="No clinics found for this vet.")

    clinics_info = [
        {
            "c_id": row[0],
            "opening_time": row[1],
            "closing_time": row[2]
        } for row in clinic_results
    ]

    # Fetch all pet IDs without filtering by owner
    pet_sql = "SELECT pet_id FROM pets"
    cursor.execute(pet_sql)
    pets = cursor.fetchall()
    cursor.close()

    if not pets:
        raise HTTPException(status_code=404, detail="No pets found.")
    
    # Debugging information
    print("Fetched pet results:", pets)  # This should show all pet IDs as tuples in a list

    # Extract only pet IDs
    pet_results = [row[0] for row in pets]
    print("List of pet IDs:", pet_results)  # This should display all pet IDs in a list

    # Render the template with clinic info and pet IDs list
    return templates.TemplateResponse("appointmentForm.html", {
        "request": request,
        "vet_id": vet_id,
        "clinics_info": clinics_info,
        "pets": pets  # Pass list of pet IDs to the template
    })

# To add appointment to DB
@app.post("/appointment/add")
async def appt_add(request: Request, vet_id: str):
    # Get form data submitted by the vet, which includes pet_id, clinic_id, appointment time, reason, and date
    form_data = await request.form()
    appt_id = generate_APPTID()
    pet_id = form_data["pet_id"]
    c_id = form_data["c_id"]
    appt_time = form_data["appt_time"]
    appt_reason = form_data["appt_reason"]
    appt_date = form_data["appt_date"]

    # Prepare data tuple for insertion in the expected order of columns
    data = (appt_id, c_id, vet_id, pet_id, appt_time, appt_reason, appt_date)

    cursor = db.cursor()

    # Insert appointment data into the appointments table
    sql_insert = "INSERT INTO appointments VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql_insert, data)

    # Update the vet_id in the pets table
    sql_update = "UPDATE pets SET vet_id = %s WHERE pet_id = %s"
    cursor.execute(sql_update, (vet_id, pet_id))

    # Commit the transaction and close the cursor
    db.commit()
    cursor.close()

    # Confirmation message
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Added the Appointment!"})

# To view the apoointments for that day
@app.get("/appointment/view", response_class=HTMLResponse)
async def view_appointments(request: Request, vet_id: str):
    cursor = db.cursor()
    sql = "SELECT * FROM appointments WHERE vet_id = %s and appt_date = curdate() and appt_time > curtime()"
    cursor.execute(sql, (vet_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("appointmentView.html", {"request": request, "res" : res})

# To delete an appointment
@app.get("/appointment/delete")
async def appt_delete(request: Request, appt_id: str):
    cursor = db.cursor()
    sql = "DELETE FROM appointments WHERE appt_id = %s"
    cursor.execute(sql, (appt_id,))
    db.commit()
    cursor.close()
    return {"Message": "Successfully deleted appointment!"}

@app.get("/clinic/view", response_class=HTMLResponse)
async def view_clinic(request: Request, admin_id: str):
    cursor = db.cursor()
    sql = "SELECT * FROM clinics WHERE admin_id = %s"
    cursor.execute(sql, (admin_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("clinicView.html", {"request": request, "res" : res})
