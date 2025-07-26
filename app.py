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
    
    user = db.relationship('User', backref='user_achievements')
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
    
    user = db.relationship('User', backref='user_skills')
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
    user = db.relationship('User', backref='battle_submissions')
    artwork = db.relationship('Artwork', backref='battle_submissions')

class BattleVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    battle_id = db.Column(db.Integer, db.ForeignKey('art_battle.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('battle_submission.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    battle = db.relationship('ArtBattle')
    submission = db.relationship('BattleSubmission')
    voter = db.relationship('User')

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
    
    user = db.relationship('User', backref=db.backref('stats', uselist=False))

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
    
    if action_type == 'artwork_uploaded':
        stats.total_artworks += value
    elif action_type == 'likes_received':
        stats.total_likes_received += value
    elif action_type == 'comment_made':
        stats.total_comments_made += value
    elif action_type == 'battle_won':
        stats.battles_won += value
    elif action_type == 'battle_participated':
        stats.battles_participated += value
    elif action_type == 'challenge_completed':
        stats.challenges_completed += value
    
    # Update streak
    today = datetime.utcnow().date()
    if stats.last_activity_date != today:
        if stats.last_activity_date == today - timedelta(days=1):
            stats.daily_streak += 1
        else:
            stats.daily_streak = 1
        stats.last_activity_date = today
        if stats.daily_streak > stats.longest_streak:
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
        create_admin_user()  # Create admin user on startup
        initialize_achievements()  # Create default achievements
        initialize_skill_trees()  # Create default skill trees
    app.run(debug=True, host='0.0.0.0', port=5000)