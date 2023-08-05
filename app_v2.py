from flask import Flask,render_template, request,redirect,url_for,flash,get_flashed_messages,session,jsonify
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from flask_sqlalchemy import SQLAlchemy,event #using middle parties will decrease flexibility   
from os import path
from sqlalchemy import func,desc
from datetime import datetime,date,timedelta
from math import ceil,floor
from requests import post

app = Flask(__name__)
app.config['SECRET_KEY'] = 'FUSRODAH'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///theAllKnowing.sqlite"

db = SQLAlchemy(app,session_options={"autoflush": False, "autocommit": False, "expire_on_commit": False})
print(db.session.autoflush)
#should i store admin in the users too? we'd have to have a is_admin column to prevent 
#users from accessing admin url after loggin in
#imp check the datetime format only store what is necesssary like just the date -> a.strftime('%Y-%m-%d')
class USERS(db.Model):
    user_name = db.Column(db.String(30),primary_key=True)
    password = db.Column(db.String(50), nullable = False)
    wallet_balance = db.Column(db.Integer,server_default = '50')
    membership = db.Column(db.Integer,default = 0)
    membership_start = db.Column(db.Date)
    membership_end = db.Column(db.Date)
    parking_status = db.Column(db.Integer, server_default = '0')    
    vehicle_number = db.Column(db.String(10),nullable = False)
    

class ADMIN(db.Model):
    user_name=db.Column(db.String(30),primary_key=True)
    password = db.Column(db.String(50),nullable=False)




class TIME(db.Model):
    
    # parking_id = db.Column(db.Integer,primary_key=True)
    parking_id = db.Column(db.Integer,primary_key=True,autoincrement = True)
    date = db.Column(db.Date)#for groupby in daily sumary
    # time = db.Column(db.DateTime,server_default = datetime.today().strftime('%H:%M'))
    #need to convert guest_id to int, so it can be stored in the same column as 
    # a logged-in user and also auto increment
    parker = db.Column(db.String(20),server_default = 'guest')
    vehicle_number = db.Column(db.String(10))
    checkin_time = db.Column(db.DateTime)
    checkout_time = db.Column(db.DateTime)
    amount_paid = db.Column(db.Integer,server_default = '0')
    membership = db.Column(db.Integer,server_default = '0')
    # slots_available = db.Column(db.Integer,default = '10')
#imp - where shoud i store number of slotssdsf



# class GUEST(db.Model):
#     guest_id = db.Column(db.Integer, autoincrement=True,primary_key=True,server_default = '1000')
#     vehicle_number = db.Column(db.String(10),nullable=False)
#     #is vehicle number necessary? -> i think yes
#     checkin_time = db.Column(db.DateTime,server_default=str(datetime.now()))
#     checkout_time = db.Column(db.DateTime)
#     # amount_paid = db.Column(db.Integer,server_default = '0') # not necessary?

class DAILY_SUMMARY(db.Model):
    # __tablename__ = 'DAILY_SUMMARY'
    #we store the summary here
    date = db.Column(db.Date,primary_key = True)
    total_slots = db.Column(db.Integer,default = 10)
    available_slots = db.Column(db.Integer,server_default = '10')
    total_parkers = db.Column(db.Integer,server_default = '0')
    guest_hourly_price = db.Column(db.Integer,server_default = '10')
    user_hourly_price = db.Column(db.Integer,server_default = '7')
    total_amount = db.Column(db.Integer,server_default = '0')
    member_count = db.Column(db.Integer,server_default = '0')
    non_member_count = db.Column(db.Integer,server_default = '0')

class SLOTS(db.Model):
    # __tablename__ = 'DAILY_SUMMARY'
    #we store the summary here
    date = db.Column(db.Date,primary_key = True)
    total_slots = db.Column(db.Integer, server_default = '10')
    available_slots = db.Column(db.Integer,server_default = '10')

class INCOME(db.Model):
    id = db.Column(db.Integer,autoincrement = True,primary_key = True)
    total_income = db.Column(db.Integer,server_default = '0')

class SUBSCRIPTION(db.Model):
    duration_in_days = db.Column(db.Integer,primary_key=True)
    cost =db.Column(db.Integer)

@event.listens_for(SUBSCRIPTION.__table__,'after_create')
def insert_def(*args,**kwargs):
        print('orreeeee')
        # db.session.add(DAILY_SUMMARY(date))
        db.session.add(INCOME(total_income =0))
        db.session.add(DAILY_SUMMARY(date = datetime.today()))
        db.session.add(SLOTS(date = datetime.today()))
        db.session.add(ADMIN(user_name='admin',password = 'admin123'))
        db.session.add(SUBSCRIPTION(duration_in_days = 28,cost = 200))
        db.session.add(SUBSCRIPTION(duration_in_days = 84,cost = 580))
        db.session.add(SUBSCRIPTION(duration_in_days = 168,cost = 1100))
        db.session.add(SUBSCRIPTION(duration_in_days = 356,cost = 2000))
        db.session.commit()
        # GUEST.query.filter(GUEST.guest_id == 1000).delete()
        # db.session.commit()
db.create_all()
# if not path.exists('theAllKnowing.sqlite'):
#     db.create_all()
    
#     print('lmao')
#     db.session.add(DAILY_SUMMARY(date = datetime.today()))
#     #primary key with default value is not working, idk why
#     db.session.flush()
#     db.session.commit()
#     # db.session.add(SLOTS(date = datetime.today().strftime('%Y-%m-%d')))
#     db.session.add(SLOTS(date = datetime.today()))
#     db.session.flush()
#     db.session.commit()
    
def daily_summary():
    print('running batches')
    i_total_amount_paid = db.session.query(func.sum(TIME.amount_paid)).filter(TIME.date == date.today()).scalar()
    if i_total_amount_paid is None:
        i_total_amount_paid = 0
    i_member_count = db.session.query(func.count()).filter(TIME.membership == 1).scalar()
    i_nonmember_count = db.session.query(func.count()).filter(TIME.membership == 0).scalar()
    i_total_parkers = i_member_count + i_nonmember_count
    i_total_checkouts = TIME.query.filter_by(checkout_time = date.today()).count()
    i_available_slots = SLOTS.query.filter_by(date = date.today()).first().available_slots
    DAILY_SUMMARY.query.filter_by(date = date.today()).update({'available_slots' : i_available_slots,'total_parkers' :i_total_parkers,'total_amount' : i_total_amount_paid,'member_count' : i_member_count,'non_member_count' : i_member_count})
    db.session.commit()
    i_hourly_price = DAILY_SUMMARY.query.filter_by(date = date.today()).first().hourly_price
    new_day = DAILY_SUMMARY(available_slots = i_available_slots,hourly_price = i_hourly_price)
    
    db.session.add(new_day)
    
    db.session.commit()


def login_required(func):
    @wraps(func)
    #we should always declare a function or class after a decorator...
    def fun(*args,**kwargs):
        if "user" in session :
            return func(*args,**kwargs)
        return redirect(url_for('index'))
    return fun

def user_login_required(func):
    @wraps(func)
    #we should always declare a function or class after a decorator...
    def fun(*args,**kwargs):
        if "user" in session and session['usertype']=='user':
            return func(*args,**kwargs)
        return redirect(url_for('userlogin',next = request.url))
    return fun

def admin_login_required(func):
    @wraps(func)
    def fun(*args,**kwargs):
        if "user" in session and session['usertype']=='admin':
            return func(*args,**kwargs)
        return redirect(url_for('adminlogin',next = request.url))
    return fun

def llogin_user(user):
    session['user']=user.user_name
    # session['user_data'] = {column.name: getattr(user, column.name) for column in user.__table__.columns}
    session['usertype']='user'
    session['is_authenticated']=1
def llogin_admin(admin):
    session['user']=admin.user_name
    # session['user_data'] = {column.name: getattr(admin, column.name) for column in admin.__table__.columns}
    session['usertype']='admin'
    session['is_authenticated']=1

def llogout_user():
    session.clear()
    session['is_authenticated']=0
    


def gohome():
    return redirect(url_for('index'))

#to do : exception and invalid input handling -> not done
# set path for invalid get endpoints -> done
@app.route('/')
def index():
    msg = get_flashed_messages()
    # slots = post('http://localhost:5000/fetchAvailableSlots').text
    slots = SLOTS.query.filter_by(date = date.today()).first().available_slots

    if 'is_authenticated' in session and session['is_authenticated'] == 1:
        if session['usertype']== 'user':
            return redirect(url_for('dashboard'))
        return redirect(url_for('adminDashboard'))
    if msg:

        return render_template('index.html',message = msg[0],slots = slots)
    return render_template('index.html',slots = slots)

@app.route('/usercheckin',methods=['POST'])
def usercheckin():
    u_info = request.form   
    user_db = USERS.query.filter_by(user_name = u_info['username']).first()
    slots = SLOTS.query.filter_by(date = date.today() ).first()
    slots.available_slots -= 1
    if user_db and u_info['password'] == user_db.password and slots.available_slots != 0:
        if user_db.parking_status == 1:
            flash('already_checkedin')
            return gohome()
        print('good checkin')
        flash(f'Hey there {user_db.user_name[0]}, your check-in time is {datetime.now().hour}:{datetime.now().minute}')
        
        #to-do include membership condition-> should i just do it myself?, in backend we can just
        #verify the condition at backend and calculated the price
        checkin = TIME(parker = user_db.user_name,checkin_time = datetime.now(),date = date.today(),vehicle_number = user_db.vehicle_number)
        user_db.parking_status = 1
        db.session.add(checkin)
        db.session.commit()
        return gohome()
    print('bad checkin')
    flash('login_failed')  
    #do some math here
    # return redirect(url_for('index'))
    return gohome()


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        if 'user' in session :
            return redirect(url_for('dashboard'))
        else:
            user_inf = request.form
            exist = USERS.query.filter_by(user_name = user_inf['username']).all()
            print(exist)
            if len(exist) >0:
                flash('user_exists')
                return redirect(url_for('signup'))
            #do some math here
            to_insert = USERS(user_name = user_inf['username'],password = user_inf['password'],vehicle_number = user_inf['vehiclenumber'])
            db.session.add(to_insert)
            db.session.commit()
            llogin_user(to_insert)
            return redirect(url_for('dashboard'))
    else:
        if 'user' in session :
            return redirect(url_for('dashboard'))
        
        msg = get_flashed_messages()
        if len(msg) == 0:
            msg =''
        else:
            msg = msg[0]
        
        return render_template('usersignup.html',msg=msg)
    

@app.route('/userlogin',methods=['POST','GET'])
def userlogin():
    if request.method == 'POST':
        # print('user' in session and session['usertype'] == 'user')
        user_inf = request.form
        user_db = USERS.query.filter_by(user_name = user_inf['username']).first()
        if user_db and user_inf['password'] == user_db.password:
            llogin_user(user_db)
            return redirect(url_for('dashboard'))
        flash('login_failed')
        return redirect(url_for('userlogin'))
    else:
        # print('user' in session and session['usertype'] == 'user')
        if 'user' in session and session['usertype'] == 'user':
           return redirect(url_for('dashboard'))
        return render_template('userlogin.html',message = get_flashed_messages())

@app.route('/dashboard')
@user_login_required
def dashboard():
    to_show = USERS.query.filter_by(user_name = session['user']).first()
    to_show.password = "you cant see this lol"
    membership_status = to_show.membership
    slots = SLOTS.query.filter_by(date = datetime.today().strftime('%Y-%m-%d')).first().available_slots
    costs = SUBSCRIPTION.query.all()
    dic ={}
    for row in costs:
        dic[row.duration_in_days] = row.cost
        # print(dic[row.duration_in_days])
    # costs = {i:j for i,j in costs}
        
    return render_template('user_dashboard.html',slots = slots,user_data = to_show,flashes = get_flashed_messages(),costs = dic)
#to do -> display content -> don
    #flashes will be a list of strings, need to show them in appropriately using js

'''
user_dashboard - 
set wallet balance
buy membership -> through wallet-> handle math like negative balances etc..
see previous parking info
reserve spot
should we generate a parking id?????
'''
########################################################
#user  functions
@app.route('/addToWallet',methods=['POST'])
@user_login_required
def addtowallet():
    print(f'add {request.form["addtowallet"]} to wallet')
    #input name in form = addtowallet
    user = USERS.query.filter_by(user_name = session['user']).first()
    user.wallet_balance+=int(request.form['addtowallet'])
    
    db.session.commit()
    flash('wallet_added')
    return redirect(url_for('dashboard'))



@app.route('/reserve',methods=['POST'])
@user_login_required
def reserve():
    #users will only see the reserve button if there are spots available...
    # db.session.execute(USERS.__table__.update().where(USERS.user_name == session['user']).values(parking_status=True))
    #imp
    USERS.query.filter_by(user_name = session['user']).update({'parking_status':True})
    
    checkin= TIME(parking_id = session['user'],checkin_time= request.form['checkintime'])
    db.session.add(checkin)
    db.session.commit()
    flash('spot_reserved')
    return redirect(url_for('dashboard'))

@app.route('/subscribe',methods=['POST'])
@user_login_required
def subscribe():
    #to handle, add the durratioon of membership to start date
    if request.method == 'POST':
        print("&&&&&&&&&&&&&&&&&&&"+request.form['duration'])
        
        slots = SLOTS.query.filter_by(date = date.today()).first()
        if slots.available_slots == 0:
            flash('cant_subscribe')
            
        else:
            user =USERS.query.filter_by(user_name = session['user']).first()
            cos = SUBSCRIPTION.query.filter_by(duration_in_days = int( request.form['duration'])).first().cost
            if user.wallet < cos:
                flash('insufficient_balance')
                return redirect(url_for('dashboard'))
            # ({'membership' : 1,'membership_start' : date.today(),'membership_end' :))})
            user.membership = 1
            user.membership_start = date.today()
            user.membership_end = date.today() + timedelta(days = int(request.form['duration']))
            # samajavaragamana
            user.wallet_balance -= cos
            slots.available_slots-=1
            db.session.commit()
            flash('subscribed')
        return redirect(url_for('dashboard'))
#########################################################


#######################
#user functs --- to quickly fetch stats to display in the user dashboard
#somehow this is making the index page run slow
@app.route('/fetchAvailableSlots',methods = ['POST'])
def fetchAvailableSlots():
    return str(SLOTS.query.filter_by(date = date.today()).first().available_slots)

@app.route('/fetchWalletBalance',methods = ['POST'])
@user_login_required
def fetchWalletBalance():
    return USERS.query.filter_by(user_name = session['user']).first().wallet_balance
#######################

#########################################################
#guest functions
@app.route('/guestcheckin',methods=['POST'])
def guestcheckin():
    #imp goto line 51
    v_number = request.form['vehiclenumber']
    
    guest = TIME.query.filter_by(vehicle_number = v_number).filter_by(parker ='guest').order_by(desc(TIME.checkin_time)).first()
    if guest:
        print(guest.parking_id)
    if guest and (not guest.checkout_time):
        flash('already_checkedin') 
        return gohome()
    guest = TIME(vehicle_number = v_number,checkin_time = datetime.now(),date = date.today())
    db.session.add(guest)
    db.session.commit()
    
    # parking_id = parking_id.guest_id
    
    slots = SLOTS.query.filter_by(date = date.today() ).first()
    slots.available_slots -= 1
    db.session.commit()
    guest = TIME.query.filter_by(vehicle_number = v_number).order_by(desc(TIME.checkin_time)).first()
    flash(f'Your parking id is {guest.parking_id}, please use it to CHECKOUT')
    return gohome()
#########################################################


#imp change the endpoints naming convention
#########################################################
#admin functions
@app.route('/changeTotalSlots',methods =['POST'])
@admin_login_required
def changeTotalSlots():
    slots = SLOTS.query.filter_by(date = date.today()).first()
    slots.available_slots += request.form['slots']
    slots.total+= request.form['slots']
    db.session.commit()
    flash('total_slots_changed')
    return redirect(url_for('adminDashboard'))

@app.route('/changeSubscriptionCost',methods =['POST'])
@admin_login_required
def changeSubscriptionCost():
    modify = request.form
    a = [28,84,168,356]
    j=0
    keys_1 = sorted(modify.keys())
    for i in keys_1:
        if modify[i] != '':
            SUBSCRIPTION.query.filter_by(duration_in_days = a[j]).update({'cost':modify[i]})
        j+=1
    # SLOTS.query.filter_by(date  = date.today()).first().update(request.form)
    #now this i a bad design -> i think i made it better-> no went back to stupid
    db.session.commit()
    flash('costs_changed')
    return  redirect(url_for('adminDashboard'))


@app.route('/searchArchives/<vehiclenumber>',methods = ['POST'])
@admin_login_required
def searchArchives(vehiclenumber):
    print(vehiclenumber)
    res = TIME.query.filter_by(vehicle_number =  vehiclenumber).all()
    lis = []
    columns =  TIME.__table__.columns.keys()
    for row in res:
        dic ={}
        lis.append({column: getattr(row, column) for column in columns})
    
    return  jsonify(lis)


@app.route('/adminAddUser',methods=['POST'])
@admin_login_required
def addUser():
    user = request.form
    if USERS.query.filter_by(user_name = user['userName']) is None:
        flash('User name already exists, please try with another username')
        print('User name already exists, please try with another username')
        return redirect(url_for('adminDashboard'))
    
    to_add = USERS(user_name = user['userName'],password = user['password'],vehicle_number = user['vehiclenumber'])
    db.session.add(to_add)
    db.session.commit()
    flash('User Successfully Added')
    return redirect(url_for('adminDashboard'))
    
@app.route('/adminAddCheckin',methods=['POST'])
@admin_login_required
def adminAddCheckin():
    u_info = request.form   
    user_db = USERS.query.filter_by(user_name = u_info['userName']).first()
    if user_db :
        if user_db.parking_status == 1:
            flash('already_checkedin')
            return redirect(url_for('adminDashboard'))
        slots = SLOTS.query.filter_by(date = date.today() ).first()
        if slots.available_slots  == 0:
            print('No slots available to park')
            return redirect(url_for('adminDashboard'))
        flash(f' {user_db.user_name[0]}, checked-in at {datetime.now().hour}:{datetime.now().minute}')
        
        
        print('good checkin')
        slots.available_slots -= 1
        #to-do include membership condition-> should i just do it myself?, in backend we can just
        #verify the condition at backend and calculated the price
        checkin = TIME(parker = user_db.user_name,checkin_time = datetime.now(),date = date.today(),vehicle_number = user_db.vehicle_number)
        user_db.parking_status = 1
        db.session.add(checkin)
        db.session.commit()
        return redirect(url_for('adminDashboard'))
    print('bad checkin')
    flash('login_failed')  
    #do some math here
    # return redirect(url_for('index'))
    return redirect(url_for('adminDashboard'))

@app.route('/adminUpdateUserPassword',methods=['POST'])
@admin_login_required
def adminUpdateUserPassword():
    if request.method == 'POST':
        get_user_info = USERS.query.filter_by(user_name = request.form['userName']).first()
        if get_user_info :
            get_user_info.password = request.form['password']
            db.session.commit()
        else:
            flash('User name not found')
        return redirect(url_for('adminDashboard'))
    
    
@app.route('/changeHourlyPrice',methods = ['POST'])
@admin_login_required
def changeHourlyPrice():
        if request.form['guest_hourlyprice']:
            DAILY_SUMMARY.query.filter_by(date = date.today()).update({'guest_hourly_price':request.form['guest_hourlyprice']})
        if request.form['user_hourlyprice']:
             DAILY_SUMMARY.query.filter_by(date = date.today()).update({'user_hourly_price':request.form['user_hourlyprice']})
        db.session.commit()
        flash('price_changed')
        return gohome()
    

@app.route('/viewAvailableSlots',methods=['POST'])
@admin_login_required
def viewAvailableSlots():
    return SLOTS.query.filter_by(date = datetime.today()).first().available_slots

@app.route('/showSummary',methods = ['POST','GET'])
@admin_login_required
def showSummary():
    if request.method == 'POST':
        return SLOTS.query.filter_by(date = request.form['date']).first()
    else:
        return render_template('showSummary.html')



        
##########################################################
#admin functions
#imp 



# @app.route('/logout')
# @user_login_required
# def logout():
#     llogout_user()
#     return gohome()


@app.route('/logout')
@login_required
def logout():
    llogout_user()
    return gohome()

@app.route('/adminlogin',methods=['POST','GET'])
def adminlogin():
    if 'user' in session:
        return gohome()
    else:
        if request.method == 'GET':
            return render_template('adminlogin.html',messages = get_flashed_messages())
        else:
            admin_inf = request.form
            db_inf = ADMIN.query.filter_by(user_name = admin_inf['username']).first()
            print(admin_inf['password'])
            print(db_inf)
            if db_inf and admin_inf['password'] == db_inf.password :
                llogin_admin(db_inf)
                return redirect(url_for('adminDashboard'))
            flash('invalid username / password')
            return redirect(url_for('adminlogin'))

@app.route('/showDailySummary',methods = ['POST'])
@admin_login_required
def showDailySummary():
    daily_summary_data = DAILY_SUMMARY.query.all()
    lis = []
    columns =  DAILY_SUMMARY.__table__.columns.keys()
    for row in daily_summary_data:
        dic ={}
        lis.append({column: getattr(row, column) for column in columns})
    
    return  jsonify(lis)


@app.route('/adminSignup',methods = ['POST','GET'])
def adminSignup():
    if request.method =='POST':
        
        new_admin =ADMIN(user_name = request.form['username'],password = request.form['password'])
        db.session.add(new_admin)
        db.session.commit()
        llogin_admin(new_admin)
        return gohome()
    else:
        return render_template('adminSignUp.html')
@app.route('/adminDashboard',methods=['GET'])
@admin_login_required
def adminDashboard():
    costs = SUBSCRIPTION.query.all()
    for row in costs:
        dic={}
        dic[row.duration_in_days] = row.cost
        msg = get_flashed_messages()
        if len(msg)>0:
            msg = get_flashed_messages()[0]
    return render_template('admindashboard.html',messages = msg,costs = dic)

@app.route('/checkout',methods=['POST','GET'])
def checkout():
    if request.method =='POST':
        
        if request.form['parkingId'].isnumeric():
            #guest
            hourlyprice = DAILY_SUMMARY.query.filter_by(date = date.today()).first().guest_hourly_price
            guest = TIME.query.filter_by(parking_id = int(request.form['parkingId'])).first()
            if guest:
                if not guest.checkout_time == None:
                    flash ('not_clocked_in')
                    return gohome()
                to_charge = to_charge = ceil((datetime.now() - guest.checkin_time).seconds /60 /60) * hourlyprice
                if to_charge < hourlyprice:
                    to_charge = hourlyprice
                session['id'] = request.form['parkingId']
                session['user_type'] = 'guest'
                session['cost'] = to_charge
                return render_template('payment.html',cost = to_charge)
            else:
                flash('parking_id_not_found')
                return gohome()
            #redirect to payment page
        else:
            user = USERS.query.filter_by(user_name = request.form['parkingId']).first()
            if user:
                if user.parking_status == 0:
                    print('is a member')
                    flash('not_clocked_in')
                    return gohome()
                to_charge = 0
                if user.membership == 0:
                    hourlyprice = DAILY_SUMMARY.query.filter_by(date = date.today()).first().user_hourly_price
                    time = TIME.query.filter_by(parker = user.user_name).order_by(desc( TIME.checkin_time )).first()
                    to_charge = to_charge = ceil((datetime.now() - time.checkin_time).seconds /60 /60) * hourlyprice
                    if to_charge < hourlyprice:
                        to_charge = hourlyprice
                    user.parking_status =0
                    session['id'] = user.user_name
                    session['cost'] = to_charge
                    session['user_type'] ='user'
                    
                    return redirect(url_for('securoPay'))
                    
                    
                else:
                    user = TIME.query.filter_by(parker = request.form['parkingId']).order_by(desc( TIME.checkin_time )).first()
                    user.checkout_time = datetime.now()
                    user.parking_status = 0
                    db.session.commit()
                    flash(f"{user.parker} successfully checked-out at {datetime.now().strftime('%H:%m')}")
                    return gohome()

            #user
            #if not suffcient balance in wallet, redirect to payment
            
@app.route('/securoPay',methods=['POST','GET'])           
def securoPay():
    if request.method == 'POST':
        if session['user_type'] == 'guest':
            guest = TIME.query.filter_by(parking_id = session['id']).first()
            guest.checkout_time = datetime.now()
            guest.amount_paid = session['cost']
            
        else:
            # user = USERS.query.filter_by(user_name = session['id']).first()
            user = TIME.query.filter_by(parker = session['id']).order_by(desc( TIME.checkin_time )).first()
            user.checkout_time = datetime.now()
            user.amount_paid = session['cost']
            u = USERS.query.filter_by(user_name = session['id']).first()
            u.parking_status = 0
            if u.wallet_balance < session['cost']:
                flash('insufficient balance')
                return gohome()
            u.wallet_balance -= session['cost']
        
        p = INCOME.query.filter_by(id = 1).first()
        p.total_income += session['cost']
        slots = SLOTS.query.filter_by(date = date.today()).first()
        slots.available_slots += 1
        db.session.commit()    
        flash(f'Payment Successfull')
        return gohome()
    else:
        return render_template('payment.html',cost = session['cost'])

# @app.route('/checkout',methods=['POST'])
# def checkout():
#     #checkout time, calc the price, increase availableslots
#     #see if user exists
#     if request.form['parkingId'].isnumeric():
#         #guest 
#         hourlyprice = DAILY_SUMMARY.query.filter_by(date = date.today()).first().hourly_price
#         guest = TIME.query.filter_by(parking_id = int(request.form['parkingId'])).first()
        
#         if guest:
#             if not guest.checkout_time == None:
#                 flash('not_clocked_in')
#                 return gohome()
#             slots = SLOTS.query.filter_by(date = date.today()).first()
#             slots.available_slots += 1
#             # time = TIME.query.filter_by(vehicle_number = guest.vehicle_number).order_by(desc( TIME.checkin_time )).first()
#             print('###########################')
#             to_charge = ceil((datetime.now() - guest.checkin_time).seconds /60 /60) * hourlyprice
#             if to_charge < hourlyprice:
#                 to_charge = hourlyprice
#             guest.checkout_time = datetime.now()
#             # guest.amount_paid = to_charge
#             # TIME.update().where(TIME.parking_id == guest.guest_id).values(amount_paid = to_charge,checkout_time = guest.checkout_time)
#             guest.amount_paid = to_charge
#             guest.checkout_time = guest.checkout_time
#             p = INCOME.query.filter_by(id = 1).first()
#             p.total_income += to_charge
#             db.session.commit()
#             flash(f'Payment Successfull')
#             return gohome()
#         else:
#             flash('parking_id_not_found')
#             return gohome()
#     else:
#         #user -> if member, do not charge
#         user = USERS.query.filter_by(user_name = request.form['parkingId']).first()
#         if user:
#             hourlyprice = DAILY_SUMMARY.query.filter_by(date = date.today()).first().hourly_price
#             if not user.parking_status :
#                 flash('not_clocked_in')
#                 return gohome()
#             time = TIME.query.filter_by(parker = request.form['parkingId']).order_by(desc( TIME.checkin_time )).first()
#             to_charge = 0
#             time.checkout_time = datetime.now()
#             if user.membership == 0:
#                 slots = SLOTS.query.filter_by(date = date.today()).first()
#                 slots.available_slots += 1
#                 to_charge = ceil((datetime.now() - time.checkin_time).seconds/60/60) * hourlyprice
                
#                 if to_charge < hourlyprice:
#                     to_charge = hourlyprice
                
#             p = INCOME.query.filter_by(id = 1).first()
#             p.total_income += to_charge
#             user.parking_status = 0   
#             time.amount_paid = to_charge
#             db.session.commit()
#             flash(f"{user.user_name} successfully checked-out at {datetime.now().strftime('%H:%m')}")
#             return gohome()
#         else:
#             flash('invalid_username')
#             return gohome()

    

@app.errorhandler(404)  
def error404(e):
    return render_template('404.html'),404

@app.errorhandler(405)
def error405(e):
    return render_template('405.html'),405

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func = daily_summary, trigger='cron', hour = 0, minute = 22 )  
    # scheduler.add_job(func = notify_admin,trigger = 'interval',seconds = 60)
    scheduler.start()

    app.run(debug=True)

#todo : summary, updates and admin functions
