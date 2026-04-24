from flask import request, redirect, render_template, session, flash
from server import app
from db import get_data_connection, get_users_connection

@app.route('/')
def index():
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    conn = get_data_connection()
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    recent_comments = conn.execute(
        "SELECT comments.*, companies.name as company_name FROM comments "
        "JOIN companies ON comments.company_id = companies.id "
        "ORDER BY comments.id DESC LIMIT 5"
    ).fetchall()
    conn.close()

    # Resolve user IDs for profile links
    user_ids = {}
    usernames = set(c['user'] for c in recent_comments)
    if usernames:
        conn_u = get_users_connection()
        for uname in usernames:
            u = conn_u.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
            if u:
                user_ids[uname] = u['id']
        conn_u.close()

    return render_template('dashboard.html', 
                           total_companies=total_companies, 
                           total_comments=total_comments,
                           recent_comments=recent_comments,
                           user_ids=user_ids)

@app.route('/companies')
def list_companies():
    if 'username' not in session:
        return redirect('/login')
    conn = get_data_connection()
    
    search = request.args.get('q', '')
    if search:
        companies = conn.execute("SELECT * FROM companies WHERE name LIKE '%" + search + "%'").fetchall()
    else:
        companies = conn.execute("SELECT * FROM companies").fetchall()

    companies_list = []
    for company in companies:
        company_dict = dict(company)
        company_dict['comment_count'] = conn.execute("SELECT COUNT(*) FROM comments WHERE company_id = ?", (company_dict['id'],)).fetchone()[0]
        companies_list.append(company_dict)
    
    conn.close()
    return render_template('companies/home.html', companies=companies_list, search=search)



@app.route('/companies/<int:company_id>', methods=['GET', 'POST'])
def company_detail(company_id):
    if 'username' not in session:
        return redirect('/login')
    conn = get_data_connection()
    company = conn.execute("SELECT * FROM companies WHERE id = " + str(company_id)).fetchone()
    comments = conn.execute("SELECT * FROM comments WHERE company_id = " + str(company_id)).fetchall()
    if request.method == 'POST':
        comment = request.form['comment']
        user = session.get('username')
        conn.execute("INSERT INTO comments (company_id, user, comment) VALUES ("+str(company_id)+", '"+user+"', '"+comment+"')")
        conn.commit()
        conn.close()
        flash("Comment added successfully.", "success")
        return redirect('/companies/'+str(company_id))
    conn.close()
    if not company:
        return render_template('errors/404.html'), 404

    # Resolve user IDs for profile links
    user_ids = {}
    usernames = set(c['user'] for c in comments)
    if usernames:
        conn_u = get_users_connection()
        for uname in usernames:
            u = conn_u.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
            if u:
                user_ids[uname] = u['id']
        conn_u.close()

    return render_template('companies/company.html', company=company, comments=comments, user_ids=user_ids)

@app.route('/companies/register', methods=['GET', 'POST'])
def register_company():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    if request.method == 'POST':
        company_name = request.form['company_name']
        description = request.form['description']
        owner = request.form.get('owner', session.get('username'))
        conn = get_data_connection()
        conn.execute("INSERT INTO companies (name, description, owner) VALUES ("+company_name+", '"+description+"', '"+owner+"')")
        conn.commit()
        conn.close()
        flash("Company registered successfully.", "success")
        return redirect('/companies')
    return render_template('companies/register_company.html')


@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    if 'username' not in session:
        return redirect('/')
    conn = get_data_connection()
    company = conn.execute("SELECT * FROM companies WHERE id = "+ str(company_id)).fetchone()
    if not company:
        conn.close()
        return render_template('errors/404.html'), 404
    if session.get('role') != 'admin' and session.get('username') != company['owner']:
        conn.close()
        return render_template('errors/403.html'), 403
    if request.method == 'POST':
        new_name = request.form['company_name']
        new_description = request.form['description']
        conn.execute("UPDATE companies SET name = '"+new_name+"', description = '"+new_description+"' WHERE id = "+str(company_id))
        conn.commit()
        conn.close()
        flash("Company updated successfully.", "success")
        return redirect('/companies')
    conn.close()
    return render_template('companies/edit_company.html', company=company)
