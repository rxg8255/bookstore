# Store this code in 'app.py' file

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'bookstore'

mysql = MySQL(app)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("SELECT * FROM accounts WHERE userid = '{}' AND password ='{}'".format(userid, password, ))
        account = conn.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['userid']
            session['type'] = account['user_type']
            msg = 'Logged in successfully !'
            return redirect(url_for('inventory', msg=msg))
        else:
            msg = 'Incorrect username / password !'
            return render_template('login.html', msg=msg)
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('type', None)
    return redirect(url_for('login'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    msg = ''
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        email = request.form['email']
        usertype = request.form['usertype']
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute('SELECT * FROM accounts WHERE userid = % s', (userid,))
        account = conn.fetchone()
        if account:
            msg = 'Account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not userid or not password or not email:
            msg = 'Please fill all details'
        else:
            conn.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s, % s)', (userid, password, email, usertype,))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            return render_template('login.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


@app.route('/inventory/<opt>',methods=['GET', 'POST'])
@app.route('/inventory', methods=['GET', 'POST'], defaults={'opt': None})
def inventory(opt):
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if opt==None or opt=='All':
            conn.execute('SELECT * FROM inventory')
        else:
            conn.execute("SELECT * from inventory where genre='{}'".format(opt))
        books = conn.fetchall()
        for book in books:
            book['cart'] = 'NO'
            book['wishlist'] = 'NO'

        conn.execute("SELECT * FROM custom where userid='{}'".format(session['id']))
        customs = conn.fetchall()
        for custom in customs:
            if custom['type'] == 'cart':
                for book in books:
                    if book['id'] == custom['bookid'] and custom['isactive'] == 1:
                        book['cart'] = 'YES'
                        book['total_price'] = book['cost'] * custom['qty']
            elif custom['type'] == 'wishlist':
                for book in books:
                    if book['id'] == custom['bookid'] and custom['isactive'] == 1:
                        book['wishlist'] = 'YES'
        return render_template('inventory.html', books=books)
    else:
        msg = 'Error loading Books, please try again'
        return render_template('login.html', msg=msg)


@app.route('/showcart')
def showcart():
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("SELECT i.bookname, i.cost, i.available, c.qty, (i.cost * c.qty) AS total, "
                     "c.bookid FROM inventory as i, custom as c "
                     "where c.isactive=true and c.type='cart' and i.id=c.bookid"
                     " and c.userid={}".format(session['id']))
        customs = conn.fetchall()
        netprice = 0
        for custom in customs:
            custom['netprice'] = 0
            netprice += custom['total']
            if custom['qty'] > custom['available']:
                custom['qty'] = custom['available']
                custom['total'] = custom['qty'] * custom['cost']
        return render_template('cart.html', items=customs, netprice=netprice)
    else:
        msg = 'Error loading Cart items, please try again'
        return render_template('login.html', msg=msg)


@app.route('/wishlistdisplay')
def wishlistdisplay():
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("SELECT i.id as iid, i.bookname, i.cost, i.available FROM inventory as i, custom as c "
                     "where c.isactive=true and c.type='wishlist' and i.id=c.bookid "
                     "and c.userid={}".format(session['id']))
        customs = conn.fetchall()
        return render_template('wishlist.html', items=customs)
    else:
        msg = 'Error loading Cart items, please try again'
        return render_template('login.html', msg=msg)


@app.route('/cart/<bookid>', methods=['GET', 'POST'])
def cart(bookid):
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("SELECT * FROM custom where type='cart' and userid={} and bookid={}".format(session['id'], bookid))
        custom = conn.fetchone()
        if custom is not None:
            if custom['isactive'] == 1:
                conn.execute("UPDATE custom SET isactive=False where type='cart' "
                             "and userid={} and bookid={}".format(session['id'], bookid))
            else:
                conn.execute("UPDATE custom SET isactive=True, qty=1 where type='cart' "
                             "and userid={} and bookid={}".format(session['id'], bookid))
        else:
            conn.execute("INSERT INTO `bookstore`.`custom` (`type`,`userid`,`bookid`,`isactive`,`qty`) "
                         "VALUES ('cart',{},{},True, 1)".format(session['id'], bookid))
        mysql.connection.commit()
        return redirect(url_for('inventory'))
    else:
        msg = 'Error loading Books, please try again'
        return render_template('login.html', msg=msg)


@app.route('/wishlist/<bookid>', methods=['GET', 'POST'])
def wishlist(bookid):
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute(
            "SELECT * FROM custom where type='wishlist' and userid={} and bookid={}".format(session['id'], bookid))
        custom = conn.fetchone()
        if custom != None:
            if custom['isactive'] == 1:
                conn.execute("UPDATE custom SET isactive=False where type='wishlist' "
                             "and userid={} and bookid={}".format(session['id'], bookid))
            else:
                conn.execute("UPDATE custom SET isactive=True where type='wishlist' "
                             "and userid={} and bookid={}".format(session['id'], bookid))
        else:
            conn.execute("INSERT INTO `bookstore`.`custom` (`type`,`userid`,`bookid`,`isactive`) "
                         "VALUES ('wishlist',{},{},True)".format(session['id'], bookid))
        mysql.connection.commit()
        return redirect(url_for('inventory'))
    else:
        msg = 'Error loading Books, please try again'
        return render_template('login.html', msg=msg)

@app.route('/caltotal/<qty>/<bookid>', methods=['GET', 'POST'])
def caltotal(qty, bookid):
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("UPDATE custom SET qty={} where type='cart' and isactive=True and "
                     "userid={} and bookid={}".format(qty, session['id'], bookid))
        mysql.connection.commit()
        return redirect(url_for('showcart'))
    else:
        msg = 'Error updating Cart, please try again'
        return render_template('login.html', msg=msg)

@app.route('/order', methods=['GET', 'POST'])
def order():
    msg = ''
    if session['loggedin']:
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute("SELECT c.id as cid,i.id as iid, i.bookname, i.cost, i.available, c.qty, (i.cost * c.qty) AS total, "
                     "c.bookid FROM inventory as i, custom as c "
                     "where c.isactive=true and c.type='cart' and i.id=c.bookid"
                     " and c.userid={}".format(session['id']))
        orders = conn.fetchall()
        netprice = 0
        for order in orders:
            netprice += order['total']
        conn.execute("INSERT INTO orders (totalamount, userid, saledate) "
                     "VALUES ({},{}, CURRENT_TIMESTAMP)".format(netprice,session['id']))
        orderid = conn.lastrowid
        for order in orders:
            conn.execute("INSERT INTO `bookstore`.`orderdetails` (`userid`, `orderid`, "
                         "`bookid`, `cost`, `qty`, `total`) "
                         "VALUES ({},{},{},{},{},"
                         "{})".format(session['id'], orderid, order['bookid'],
                                       order['cost'], order['qty'], order['total']))
            conn.execute("UPDATE inventory SET available={} where id={}".format(order['available']-order['qty'],order['iid']))
            conn.execute("UPDATE custom SET isactive=False where id={}".format(order['cid']))
        mysql.connection.commit()
        return redirect(url_for('inventory'))

@app.route('/addinventory', methods=['GET', 'POST'])
def addinventory():
    msg = ''
    if session['type'] !=2:
        msg="Sorry, you are unable to access this page. Login as Manager"
        return render_template('login.html', msg=msg)
    if request.method == 'POST':
        bookname = request.form['bookname']
        genre = request.form['genre']
        available = request.form['available']
        cost = request.form['cost']
        conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        conn.execute('SELECT * FROM inventory WHERE bookname = % s and genre= % s', (bookname,genre,))
        account = conn.fetchone()
        if account:
            conn.execute("UPDATE inventory SET available={}, cost={} WHERE bookname ='{}' "
                         "and genre='{}' ", (available,cost,bookname,genre))
        elif not bookname or not genre or not cost or not available:
            msg = 'Please fill all details'
        else:
            conn.execute('INSERT INTO inventory VALUES (NULL, % s, % s, % s, % s)',
                         (bookname, genre, available, cost,))
            mysql.connection.commit()
            msg = 'You have successfully added Book !'
            return render_template('addinventory.html', msg=msg)
    return render_template('addinventory.html', msg=msg)


@app.route('/orderdetails', methods=['GET', 'POST'])
def orderdetails():
    msg = ''
    conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if session['type'] == 1 and session['loggedin']:
        conn.execute(
            "select o.id, o.totalamount as billamount, a.userid, a.email, o.saledate "
            "from orders o, accounts a where o.userid=a.id and o.userid={}".format(session['id']))
        orders = conn.fetchall()
        return render_template('orders.html', orders=orders)
    elif session['type'] == 2 and session['loggedin']:
        conn.execute("select o.id, o.totalamount as billamount, a.userid, a.email, o.saledate "
                     "from orders o, accounts a where o.userid=a.id")
        orders = conn.fetchall()
        return render_template('orders.html', orders=orders)
    else:
        msg = 'Error loading Orders, please try again'
        return render_template('login.html', msg=msg)

@app.route('/billdetails/<orderid>', methods=['GET', 'POST'])
def billdetails(orderid):
    msg = ''
    conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if session['loggedin']:
        conn.execute(
            "select i.bookname, i.genre,o.saledate, od.total, od.qty, od.cost, od.orderid "
            "from orderdetails as od, inventory as i, orders o "
            "where od.bookid=i.id and o.id=od.orderid and od.orderid={}".format(orderid))
        sales = conn.fetchall()
        return render_template('sales.html', sales=sales)
    else:
        msg = 'Error loading Sales, please try again'
        return render_template('login.html', msg=msg)

@app.route('/movetocart/<iid>', methods=['GET', 'POST'])
def movetocart(iid):
    msg = ''
    conn = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if session['loggedin']:
        conn.execute("UPDATE custom SET isactive=True where userid={} and bookid={} and "
                     "type='cart'".format(session['id'],iid))
        conn.execute("UPDATE custom SET isactive=False where userid={} and bookid={} and "
                     "type='wishlist'".format(session['id'], iid))
        mysql.connection.commit()
        return redirect(url_for('wishlistdisplay'))
    else:
        msg = 'Error moving item to cart, please try again'
        return render_template('login.html', msg=msg)