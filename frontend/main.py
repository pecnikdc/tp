from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from warrant import Cognito

#https://github.com/capless/warrant
 
app = Flask(__name__)

cognito_id = 'us-west-2_CX8ab1Juf'
app_id = 'vn07r57alj9skvd2809gp6dml'
 
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "Hello Boss!"

@app.route('/register_page')
def register_page():
    
        return render_template('register.html')

@app.route('/register_confim')
def register_confirm(username):
    
        return render_template('register_confirm.html',username=username)

@app.route('/register_confirm_verify', methods=['POST'])
def register_confirm_verify():
    
    try:
        u = Cognito(cognito_id,app_id)

        code = request.form['confirmation_code']
        username = request.form['username']

        u.confirm_sign_up(code,username=username)
    
    except:

        return render_template('register_confirm.html',username=username,error_message="invalid code")

    
    return home()
 
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    mobile = request.form['phone']

    u = Cognito(cognito_id, app_id)

    u.add_base_attributes(email=email)

    u.register(username, password)

    return register_confirm(username)
 
@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
        u = Cognito(cognito_id,app_id,
            username=request.form['username'])
        
        
        return "Hello Boss!"

    else:
        flash('wrong password!')
    
    return home()

@app.route('/calendar')
def calendar():
    
        return render_template('calendar.html')

@app.route('/account')
def account():

    u = Cognito(cognito_id,app_id,
    username='pecnikdc')

    user = u.get_user(attr_map={"username":"username","email":"email"})
    
    return render_template('account.html',username=user.get("username"), email=user.get("email"))

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
