import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

application = Flask(__name__)
application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'local-development-only-change-me')
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///students-local.db').replace('postgres://', 'postgresql://', 1)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    register_number = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), nullable=False)

with application.app_context():
    db.create_all()

@application.get('/health')
def health():
    return jsonify(status='ok')

@application.get('/')
def index():
    q = request.args.get('q', '').strip()
    query = Student.query
    if q:
        query = query.filter(or_(Student.name.ilike(f'%{q}%'), Student.register_number.ilike(f'%{q}%'), Student.department.ilike(f'%{q}%')))
    return render_template('index.html', students=query.order_by(Student.id.desc()).all(), q=q)

@application.post('/students')
def add_student():
    data = {k: request.form.get(k, '').strip() for k in ('register_number','name','department','email')}
    if not all(data.values()):
        flash('All fields are required.', 'error')
        return redirect(url_for('index'))
    try:
        db.session.add(Student(**data))
        db.session.commit()
        flash('Student added successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Register number already exists.', 'error')
    return redirect(url_for('index'))

@application.post('/students/<int:student_id>/edit')
def edit_student(student_id):
    student = db.get_or_404(Student, student_id)
    data = {k: request.form.get(k, '').strip() for k in ('register_number','name','department','email')}
    if not all(data.values()):
        flash('All fields are required.', 'error')
        return redirect(url_for('index'))
    for k,v in data.items():
        setattr(student, k, v)
    try:
        db.session.commit()
        flash('Student updated.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Register number already exists.', 'error')
    return redirect(url_for('index'))

@application.post('/students/<int:student_id>/delete')
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    application.run(debug=os.environ.get('FLASK_DEBUG') == '1')
