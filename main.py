import os
import uuid
from flask import Flask, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ---------------- 기본 설정 ----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memories.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# ---------------- DB 모델 ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)   # YYYY-MM-DD
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- 인증 ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = User(
        username=data['username'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '회원가입 완료'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({'message': '로그인 성공'})
    return jsonify({'error': '로그인 실패'}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': '로그아웃 완료'})

# ---------------- 추억 업로드 ----------------
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    date = request.form.get('date')
    content = request.form.get('content')
    file = request.files.get('image')

    filename = None
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    memory = Memory(
        date=date,
        content=content,
        image=filename,
        user_id=current_user.id
    )
    db.session.add(memory)
    db.session.commit()

    return jsonify({'message': '추억 저장 완료'})

# ---------------- 날짜별 조회 ----------------
@app.route('/memories/<date>')
@login_required
def memories_by_date(date):
    memories = Memory.query.filter_by(
        user_id=current_user.id,
        date=date
    ).order_by(Memory.id.desc()).all()

    return jsonify([
        {
            'content': m.content,
            'image': m.image,
            'date': m.date
        } for m in memories
    ])

# ---------------- 실행 ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
