create database if not exists susu;
use susu;

create table if not exists people (
p_id varchar(5) primary key,		-- PXXX
p_firstName varchar(25),
p_lastName varchar(25),
p_phone BIGINT unique,
p_locality varchar(25),
p_street varchar(25),
p_houseNum int,
p_password varchar(25));

create table if not exists vets (
vet_id varchar(5) primary key,		-- VXXX
vet_firstName varchar(25),
vet_lastName varchar(25),
vet_phone BIGINT unique,
vet_degree enum('Diploma', 'Bachelors', 'Doctor of Medicine'),
vet_experience int,
vet_fee int,
password varchar(25));

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
foreign key(p_id) references people(p_id) on delete cascade,
foreign key (vet_id) references vets(vet_id) on delete cascade); -- Upcoming appointment du ID

create table if not exists vaccinations (
vac_id varchar(5),				-- VAXX
pet_id varchar(5),
primary key (vac_id, pet_id),
vac_name enum("Rabies", "Flu", "S3P"),
vac_date date,
foreign key (pet_id) references pets(pet_id) on delete cascade);

create table if not exists clinics (
c_id varchar(5) primary key,	-- CXXX
c_locality varchar(25),
c_street varchar(25),
c_doorNum int,
c_opensAt time,
c_closesAt time,
admin_id varchar(25));

 
create table if not exists employments(
c_id varchar(5),				
vet_id varchar(5),
foreign key (c_id) references clinics(c_id) on delete cascade,
foreign key (vet_id) references vets(vet_id) on delete cascade,
primary key (c_id, vet_id));


create table if not exists appointments (
appt_id varchar(5) primary key,		-- AXXX
c_id varchar(5),
vet_id varchar(5),k
pet_id varchar(5),
appt_time time,
appt_reason enum("Emergency", "Vaccination", "Routine"),
appt_date date,
foreign key (c_id) references clinics(c_id) on delete cascade,
foreign key (vet_id) references vets(vet_id) on delete cascade,
foreign key(pet_id) references pets(pet_id) on delete cascade);

-- Procedure to order appointments by date and reason (Emergency > Vaccination > Routine)
create procedure GetAppts(IN in_CID varchar(5), IN in_VID varchar(5))
begin
 select * from appointments a
 where a.c_id = 'C300' and a.vet_id = 'V500'
 order by appt_date, appt_reason;
end //
delimiter ;

-- Function to return number of 