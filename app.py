from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)

job_csv = 'jobs.csv'
user_csv = 'users.csv'
application_csv = 'applications.csv'

# Ensure CSV files exist
if not os.path.exists(job_csv):
    pd.DataFrame(columns=['id', 'title', 'company', 'description', 'salary', 'posted_by']).to_csv(job_csv, index=False)
if not os.path.exists(user_csv):
    pd.DataFrame(columns=['id', 'name', 'email', 'password', 'role']).to_csv(user_csv, index=False)
if not os.path.exists(application_csv):
    pd.DataFrame(columns=['id', 'job_id', 'user_id']).to_csv(application_csv, index=False)

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    users = pd.read_csv(user_csv)
    if request.method == 'POST':
        if users.empty or users['id'].isnull().all():
            new_id = 1
        else:
            new_id = int(users['id'].max()) + 1
        new_user = {
            'id': new_id,
            'name': request.form['name'],
            'email': request.form['email'],
            'password': request.form['password'],
            'role': request.form['role']
        }
        users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        users.to_csv(user_csv, index=False)
        return redirect(f"/dashboard/{new_id}")
    user_read = users.to_dict(orient='records')
    return render_template('home.html', user_read=user_read)

@app.route('/dashboard/<int:user_id>', methods=['GET', 'POST'])
def dashboard(user_id):
    users = pd.read_csv(user_csv)
    jobs = pd.read_csv(job_csv)
    applications = pd.read_csv(application_csv)

    user_records = users.loc[users['id'] == user_id].to_dict(orient='records')
    if not user_records:
        return "User not found", 404
    user = user_records[0]

    if request.method == 'POST' and user['role'] == 'recruiter':
        if jobs.empty or jobs['id'].isnull().all():
            new_id = 1
        else:
            new_id = int(jobs['id'].max()) + 1
        new_job = {
            'id': new_id,
            'title': request.form['title'],
            'company': request.form['company'],
            'description': request.form['description'],
            'salary': request.form['salary'],
            'posted_by': user['name']
        }
        jobs = pd.concat([jobs, pd.DataFrame([new_job])], ignore_index=True)
        jobs.to_csv(job_csv, index=False)

    jobs_read = jobs.to_dict(orient='records')
    applied_users = []

    if user['role'] == 'recruiter':
        my_jobs = jobs[jobs['posted_by'] == user['name']]
        for _, job in my_jobs.iterrows():
            applied = applications[applications['job_id'] == job['id']]
            for _, app_row in applied.iterrows():
                applicant = users[users['id'] == app_row['user_id']]
                if not applicant.empty:
                    applied_users.append({
                        'job_title': job['title'],
                        'applicant_name': applicant.iloc[0]['name'],
                        'applicant_email': applicant.iloc[0]['email']
                    })

    return render_template('dashboard.html', user=user, jobs=jobs_read, applied_users=applied_users)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    jobs = pd.read_csv(job_csv)
    job_records = jobs.loc[jobs['id'] == job_id].to_dict(orient='records')
    if not job_records:
        return "Job not found", 404
    job = job_records[0]
    return render_template('job_detail.html', job=job)

@app.route('/apply/job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    applications = pd.read_csv(application_csv)
    jobs = pd.read_csv(job_csv)

    applications['job_id'] = applications['job_id'].astype(int)
    applications['user_id'] = applications['user_id'].astype(int)

    user_id = int(request.form['user_id'])
    already_applied = applications[(applications['job_id'] == job_id) & (applications['user_id'] == user_id)]
    if not already_applied.empty:
        return "Already Applied to this job!"

    new_id = int(applications['id'].max()) + 1 if not applications.empty else 1
    new_application = {'id': new_id, 'job_id': job_id, 'user_id': user_id}
    applications = pd.concat([applications, pd.DataFrame([new_application])], ignore_index=True)
    applications.to_csv(application_csv, index=False)
    return redirect(request.referrer or url_for('dashboard', user_id=user_id))

@app.route('/delete/job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    jobs = pd.read_csv(job_csv)
    jobs = jobs[jobs['id'] != job_id]
    jobs.to_csv(job_csv, index=False)
    return redirect(request.referrer or url_for('home'))

@app.route('/delete/recruiter/<int:user_id>', methods=['POST'])
def delete_recruiter(user_id):
    users = pd.read_csv(user_csv)
    users = users[users['id'] != user_id]
    users.to_csv(user_csv, index=False)
    return redirect('/home')

@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    jobs = pd.read_csv(job_csv)
    job_records = jobs.loc[jobs['id'] == job_id].to_dict(orient='records')
    if not job_records:
        return "Job not found", 404
    job = job_records[0]

    if request.method == 'POST':
        jobs.loc[jobs['id'] == job_id, ['title', 'company', 'description', 'salary']] = [
            request.form['title'],
            request.form['company'],
            request.form['description'],
            request.form['salary']
        ]
        jobs.to_csv(job_csv, index=False)
        return redirect(request.referrer or url_for('home'))

    return render_template('edit_job.html', job=job)

@app.route('/logout')
def logout():
    return redirect('/home')

if __name__ == '__main__':
    app.run(debug=True)
