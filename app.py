from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # For template compatibility
    is_admin = db.Column(db.Boolean, default=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    artworks = db.relationship('Artwork', backref='artist', lazy=True)
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    challenge_submissions = db.relationship('ChallengeSubmission', backref='user', lazy=True)
    user_achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    user_skills = db.relationship('UserSkill', backref='user', lazy=True)
    battle_submissions = db.relationship('BattleSubmission', backref='user', lazy=True)
    battle_votes = db.relationship('BattleVote', backref='voter', lazy=True)
    stats = db.relationship('UserStats', backref=db.backref('user', uselist=False), lazy=True)

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
    battle_submissions = db.relationship('BattleSubmission', backref='artwork', lazy=True)

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
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='General')  # Keep for backward compatibility
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    
    comments = db.relationship('Comment', backref='post', lazy=True)
    category_obj = db.relationship('ForumCategory', backref='posts')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-comments')
    color = db.Column(db.String(20), default='primary')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserFollow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a user can't follow the same person twice
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'like', 'comment', 'follow', 'battle_win', etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(200))  # Link to relevant page
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional: Link to related objects
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who triggered the notification
    related_post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'))
    related_artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'))
    
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    related_user = db.relationship('User', foreign_keys=[related_user_id])

class ActivityFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # 'upload', 'like', 'comment', 'follow', 'battle_join'
    target_type = db.Column(db.String(50))  # 'artwork', 'post', 'user', 'battle'
    target_id = db.Column(db.Integer)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')

class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='Beginner')
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), default='General')
    estimated_hours = db.Column(db.Integer, default=1)
    thumbnail_url = db.Column(db.String(200))
    prerequisites = db.Column(db.Text)  # JSON string of prerequisite path IDs
    completion_reward_xp = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lessons = db.relationship('Lesson', backref='learning_path', lazy=True, cascade='all, delete-orphan')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_type = db.Column(db.String(20), default='theory')  # theory, practical, quiz, video
    order = db.Column(db.Integer, default=0)
    estimated_minutes = db.Column(db.Integer, default=15)
    video_url = db.Column(db.String(200))
    practice_prompt = db.Column(db.Text)
    quiz_data = db.Column(db.Text)  # JSON string for quiz questions
    completion_xp = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPathProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    current_lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    progress_percentage = db.Column(db.Float, default=0.0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Ensure unique user-path combination
    __table_args__ = (db.UniqueConstraint('user_id', 'path_id'),)

class UserLessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed_at = db.Column(db.DateTime)
    quiz_score = db.Column(db.Float)  # For quiz lessons
    practice_submitted = db.Column(db.Boolean, default=False)  # For practical lessons
    time_spent_minutes = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)  # User's personal notes
    
    # Ensure unique user-lesson combination
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    tutorial_type = db.Column(db.String(20), default='technique')  # technique, tool, style, beginner
    difficulty = db.Column(db.String(20), default='Beginner')
    estimated_minutes = db.Column(db.Integer, default=30)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    thumbnail_url = db.Column(db.String(200))
    tags = db.Column(db.String(200))  # Comma-separated tags
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='tutorials')

class ArtTechnique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # drawing, painting, digital, mixed_media
    difficulty = db.Column(db.String(20), default='Beginner')
    tools_required = db.Column(db.Text)  # JSON string of required tools
    step_by_step = db.Column(db.Text)  # JSON string of steps
    example_images = db.Column(db.Text)  # JSON string of image URLs
    tips_and_tricks = db.Column(db.Text)
    common_mistakes = db.Column(db.Text)
    related_techniques = db.Column(db.Text)  # JSON string of related technique IDs
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', backref='art_techniques')

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='fas fa-trophy')
    category = db.Column(db.String(50), default='General')
    points = db.Column(db.Integer, default=10)
    requirement_type = db.Column(db.String(50))  # 'artworks_count', 'streak', 'likes', etc.
    requirement_value = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    achievement = db.relationship('Achievement', backref='user_achievements')

class SkillTree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'drawing', 'painting', 'digital', etc.
    level = db.Column(db.Integer, default=1)
    experience_required = db.Column(db.Integer, default=100)
    parent_skill_id = db.Column(db.Integer, db.ForeignKey('skill_tree.id'))
    icon = db.Column(db.String(50), default='fas fa-star')
    is_active = db.Column(db.Boolean, default=True)
    
    parent = db.relationship('SkillTree', remote_side=[id], backref='children')

class UserSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_tree.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    unlocked_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill = db.relationship('SkillTree', backref='user_skills')

class ArtBattle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    voting_end_date = db.Column(db.DateTime)
    max_participants = db.Column(db.Integer, default=100)
    entry_fee = db.Column(db.Integer, default=0)  # Experience points
    prize_exp = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, active, voting, completed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    creator = db.relationship('User', backref='created_battles')

class BattleSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    battle_id = db.Column(db.Integer, db.ForeignKey('art_battle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    votes = db.Column(db.Integer, default=0)
    
    battle = db.relationship('ArtBattle', backref='submissions')

class BattleVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    battle_id = db.Column(db.Integer, db.ForeignKey('art_battle.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('battle_submission.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    battle = db.relationship('ArtBattle')
    submission = db.relationship('BattleSubmission')

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    daily_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)
    total_artworks = db.Column(db.Integer, default=0)
    total_likes_received = db.Column(db.Integer, default=0)
    total_comments_made = db.Column(db.Integer, default=0)
    battles_won = db.Column(db.Integer, default=0)
    battles_participated = db.Column(db.Integer, default=0)
    challenges_completed = db.Column(db.Integer, default=0)

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

# Admin initialization function
def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin = User.query.filter_by(username='Knotico').first()
    if not admin:
        admin = User(
            username='Knotico',
            email='admin@artai.com',
            password_hash=generate_password_hash('Millie1991'),
            is_admin=True,
            level=10,
            experience=9999
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user 'Knotico' created successfully!")
    else:
        # Ensure existing user has admin privileges
        admin.is_admin = True
        admin.level = 10
        admin.experience = 9999
        db.session.commit()
        print("✅ Admin user 'Knotico' updated with admin privileges!")

def initialize_achievements():
    """Create default achievements if they don't exist"""
    default_achievements = [
        {
            'name': 'First Upload',
            'description': 'Upload your first artwork to the gallery',
            'icon': 'fas fa-upload',
            'category': 'Milestones',
            'points': 10,
            'requirement_type': 'artworks_count',
            'requirement_value': 1
        },
        {
            'name': 'Art Enthusiast',
            'description': 'Upload 10 artworks',
            'icon': 'fas fa-palette',
            'category': 'Milestones',
            'points': 50,
            'requirement_type': 'artworks_count',
            'requirement_value': 10
        },
        {
            'name': 'Week Warrior',
            'description': 'Maintain a 7-day drawing streak',
            'icon': 'fas fa-fire',
            'category': 'Streaks',
            'points': 30,
            'requirement_type': 'streak',
            'requirement_value': 7
        },
        {
            'name': 'Popular Artist',
            'description': 'Receive 100 likes on your artworks',
            'icon': 'fas fa-heart',
            'category': 'Social',
            'points': 40,
            'requirement_type': 'likes',
            'requirement_value': 100
        },
        {
            'name': 'Battle Rookie',
            'description': 'Participate in your first art battle',
            'icon': 'fas fa-sword-crossed',
            'category': 'Battles',
            'points': 25,
            'requirement_type': 'battles_participated',
            'requirement_value': 1
        },
        {
            'name': 'Champion',
            'description': 'Win your first art battle',
            'icon': 'fas fa-crown',
            'category': 'Battles',
            'points': 100,
            'requirement_type': 'battles_won',
            'requirement_value': 1
        }
    ]
    
    for ach_data in default_achievements:
        existing = Achievement.query.filter_by(name=ach_data['name']).first()
        if not existing:
            achievement = Achievement(**ach_data)
            db.session.add(achievement)
    
    db.session.commit()
    print("✅ Default achievements initialized!")

def initialize_skill_trees():
    """Create default skill trees"""
    default_skills = [
        {
            'name': 'Basic Drawing',
            'description': 'Fundamental drawing skills',
            'category': 'drawing',
            'level': 1,
            'experience_required': 100,
            'icon': 'fas fa-pencil-alt'
        },
        {
            'name': 'Advanced Sketching',
            'description': 'Complex sketching techniques',
            'category': 'drawing',
            'level': 2,
            'experience_required': 250,
            'icon': 'fas fa-pen-fancy'
        },
        {
            'name': 'Color Theory',
            'description': 'Understanding color relationships',
            'category': 'theory',
            'level': 1,
            'experience_required': 150,
            'icon': 'fas fa-palette'
        },
        {
            'name': 'Digital Art',
            'description': 'Digital creation techniques',
            'category': 'digital',
            'level': 1,
            'experience_required': 200,
            'icon': 'fas fa-laptop'
        }
    ]
    
    for skill_data in default_skills:
        existing = SkillTree.query.filter_by(name=skill_data['name']).first()
        if not existing:
            skill = SkillTree(**skill_data)
            db.session.add(skill)
    
    db.session.commit()
    print("✅ Default skill trees initialized!")

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
            ai_analysis = ai_analyzer.analyze_artwork(filepath)
            
            artwork = Artwork(
                title=request.form['title'],
                description=request.form['description'],
                filename=unique_filename,
                user_id=current_user.id,
                ai_feedback=ai_analysis['feedback'],
                ai_score=ai_analysis['score'],
                category=request.form.get('category', 'Other'),
                tags=request.form.get('tags', '')
            )
            
            db.session.add(artwork)
            db.session.commit()
            
            # Update user stats and check achievements
            update_user_stats(current_user.id, 'artwork_uploaded')
            check_achievements(current_user.id)
            
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
    
    # Check if submitting from gallery
    if request.form.get('from_gallery') == 'true':
        selected_artwork_id = request.form.get('selected_artwork_id')
        if not selected_artwork_id:
            flash('No artwork selected from gallery')
            return redirect(url_for('challenge_detail', challenge_id=challenge_id))
        
        # Verify the artwork belongs to the current user
        artwork = Artwork.query.filter_by(id=selected_artwork_id, user_id=current_user.id).first()
        if not artwork:
            flash('Invalid artwork selection')
            return redirect(url_for('challenge_detail', challenge_id=challenge_id))
        
        # Check if already submitted this artwork to this challenge
        existing_submission = ChallengeSubmission.query.filter_by(
            user_id=current_user.id, 
            challenge_id=challenge_id,
            artwork_id=artwork.id
        ).first()
        
        if existing_submission:
            flash('This artwork has already been submitted to this challenge')
            return redirect(url_for('challenge_detail', challenge_id=challenge_id))
        
        # Create submission
        submission = ChallengeSubmission(
            user_id=current_user.id,
            challenge_id=challenge_id,
            artwork_id=artwork.id
        )
        db.session.add(submission)
        db.session.commit()
        
        flash('Gallery artwork submitted successfully!')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    # Original upload logic
    if 'artwork_file' not in request.files:
        flash('No file selected')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    file = request.files['artwork_file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Try to analyze artwork with AI (optional for challenges)
        ai_feedback = "Challenge submission"
        ai_score = 0.0
        try:
            ai_analysis = ai_analyzer.analyze_artwork(filepath)
            ai_feedback = ai_analysis.get('feedback', 'Challenge submission')
            ai_score = ai_analysis.get('score', 0.0)
        except Exception as e:
            print(f"AI analysis failed for challenge submission: {e}")
            # Continue without AI analysis for challenges
        
        # Create artwork first
        artwork = Artwork(
            title=f"Challenge: {challenge.title}",
            description=request.form.get('description', ''),
            filename=unique_filename,
            user_id=current_user.id,
            category='Challenge',
            ai_feedback=ai_feedback,
            ai_score=ai_score
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

@app.route('/api/user/artworks')
@login_required
def api_user_artworks():
    """API endpoint to get current user's artworks for gallery selection"""
    artworks = Artwork.query.filter_by(user_id=current_user.id).order_by(Artwork.upload_date.desc()).all()
    
    artworks_data = []
    for artwork in artworks:
        artworks_data.append({
            'id': artwork.id,
            'title': artwork.title,
            'filename': artwork.filename,
            'description': artwork.description,
            'upload_date': artwork.upload_date.strftime('%Y-%m-%d'),
            'category': artwork.category
        })
    
    return jsonify(artworks_data)

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
    
    # Update user stats
    update_user_stats(current_user.id, 'likes_given')
    check_achievements(post.author_id)
    
    return jsonify({'success': True, 'likes': post.likes})

# Achievement and stats functions
def update_user_stats(user_id, action_type, value=1):
    """Update user statistics"""
    stats = UserStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id)
        db.session.add(stats)
    
    # Ensure all stats values are not None before adding
    if action_type == 'artwork_uploaded':
        stats.total_artworks = (stats.total_artworks or 0) + value
    elif action_type == 'likes_received':
        stats.total_likes_received = (stats.total_likes_received or 0) + value
    elif action_type == 'comment_made':
        stats.total_comments_made = (stats.total_comments_made or 0) + value
    elif action_type == 'battle_won':
        stats.battles_won = (stats.battles_won or 0) + value
    elif action_type == 'battle_participated':
        stats.battles_participated = (stats.battles_participated or 0) + value
    elif action_type == 'challenge_completed':
        stats.challenges_completed = (stats.challenges_completed or 0) + value
    
    # Update streak
    today = datetime.utcnow().date()
    if stats.last_activity_date != today:
        if stats.last_activity_date == today - timedelta(days=1):
            stats.daily_streak = (stats.daily_streak or 0) + 1
        else:
            stats.daily_streak = 1
        stats.last_activity_date = today
        
        # Update longest streak if needed
        if stats.daily_streak > (stats.longest_streak or 0):
            stats.longest_streak = stats.daily_streak
    
    db.session.commit()

def check_achievements(user_id):
    """Check and award achievements for user"""
    user = User.query.get(user_id)
    stats = UserStats.query.filter_by(user_id=user_id).first()
    if not stats:
        return
    
    achievements = Achievement.query.filter_by(is_active=True).all()
    
    for achievement in achievements:
        # Check if user already has this achievement
        existing = UserAchievement.query.filter_by(
            user_id=user_id, 
            achievement_id=achievement.id
        ).first()
        
        if existing:
            continue
        
        # Check if user meets requirements
        earned = False
        if achievement.requirement_type == 'artworks_count':
            earned = stats.total_artworks >= achievement.requirement_value
        elif achievement.requirement_type == 'streak':
            earned = stats.daily_streak >= achievement.requirement_value
        elif achievement.requirement_type == 'likes':
            earned = stats.total_likes_received >= achievement.requirement_value
        elif achievement.requirement_type == 'battles_participated':
            earned = stats.battles_participated >= achievement.requirement_value
        elif achievement.requirement_type == 'battles_won':
            earned = stats.battles_won >= achievement.requirement_value
        
        if earned:
            # Award achievement
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id
            )
            db.session.add(user_achievement)
            
            # Award experience points
            user.experience += achievement.points
            db.session.commit()
            
            print(f"🏆 User {user.username} earned achievement: {achievement.name}")

def create_notification(user_id, type, title, message, url=None, related_user_id=None, related_post_id=None, related_artwork_id=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        url=url,
        related_user_id=related_user_id,
        related_post_id=related_post_id,
        related_artwork_id=related_artwork_id
    )
    db.session.add(notification)
    db.session.flush()  # Get the ID without committing
    return notification

def create_activity(user_id, action_type, target_type=None, target_id=None, message=None):
    """Create an activity feed entry"""
    if not message:
        user = User.query.get(user_id)
        if action_type == 'upload' and target_type == 'artwork':
            artwork = Artwork.query.get(target_id)
            message = f"{user.username} uploaded a new artwork: {artwork.title}"
        elif action_type == 'like' and target_type == 'artwork':
            artwork = Artwork.query.get(target_id)
            message = f"{user.username} liked {artwork.artist.username}'s artwork"
        elif action_type == 'comment' and target_type == 'post':
            post = ForumPost.query.get(target_id)
            message = f"{user.username} commented on {post.title}"
        elif action_type == 'follow' and target_type == 'user':
            followed_user = User.query.get(target_id)
            message = f"{user.username} started following {followed_user.username}"
        elif action_type == 'battle_join':
            battle = ArtBattle.query.get(target_id)
            message = f"{user.username} joined the {battle.title} battle"
        else:
            message = f"{user.username} performed {action_type}"
    
    activity = ActivityFeed(
        user_id=user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        message=message
    )
    db.session.add(activity)
    return activity

def initialize_forum_categories():
    """Initialize default forum categories"""
    categories = [
        {
            'name': 'General Discussion',
            'description': 'General art and platform discussions',
            'icon': 'fas fa-comments',
            'color': 'primary'
        },
        {
            'name': 'Artwork Showcase',
            'description': 'Share your latest creations',
            'icon': 'fas fa-palette',
            'color': 'success'
        },
        {
            'name': 'Tutorials & Tips',
            'description': 'Learn and teach art techniques',
            'icon': 'fas fa-graduation-cap',
            'color': 'info'
        },
        {
            'name': 'Critiques & Feedback',
            'description': 'Get constructive feedback on your work',
            'icon': 'fas fa-search',
            'color': 'warning'
        },
        {
            'name': 'Challenges & Contests',
            'description': 'Participate in art challenges',
            'icon': 'fas fa-trophy',
            'color': 'danger'
        },
        {
            'name': 'AI Art Discussion',
            'description': 'Discuss AI tools and techniques',
            'icon': 'fas fa-robot',
            'color': 'secondary'
        },
        {
            'name': 'Community Events',
            'description': 'Platform news and community events',
            'icon': 'fas fa-calendar',
            'color': 'dark'
        }
    ]
    
    for cat_data in categories:
        existing = ForumCategory.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = ForumCategory(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    print("✅ Forum categories initialized!")

def initialize_learning_paths():
    """Initialize default learning paths and lessons"""
    learning_paths_data = [
        {
            'title': 'Digital Art Fundamentals',
            'description': 'Master the basics of digital art creation, from tools to techniques',
            'difficulty': 'Beginner',
            'category': 'Digital Art',
            'estimated_hours': 8,
            'order': 1,
            'completion_reward_xp': 100,
            'lessons': [
                {
                    'title': 'Introduction to Digital Art Tools',
                    'content': 'Learn about the essential software and hardware for digital art creation. We\'ll cover popular programs like Photoshop, Procreate, and free alternatives like GIMP and Krita.',
                    'lesson_type': 'theory',
                    'order': 1,
                    'estimated_minutes': 20,
                    'completion_xp': 15
                },
                {
                    'title': 'Understanding Layers and Blending Modes',
                    'content': 'Layers are the foundation of digital art. Learn how to organize your artwork, use different blending modes, and create non-destructive workflows.',
                    'lesson_type': 'practical',
                    'order': 2,
                    'estimated_minutes': 30,
                    'practice_prompt': 'Create a simple landscape using at least 5 different layers and 3 different blending modes.',
                    'completion_xp': 20
                },
                {
                    'title': 'Color Theory in Digital Art',
                    'content': 'Explore color relationships, color harmony, and how digital screens affect color perception. Learn to create compelling color palettes.',
                    'lesson_type': 'theory',
                    'order': 3,
                    'estimated_minutes': 25,
                    'completion_xp': 15
                },
                {
                    'title': 'Digital Painting Techniques Quiz',
                    'content': 'Test your knowledge of digital painting fundamentals.',
                    'lesson_type': 'quiz',
                    'order': 4,
                    'estimated_minutes': 10,
                    'quiz_data': '{"questions": [{"question": "What is the primary advantage of using layers in digital art?", "options": ["Better colors", "Non-destructive editing", "Faster rendering", "Smaller file size"], "correct": 1}]}',
                    'completion_xp': 25
                }
            ]
        },
        {
            'title': 'Traditional Drawing Skills',
            'description': 'Build a strong foundation in traditional drawing techniques that apply to all art forms',
            'difficulty': 'Beginner',
            'category': 'Traditional Art',
            'estimated_hours': 12,
            'order': 2,
            'completion_reward_xp': 150,
            'lessons': [
                {
                    'title': 'Line Quality and Control',
                    'content': 'Develop confident, expressive lines. Learn about line weight, texture, and how lines can convey emotion and movement.',
                    'lesson_type': 'practical',
                    'order': 1,
                    'estimated_minutes': 45,
                    'practice_prompt': 'Practice drawing continuous lines without lifting your pencil. Create 10 different line textures.',
                    'completion_xp': 20
                },
                {
                    'title': 'Understanding Perspective',
                    'content': 'Master one-point, two-point, and three-point perspective. Learn how to create depth and dimension in your drawings.',
                    'lesson_type': 'theory',
                    'order': 2,
                    'estimated_minutes': 40,
                    'completion_xp': 18
                },
                {
                    'title': 'Shading and Value Studies',
                    'content': 'Learn to see and render light, shadow, and form. Understand how value creates volume and mood in your artwork.',
                    'lesson_type': 'practical',
                    'order': 3,
                    'estimated_minutes': 50,
                    'practice_prompt': 'Create a value study of 5 simple objects using only 5 different values.',
                    'completion_xp': 25
                }
            ]
        },
        {
            'title': 'Character Design Mastery',
            'description': 'Create compelling characters from concept to final illustration',
            'difficulty': 'Intermediate',
            'category': 'Character Design',
            'estimated_hours': 15,
            'order': 3,
            'prerequisites': '["1", "2"]',  # Requires completion of paths 1 and 2
            'completion_reward_xp': 200,
            'lessons': [
                {
                    'title': 'Character Concept Development',
                    'content': 'Learn to develop unique character concepts. Explore personality, backstory, and how these elements influence visual design.',
                    'lesson_type': 'theory',
                    'order': 1,
                    'estimated_minutes': 35,
                    'completion_xp': 20
                },
                {
                    'title': 'Anatomy and Proportions',
                    'content': 'Understand human anatomy basics and how to stylize proportions for different character types and art styles.',
                    'lesson_type': 'practical',
                    'order': 2,
                    'estimated_minutes': 60,
                    'practice_prompt': 'Draw the same character in 3 different proportion styles (realistic, cartoon, chibi).',
                    'completion_xp': 30
                },
                {
                    'title': 'Character Expressions and Emotions',
                    'content': 'Master facial expressions and body language to convey personality and emotion effectively.',
                    'lesson_type': 'practical',
                    'order': 3,
                    'estimated_minutes': 45,
                    'practice_prompt': 'Create an expression sheet showing 8 different emotions for your character.',
                    'completion_xp': 25
                }
            ]
        },
        {
            'title': 'AI Art Integration',
            'description': 'Learn to effectively combine AI tools with traditional art skills',
            'difficulty': 'Advanced',
            'category': 'AI Art',
            'estimated_hours': 6,
            'order': 4,
            'completion_reward_xp': 120,
            'lessons': [
                {
                    'title': 'Understanding AI Art Tools',
                    'content': 'Explore different AI art platforms, their strengths, and how to choose the right tool for your project.',
                    'lesson_type': 'theory',
                    'order': 1,
                    'estimated_minutes': 25,
                    'completion_xp': 15
                },
                {
                    'title': 'Prompt Engineering for Artists',
                    'content': 'Master the art of writing effective prompts to get the results you want from AI art generators.',
                    'lesson_type': 'practical',
                    'order': 2,
                    'estimated_minutes': 40,
                    'practice_prompt': 'Create 5 different AI artworks by refining and improving your prompts iteratively.',
                    'completion_xp': 25
                },
                {
                    'title': 'AI + Human Collaboration',
                    'content': 'Learn professional workflows for combining AI-generated elements with hand-drawn art for commercial projects.',
                    'lesson_type': 'practical',
                    'order': 3,
                    'estimated_minutes': 50,
                    'practice_prompt': 'Create a final artwork that combines AI-generated backgrounds with hand-drawn characters.',
                    'completion_xp': 30
                }
            ]
        }
    ]
    
    for path_data in learning_paths_data:
        existing_path = LearningPath.query.filter_by(title=path_data['title']).first()
        if not existing_path:
            # Create the learning path
            lessons_data = path_data.pop('lessons')
            path = LearningPath(**path_data)
            db.session.add(path)
            db.session.flush()  # Get the path ID
            
            # Create lessons for this path
            for lesson_data in lessons_data:
                lesson_data['path_id'] = path.id
                lesson = Lesson(**lesson_data)
                db.session.add(lesson)
    
    db.session.commit()
    print("✅ Learning paths and lessons initialized!")

def initialize_tutorials():
    """Initialize sample tutorials"""
    tutorials_data = [
        {
            'title': 'Mastering Digital Brushes',
            'description': 'Learn to create custom brushes and understand brush dynamics in digital art software',
            'content': '''# Mastering Digital Brushes

Digital brushes are the foundation of digital painting. Understanding how to use and create custom brushes will dramatically improve your artwork.

## Understanding Brush Properties

### Opacity and Flow
- **Opacity**: Controls the transparency of each stroke
- **Flow**: Controls how paint builds up within a single stroke

### Brush Dynamics
- **Pressure Sensitivity**: Link brush properties to pen pressure
- **Tilt and Rotation**: Use pen angle for varied effects
- **Velocity**: Stroke speed affects brush behavior

## Creating Custom Brushes

1. Start with a base texture or shape
2. Define brush tip behavior
3. Set up pressure dynamics
4. Test and refine your brush

## Pro Tips
- Save your favorite brush settings as presets
- Experiment with texture brushes for backgrounds
- Use different brushes for different art styles
- Don't rely too heavily on fancy brushes - skill matters more

Practice these techniques and watch your digital art improve dramatically!''',
            'tutorial_type': 'technique',
            'difficulty': 'Intermediate',
            'estimated_minutes': 45,
            'tags': 'digital art, brushes, technique, photoshop, procreate',
            'is_featured': True
        },
        {
            'title': 'Color Theory for Beginners',
            'description': 'Understand the fundamentals of color and how to create harmonious color schemes',
            'content': '''# Color Theory Fundamentals

Color is one of the most powerful tools in an artist's arsenal. Understanding color theory will help you create more impactful and harmonious artwork.

## The Color Wheel

### Primary Colors
- Red, Blue, Yellow (traditional)
- Red, Green, Blue (digital/light)

### Secondary Colors
Created by mixing two primary colors

### Tertiary Colors
Created by mixing a primary and secondary color

## Color Relationships

### Complementary Colors
Colors opposite each other on the color wheel
- Create high contrast and vibrant effects
- Use sparingly for maximum impact

### Analogous Colors
Colors next to each other on the color wheel
- Create harmony and unity
- Great for natural, peaceful scenes

### Triadic Colors
Three colors evenly spaced on the color wheel
- Vibrant but balanced
- Choose one dominant color

## Color Temperature
- **Warm colors**: Reds, oranges, yellows (energetic, advancing)
- **Cool colors**: Blues, greens, purples (calming, receding)

## Practical Applications
1. Choose a dominant color temperature
2. Use the opposite temperature for accents
3. Consider the mood you want to convey
4. Study master paintings for color inspiration

Remember: Rules are meant to be broken once you understand them!''',
            'tutorial_type': 'theory',
            'difficulty': 'Beginner',
            'estimated_minutes': 30,
            'tags': 'color theory, fundamentals, harmony, painting',
            'is_featured': True
        }
    ]
    
    admin_user = User.query.filter_by(username='Knotico').first()
    if admin_user:
        for tutorial_data in tutorials_data:
            existing_tutorial = Tutorial.query.filter_by(title=tutorial_data['title']).first()
            if not existing_tutorial:
                tutorial_data['author_id'] = admin_user.id
                tutorial = Tutorial(**tutorial_data)
                db.session.add(tutorial)
    
    db.session.commit()
    print("✅ Sample tutorials initialized!")

@app.route('/roadmap')
def roadmap():
    learning_paths = LearningPath.query.filter_by(is_active=True).order_by(LearningPath.order).all()
    return render_template('roadmap.html', learning_paths=learning_paths)

@app.route('/achievements')
def achievements():
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    user_achievements = []
    
    if current_user.is_authenticated:
        user_achievements = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('achievements.html', achievements=all_achievements, user_achievements=user_achievements)

@app.route('/leaderboard')
def leaderboard():
    # Top artists by experience
    top_artists = User.query.order_by(User.experience.desc()).limit(10).all()
    
    # Top by different categories
    top_uploaders = db.session.query(User, UserStats).join(UserStats).order_by(UserStats.total_artworks.desc()).limit(10).all()
    top_liked = db.session.query(User, UserStats).join(UserStats).order_by(UserStats.total_likes_received.desc()).limit(10).all()
    top_streaks = db.session.query(User, UserStats).join(UserStats).order_by(UserStats.longest_streak.desc()).limit(10).all()
    
    return render_template('leaderboard.html', 
                         top_artists=top_artists,
                         top_uploaders=top_uploaders,
                         top_liked=top_liked,
                         top_streaks=top_streaks)

@app.route('/battles')
def art_battles():
    active_battles = ArtBattle.query.filter_by(status='active').all()
    upcoming_battles = ArtBattle.query.filter_by(status='upcoming').all()
    completed_battles = ArtBattle.query.filter_by(status='completed').order_by(ArtBattle.end_date.desc()).limit(5).all()
    
    return render_template('art_battles.html', 
                         active_battles=active_battles,
                         upcoming_battles=upcoming_battles,
                         completed_battles=completed_battles)

@app.route('/battle/<int:battle_id>')
def battle_detail(battle_id):
    battle = ArtBattle.query.get_or_404(battle_id)
    submissions = BattleSubmission.query.filter_by(battle_id=battle_id).all()
    
    user_submission = None
    if current_user.is_authenticated:
        user_submission = BattleSubmission.query.filter_by(
            battle_id=battle_id, 
            user_id=current_user.id
        ).first()
    
    return render_template('battle_detail.html', 
                         battle=battle, 
                         submissions=submissions, 
                         user_submission=user_submission)

@app.route('/profile/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    stats = UserStats.query.filter_by(user_id=user.id).first()
    
    if not stats:
        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
    
    # Get user's artworks
    artworks = Artwork.query.filter_by(user_id=user.id).order_by(Artwork.upload_date.desc()).limit(12).all()
    
    # Get user's achievements
    user_achievements = db.session.query(Achievement).join(UserAchievement).filter(
        UserAchievement.user_id == user.id
    ).all()
    
    return render_template('profile_enhanced.html', 
                         user=user, 
                         stats=stats, 
                         artworks=artworks, 
                         achievements=user_achievements)

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

@app.route('/ai_style_transfer/<int:artwork_id>')
@login_required
def ai_style_transfer_page(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    
    available_styles = [
        {'id': 'van_gogh', 'name': 'Van Gogh', 'description': 'Swirling brushstrokes and vivid colors'},
        {'id': 'picasso', 'name': 'Picasso', 'description': 'Cubist geometric abstraction'},
        {'id': 'monet', 'name': 'Monet', 'description': 'Soft impressionist lighting'},
        {'id': 'dali', 'name': 'Salvador Dalí', 'description': 'Surrealist dream-like distortions'},
        {'id': 'watercolor', 'name': 'Watercolor', 'description': 'Soft watercolor painting effect'},
        {'id': 'oil_painting', 'name': 'Oil Painting', 'description': 'Rich oil painting texture'},
        {'id': 'sketch', 'name': 'Pencil Sketch', 'description': 'Classic pencil drawing style'},
        {'id': 'anime', 'name': 'Anime Style', 'description': 'Japanese animation art style'}
    ]
    
    return render_template('ai_style_transfer.html', artwork=artwork, styles=available_styles)

@app.route('/apply_style/<int:artwork_id>/<style_name>')
@login_required
def apply_style(artwork_id, style_name):
    try:
        artwork = Artwork.query.get_or_404(artwork_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], artwork.filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Artwork file not found'})
        
        styled_image, message = ai_analyzer.apply_style_transfer(file_path, style_name)
        
        if styled_image is None:
            return jsonify({'success': False, 'error': message})
        
        return jsonify({
            'success': True, 
            'styled_image': styled_image, 
            'message': message,
            'style_name': style_name.replace('_', ' ').title()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/color_palette/<int:artwork_id>')
@login_required
def generate_palette(artwork_id):
    palette_type = request.args.get('type', 'harmonious')
    
    try:
        artwork = Artwork.query.get_or_404(artwork_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], artwork.filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Artwork file not found'})
        
        palette_data, message = ai_analyzer.generate_color_palette(file_path, palette_type)
        
        if palette_data is None:
            return jsonify({'success': False, 'error': message})
        
        return jsonify({
            'success': True,
            'palette': palette_data,
            'message': message
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Learning & Education Routes
@app.route('/learning')
def learning_center():
    # Get learning paths organized by category
    categories = {}
    all_paths = LearningPath.query.filter_by(is_active=True).order_by(LearningPath.order).all()
    
    for path in all_paths:
        category = path.category
        if category not in categories:
            categories[category] = []
        
        # Get user progress if logged in
        user_progress = None
        if current_user.is_authenticated:
            user_progress = UserPathProgress.query.filter_by(
                user_id=current_user.id, path_id=path.id
            ).first()
        
        categories[category].append({
            'path': path,
            'progress': user_progress
        })
    
    # Get featured tutorials
    featured_tutorials = Tutorial.query.filter_by(is_featured=True, is_active=True).limit(6).all()
    
    # Get recent tutorials
    recent_tutorials = Tutorial.query.filter_by(is_active=True).order_by(
        Tutorial.created_at.desc()
    ).limit(8).all()
    
    return render_template('learning_center.html', 
                         categories=categories,
                         featured_tutorials=featured_tutorials,
                         recent_tutorials=recent_tutorials)

@app.route('/learning/path/<int:path_id>')
def learning_path_detail(path_id):
    path = LearningPath.query.get_or_404(path_id)
    lessons = Lesson.query.filter_by(path_id=path_id, is_active=True).order_by(Lesson.order).all()
    
    # Get user progress if logged in
    user_progress = None
    lesson_progress = {}
    if current_user.is_authenticated:
        user_progress = UserPathProgress.query.filter_by(
            user_id=current_user.id, path_id=path_id
        ).first()
        
        # Get progress for each lesson
        for lesson in lessons:
            progress = UserLessonProgress.query.filter_by(
                user_id=current_user.id, lesson_id=lesson.id
            ).first()
            lesson_progress[lesson.id] = progress
    
    return render_template('learning_path_detail.html', 
                         path=path, 
                         lessons=lessons,
                         user_progress=user_progress,
                         lesson_progress=lesson_progress)

@app.route('/learning/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    path = lesson.learning_path
    
    # Get or create user progress
    user_progress = UserPathProgress.query.filter_by(
        user_id=current_user.id, path_id=path.id
    ).first()
    
    if not user_progress:
        user_progress = UserPathProgress(
            user_id=current_user.id,
            path_id=path.id,
            current_lesson_id=lesson_id
        )
        db.session.add(user_progress)
        db.session.commit()
    
    # Get lesson progress
    lesson_progress = UserLessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()
    
    # Get next and previous lessons
    all_lessons = Lesson.query.filter_by(path_id=path.id, is_active=True).order_by(Lesson.order).all()
    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson_id), 0)
    
    next_lesson = all_lessons[current_index + 1] if current_index + 1 < len(all_lessons) else None
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    
    return render_template('lesson_detail.html',
                         lesson=lesson,
                         path=path,
                         lesson_progress=lesson_progress,
                         next_lesson=next_lesson,
                         prev_lesson=prev_lesson)

@app.route('/learning/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Get or create lesson progress
    lesson_progress = UserLessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()
    
    if not lesson_progress:
        lesson_progress = UserLessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        db.session.add(lesson_progress)
    
    # Mark as completed if not already
    if not lesson_progress.completed_at:
        lesson_progress.completed_at = datetime.utcnow()
        
        # Award experience points
        current_user.experience += lesson.completion_xp
        
        # Handle lesson-specific completion
        if lesson.lesson_type == 'quiz':
            quiz_score = float(request.form.get('quiz_score', 0))
            lesson_progress.quiz_score = quiz_score
        elif lesson.lesson_type == 'practical':
            lesson_progress.practice_submitted = True
            notes = request.form.get('notes', '')
            lesson_progress.notes = notes
        
        # Update path progress
        path_progress = UserPathProgress.query.filter_by(
            user_id=current_user.id, path_id=lesson.path_id
        ).first()
        
        if path_progress:
            # Calculate overall progress
            total_lessons = Lesson.query.filter_by(path_id=lesson.path_id, is_active=True).count()
            completed_lessons = UserLessonProgress.query.filter_by(
                user_id=current_user.id
            ).join(Lesson).filter(
                Lesson.path_id == lesson.path_id,
                UserLessonProgress.completed_at.isnot(None)
            ).count()
            
            path_progress.progress_percentage = (completed_lessons / total_lessons) * 100
            
            # Check if path is completed
            if completed_lessons == total_lessons and not path_progress.completed_at:
                path_progress.completed_at = datetime.utcnow()
                current_user.experience += lesson.learning_path.completion_reward_xp
                
                # Create notification
                create_notification(
                    user_id=current_user.id,
                    type='achievement',
                    title='Learning Path Completed!',
                    message=f'You completed the "{lesson.learning_path.title}" learning path!',
                    url=url_for('learning_path_detail', path_id=lesson.path_id)
                )
        
        # Create activity
        create_activity(
            user_id=current_user.id,
            action_type='lesson_complete',
            target_type='lesson',
            target_id=lesson_id,
            message=f"{current_user.username} completed lesson: {lesson.title}"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Lesson completed! +{lesson.completion_xp} XP',
            'xp_gained': lesson.completion_xp
        })
    
    return jsonify({'success': True, 'message': 'Lesson already completed'})

@app.route('/tutorials')
def tutorials():
    # Filter options
    difficulty = request.args.get('difficulty', '')
    tutorial_type = request.args.get('type', '')
    search = request.args.get('search', '')
    
    # Build query
    query = Tutorial.query.filter_by(is_active=True)
    
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if tutorial_type:
        query = query.filter_by(tutorial_type=tutorial_type)
    if search:
        query = query.filter(Tutorial.title.contains(search) | Tutorial.tags.contains(search))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    tutorials_paginated = query.order_by(Tutorial.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get featured tutorials for sidebar
    featured = Tutorial.query.filter_by(is_featured=True, is_active=True).limit(5).all()
    
    return render_template('tutorials.html', 
                         tutorials=tutorials_paginated,
                         featured_tutorials=featured,
                         current_filters={
                             'difficulty': difficulty,
                             'type': tutorial_type,
                             'search': search
                         })

@app.route('/tutorial/<int:tutorial_id>')
def tutorial_detail(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Increment view count
    tutorial.views += 1
    db.session.commit()
    
    # Get related tutorials
    related = Tutorial.query.filter(
        Tutorial.tutorial_type == tutorial.tutorial_type,
        Tutorial.id != tutorial_id,
        Tutorial.is_active == True
    ).limit(4).all()
    
    return render_template('tutorial_detail.html', tutorial=tutorial, related_tutorials=related)

# Community Routes
@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot follow yourself'})
    
    target_user = User.query.get_or_404(user_id)
    
    # Check if already following
    existing_follow = UserFollow.query.filter_by(
        follower_id=current_user.id,
        following_id=user_id
    ).first()
    
    if existing_follow:
        return jsonify({'success': False, 'error': 'Already following this user'})
    
    # Create follow relationship
    follow = UserFollow(
        follower_id=current_user.id,
        following_id=user_id
    )
    db.session.add(follow)
    
    # Create notification for followed user
    create_notification(
        user_id=user_id,
        type='follow',
        title='New Follower',
        message=f'{current_user.username} started following you!',
        url=url_for('profile', username=current_user.username),
        related_user_id=current_user.id
    )
    
    # Create activity
    create_activity(
        user_id=current_user.id,
        action_type='follow',
        target_type='user',
        target_id=user_id
    )
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Now following {target_user.username}'})

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    follow = UserFollow.query.filter_by(
        follower_id=current_user.id,
        following_id=user_id
    ).first()
    
    if not follow:
        return jsonify({'success': False, 'error': 'Not following this user'})
    
    db.session.delete(follow)
    db.session.commit()
    
    target_user = User.query.get(user_id)
    return jsonify({'success': True, 'message': f'Unfollowed {target_user.username}'})

@app.route('/notifications')
@login_required
def notifications():
    # Mark all notifications as read when viewing
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.is_read = True
    
    # Get all notifications
    all_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    db.session.commit()
    
    return render_template('notifications.html', notifications=all_notifications)

@app.route('/activity_feed')
def activity_feed():
    # Get activities from followed users if logged in
    if current_user.is_authenticated:
        # Get user's follows
        following_ids = db.session.query(UserFollow.following_id).filter_by(
            follower_id=current_user.id
        ).subquery()
        
        # Get activities from followed users + own activities
        activities = ActivityFeed.query.filter(
            db.or_(
                ActivityFeed.user_id.in_(following_ids),
                ActivityFeed.user_id == current_user.id
            )
        ).order_by(ActivityFeed.created_at.desc()).limit(50).all()
    else:
        # Public activity feed
        activities = ActivityFeed.query.order_by(
            ActivityFeed.created_at.desc()
        ).limit(20).all()
    
    return render_template('activity_feed.html', activities=activities)

@app.route('/forum/categories')
def forum_categories():
    categories = ForumCategory.query.all()
    
    # Get post counts and latest posts for each category
    category_stats = []
    for category in categories:
        post_count = ForumPost.query.filter_by(category_id=category.id).count()
        latest_post = ForumPost.query.filter_by(category_id=category.id).order_by(
            ForumPost.created_date.desc()
        ).first()
        
        category_stats.append({
            'category': category,
            'post_count': post_count,
            'latest_post': latest_post
        })
    
    return render_template('forum_categories.html', category_stats=category_stats)

@app.route('/forum/category/<int:category_id>')
def forum_category_posts(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = ForumPost.query.filter_by(category_id=category_id).order_by(
        ForumPost.is_pinned.desc(),
        ForumPost.created_date.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('forum_category_posts.html', category=category, posts=posts)

@app.route('/users/discover')
def discover_users():
    # Get top artists by various metrics
    top_by_artworks = User.query.join(UserStats).order_by(
        UserStats.total_artworks.desc()
    ).limit(10).all()
    
    top_by_experience = User.query.order_by(User.experience.desc()).limit(10).all()
    
    recently_joined = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get users with most followers
    follower_counts = db.session.query(
        UserFollow.following_id,
        db.func.count(UserFollow.follower_id).label('follower_count')
    ).group_by(UserFollow.following_id).order_by(
        db.func.count(UserFollow.follower_id).desc()
    ).limit(10).all()
    
    popular_users = []
    for user_id, count in follower_counts:
        user = User.query.get(user_id)
        if user:
            popular_users.append((user, count))
    
    return render_template('discover_users.html', 
                         top_by_artworks=top_by_artworks,
                         top_by_experience=top_by_experience,
                         recently_joined=recently_joined,
                         popular_users=popular_users)

# Art Battle Routes
@app.route('/battles/create', methods=['GET', 'POST'])
@login_required
def create_battle():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        theme = request.form['theme']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M')
        voting_end_date = datetime.strptime(request.form['voting_end_date'], '%Y-%m-%dT%H:%M')
        max_participants = int(request.form.get('max_participants', 50))
        prize_description = request.form.get('prize_description', '')
        
        # Validate dates
        if start_date >= end_date or end_date >= voting_end_date:
            flash('Invalid dates. Start < Submission End < Voting End', 'error')
            return redirect(url_for('create_battle'))
        
        battle = ArtBattle(
            title=title,
            description=description,
            theme=theme,
            start_date=start_date,
            end_date=end_date,
            voting_end_date=voting_end_date,
            max_participants=max_participants,
            prize_description=prize_description,
            creator_id=current_user.id
        )
        
        db.session.add(battle)
        db.session.commit()
        
        flash('Art Battle created successfully!', 'success')
        return redirect(url_for('battle_detail', battle_id=battle.id))
    
    return render_template('create_battle.html')

@app.route('/battle/<int:battle_id>/join', methods=['POST'])
@login_required
def join_battle(battle_id):
    battle = ArtBattle.query.get_or_404(battle_id)
    
    # Check if battle is open for submissions
    now = datetime.utcnow()
    if now < battle.start_date:
        return jsonify({'success': False, 'error': 'Battle has not started yet'})
    if now > battle.end_date:
        return jsonify({'success': False, 'error': 'Battle submission period has ended'})
    
    # Check if user already submitted
    existing_submission = BattleSubmission.query.filter_by(
        battle_id=battle_id, user_id=current_user.id
    ).first()
    
    if existing_submission:
        return jsonify({'success': False, 'error': 'You have already submitted to this battle'})
    
    # Check if battle is full
    current_participants = BattleSubmission.query.filter_by(battle_id=battle_id).count()
    if current_participants >= battle.max_participants:
        return jsonify({'success': False, 'error': 'Battle is full'})
    
    return jsonify({'success': True, 'message': 'You can now submit your artwork'})

@app.route('/battle/<int:battle_id>/submit', methods=['POST'])
@login_required
def submit_to_battle(battle_id):
    battle = ArtBattle.query.get_or_404(battle_id)
    
    # Validation checks (same as join_battle)
    now = datetime.utcnow()
    if now < battle.start_date or now > battle.end_date:
        flash('Battle submission period is not active', 'error')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    existing_submission = BattleSubmission.query.filter_by(
        battle_id=battle_id, user_id=current_user.id
    ).first()
    
    if existing_submission:
        flash('You have already submitted to this battle', 'error')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    # Handle file upload
    if 'artwork_file' not in request.files:
        flash('No artwork file provided', 'error')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    file = request.files['artwork_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    if file and allowed_file(file.filename):
        # Create artwork entry
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Create artwork
        artwork = Artwork(
            title=request.form.get('title', f'Battle Entry: {battle.title}'),
            description=request.form.get('description', f'My submission for {battle.title}'),
            filename=unique_filename,
            artist_id=current_user.id
        )
        db.session.add(artwork)
        db.session.flush()  # Get artwork ID
        
        # Create battle submission
        submission = BattleSubmission(
            battle_id=battle_id,
            user_id=current_user.id,
            artwork_id=artwork.id,
            submission_title=request.form.get('title', artwork.title)
        )
        db.session.add(submission)
        
        # Update user stats
        update_user_stats(current_user.id, 'battles_participated')
        
        db.session.commit()
        
        flash('Successfully submitted to the battle!', 'success')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    flash('Invalid file type', 'error')
    return redirect(url_for('battle_detail', battle_id=battle_id))

@app.route('/battle/<int:battle_id>/vote/<int:submission_id>', methods=['POST'])
@login_required
def vote_battle(battle_id, submission_id):
    battle = ArtBattle.query.get_or_404(battle_id)
    submission = BattleSubmission.query.get_or_404(submission_id)
    
    # Check if voting is active
    now = datetime.utcnow()
    if now <= battle.end_date:
        return jsonify({'success': False, 'error': 'Voting has not started yet'})
    if now > battle.voting_end_date:
        return jsonify({'success': False, 'error': 'Voting has ended'})
    
    # Check if user is trying to vote for their own submission
    if submission.user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot vote for your own submission'})
    
    # Check if user already voted in this battle
    existing_vote = BattleVote.query.filter_by(
        battle_id=battle_id, user_id=current_user.id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.submission_id = submission_id
        existing_vote.voted_at = datetime.utcnow()
    else:
        # Create new vote
        vote = BattleVote(
            battle_id=battle_id,
            submission_id=submission_id,
            user_id=current_user.id
        )
        db.session.add(vote)
    
    db.session.commit()
    
    # Get updated vote count
    vote_count = BattleVote.query.filter_by(submission_id=submission_id).count()
    
    return jsonify({
        'success': True, 
        'message': 'Vote recorded!',
        'vote_count': vote_count
    })

@app.route('/battle/<int:battle_id>/results')
def battle_results(battle_id):
    battle = ArtBattle.query.get_or_404(battle_id)
    
    # Check if voting has ended
    now = datetime.utcnow()
    if now <= battle.voting_end_date:
        flash('Voting is still in progress', 'info')
        return redirect(url_for('battle_detail', battle_id=battle_id))
    
    # Get submissions with vote counts
    submissions = db.session.query(
        BattleSubmission,
        Artwork,
        User,
        db.func.count(BattleVote.id).label('vote_count')
    ).join(
        Artwork, BattleSubmission.artwork_id == Artwork.id
    ).join(
        User, BattleSubmission.user_id == User.id
    ).outerjoin(
        BattleVote, BattleSubmission.id == BattleVote.submission_id
    ).filter(
        BattleSubmission.battle_id == battle_id
    ).group_by(
        BattleSubmission.id
    ).order_by(
        db.func.count(BattleVote.id).desc()
    ).all()
    
    # Update battle status if not already done
    if battle.status != 'completed':
        battle.status = 'completed'
        
        # Award winner
        if submissions:
            winner_submission = submissions[0][0]  # BattleSubmission object
            battle.winner_id = winner_submission.user_id
            
            # Update winner stats
            update_user_stats(winner_submission.user_id, 'battles_won')
            
            # Award experience to winner
            winner = User.query.get(winner_submission.user_id)
            winner.experience += 100  # Battle win bonus
        
        db.session.commit()
    
    return render_template('battle_results.html', battle=battle, submissions=submissions)

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
    
    # Calculate admin statistics
    stats = {
        'total_users': User.query.count(),
        'total_artworks': Artwork.query.count(),
        'total_challenges': Challenge.query.filter_by(is_active=True).count(),
        'total_posts': ForumPost.query.count(),
        'total_battles': ArtBattle.query.count(),
        'total_learning_paths': LearningPath.query.filter_by(is_active=True).count(),
        'recent_signups': User.query.filter(User.join_date >= datetime.utcnow() - timedelta(days=7)).count(),
        'active_battles': ArtBattle.query.filter(ArtBattle.end_date > datetime.utcnow()).count()
    }
    
    return render_template('admin_panel.html', users=users, challenges=challenges, 
                         learning_paths=learning_paths, stats=stats)

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

@app.route('/admin/ai_learning_path', methods=['GET', 'POST'])
@login_required
def admin_ai_learning_path():
    """Create learning paths with AI assistance"""
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        difficulty = request.form.get('difficulty', 'Beginner')
        description = request.form.get('description', '').strip()
        
        if not topic:
            flash('Topic is required')
            return render_template('admin_ai_learning_path.html')
        
        try:
            # Generate AI-powered learning path
            ai_content = ai_guide_generator.generate_comprehensive_learning_path(
                topic, difficulty, description
            )
            
            # Create the learning path
            learning_path = LearningPath(
                title=ai_content['title'],
                description=ai_content['description'],
                difficulty=difficulty,
                order=LearningPath.query.count() + 1,
                category=ai_content.get('category', 'General'),
                estimated_hours=ai_content.get('estimated_hours', 2)
            )
            db.session.add(learning_path)
            db.session.flush()  # Get the ID
            
            # Create lessons for this learning path
            for lesson_data in ai_content.get('lessons', []):
                lesson = Lesson(
                    path_id=learning_path.id,
                    title=lesson_data['title'],
                    content=lesson_data['content'],
                    lesson_type=lesson_data.get('type', 'theory'),
                    order=lesson_data['order'],
                    estimated_minutes=lesson_data.get('estimated_minutes', 15),
                    completion_xp=lesson_data.get('xp', 10)
                )
                db.session.add(lesson)
            
            db.session.commit()
            flash(f'AI-generated learning path "{ai_content["title"]}" created successfully with {len(ai_content.get("lessons", []))} lessons!')
            return redirect(url_for('admin_panel'))
            
        except Exception as e:
            flash(f'Error creating AI learning path: {str(e)}')
            return render_template('admin_ai_learning_path.html')
    
    return render_template('admin_ai_learning_path.html')

@app.route('/start_learning', methods=['GET', 'POST'])
@login_required
def start_learning():
    """User-facing learning path creation with AI"""
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        skill_level = request.form.get('skill_level', 'Beginner')
        interests = request.form.get('interests', '').strip()
        
        if not topic:
            flash('Please specify what you want to learn')
            return render_template('start_learning.html')
        
        try:
            # Generate personalized learning path with AI
            description = f"Personalized learning path for {current_user.username}"
            if interests:
                description += f" with focus on {interests}"
                
            ai_content = ai_guide_generator.generate_comprehensive_learning_path(
                topic, skill_level, description
            )
            
            # Check if learning path already exists for this user and topic
            existing_path = LearningPath.query.filter(
                LearningPath.title.ilike(f"%{topic}%"),
                LearningPath.difficulty == skill_level
            ).first()
            
            if existing_path:
                # Check if user already enrolled
                existing_progress = UserPathProgress.query.filter_by(
                    user_id=current_user.id,
                    path_id=existing_path.id
                ).first()
                
                if existing_progress:
                    flash(f'You are already enrolled in "{existing_path.title}"!')
                    return redirect(url_for('ai_guide', path_id=existing_path.id))
                else:
                    # Enroll user in existing path
                    progress = UserPathProgress(
                        user_id=current_user.id,
                        path_id=existing_path.id
                    )
                    db.session.add(progress)
                    db.session.commit()
                    flash(f'Enrolled in existing course: "{existing_path.title}"!')
                    return redirect(url_for('ai_guide', path_id=existing_path.id))
            
            # Create new learning path
            learning_path = LearningPath(
                title=ai_content['title'],
                description=ai_content['description'],
                difficulty=skill_level,
                order=LearningPath.query.count() + 1,
                category=ai_content.get('category', 'Personalized'),
                estimated_hours=ai_content.get('estimated_hours', 2)
            )
            db.session.add(learning_path)
            db.session.flush()
            
            # Create lessons
            for lesson_data in ai_content.get('lessons', []):
                lesson = Lesson(
                    path_id=learning_path.id,
                    title=lesson_data['title'],
                    content=lesson_data['content'],
                    lesson_type=lesson_data.get('type', 'theory'),
                    order=lesson_data['order'],
                    estimated_minutes=lesson_data.get('estimated_minutes', 15),
                    completion_xp=lesson_data.get('xp', 10)
                )
                db.session.add(lesson)
            
            # Enroll user in the new path
            progress = UserPathProgress(
                user_id=current_user.id,
                path_id=learning_path.id
            )
            db.session.add(progress)
            db.session.commit()
            
            flash(f'🎉 Created your personalized learning path: "{ai_content["title"]}"!')
            return redirect(url_for('ai_guide', path_id=learning_path.id))
            
        except Exception as e:
            flash(f'Error creating your learning path: {str(e)}')
            return render_template('start_learning.html')
    
    return render_template('start_learning.html')

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Advanced analytics dashboard for admins"""
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    # User growth analytics
    user_growth = []
    for i in range(30):  # Last 30 days
        date = datetime.utcnow().date() - timedelta(days=i)
        count = User.query.filter(User.join_date >= date).count()
        user_growth.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    # Most active users
    top_users = db.session.query(User, UserStats).join(UserStats).order_by(
        (UserStats.total_artworks + UserStats.total_comments_made + UserStats.battles_participated).desc()
    ).limit(10).all()
    
    # Popular learning paths
    popular_paths = db.session.query(LearningPath, db.func.count(UserPathProgress.id)).outerjoin(
        UserPathProgress
    ).group_by(LearningPath.id).order_by(db.func.count(UserPathProgress.id).desc()).limit(5).all()
    
    # Battle participation stats
    battle_stats = {
        'total_battles': ArtBattle.query.count(),
        'active_battles': ArtBattle.query.filter(ArtBattle.end_date > datetime.utcnow()).count(),
        'completed_battles': ArtBattle.query.filter(ArtBattle.end_date <= datetime.utcnow()).count(),
        'total_submissions': BattleSubmission.query.count()
    }
    
    # Engagement statistics
    engagement_stats = {
        'total_likes': 0,  # Would need to implement likes system
        'total_comments': Comment.query.count() if 'Comment' in globals() else 0,
        'total_shares': 0,  # Would need to implement sharing system
        'total_views': 0   # Would need to implement view tracking
    }
    
    # Basic analytics data
    analytics_data = {
        'total_users': User.query.count(),
        'total_artworks': Artwork.query.count(),
        'active_challenges': Challenge.query.filter_by(is_active=True).count(),
        'active_battles': ArtBattle.query.filter(ArtBattle.end_date > datetime.utcnow()).count(),
        'new_users_this_week': User.query.filter(User.join_date >= datetime.utcnow() - timedelta(days=7)).count(),
        'new_artworks_this_week': Artwork.query.filter(Artwork.upload_date >= datetime.utcnow() - timedelta(days=7)).count(),
        'total_challenge_submissions': ChallengeSubmission.query.count(),
        'total_battle_participants': BattleSubmission.query.count()
    }
    
    return render_template('admin_analytics.html', 
                         user_growth=user_growth, 
                         top_users=top_users,
                         popular_paths=popular_paths,
                         battle_stats=battle_stats,
                         engagement_stats=engagement_stats,
                         **analytics_data)

@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def toggle_user_admin(user_id):
    """Toggle admin status for a user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'is_admin': user.is_admin,
        'message': f'User {user.username} admin status updated'
    })

@app.route('/admin/maintenance')
@login_required
def maintenance_panel():
    """System maintenance and cleanup tools"""
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    # System health checks
    health_stats = {
        'database_size': 'N/A',  # Would need OS-specific implementation
        'orphaned_files': 0,     # Could check for files without database records
        'inactive_users': User.query.filter(User.join_date < datetime.utcnow() - timedelta(days=90)).count(),
        'empty_learning_paths': LearningPath.query.filter(~LearningPath.lessons.any()).count(),
        'unmoderated_posts': ForumPost.query.filter_by(is_approved=False).count() if hasattr(ForumPost, 'is_approved') else 0
    }
    
    return render_template('maintenance_panel.html', health_stats=health_stats)

@app.route('/api/user_activity')
@login_required
def user_activity_api():
    """API endpoint for user activity data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Daily activity for the last 7 days
    activity_data = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        
        # Count various activities for this date
        artworks = Artwork.query.filter(
            db.func.date(Artwork.upload_date) == date
        ).count()
        
        posts = ForumPost.query.filter(
            db.func.date(ForumPost.created_date) == date
        ).count()
        
        activity_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'artworks': artworks,
            'posts': posts,
            'total': artworks + posts
        })
    
    return jsonify(activity_data)

# Advanced Drawing Features
@app.route('/draw')
@login_required
def advanced_drawing():
    """Advanced drawing studio with AI features"""
    return render_template('advanced_drawing.html')

@app.route('/api/save_drawing', methods=['POST'])
@login_required
def save_drawing():
    """Save drawing from canvas"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        title = data.get('title', 'Untitled Drawing')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Remove data URL prefix
        if image_data.startswith('data:image/png;base64,'):
            image_data = image_data.replace('data:image/png;base64,', '')
        
        # Generate unique filename
        filename = f"drawing_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # Create artwork record
        artwork = Artwork(
            title=title,
            description="Created with Advanced Drawing Studio",
            filename=filename,
            user_id=current_user.id,
            category='Digital Art'
        )
        db.session.add(artwork)
        
        # Update user stats
        update_user_stats(current_user.id, 'artwork_uploaded')
        
        db.session.commit()
        
        return jsonify({'success': True, 'artwork_id': artwork.id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_analyze_drawing', methods=['POST'])
@login_required
def ai_analyze_drawing():
    """Analyze drawing and provide AI suggestions"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Simulate AI analysis (replace with actual AI service)
        suggestions = [
            "Consider adding more contrast to make the subject stand out",
            "The composition could benefit from the rule of thirds",
            "Try adding highlights to create more depth",
            "The color palette is well balanced",
            "Consider adding shadows for more realism"
        ]
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_style_transfer', methods=['POST'])
@login_required
def ai_style_transfer():
    """Apply AI style transfer to drawing"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        style = data.get('style', 'Van Gogh')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Simulate style transfer (replace with actual AI service)
        # For now, just return the original image with a message
        return jsonify({
            'styled_image': image_data,
            'message': f'Style transfer with {style} style applied (simulated)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Social Features
@app.route('/social')
@login_required
def social_hub():
    """Social hub with friends, groups, and messaging"""
    # Get user's friends
    friends = []  # Would implement friend system
    
    # Get recent activity from friends
    friend_activity = []  # Would get friend activities
    
    # Get suggested users to follow
    suggested_users = User.query.filter(
        User.id != current_user.id,
        User.is_admin == False
    ).order_by(db.func.random()).limit(5).all()
    
    return render_template('social_hub.html', 
                         friends=friends,
                         friend_activity=friend_activity,
                         suggested_users=suggested_users)

# Portfolio Features
@app.route('/portfolio/<username>')
def user_portfolio(username):
    """Enhanced user portfolio with collections and themes"""
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's artworks organized by collections
    artworks = Artwork.query.filter_by(user_id=user.id).order_by(Artwork.upload_date.desc()).all()
    
    # Get user's achievements
    user_achievements = db.session.query(UserAchievement, Achievement).join(
        Achievement
    ).filter(UserAchievement.user_id == user.id).all()
    
    # Get user's stats
    stats = UserStats.query.filter_by(user_id=user.id).first()
    if not stats:
        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
    
    # Get user's learning progress
    learning_progress = UserPathProgress.query.filter_by(user_id=user.id).all()
    
    return render_template('enhanced_portfolio.html',
                         user=user,
                         artworks=artworks,
                         user_achievements=user_achievements,
                         stats=stats,
                         learning_progress=learning_progress)

# Art Marketplace
@app.route('/marketplace')
def art_marketplace():
    """Art marketplace for buying/selling artwork"""
    # Get featured artworks
    featured_artworks = Artwork.query.filter(
        Artwork.ai_score >= 8.0
    ).order_by(Artwork.upload_date.desc()).limit(6).all()
    
    # Get recent artworks
    recent_artworks = Artwork.query.order_by(
        Artwork.upload_date.desc()
    ).limit(12).all()
    
    # Get categories
    categories = db.session.query(Artwork.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('marketplace.html',
                         featured_artworks=featured_artworks,
                         recent_artworks=recent_artworks,
                         categories=categories)



@app.route('/api/start_stream', methods=['POST'])
@login_required
def start_stream():
    """Start a live art stream"""
    try:
        data = request.get_json()
        title = data.get('title', 'Untitled Stream')
        description = data.get('description', '')
        
        # Create stream record (would integrate with streaming service)
        stream_data = {
            'stream_id': f"stream_{current_user.id}_{datetime.utcnow().timestamp()}",
            'title': title,
            'description': description,
            'streamer': current_user.username,
            'start_time': datetime.utcnow().isoformat(),
            'status': 'live'
        }
        
        return jsonify(stream_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Art Challenges System
@app.route('/daily_challenge')
def daily_challenge():
    """Daily art challenge with themes and prompts"""
    today = datetime.utcnow().date()
    
    # Get today's challenge or create one
    challenge = Challenge.query.filter(
        db.func.date(Challenge.start_date) == today
    ).first()
    
    if not challenge:
        # Create daily challenge
        themes = [
            "Draw something blue", "Minimalist landscape", "Character portrait",
            "Abstract emotions", "Favorite food", "Dream house", "Mythical creature",
            "Retro futurism", "Nature scene", "Urban architecture"
        ]
        theme = themes[today.day % len(themes)]
        
        challenge = Challenge(
            title=f"Daily Challenge - {theme}",
            description=f"Today's theme: {theme}. Create your interpretation!",
            requirements=f"Create artwork inspired by: {theme}",
            end_date=datetime.combine(today + timedelta(days=1), datetime.min.time()),
            difficulty='Beginner',
            reward_exp=50
        )
        db.session.add(challenge)
        db.session.commit()
    
    # Get today's submissions
    submissions = ChallengeSubmission.query.filter_by(
        challenge_id=challenge.id
    ).join(Artwork).order_by(Artwork.upload_date.desc()).all()
    
    return render_template('daily_challenge.html',
                         challenge=challenge,
                         submissions=submissions)

# Collaborative Drawing
@app.route('/collaborate')
@login_required
def collaborative_drawing():
    """Real-time collaborative drawing rooms"""
    return render_template('collaborative_drawing.html')

@app.route('/api/create_collab_room', methods=['POST'])
@login_required
def create_collab_room():
    """Create a collaborative drawing room"""
    try:
        data = request.get_json()
        room_name = data.get('name', 'Untitled Room')
        max_users = data.get('max_users', 4)
        
        room_data = {
            'room_id': f"room_{current_user.id}_{datetime.utcnow().timestamp()}",
            'name': room_name,
            'creator': current_user.username,
            'max_users': max_users,
            'current_users': 1,
            'created_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(room_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def migrate_database():
    """Handle database schema migrations"""
    try:
        with db.engine.connect() as conn:
            # Migrate learning_path table
            result = conn.execute(db.text("PRAGMA table_info(learning_path)"))
            existing_lp_columns = [row[1] for row in result]
            
            lp_expected_columns = {
                'category': "VARCHAR(50) DEFAULT 'General'",
                'estimated_hours': "INTEGER DEFAULT 1",
                'thumbnail_url': "VARCHAR(200)",
                'prerequisites': "TEXT",
                'completion_reward_xp': "INTEGER DEFAULT 50",
                'created_at': "DATETIME DEFAULT CURRENT_TIMESTAMP"
            }
            
            lp_columns_added = []
            for column_name, column_def in lp_expected_columns.items():
                if column_name not in existing_lp_columns:
                    print(f"🔄 Adding missing '{column_name}' column to learning_path table...")
                    conn.execute(db.text(f"ALTER TABLE learning_path ADD COLUMN {column_name} {column_def}"))
                    lp_columns_added.append(column_name)
            
            # Migrate user table
            result = conn.execute(db.text("PRAGMA table_info(user)"))
            existing_user_columns = [row[1] for row in result]
            
            user_expected_columns = {
                'created_at': "DATETIME DEFAULT CURRENT_TIMESTAMP"
            }
            
            user_columns_added = []
            for column_name, column_def in user_expected_columns.items():
                if column_name not in existing_user_columns:
                    print(f"🔄 Adding missing '{column_name}' column to user table...")
                    conn.execute(db.text(f"ALTER TABLE user ADD COLUMN {column_name} {column_def}"))
                    user_columns_added.append(column_name)
            
            if lp_columns_added or user_columns_added:
                conn.commit()
                all_added = lp_columns_added + user_columns_added
                print(f"✅ Added columns: {', '.join(all_added)}")
            else:
                print("✅ All database columns are up to date!")
                
    except Exception as e:
        print(f"⚠️ Migration check failed: {e}")
        print("🔄 Recreating database tables...")
        db.drop_all()
        db.create_all()
        print("✅ Database recreated successfully!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_database()  # Handle database migrations
        create_admin_user()  # Create admin user on startup
        initialize_achievements()  # Create default achievements
        initialize_skill_trees()  # Create default skill trees
        initialize_forum_categories()  # Create default forum categories
        initialize_learning_paths()  # Create default learning paths and lessons
        initialize_tutorials()  # Create sample tutorials
    app.run(debug=True, host='0.0.0.0', port=5000)