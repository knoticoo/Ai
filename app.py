from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
from PIL import Image
import io
import base64
import numpy as np
import cv2
from ai_analyzer import AIAnalyzer
from ai_guide_generator import AIGuideGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///art_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize AI components
ai_analyzer = AIAnalyzer()
ai_guide_generator = AIGuideGenerator()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    profile_picture = db.Column(db.String(200), default='default.jpg')
    bio = db.Column(db.Text, default='')
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    artworks = db.relationship('Artwork', backref='artist', lazy=True)
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    challenge_submissions = db.relationship('ChallengeSubmission', backref='user', lazy=True)

class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ai_feedback = db.Column(db.Text)
    ai_score = db.Column(db.Float)
    category = db.Column(db.String(50))
    tags = db.Column(db.String(200))

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    difficulty = db.Column(db.String(20), default='Beginner')
    reward_exp = db.Column(db.Integer, default=100)

class ChallengeSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='General')
    likes = db.Column(db.Integer, default=0)
    
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='Beginner')
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom template filter
@app.template_filter('nl2br')
def nl2br_filter(text):
    return text.replace('\n', '<br>\n') if text else ''

# Error handlers
@app.errorhandler(414)
def request_uri_too_long(error):
    return render_template('error.html', 
                         error_code=414, 
                         error_message="Request URI too long"), 414

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

# Routes
@app.route('/')
def index():
    recent_artworks = Artwork.query.order_by(Artwork.upload_date.desc()).limit(6).all()
    active_challenges = Challenge.query.filter_by(is_active=True).limit(3).all()
    return render_template('index.html', recent_artworks=recent_artworks, active_challenges=active_challenges)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_artwork():
    if request.method == 'POST':
        if 'artwork' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['artwork']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Analyze artwork with AI
            ai_feedback, ai_score = ai_analyzer.analyze_artwork(filepath)
            
            artwork = Artwork(
                title=request.form['title'],
                description=request.form['description'],
                filename=unique_filename,
                user_id=current_user.id,
                ai_feedback=ai_feedback,
                ai_score=ai_score,
                category=request.form.get('category', 'Other'),
                tags=request.form.get('tags', '')
            )
            
            db.session.add(artwork)
            db.session.commit()
            
            flash('Artwork uploaded successfully!')
            return redirect(url_for('gallery'))
    
    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Artwork.query
    if category:
        query = query.filter_by(category=category)
    
    artworks = query.order_by(Artwork.upload_date.desc()).paginate(
        page=page, per_page=12, error_out=False)
    
    categories = db.session.query(Artwork.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('gallery.html', artworks=artworks, categories=categories)

@app.route('/artwork/<int:artwork_id>')
def artwork_detail(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    return render_template('artwork_detail.html', artwork=artwork)

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    artworks = Artwork.query.filter_by(user_id=user.id).order_by(Artwork.upload_date.desc()).all()
    return render_template('profile.html', user=user, artworks=artworks)

@app.route('/challenges')
def challenges():
    active_challenges = Challenge.query.filter_by(is_active=True).all()
    completed_challenges = []
    if current_user.is_authenticated:
        completed_challenges = ChallengeSubmission.query.filter_by(
            user_id=current_user.id, is_approved=True).all()
    return render_template('challenges.html', 
                         active_challenges=active_challenges,
                         completed_challenges=completed_challenges)

@app.route('/challenge/<int:challenge_id>')
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    submissions = ChallengeSubmission.query.filter_by(challenge_id=challenge_id).all()
    return render_template('challenge_detail.html', challenge=challenge, submissions=submissions)

@app.route('/submit_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def submit_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    if 'artwork' not in request.files:
        flash('No file selected')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    file = request.files['artwork']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Create artwork first
        artwork = Artwork(
            title=f"Challenge: {challenge.title}",
            description=request.form.get('description', ''),
            filename=unique_filename,
            user_id=current_user.id,
            category='Challenge'
        )
        db.session.add(artwork)
        db.session.flush()  # Get the artwork ID
        
        # Create submission
        submission = ChallengeSubmission(
            user_id=current_user.id,
            challenge_id=challenge_id,
            artwork_id=artwork.id
        )
        db.session.add(submission)
        db.session.commit()
        
        flash('Challenge submission successful!')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

@app.route('/forum')
def forum():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = ForumPost.query
    if category:
        query = query.filter_by(category=category)
    
    posts = query.order_by(ForumPost.created_date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    categories = db.session.query(ForumPost.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('forum.html', posts=posts, categories=categories)

@app.route('/forum/post/<int:post_id>')
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('forum_post.html', post=post)

@app.route('/forum/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        post = ForumPost(
            title=request.form['title'],
            content=request.form['content'],
            author_id=current_user.id,
            category=request.form.get('category', 'General')
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!')
        return redirect(url_for('forum'))
    
    return render_template('new_post.html')

@app.route('/forum/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    comment = Comment(
        content=request.form['content'],
        author_id=current_user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added successfully!')
    return redirect(url_for('forum_post', post_id=post_id))

@app.route('/forum/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return jsonify({'success': True, 'likes': post.likes})

@app.route('/roadmap')
def roadmap():
    learning_paths = LearningPath.query.filter_by(is_active=True).order_by(LearningPath.order).all()
    return render_template('roadmap.html', learning_paths=learning_paths)

@app.route('/ai_guide/<int:path_id>')
@login_required
def ai_guide(path_id):
    learning_path = LearningPath.query.get_or_404(path_id)
    guide_content = ai_guide_generator.generate_guide(learning_path.title, learning_path.description)
    return render_template('ai_guide.html', learning_path=learning_path, guide_content=guide_content)

@app.route('/ai_redraw/<int:artwork_id>')
@login_required
def ai_redraw(artwork_id):
    try:
        artwork = Artwork.query.get_or_404(artwork_id)
        
        # Check if the artwork file exists
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], artwork.filename)
        if not os.path.exists(file_path):
            flash('Original artwork file not found.', 'error')
            return redirect(url_for('gallery'))
        
        # Attempt to redraw the artwork
        redrawn_image, message = ai_analyzer.redraw_artwork(file_path)
        
        if redrawn_image is None:
            flash(f'AI redraw failed: {message}', 'error')
            return redirect(url_for('artwork_detail', artwork_id=artwork_id))
        
        return render_template('ai_redraw.html', artwork=artwork, redrawn_image=redrawn_image, message=message)
    
    except Exception as e:
        flash(f'An error occurred during AI redraw: {str(e)}', 'error')
        return redirect(url_for('gallery'))

# Admin routes
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    users = User.query.all()
    challenges = Challenge.query.all()
    learning_paths = LearningPath.query.all()
    return render_template('admin_panel.html', users=users, challenges=challenges, learning_paths=learning_paths)

@app.route('/admin/challenge/new', methods=['GET', 'POST'])
@login_required
def new_challenge():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        challenge = Challenge(
            title=request.form['title'],
            description=request.form['description'],
            requirements=request.form['requirements'],
            difficulty=request.form['difficulty'],
            reward_exp=int(request.form['reward_exp'])
        )
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully!')
        return redirect(url_for('admin_panel'))
    
    return render_template('new_challenge.html')

@app.route('/admin/learning_path/new', methods=['GET', 'POST'])
@login_required
def new_learning_path():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        learning_path = LearningPath(
            title=request.form['title'],
            description=request.form['description'],
            difficulty=request.form['difficulty'],
            order=int(request.form['order'])
        )
        db.session.add(learning_path)
        db.session.commit()
        flash('Learning path created successfully!')
        return redirect(url_for('admin_panel'))
    
    return render_template('new_learning_path.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)