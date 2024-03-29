import datetime
from flask import Flask, render_template, request, redirect, url_for
from sqlite3 import connect, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

custID = ''
custEmail = ''
orderDetails = []

try:
    connection = connect(r"./databases/database.db")
    cursor = connection.cursor()
    cursor.execute("""SELECT ItemType, Ingredients, Description, course, flavour, Price FROM menu;""")
    menu_items = cursor.fetchall()
except:
    print("Database connection error")
finally:
    cursor.close()
    connection.close()

@app.route('/')
@app.route('/index')
def index():
    return render_template('base.html', items=menu_items)

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        fName = request.form['fname']
        lName = request.form['lname']
        sEmail = request.form['email']
        phone = request.form['phoneNum']
        sPwd = request.form['pwd'] 
        try:
            connection = connect(r"./databases/database.db")
            cursor = connection.cursor()
            cursor.execute("""INSERT INTO customer('Name','Email','pwdhash','phone_number') VALUES (?,?,?,?);""", ( fName + " " + lName, sEmail, generate_password_hash(sPwd), phone))
            connection.commit()
        except (IntegrityError, ) as e:
            print("Exception: ", repr(e))
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Database connection error</h1></html>"
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        global custEmail
        email= request.form['email']
        pwd = request.form['pwd']

        try:
            connection = connect(r"./databases/database.db")
            cursor = connection.cursor()
            cursor.execute("""SELECT Name, Email, pwdhash FROM customer;""")
            users_list = cursor.fetchall()
        except (IntegrityError, ) as e:
            print("Exception: ", repr(e))
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Database connection error</h1></html>"
        finally:
            cursor.close()
            connection.close()
        user = {}
        
        for i, n in enumerate(users_list):
            user[users_list[i][1].lower()] = users_list[i][2]

        # Check the password hash of the user in database
        if (email.lower() in user) and (user[email.lower()], pwd):
            custEmail = email
            print('email: ', custEmail)
            return redirect(url_for('index'))
        else:
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>wrong password</h1></html>"
    else:
        return render_template('login.html')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    checkout = []
    if request.method == 'POST':
        return redirect(url_for('billing'), code=307)
    else:
        return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Cart if empty !</h1></html>"

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/billing', methods=['POST'])
def billing():
    if request.method == 'POST':
        global orderDetails 
        temp = []
        checkout = []
        total = 0
        index = 0

        for item, value in request.form.items():
            print('item: value', item, ': ', value)
            checkout.append(item)
        try:
            connection = connect(r"./databases/database.db")
            cursor = connection.cursor()
            for index, item in enumerate(checkout):
                cursor.execute(
                    """SELECT Price FROM menu where ItemType =?;""", (item,))
                itemPrice = cursor.fetchall()[0][0]
                total += itemPrice
                temp.append((index, item, itemPrice))
            else:
                temp.append((index + 1, 'Total', total))
            print('Checked out: ', temp)
            orderDetails = temp
            print('Checked out: ', orderDetails)
            return render_template('billing.html', checkedItems=temp)
        except (IntegrityError, ) as e:
            print("Exception: ", repr(e))
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Database error</h1></html>"
        finally:
            cursor.close()
            connection.close() 
    else:
        return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Billing Page error</h1></html>"

@app.route('/payment', methods=['POST'])
def accept_payment():
    if request.method == 'POST':
        global orderDetails
        global custEmail
        global custID
        temp = []
        checkout = []
        total = 0
        print('payment request: ', orderDetails)
        try:
            connection = connect(r"./databases/database.db")
            cursor = connection.cursor()
            custIdQuery =\
                "SELECT CustID FROM customer WHERE Email=\"{email}\"".format(
                    email=custEmail)
            print("Query: ", custIdQuery)
            cursor.execute(custIdQuery)
            customerId = cursor.fetchall()[0][0]
            custID = customerId

            dt = datetime.datetime.now()
            ordDate = dt.strftime('%Y-%m-%d') 
            ordTime = dt.strftime('%H:%M:%S') 
            # OrderID is a unique key, auto-populated
            staffQuery = "SELECT StaffID from Staff WHERE StaffName=\"Ken\"" 
            cursor.execute(staffQuery)
            staffId = cursor.fetchall()[0][0]
            orderInsertQuery =\
                "INSERT INTO CustOrder (OrderDate, OrderTime, CustID, StaffID) "\
                "VALUES (\"{dt}\", \"{tn}\", {ci}, {st})".format(dt=ordDate,
                                                                 tn=ordTime,
                                                                 ci=customerId,
                                                                 st=staffId)
            print('XXXX..........', orderInsertQuery)
            cursor.execute(orderInsertQuery)
            print('customerId: ', customerId)

            # Insert into the Order table here...

            totalPrice = orderDetails[-1][2] # This will get the total price.

            ordIdQuery = "SELECT OrderID from CustOrder WHERE CustID={cid} "\
                "AND OrderDate=\"{od}\" AND OrderTime=\"{ot}\"".format(
                    cid=customerId, od=ordDate, ot=ordTime)

            print('XXXX..........', ordIdQuery)
            cursor.execute(ordIdQuery)
            orderId = cursor.fetchall()[0][0]
            print('orderId: ', orderId)

            billInsertQuery =\
                "INSERT INTO Bill (BillDate, BillTime, OrderID, TotalPrice) "\
                "VALUES (\"{dt}\", \"{tn}\", {oi}, {price})".format(
                    dt=ordDate, tn=ordTime, oi=orderId, price=totalPrice)
            print('billInsertQuery: ', billInsertQuery)
            cursor.execute(billInsertQuery)
            # Update bill table here...
            return render_template('orderSuccess.html',
                                   checkedItems=orderDetails)
        except (IntegrityError, ) as e:
            print("Exception: ", repr(e))
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Database error</h1></html>"
        finally:
            connection.commit()
            cursor.close()
            connection.close() 

@app.route('/feedback', methods=['POST'])
def get_feedback():
    return render_template('feedback.html')

@app.route('/saveFeedback', methods=['POST'])
def save_feedback():
    if request.method == 'POST':
        global orderDetails
        global custID
        print("Feedback......", request.form['w3review'])
        fbSaveQuery = "INSERT INTO Feedback (FeedbackDescription, CustID) "\
            "VALUES (\"{fb}\", {cid})".format(fb=request.form['w3review'], cid=custID)
        print("fbSaveQuery...................", fbSaveQuery)
        try:
            connection = connect(r"./databases/database.db")
            cursor = connection.cursor()
            cursor.execute(fbSaveQuery)
        except (IntegrityError, ) as e:
            print("Exception: ", repr(e))
            return "<!Doctype html><html lang='en'><head><title>Cookzone</title></head><body></body><h1>Error while submitting feedback.</h1></html>"
        finally:
            connection.commit()
            cursor.close()
            connection.close()
    return render_template('thanks.html')

    
if __name__ == "__main__":
    app.run(debug=True)
