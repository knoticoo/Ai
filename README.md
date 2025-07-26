# ArtAI - AI-Powered Art Analysis & Learning Platform

🎨 **Transform Your Art with AI** - Get instant feedback, personalized learning guides, and join a community of artists.

## ✨ Features

- **🤖 AI Art Analysis** - Get detailed feedback on composition, color theory, technique, and style
- **📚 Learning Roadmap** - AI-generated comprehensive guides for any art technique
- **🏆 Art Challenges** - Participate in regular challenges to improve your skills
- **👥 Community Forum** - Connect with other artists and share your progress
- **🎭 AI Redraw** - See your artwork reimagined with AI-powered stylization
- **📊 Progress Tracking** - Monitor your artistic development with detailed analytics
- **👨‍💼 Admin Panel** - Manage challenges, learning paths, and user settings

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Ubuntu VPS (or any Linux system)
- At least 4GB RAM (for AI models)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd artai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the application**
   ```bash
   python start.py
   ```

4. **Start the server**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to `http://your-server-ip:5000`
   - Login with admin credentials:
     - Username: `admin`
     - Password: `admin123`

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=sqlite:///art_app.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

### Production Deployment

For production deployment on Ubuntu VPS:

1. **Install system dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup Gunicorn**
   ```bash
   pip install gunicorn
   ```

4. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/artai.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=ArtAI Web Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/your/artai
   Environment="PATH=/path/to/your/artai/venv/bin"
   ExecStart=/path/to/your/artai/venv/bin/gunicorn --workers 3 --bind unix:artai.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start the service**
   ```bash
   sudo systemctl start artai
   sudo systemctl enable artai
   ```

6. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/artai
   ```

   Add the following configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/path/to/your/artai/artai.sock;
       }

       location /static {
           alias /path/to/your/artai/static;
       }
   }
   ```

7. **Enable the site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/artai /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## 📁 Project Structure

```
artai/
├── app.py                 # Main Flask application
├── ai_analyzer.py         # AI art analysis module
├── ai_guide_generator.py  # AI learning guide generator
├── start.py              # Startup script
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── gallery.html
│   ├── challenges.html
│   ├── roadmap.html
│   └── ai_guide.html
├── static/               # Static files
│   ├── css/
│   ├── js/
│   └── uploads/          # Uploaded artwork
└── art_app.db           # SQLite database
```

## 🎯 Usage Guide

### For Users

1. **Registration & Login**
   - Create an account or login with existing credentials
   - Complete your profile with bio and preferences

2. **Upload Artwork**
   - Click "Upload" in the navigation
   - Drag & drop or select your artwork file
   - Add title, description, category, and tags
   - Get instant AI analysis and feedback

3. **Explore Learning**
   - Visit the "Roadmap" section
   - Choose a learning path that interests you
   - Follow AI-generated guides and exercises

4. **Participate in Challenges**
   - Browse active challenges
   - Submit your artwork for the challenge
   - Earn XP and recognition

5. **Join the Community**
   - Post in the forum
   - Comment on other artists' work
   - Share your progress and get feedback

### For Admins

1. **Access Admin Panel**
   - Login with admin credentials
   - Click on your username → Admin Panel

2. **Manage Challenges**
   - Create new challenges
   - Set requirements and rewards
   - Monitor submissions

3. **Manage Learning Paths**
   - Add new learning paths
   - Organize content by difficulty
   - Update existing guides

4. **User Management**
   - View all users
   - Monitor activity
   - Manage permissions

## 🤖 AI Features

### Art Analysis
- **Composition Analysis** - Rule of thirds, focal points, balance
- **Color Theory** - Palette analysis, contrast, harmony
- **Technique Assessment** - Brush strokes, texture, detail level
- **Style Classification** - Artistic movement identification
- **Scoring System** - Overall quality score (1-10)

### Learning Guides
- **Personalized Content** - Tailored to your skill level
- **Step-by-step Instructions** - Clear, actionable guidance
- **Practice Exercises** - Hands-on learning activities
- **Common Mistakes** - What to avoid and how to improve
- **Resource Recommendations** - Additional learning materials

### AI Redraw
- **Style Transfer** - Apply different artistic styles
- **Enhancement** - Improve composition and colors
- **Variations** - Generate multiple interpretations

## 🔧 Technical Details

### AI Models Used
- **Computer Vision** - OpenCV for image processing
- **Machine Learning** - Scikit-learn for analysis
- **Deep Learning** - PyTorch for advanced features
- **Image Processing** - PIL for image manipulation

### Database Schema
- **Users** - User accounts and profiles
- **Artworks** - Uploaded artwork and metadata
- **Challenges** - Art challenges and requirements
- **Forum Posts** - Community discussions
- **Learning Paths** - Educational content structure

### Security Features
- **Password Hashing** - Secure password storage
- **File Upload Validation** - Safe file handling
- **Session Management** - Secure user sessions
- **Admin Authentication** - Protected admin functions

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

2. **Database Issues**
   ```bash
   rm art_app.db
   python start.py
   ```

3. **Upload Directory**
   ```bash
   mkdir -p static/uploads
   chmod 755 static/uploads
   ```

4. **Permission Issues**
   ```bash
   sudo chown -R www-data:www-data /path/to/artai
   sudo chmod -R 755 /path/to/artai
   ```

### Performance Optimization

1. **Enable Caching**
   ```python
   # Add to app.py
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

2. **Image Optimization**
   ```python
   # Add image compression
   from PIL import Image
   import io
   ```

3. **Database Optimization**
   ```sql
   -- Add indexes for better performance
   CREATE INDEX idx_artwork_user_id ON artwork(user_id);
   CREATE INDEX idx_artwork_category ON artwork(category);
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation** - Check this README first
- **Issues** - Report bugs on GitHub
- **Discussions** - Ask questions in GitHub Discussions
- **Email** - Contact admin@artai.com

## 🎉 Acknowledgments

- Flask community for the excellent web framework
- OpenCV team for computer vision capabilities
- PyTorch team for deep learning tools
- Bootstrap team for the beautiful UI components

---

**Made with ❤️ for the art community**