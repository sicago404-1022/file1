import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key' # 실제 서비스 시 복잡한 문자열로 변경
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memories.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- 데이터베이스 모델 ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    memories = db.relationship('Memory', backref='author', lazy=True)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD 형식
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 라우팅 설정 ---

@app.route('/')
@login_required
def index():
    # 기본적으로 1월 달력을 보여줌 (확장 가능)
    return render_template('calendar.html', year=2025)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    date = request.form.get('date')
    content = request.form.get('content')
    file = request.files.get('image')
    
    filename = None
    if file:
        filename = secure_filename(f"{date}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    new_memory = Memory(date=date, content=content, image_path=filename, author=current_user)
    db.session.add(new_memory)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/get_memories/<date>')
@login_required
def get_memories(date):
    memories = Memory.query.filter_by(date=date, user_id=current_user.id).all()
    # 이 부분은 JSON으로 반환하거나 템플릿의 일부로 사용
    return render_template('feed_snippet.html', memories=memories, date=date)

# 로그인/회원가입 등은 생략 (기본 구조만 제공)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # 데이터베이스 생성
    app.run(debug=True)
