create database if not exists susu;
use susu;

create table if not exists people (
p_id varchar(5) primary key,		-- PXXX
p_firstName varchar(25),
p_lastName varchar(25),
p_phone BIGINT unique,
p_locality varchar(25),
p_street varchar(25),
p_houseNum int);

create table if not exists vets (
vet_id varchar(5) primary key,		-- VXXX
vet_firstName varchar(25),
vet_lastName varchar(25),
vet_phone BIGINT unique,
vet_degree enum('Diploma', 'Bachelors', 'Doctor of Medicine'),
vet_experience int,
vet_fee int);

create table if not exists pets (
pet_id varchar(5) primary key,	-- PEXXX
-- MAKE BELOW 2 FOREIGN KEY
p_id varchar(5),				
vet_id varchar(5),
pet_name varchar(25),
pet_species varchar(25),
pet_breed varchar(25),
pet_gender enum("M", "F"),
pet_dob date,
appt_id varchar(5),
foreign key(p_id) references people(p_id),
foreign key (vet_id) references vets(vet_id)); -- Upcoming appointment du ID

create table if not exists vaccinations (
vac_id varchar(5),				-- VAXX
pet_id varchar(5),
primary key (vac_id, pet_id),
vac_name enum("Rabies", "Flu", "S3P"),
vac_date date,
foreign key (pet_id) references pets(pet_id));

create table if not exists clinics (
c_id varchar(5) primary key,	-- CXXX
c_locality varchar(25),
c_street varchar(25),
c_doorNum int,
c_opensAt time,
c_closesAt time);

 
create table if not exists employments(
c_id varchar(5),				
vet_id varchar(5),
foreign key (c_id) references clinics(c_id),
foreign key (vet_id) references vets(vet_id),
primary key (c_id, vet_id));


create table if not exists appointments (
appt_id varchar(5) primary key,		-- AXXX
c_id varchar(5),
vet_id varchar(5),
pet_id varchar(5),
appt_time time,
appt_reason enum("Emergency", "Vaccination", "Routine"),
foreign key (c_id) references clinics(c_id),
foreign key (vet_id) references vets(vet_id),
foreign key(pet_id) references pets(pet_id));















