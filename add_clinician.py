import datetime
import json
import click
import pymongo
import os
import numbers
import re
from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId
from bson.code import Code
from passlib.hash import pbkdf2_sha512

client = MongoClient('localhost', 27017)

# Get the DB
db = client.sm

#REGEX for user INFO
mail_re =   re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
zip_re    =   re.compile(r'(^\d{5,5}$)')
phone_re    =   re.compile(r'(^\d{10,10}$)')

# Receive one of avaiable  in the list of showed options 

def valid_list_selection(intp,len):
    while any((not isinstance(m, numbers.Integral)) or (m not in range(1, len + 1)) for m in intp) :          
        print("Out of length limits , try again ! \n\n")
        inpu = raw_input("Enter your list of selections = \n\n")
        newls = list(int(e)-1 for e in inpu.split(","))
        intp = valid_list_selection(newls,len)
    return intp

def get_list_selection(max):
    inp = raw_input("Please enter your selection = \n\n")
    spi_list = list(int(e)-1 for e in inp.split(","))
    mylist = valid_list_selection(spi_list,max)
    return mylist

def get_selection(len):
    inp = int(raw_input("Please enter your selection = \n\n"))
    while not (isinstance(inp, numbers.Integral) and (inp in range(1, len + 1))):
        inp = int(raw_input("Out of length limits , try entry again ! \n\n"))
    return (inp - 1)

def username_entry():    
    usn = raw_input("Give username = \n")
    # Select USERS collection
    usnames = db.users.find_one({"username":usn})
    if not usnames:
        return str(usn)
    else:
        print("Duplicated entry! Please give another USERNAME  = ")
        username_entry()

def input_email():
    in_email = raw_input("Give user EMAIL = \n")
    valid_mail = re.match(mail_re, in_email)
    if valid_mail :
        #print(email)
        return str(in_email)
    else:
        print("Please give another email with valid format ! ")
        input_email()

def user_email_entry():
    usma = input_email()
    # Select USERS emails collection   
    users_same_email = db.users.find_one({"email":usma})
    if not users_same_email:
        return str(usma)
    else:
        print("Duplicated entry! Please give another EMAIL  = ")
        user_email_entry()

def zip_entry():
    entry = raw_input("Please provide a user ZIP with 5 digits formats ! \n")
    if re.match(zip_re,entry):
        return entry
    else:
        print("INVALID entry, please try again ! \n")
        zip_entry()

def phone_entry():
    entry = raw_input("telephone number = ")
    if re.match(phone_re,entry):
        return entry
    else:
        print("INVALID entry, please try again ! \n")
        phone_entry()

def choose_one_facility():
    all_facilities = list(db.facilities.find())
    fname_list = [f['name'] for f in all_facilities]
    fid_list = [f['_id'] for f in all_facilities]
    for f in fname_list:
        print("\t [[[ {} ]]] / \t Facility name = {} => \n ".format(fname_list.index(f)+1,f))    
    print("Chose your facility = \n")    
    in_choice = get_selection(len(all_facilities))
    choice =   fid_list[in_choice]
    choice_name =   fname_list[in_choice]
    print("You chosen the fact named :{} \n\n".format(choice_name))
    return choice

def choose_multi_facilities():
    all_facilities = list(db.facilities.find())
    fname_list = [f['name'] for f in all_facilities]     
    for f in fname_list:
        print("\t [[[ {} ]]] / \t Facility name = {} => \n ".format(fname_list.index(f)+1,f))    
    print("Chose multiple facilities = separate with COMMA  \n")
    # Entry a list of INT Numbers for selected options , separate with COMMA
    inp = raw_input()
    mlist = list(int(e) for e in inp.split(","))
    lichosen =[]
    fid_list = [f['_id'] for f in all_facilities]
    print("Multiple chosen facilities are  \n")
    for e in mlist:
        lichosen.append(fid_list[e])
        print("Facility # = {} , named : {} \n".format(e,fname_list[e-1]))
    return lichosen

#generate hexadecimal function
def gen_hex_salt():
    sa= os.urandom(32)
    return sa.encode('hex')

#generate hashed Password with PBKDF 2 algorithm
def gen_pbkdf_pass(sal,upass):
    gen_pass = pbkdf2_sha512.using(rounds=1000,salt = sal).hash(upass)
    return gen_pass

#Showing entry UI 
print("\n Adding new USER \n Giving user informations \n")
@click.command()

@click.option('--ufname', prompt='User first name ?',
              help='User first name ?')
@click.option('--ulname', prompt='User last  name ?',
              help='User last  name ?')              
@click.option('--uadr', prompt='User address ?',
              help='User address are ?')
@click.option('--ucity', prompt='User address city ?',
              help='User address city is = ?')
@click.option('--ustate', prompt='User address state is = ?',
              help='User address state is = ?')

def create_user(ufname,ulname,uadr,ucity,ustate):
    umail = user_email_entry()

    click.echo("Choice your USER NAME = \n")
    uuname = username_entry()

    uzip = zip_entry()
    
    utel1 = phone_entry()

    print("Please provide a user PHONE 2 with 10 digits formats ! \n")    
    utel2 = raw_input()

    print("Please provide a user FAX with 10 digits formats ! \n")
    ufax = raw_input()
    
    print("User role is one either followings number:\n1/Admin (system admin )\n2/Facility Admin (facility admin) \n3/Clinic Physician \n4/Clinic Technician \n5/Call Center Technician \n6/Call Center Supervisor \n") 

    try:
        role_choice = get_selection(6)
    except TypeError:
        role_choice = None

    fchoice = None
    chosen_facilities_list = None
    roles = ['Admin', 'Facility Admin', 'Clinic Physician', 'Clinic Technician', 'Call Center Technician', 'Call Center Supervisor']
    
    if role_choice:
        urole = roles[role_choice - 1]
    
    if urole in ['Facility Admin', 'Clinic Physician', 'Clinic Technician']:
        fchoice = choose_one_facility()
    elif urole in ['Call Center Technician', 'Call Center Supervisor']:
        chosen_facilities_list = choose_multi_facilities()

    
    #PASSWORD GEN
    # password = upass
    my_salt = gen_hex_salt()
    #print(str(my_salt))
    print("Give a new password  = ")
    password = str(raw_input())
    hashed_pass = gen_pbkdf_pass(my_salt,password).encode('hex')
    print("Your encrypted password  = ")
    print(hashed_pass)
    
    #create a new User
    my_user = {
        "inUseReportSetting":"",
        "inUseStudySetting":"",
        "hash": hashed_pass,
        "salt": my_salt,
        "firstName" : ufname,
        "lastName" : ulname,
        "username" : uuname,
        "email" : umail,
        "role" : urole,
        "contact":{
                "address" : uadr,
                "city" : ucity,
                "state" : ustate,
                "zip" : uzip,
                "phone1" : utel1,
                "phone2" : utel2,
                "fax" : ufax
            },
        "supportUsers" : [],
        "supportFacilities" : [],
        "isDisabled" : False,
        "canLogin" : True
    }

    if urole == 'Clinic Physician':
        #create a new Study setting
        study_sett = {"duration":1440,"preEventTime":30,"postEventTime":30,"bradycardiaThreshold":60,"tachycardiaThreshold":120,"pauseLevel":2.5,"pauseDetection":True,"afibDetection":True,"diagnosticLead":2,"__v":0}
        new_stu = db.studysettings.insert_one(study_sett).inserted_id
        
        # #create a new Report setting
        report_sett = {"reportDelivery":"Portal only","reportFrequency":"End of study","__v":0}
        new_rep = db.reportsettings.insert_one(report_sett).inserted_id

        my_user['studySetting'] = new_stu
        my_user['reportSetting'] = new_rep

    try:
        new_user = db.users.insert_one(my_user).inserted_id

        if fchoice is not None:
            db.facilities.update({'_id': fchoice}, {"$push": { "users" : new_user}},upsert=True)
            if urole=="Facility Admin":
                db.facilities.update({'_id': fchoice}, {"$set": { "adminUser" : new_user}})
        if chosen_facilities_list is not None :
            for f in chosen_facilities_list:
                db.users.update({'_id': new_user}, {"$push": { "supportFacilities" : f}})                
    except Exception as inst:
        print(type(inst))    # the exception instance
        print(inst.args)     # arguments stored in .args
        print(inst)          # overridden in exception subclasses

if __name__ == '__main__':
	create_user()
