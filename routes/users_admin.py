from flask import request, redirect, render_template, session, flash
from server import app
from db import get_users_connection, get_data_connection, hash_password


@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    conn_u = get_users_connection()
    users = conn_u.execute("SELECT * FROM users").fetchall()
    conn_u.close()

    conn_d = get_data_connection()
    companies = conn_d.execute("SELECT * FROM companies").fetchall()
    conn_d.close()

    return render_template('admin/admin_users.html', users=users, companies=companies)


@app.route('/admin/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    company_id = request.form.get('company_id') if role == 'owner' else None

    conn = get_users_connection()
    if company_id:
        conn.execute("INSERT INTO users (username, password, role, company_id) VALUES ('"+username+"', '"+hash_password(password)+"', "+role+", "+company_id+")")
    else:
        conn.execute("INSERT INTO users (username, password, role) VALUES ('"+username+"', '"+hash_password(password)+"', "+role+")")
    conn.commit()
    conn.close()
    flash("User created successfully.", "success")
    return redirect('/admin/users')


@app.route('/admin/users/edit', methods=['POST'])
def edit_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    username = request.form['username']
    new_role = request.form['role']
    company_id = request.form.get('company_id') if new_role == 'owner' else None

    conn = get_users_connection()
    if company_id:
        conn.execute("UPDATE users SET role = ?, company_id = ? WHERE username = ?", (new_role, company_id, username))
    else:
        conn.execute("UPDATE users SET role = ?, company_id = NULL WHERE username = ?", (new_role, username))
    conn.commit()
    conn.close()
    flash("User updated.", "success")
    return redirect('/admin/users')


@app.route('/admin/users/delete', methods=['POST'])
def delete_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    username = request.form['username']
    conn = get_users_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    flash("User deleted.", "warning")
    return redirect('/admin/users')
