#!/usr/bin/env python3
"""
ArtAI Startup Script
Initializes the database and creates an admin user
"""

from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    """Create an admin user if it doesn't exist"""
    with app.app_context():
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@artai.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                join_date=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Please change the password after first login!")
        else:
            print("✅ Admin user already exists")

def create_sample_data():
    """Create sample learning paths and challenges"""
    from app import LearningPath, Challenge
    
    with app.app_context():
        # Create sample learning paths
        learning_paths = [
            {
                'title': 'Drawing Fundamentals',
                'description': 'Master the basics of drawing including line quality, shapes, and perspective.',
                'difficulty': 'Beginner',
                'order': 1
            },
            {
                'title': 'Color Theory Mastery',
                'description': 'Learn color theory principles and how to create harmonious color palettes.',
                'difficulty': 'Beginner',
                'order': 2
            },
            {
                'title': 'Watercolor Techniques',
                'description': 'Explore watercolor painting techniques from basic washes to advanced layering.',
                'difficulty': 'Intermediate',
                'order': 3
            },
            {
                'title': 'Digital Art Basics',
                'description': 'Get started with digital art tools and techniques.',
                'difficulty': 'Beginner',
                'order': 4
            },
            {
                'title': 'Composition Principles',
                'description': 'Learn composition rules and how to create visually appealing artwork.',
                'difficulty': 'Intermediate',
                'order': 5
            }
        ]
        
        for path_data in learning_paths:
            existing = LearningPath.query.filter_by(title=path_data['title']).first()
            if not existing:
                path = LearningPath(**path_data)
                db.session.add(path)
        
        # Create sample challenges
        challenges = [
            {
                'title': 'Daily Sketch Challenge',
                'description': 'Draw something every day for a week. Focus on improving your line quality and observation skills.',
                'requirements': 'Submit 7 sketches, one for each day. Any subject is acceptable.',
                'difficulty': 'Beginner',
                'reward_exp': 100
            },
            {
                'title': 'Color Harmony Challenge',
                'description': 'Create artwork using only complementary colors. Show how opposites can work together beautifully.',
                'requirements': 'Use only two complementary colors plus white and black. Any medium is acceptable.',
                'difficulty': 'Intermediate',
                'reward_exp': 150
            },
            {
                'title': 'Perspective Mastery',
                'description': 'Draw a complex scene with multiple objects in different perspectives.',
                'requirements': 'Include at least 3 objects at different distances. Show clear perspective lines.',
                'difficulty': 'Advanced',
                'reward_exp': 200
            }
        ]
        
        for challenge_data in challenges:
            existing = Challenge.query.filter_by(title=challenge_data['title']).first()
            if not existing:
                challenge = Challenge(**challenge_data)
                db.session.add(challenge)
        
        db.session.commit()
        print("✅ Sample learning paths and challenges created!")

def main():
    """Main startup function"""
    print("🚀 Starting ArtAI Application...")
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
    
    # Create admin user
    create_admin_user()
    
    # Create sample data
    create_sample_data()
    
    print("\n🎨 ArtAI is ready to use!")
    print("📝 To start the application, run: python app.py")
    print("🌐 The application will be available at: http://localhost:5000")
    print("\n📋 Quick Start Guide:")
    print("   1. Login with admin/admin123")
    print("   2. Upload your first artwork")
    print("   3. Explore the learning roadmap")
    print("   4. Participate in challenges")
    print("   5. Join the community forum")

if __name__ == '__main__':
    main()