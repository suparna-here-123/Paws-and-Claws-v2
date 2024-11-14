import mysql.connector, os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import timedelta, date, datetime
from dotenv import load_dotenv

load_dotenv()

# Creating database connection
db = mysql.connector.connect(
    host='localhost',
    user=os.getenv('USER'),
    password=os.getenv('PASSWORD'),
    database='susu'
)

# Creating an instance of the App
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/")
async def root(request : Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ------------------------ PERSON/ FUNCTIONS ------------------------
def generate_PID() :
    cursor = db.cursor()
    cursor.execute(f"SELECT p_id FROM people order by p_id LIMIT 1")
    last_pid = int(cursor.fetchall()[0][0][1:])
    new_pid = 'P' + str(last_pid - 1)
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

    # Redirect to userHomePage here
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Added Pet!"})

'''
FOR SUYOG TO EDIT ---------------------------------------------
'''
#Need to show pet details that are in for an appointment today
@app.get("/pet/vet_view", response_class=HTMLResponse)
async def render_pet_vet_view(request: Request, vet_id):
    cursor=db.cursor()
    query = """
        SELECT p.pet_id, p.pet_name, p.pet_species, p.pet_breed, p.pet_gender, p.pet_dob, a.appt_id, a.appt_time, a.appt_reason, a.vet_id
        FROM pets p JOIN appointments a ON p.pet_id = a.pet_id
        WHERE a.vet_id = %s AND a.appt_date = curdate() AND a.appt_time > curtime()
    """
    cursor.execute(query, (vet_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("petVetView.html", {"request": request, "res" : res})

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

def convert(datetime_ele) :
    # Convert closing time to HH:MM
    hours, rem = divmod(datetime_ele.seconds, 3600)
    mins = rem // 60
    formatted = f"{hours:02}:{mins:02}"
    return formatted

@app.post("/user/book")
async def user_book(request : Request, c_id, vet_id, pet_id) :
    form_data = await request.form()
    form_data = tuple(value for key, value in form_data.items())
    form_time, form_date = form_data[0], form_data[-1]

    # First check if this appointment date and time exists
    cursor = db.cursor()
    check_sql = "SELECT * FROM appointments"
    cursor.execute(check_sql)
    all_appts = cursor.fetchall()

    for appt in all_appts :
        appt_c_id, appt_vet_id, appt_time, appt_date = appt[1], appt[2], str(appt[4])[0:5], str(appt[-1])

        # Preventing double booking of appointment for SAME(DOC, DATE, TIME)
        if vet_id == appt_vet_id and  form_time == appt_time and form_date == appt_date :
            return templates.TemplateResponse("message.html", {"request": request, "message" : "Doctor isn't free at this time :("})

    appt_id = generate_ApptID()
    data = (appt_id,) + (c_id, vet_id, pet_id) + form_data
    sql = 'INSERT INTO appointments VALUE (%s, %s, %s, %s, %s, %s, %s)'
    
    cursor.execute(sql, data)
    db.commit()
    cursor.close()

    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully booked appointment!"})

@app.get("/user/upcoming")
async def user_upcoming(request : Request, p_id) :
    cursor = db.cursor()

    # Step 1 : Find all pets of this user
    sql_1 = "(SELECT pet_id, pet_name FROM pets WHERE p_id = %s) AS alias_1"

    # Step 2 : Find all appointments with these pet IDs
    sql_2 = "SELECT appt_id, c_id, vet_id, a.pet_id, alias_1.pet_name, appt_time, appt_reason, appt_date FROM appointments a JOIN " + sql_1 + " ON a.pet_id = alias_1.pet_id where appt_date >= curdate() and appt_time >= curtime()"
    cursor.execute(sql_2, (p_id,))
    appts = cursor.fetchall()
    f_appts = []
    for appt in appts :
        new = list(appt)
        new[5] = convert(new[5])
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


@app.get("/vet/enroll", response_class = HTMLResponse)
async def vet_enroll(request : Request, v_id : str) :
    cursor = db.cursor()

    # Retrieving clinics where current vet does not work - with option to join
    sql = """SELECT * 
            FROM clinics c
            LEFT JOIN employments e ON c.c_id = e.c_id AND e.vet_id = %s
            WHERE e.c_id IS NULL;
            """
    
    # need to modify this query to show only the clinics where the vet is not already enrolled
    cursor.execute(sql, (v_id,))
    clinics = cursor.fetchall()
    
    return templates.TemplateResponse("vetEnroll.html", {"request": request, "clinics" : clinics, "vet_id" : v_id})

@app.post("/vet/enroll")
async def vet_enroll(request : Request) :
    form_data = await request.form()
    v_id, c_id = (value for key, value in form_data.items())

    cursor = db.cursor()
    sql = "INSERT INTO employments VALUE (%s, %s)"
    cursor.execute(sql, (c_id, v_id))
    db.commit()
    cursor.close()

    return templates.TemplateResponse("message.html", {"request": request, "message" : f"Successfully Enrolled! You now work in the clinic {c_id}"})

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
    WHERE employments.vet_id = %s
    """
    cursor.execute(clinic_sql, (vet_id,))
    clinic_results = cursor.fetchall()
    
    # Check if clinic IDs were found
    if not clinic_results:
        cursor.close()
        return templates.TemplateResponse("message.html", {"request": request, "message" : "You don't work in any clinic yet, please enroll in a clinic first."})

    clinics_info = [
        {
            "c_id": row[0],
            "opening_time": row[1],
            "closing_time": row[2]
        } for row in clinic_results
    ]

    # Fetch all pet IDs that were previously treated by the vet
    pet_sql = "SELECT pet_id FROM pets WHERE vet_id = %s"
    cursor.execute(pet_sql, (vet_id,))
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

    sql1= "select appt_time, appt_date, c_id from appointments"
    cursor.execute(sql1)
    res = cursor.fetchall()
    for i in res:
        # Given values
        time_delta = i[0]
        given_date = i[1]
        given_clinic = i[2]

        # Combine the date and time
        result_datetime = datetime.combine(given_date, datetime.min.time()) + time_delta

        # Extract date and time separately
        formatted_time = result_datetime.strftime("%H:%M")  # Time as "HH:MM"
        formatted_date = result_datetime.strftime("%Y-%m-%d")  # Date as "YYYY-MM-DD"
        if formatted_time == appt_time and formatted_date == appt_date and given_clinic == c_id:
            return templates.TemplateResponse("message.html", {"request": request, "message" : "Appointment time already booked! Please select a different time"})

    # Insert appointment data into the appointments table
    sql_insert = "INSERT INTO appointments VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql_insert, data)

    # # Update the vet_id in the pets table
    # sql_update = "UPDATE pets SET vet_id = %s WHERE pet_id = %s"
    # cursor.execute(sql_update, (vet_id, pet_id))

    # Commit the transaction and close the cursor
    db.commit()
    cursor.close()

    # Confirmation message
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Successfully Added the Appointment!"})

# To view the apoointments for that day
@app.get("/appointment/view", response_class=HTMLResponse)
async def view_appointments(request: Request, vet_id: str):
    cursor = db.cursor()
    sql = "SELECT * FROM appointments WHERE vet_id = %s and appt_date = curdate()"
    cursor.execute(sql, (vet_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("appointmentView.html", {"request": request, "res" : res, "vet_id" : vet_id})

# To finish an appointment
@app.post("/appointment/finish")
async def appt_finish(request: Request, appt_id: str, vet_id: str):
    cursor = db.cursor()
    sql_select = "SELECT pet_id FROM appointments WHERE appt_id = %s"
    cursor.execute(sql_select, (appt_id,))
    result = cursor.fetchone()
    if result:
        pet_id = result[0]
        sql_update = "UPDATE pets SET vet_id = %s WHERE pet_id = %s"
        cursor.execute(sql_update, (vet_id, pet_id))
        db.commit()
    # sql = "DELETE FROM appointments WHERE appt_id = %s"
    # cursor.execute(sql, (appt_id,))
    db.commit()
    cursor.close()
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Appointment Finished!"})

# To delete an appointment
@app.post("/appointment/delete")
async def appt_delete(request: Request, appt_id: str):
    cursor = db.cursor()
    sql = "DELETE FROM appointments WHERE appt_id = %s"
    cursor.execute(sql, (appt_id,))
    db.commit()
    cursor.close()
    return templates.TemplateResponse("message.html", {"request": request, "message" : "Appointment Deleted!"})

@app.get("/clinic/view", response_class=HTMLResponse)
async def view_clinic(request: Request, admin_id: str):
    cursor = db.cursor()
    sql = "SELECT * FROM clinics WHERE admin_id = %s"
    cursor.execute(sql, (admin_id,))
    res = cursor.fetchall()
    return templates.TemplateResponse("clinicView.html", {"request": request, "res" : res})
