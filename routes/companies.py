from flask import request, redirect, render_template, session, flash, url_for
from db import get_data_connection, get_users_connection


# -------------------------
# COMPANIES LIST
# -------------------------
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
