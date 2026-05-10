from flask import request, redirect, render_template, session, flash, url_for
from urllib.parse import urlparse, urljoin

from server import app
from db import get_data_connection, get_users_connection


# -------------------------
# UTILIDAD SEGURIDAD
# -------------------------
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route('/')
def index():
    return redirect('/login')


# -------------------------
# AUTH (OPEN REDIRECT FIX)
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next', '/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_users_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password))
        ).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # 🔐 FIX OPEN REDIRECT
            if not next_url or not is_safe_url(next_url):
                next_url = '/dashboard'

            return redirect(next_url)

        flash("Invalid credentials", "error")

    return render_template('auth/login.html')


# -------------------------
# DASHBOARD
# -------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    conn = get_data_connection()

    total_companies = conn.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    total_comments = conn.execute(
        "SELECT COUNT(*) FROM comments"
    ).fetchone()[0]

    recent_comments = conn.execute(
        """
        SELECT comments.*, companies.name as company_name
        FROM comments
        JOIN companies ON comments.company_id = companies.id
        ORDER BY comments.id DESC
        LIMIT 5
        """
    ).fetchall()

    conn.close()

    user_ids = {}
    usernames = set(c['user'] for c in recent_comments)

    if usernames:
        conn_u = get_users_connection()

        for uname in usernames:
            u = conn_u.execute(
                "SELECT id FROM users WHERE username = ?",
                (uname,)
            ).fetchone()

            if u:
                user_ids[uname] = u['id']

        conn_u.close()

    return render_template(
        'dashboard.html',
        total_companies=total_companies,
        total_comments=total_comments,
        recent_comments=recent_comments,
        user_ids=user_ids
    )


# -------------------------
# COMPANIES LIST
# -------------------------
@app.route('/companies')
def list_companies():

    if 'username' not in session:
        return redirect('/login')

    conn = get_data_connection()

    search = request.args.get('q', '').strip()

    if search:
        companies = conn.execute(
            "SELECT * FROM companies WHERE name LIKE ?",
            ('%' + search + '%',)
        ).fetchall()
    else:
        companies = conn.execute(
            "SELECT * FROM companies"
        ).fetchall()

    companies_list = []

    for company in companies:
        company_dict = dict(company)

        company_dict['comment_count'] = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE company_id = ?",
            (company_dict['id'],)
        ).fetchone()[0]

        companies_list.append(company_dict)

    conn.close()

    return render_template(
        'companies/home.html',
        companies=companies_list,
        search=search
    )


# -------------------------
# COMPANY DETAIL
# -------------------------
@app.route('/companies/<int:company_id>', methods=['GET', 'POST'])
def company_detail(company_id):

    if 'username' not in session:
        return redirect('/login')

    conn = get_data_connection()

    company = conn.execute(
        "SELECT * FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()

    comments = conn.execute(
        "SELECT * FROM comments WHERE company_id = ?",
        (company_id,)
    ).fetchall()

    if request.method == 'POST':

        comment = request.form['comment'].strip()
        user = session.get('username')

        conn.execute(
            "INSERT INTO comments (company_id, user, comment) VALUES (?, ?, ?)",
            (company_id, user, comment)
        )

        conn.commit()
        conn.close()

        flash("Comment added successfully.", "success")

        return redirect(f'/companies/{company_id}')

    conn.close()

    if not company:
        return render_template('errors/404.html'), 404

    user_ids = {}
    usernames = set(c['user'] for c in comments)

    if usernames:
        conn_u = get_users_connection()

        for uname in usernames:
            u = conn_u.execute(
                "SELECT id FROM users WHERE username = ?",
                (uname,)
            ).fetchone()

            if u:
                user_ids[uname] = u['id']

        conn_u.close()

    return render_template(
        'companies/company.html',
        company=company,
        comments=comments,
        user_ids=user_ids
    )


# -------------------------
# REGISTER COMPANY
# -------------------------
@app.route('/companies/register', methods=['GET', 'POST'])
def register_company():

    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403

    if request.method == 'POST':

        company_name = request.form['company_name'].strip()
        description = request.form['description'].strip()
        owner = request.form.get('owner', session.get('username')).strip()

        conn = get_data_connection()

        conn.execute(
            "INSERT INTO companies (name, description, owner) VALUES (?, ?, ?)",
            (company_name, description, owner)
        )

        conn.commit()
        conn.close()

        flash("Company registered successfully.", "success")

        return redirect('/companies')

    return render_template('companies/register_company.html')


# -------------------------
# EDIT COMPANY
# -------------------------
@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):

    if 'username' not in session:
        return redirect('/')

    conn = get_data_connection()

    company = conn.execute(
        "SELECT * FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()

    if not company:
        conn.close()
        return render_template('errors/404.html'), 404

    if session.get('role') != 'admin' and session.get('username') != company['owner']:
        conn.close()
        return render_template('errors/403.html'), 403

    if request.method == 'POST':

        new_name = request.form['company_name'].strip()
        new_description = request.form['description'].strip()

        conn.execute(
            "UPDATE companies SET name = ?, description = ? WHERE id = ?",
            (new_name, new_description, company_id)
        )

        conn.commit()
        conn.close()

        flash("Company updated successfully.", "success")

        return redirect('/companies')

    conn.close()

    return render_template(
        'companies/edit_company.html',
        company=company
    )
