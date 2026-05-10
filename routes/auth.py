from db import get_users_connection, hash_password
from flask import request, redirect, render_template, session, flash
from server import app

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/dashboard')
    next_url = request.args.get('next', '/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_users_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password))).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['company_id'] = user['company_id']
            session.permanent = True
            return redirect(next_url)
        else:
            flash("Invalid username or password", "danger")
            return render_template('auth/login.html', next_url=next_url)
    return render_template('auth/login.html', next_url=next_url)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')
