import json
import random
from datetime import datetime

class AIGuideGenerator:
    def __init__(self):
        """Initialize AI guide generator with art learning content"""
        
        # Art technique databases
        self.techniques = {
            'drawing': {
                'fundamentals': [
                    'Line quality and control',
                    'Basic shapes and forms',
                    'Perspective principles',
                    'Value and shading',
                    'Proportions and anatomy'
                ],
                'advanced': [
                    'Gesture drawing',
                    'Figure drawing',
                    'Portrait techniques',
                    'Composition mastery',
                    'Mixed media approaches'
                ]
            },
            'painting': {
                'watercolor': [
                    'Wet-on-wet techniques',
                    'Color mixing and theory',
                    'Brush control and strokes',
                    'Layering and glazing',
                    'Paper selection and preparation'
                ],
                'oil': [
                    'Fat over lean principle',
                    'Color mixing and palettes',
                    'Brush techniques and tools',
                    'Drying times and mediums',
                    'Canvas preparation'
                ],
                'acrylic': [
                    'Fast-drying properties',
                    'Color mixing techniques',
                    'Texture and impasto',
                    'Glazing and layering',
                    'Surface preparation'
                ],
                'digital': [
                    'Digital brush settings',
                    'Layer management',
                    'Color theory in digital art',
                    'Composition tools',
                    'Export and optimization'
                ]
            },
            'composition': [
                'Rule of thirds',
                'Golden ratio',
                'Leading lines',
                'Focal points',
                'Balance and symmetry',
                'Negative space',
                'Depth and perspective',
                'Color harmony'
            ],
            'color_theory': [
                'Color wheel basics',
                'Primary, secondary, and tertiary colors',
                'Warm vs cool colors',
                'Complementary colors',
                'Analogous color schemes',
                'Monochromatic palettes',
                'Color psychology',
                'Color mixing techniques'
            ]
        }
        
        # Exercise templates
        self.exercises = {
            'beginner': [
                'Practice drawing basic shapes for 30 minutes daily',
                'Create a value scale using only pencil',
                'Draw the same object from 3 different angles',
                'Practice contour drawing for 15 minutes',
                'Create a simple still life composition'
            ],
            'intermediate': [
                'Complete a figure drawing study',
                'Paint a landscape using limited palette',
                'Create a portrait focusing on proportions',
                'Experiment with different brush techniques',
                'Study and replicate a master artwork'
            ],
            'advanced': [
                'Create a series of related artworks',
                'Develop a personal style through experimentation',
                'Master complex lighting scenarios',
                'Combine multiple mediums in one piece',
                'Create artwork with strong emotional impact'
            ]
        }
        
        # Tips and advice
        self.tips = [
            "Always start with a light sketch before committing to final lines",
            "Take regular breaks to avoid eye strain and maintain fresh perspective",
            "Study the work of artists you admire to understand their techniques",
            "Don't be afraid to make mistakes - they're part of the learning process",
            "Keep a sketchbook for daily practice and idea development",
            "Experiment with different materials to find what works best for you",
            "Focus on the process rather than just the final result",
            "Use reference images to improve accuracy and understanding",
            "Practice regularly, even if just for 15 minutes a day",
            "Join art communities to get feedback and inspiration"
        ]

    def generate_guide(self, title, description):
        """
        Generate a comprehensive learning guide
        Returns: dictionary with guide content
        """
        try:
            # Determine the type of guide based on title and description
            guide_type = self._determine_guide_type(title, description)
            
            # Generate guide content
            guide_content = self._create_guide_content(guide_type, title)
            
            # Return structured data
            return {
                'title': title,
                'guide_type': guide_type,
                'content': guide_content,
                'created_at': datetime.now().strftime('%B %d, %Y at %H:%M'),
                'estimated_time': self._get_estimated_time(guide_type),
                'difficulty': self._get_difficulty(guide_type),
                'quick_tips': self._get_quick_tips(guide_type)
            }
            
        except Exception as e:
            print(f"Error generating guide: {e}")
            return self._generate_fallback_guide(title)

    def generate_comprehensive_learning_path(self, topic, difficulty='Beginner', description=''):
        """
        Generate a complete learning path with multiple lessons
        """
        try:
            # Determine the category and type
            guide_type = self._determine_guide_type(topic, description)
            
            # Generate structured learning path
            learning_path_data = {
                'title': f"{topic} - {difficulty} Course",
                'description': description or f"Master {topic.lower()} with this comprehensive {difficulty.lower()} course",
                'category': guide_type.title().replace('_', ' '),
                'estimated_hours': self._calculate_course_hours(difficulty),
                'lessons': []
            }
            
            # Generate lessons based on difficulty and topic
            lesson_topics = self._generate_lesson_structure(guide_type, difficulty)
            
            for i, lesson_topic in enumerate(lesson_topics, 1):
                lesson_content = self._generate_lesson_content(lesson_topic, guide_type, difficulty)
                
                lesson = {
                    'title': lesson_topic['title'],
                    'content': lesson_content,
                    'type': lesson_topic.get('type', 'theory'),
                    'order': i,
                    'estimated_minutes': lesson_topic.get('duration', 20),
                    'xp': lesson_topic.get('xp', 15)
                }
                learning_path_data['lessons'].append(lesson)
            
            return learning_path_data
            
        except Exception as e:
            print(f"Error generating comprehensive learning path: {e}")
            return self._generate_fallback_learning_path(topic, difficulty)

    def _calculate_course_hours(self, difficulty):
        """Calculate estimated course hours based on difficulty"""
        hours_map = {
            'Beginner': 3,
            'Intermediate': 5,
            'Advanced': 8,
            'Expert': 12
        }
        return hours_map.get(difficulty, 3)

    def _generate_lesson_structure(self, guide_type, difficulty):
        """Generate lesson structure based on type and difficulty"""
        base_lessons = {
            'drawing': [
                {'title': 'Introduction to Drawing Fundamentals', 'type': 'theory', 'duration': 15, 'xp': 10},
                {'title': 'Line Quality and Control', 'type': 'practical', 'duration': 30, 'xp': 20},
                {'title': 'Basic Shapes and Forms', 'type': 'practical', 'duration': 25, 'xp': 15},
                {'title': 'Understanding Perspective', 'type': 'theory', 'duration': 20, 'xp': 15},
                {'title': 'Shading and Value', 'type': 'practical', 'duration': 35, 'xp': 25}
            ],
            'painting': [
                {'title': 'Color Theory Basics', 'type': 'theory', 'duration': 20, 'xp': 15},
                {'title': 'Brush Techniques', 'type': 'practical', 'duration': 30, 'xp': 20},
                {'title': 'Color Mixing', 'type': 'practical', 'duration': 25, 'xp': 15},
                {'title': 'Composition Principles', 'type': 'theory', 'duration': 20, 'xp': 15},
                {'title': 'Creating Your First Painting', 'type': 'practical', 'duration': 45, 'xp': 30}
            ],
            'digital': [
                {'title': 'Digital Art Software Overview', 'type': 'theory', 'duration': 15, 'xp': 10},
                {'title': 'Digital Brushes and Tools', 'type': 'practical', 'duration': 25, 'xp': 15},
                {'title': 'Layers and Blending Modes', 'type': 'practical', 'duration': 30, 'xp': 20},
                {'title': 'Digital Color Theory', 'type': 'theory', 'duration': 20, 'xp': 15},
                {'title': 'Creating Digital Artwork', 'type': 'practical', 'duration': 40, 'xp': 25}
            ]
        }
        
        lessons = base_lessons.get(guide_type, base_lessons['drawing'])
        
        # Add difficulty-specific lessons
        if difficulty in ['Intermediate', 'Advanced']:
            advanced_lessons = [
                {'title': 'Advanced Techniques', 'type': 'practical', 'duration': 35, 'xp': 25},
                {'title': 'Style Development', 'type': 'theory', 'duration': 25, 'xp': 20}
            ]
            lessons.extend(advanced_lessons)
        
        if difficulty == 'Advanced':
            expert_lessons = [
                {'title': 'Professional Workflow', 'type': 'theory', 'duration': 30, 'xp': 25},
                {'title': 'Portfolio Development', 'type': 'practical', 'duration': 40, 'xp': 30}
            ]
            lessons.extend(expert_lessons)
        
        return lessons

    def _generate_lesson_content(self, lesson_topic, guide_type, difficulty):
        """Generate detailed content for a specific lesson"""
        content = []
        
        # Lesson header
        content.append(f"# {lesson_topic['title']}")
        content.append(f"*Estimated time: {lesson_topic['duration']} minutes*")
        content.append("")
        
        # Learning objectives
        content.append("## Learning Objectives")
        objectives = self._get_lesson_objectives(lesson_topic['title'], guide_type)
        for obj in objectives:
            content.append(f"- {obj}")
        content.append("")
        
        # Main content
        content.append("## Lesson Content")
        main_content = self._generate_lesson_main_content(lesson_topic['title'], guide_type, difficulty)
        content.extend(main_content)
        content.append("")
        
        # Practice exercises
        if lesson_topic['type'] == 'practical':
            content.append("## Practice Exercises")
            exercises = self._get_lesson_exercises(lesson_topic['title'], guide_type)
            for i, exercise in enumerate(exercises, 1):
                content.append(f"{i}. {exercise}")
            content.append("")
        
        # Key takeaways
        content.append("## Key Takeaways")
        takeaways = self._get_lesson_takeaways(lesson_topic['title'], guide_type)
        for takeaway in takeaways:
            content.append(f"- {takeaway}")
        content.append("")
        
        return '\n'.join(content)

    def _get_lesson_objectives(self, lesson_title, guide_type):
        """Generate learning objectives for a lesson"""
        objectives_map = {
            'Introduction to Drawing Fundamentals': [
                'Understand the basic principles of drawing',
                'Learn about essential drawing tools and materials',
                'Identify different drawing techniques and styles'
            ],
            'Line Quality and Control': [
                'Master different types of lines and their uses',
                'Develop steady hand control and precision',
                'Practice line weight variation techniques'
            ],
            'Basic Shapes and Forms': [
                'Draw accurate geometric shapes',
                'Understand form and volume',
                'Apply shapes to create complex objects'
            ],
            'Color Theory Basics': [
                'Understand primary, secondary, and tertiary colors',
                'Learn about color relationships and harmony',
                'Apply color theory to create mood and atmosphere'
            ]
        }
        return objectives_map.get(lesson_title, [
            'Understand the key concepts of this lesson',
            'Apply the techniques in practical exercises',
            'Build upon previous knowledge and skills'
        ])

    def _generate_lesson_main_content(self, lesson_title, guide_type, difficulty):
        """Generate main content for a lesson"""
        content = []
        
        if 'Introduction' in lesson_title:
            content.extend([
                "Welcome to this comprehensive lesson on art fundamentals!",
                "",
                "In this lesson, we'll cover the essential concepts you need to know to get started.",
                "Whether you're a complete beginner or looking to refresh your knowledge, this lesson",
                "will provide a solid foundation for your artistic journey.",
                "",
                "### What You'll Learn",
                "- Core principles and techniques",
                "- Essential tools and materials",
                "- Best practices for getting started",
                "",
                "### Getting Started",
                "Before we begin, make sure you have your materials ready and a comfortable workspace set up."
            ])
        elif 'Line' in lesson_title:
            content.extend([
                "Lines are the foundation of all drawing. Mastering line quality and control",
                "is essential for creating expressive and accurate artwork.",
                "",
                "### Types of Lines",
                "- **Contour lines**: Define the edges and shapes of objects",
                "- **Gesture lines**: Capture movement and energy",
                "- **Construction lines**: Help build accurate proportions",
                "",
                "### Line Weight and Variation",
                "Varying your line weight adds depth and interest to your drawings:",
                "- Thick lines bring elements forward",
                "- Thin lines push elements back",
                "- Broken lines suggest texture or uncertainty"
            ])
        elif 'Color' in lesson_title:
            content.extend([
                "Color is one of the most powerful tools in an artist's toolkit.",
                "Understanding color theory will help you create more compelling and harmonious artwork.",
                "",
                "### The Color Wheel",
                "The color wheel is your guide to understanding color relationships:",
                "- **Primary colors**: Red, blue, yellow - cannot be mixed from other colors",
                "- **Secondary colors**: Orange, green, violet - mixed from two primaries",
                "- **Tertiary colors**: Mixed from a primary and secondary color",
                "",
                "### Color Harmony",
                "Learn to create pleasing color combinations using these schemes:",
                "- Complementary: Colors opposite on the wheel",
                "- Analogous: Colors next to each other on the wheel",
                "- Triadic: Three colors equally spaced on the wheel"
            ])
        else:
            # Generic content
            content.extend([
                f"In this lesson, we'll explore the important concepts of {lesson_title.lower()}.",
                "",
                "This lesson builds upon what you've learned previously and introduces new",
                "techniques and concepts that will enhance your artistic skills.",
                "",
                "### Key Points to Remember",
                "- Practice regularly to develop muscle memory",
                "- Don't be afraid to make mistakes - they're part of learning",
                "- Take your time and focus on quality over quantity",
                "",
                "### Step-by-Step Process",
                "Follow these steps to get the most out of this lesson:",
                "1. Read through all the material first",
                "2. Gather your materials and set up your workspace",
                "3. Practice the techniques shown",
                "4. Complete the exercises at your own pace",
                "5. Review and reflect on what you've learned"
            ])
        
        return content

    def _get_lesson_exercises(self, lesson_title, guide_type):
        """Get practice exercises for a lesson"""
        exercises_map = {
            'Line Quality and Control': [
                'Draw 20 straight lines without using a ruler',
                'Practice drawing smooth curves and circles',
                'Create a drawing using only different line weights',
                'Draw the same object with different line styles'
            ],
            'Basic Shapes and Forms': [
                'Draw 10 perfect circles, squares, and triangles',
                'Combine basic shapes to create simple objects',
                'Practice drawing 3D forms (cubes, spheres, cylinders)',
                'Create a still life using only basic geometric forms'
            ],
            'Color Mixing': [
                'Mix all secondary colors from primaries',
                'Create a color wheel using paint',
                'Practice mixing different values of the same color',
                'Create a small painting using only 3 colors'
            ]
        }
        return exercises_map.get(lesson_title, [
            'Practice the main technique demonstrated in this lesson',
            'Create a small study applying what you\'ve learned',
            'Experiment with variations of the technique',
            'Share your work with the community for feedback'
        ])

    def _get_lesson_takeaways(self, lesson_title, guide_type):
        """Get key takeaways for a lesson"""
        return [
            'Regular practice is essential for improvement',
            'Understanding fundamentals builds a strong foundation',
            'Don\'t rush - take time to master each concept',
            'Apply what you learn to your own creative projects',
            'Seek feedback to continue growing as an artist'
        ]

    def _generate_fallback_learning_path(self, topic, difficulty):
        """Generate a simple fallback learning path if AI generation fails"""
        return {
            'title': f"{topic} - {difficulty} Course",
            'description': f"Learn {topic.lower()} with this structured course",
            'category': 'General',
            'estimated_hours': 3,
            'lessons': [
                {
                    'title': f'Introduction to {topic}',
                    'content': f'# Introduction to {topic}\n\nWelcome to this course on {topic.lower()}. In this lesson, you\'ll learn the fundamentals and get started with the basics.',
                    'type': 'theory',
                    'order': 1,
                    'estimated_minutes': 20,
                    'xp': 15
                },
                {
                    'title': f'Basic {topic} Techniques',
                    'content': f'# Basic {topic} Techniques\n\nNow that you understand the fundamentals, let\'s practice some basic techniques.',
                    'type': 'practical',
                    'order': 2,
                    'estimated_minutes': 30,
                    'xp': 20
                }
            ]
        }

    def _determine_guide_type(self, title, description):
        """Determine the type of guide based on title and description"""
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        if any(word in title_lower for word in ['draw', 'sketch', 'line']):
            return 'drawing'
        elif any(word in title_lower for word in ['paint', 'color', 'brush']):
            if any(word in title_lower for word in ['watercolor', 'water']):
                return 'watercolor'
            elif any(word in title_lower for word in ['oil', 'canvas']):
                return 'oil'
            elif any(word in title_lower for word in ['acrylic', 'fast']):
                return 'acrylic'
            elif any(word in title_lower for word in ['digital', 'computer']):
                return 'digital'
            else:
                return 'painting'
        elif any(word in title_lower for word in ['composition', 'layout', 'arrange']):
            return 'composition'
        elif any(word in title_lower for word in ['color', 'palette', 'hue']):
            return 'color_theory'
        else:
            # Default to drawing fundamentals
            return 'drawing'

    def _create_guide_content(self, guide_type, title):
        """Create comprehensive guide content"""
        content = []
        
        # Header
        content.append(f"# {title}")
        content.append(f"*Generated on {datetime.now().strftime('%B %d, %Y')}*")
        content.append("")
        
        # Introduction
        content.append("## Introduction")
        content.append(self._generate_introduction(guide_type))
        content.append("")
        
        # Key Concepts
        content.append("## Key Concepts")
        concepts = self._get_concepts(guide_type)
        for i, concept in enumerate(concepts, 1):
            content.append(f"{i}. **{concept}**")
            content.append(f"   {self._generate_concept_explanation(concept)}")
            content.append("")
        
        # Step-by-Step Process
        content.append("## Step-by-Step Process")
        steps = self._generate_steps(guide_type)
        for i, step in enumerate(steps, 1):
            content.append(f"### Step {i}: {step['title']}")
            content.append(step['description'])
            if step.get('tips'):
                content.append("**Tips:** " + step['tips'])
            content.append("")
        
        # Exercises
        content.append("## Practice Exercises")
        exercises = self._get_exercises(guide_type)
        for i, exercise in enumerate(exercises, 1):
            content.append(f"{i}. {exercise}")
        content.append("")
        
        # Common Mistakes
        content.append("## Common Mistakes to Avoid")
        mistakes = self._generate_common_mistakes(guide_type)
        for mistake in mistakes:
            content.append(f"- **{mistake['title']}**: {mistake['description']}")
        content.append("")
        
        # Tips and Advice
        content.append("## Pro Tips")
        selected_tips = random.sample(self.tips, min(5, len(self.tips)))
        for tip in selected_tips:
            content.append(f"- {tip}")
        content.append("")
        
        # Resources
        content.append("## Additional Resources")
        resources = self._generate_resources(guide_type)
        for resource in resources:
            content.append(f"- {resource}")
        content.append("")
        
        # Conclusion
        content.append("## Conclusion")
        content.append(self._generate_conclusion(guide_type))
        
        return "\n".join(content)

    def _generate_introduction(self, guide_type):
        """Generate introduction based on guide type"""
        introductions = {
            'drawing': "Drawing is the foundation of all visual arts. This guide will help you develop essential drawing skills, from basic line work to advanced techniques. Whether you're a complete beginner or looking to refine your skills, these principles will strengthen your artistic foundation.",
            'watercolor': "Watercolor painting is known for its luminous, transparent qualities and unique challenges. This guide covers the fundamental techniques that will help you master this beautiful medium, from basic washes to advanced layering techniques.",
            'oil': "Oil painting offers incredible versatility and depth. This guide will teach you the essential techniques for working with oils, from proper setup and materials to advanced painting methods that have been used by masters for centuries.",
            'acrylic': "Acrylic paint is a versatile, fast-drying medium perfect for both beginners and experienced artists. This guide covers everything from basic techniques to advanced applications, helping you make the most of this accessible medium.",
            'digital': "Digital art opens up endless possibilities for creativity. This guide will help you navigate the digital landscape, from basic tools and techniques to advanced features that can enhance your artistic workflow.",
            'composition': "Composition is the backbone of successful artwork. This guide explores the fundamental principles that make artwork visually appealing and effective, helping you create more compelling pieces.",
            'color_theory': "Understanding color is crucial for any artist. This guide breaks down color theory into practical concepts that you can apply immediately to improve your artwork and develop your color sense."
        }
        return introductions.get(guide_type, introductions['drawing'])

    def _get_concepts(self, guide_type):
        """Get key concepts for the guide type"""
        if guide_type == 'drawing':
            return self.techniques['drawing']['fundamentals'][:5]
        elif guide_type in ['watercolor', 'oil', 'acrylic', 'digital']:
            return self.techniques['painting'][guide_type][:5]
        elif guide_type == 'composition':
            return self.techniques['composition'][:5]
        elif guide_type == 'color_theory':
            return self.techniques['color_theory'][:5]
        else:
            return self.techniques['drawing']['fundamentals'][:5]

    def _generate_concept_explanation(self, concept):
        """Generate explanation for a concept"""
        explanations = {
            'Line quality and control': "The foundation of drawing. Practice creating lines of varying thickness and pressure to add depth and interest to your work.",
            'Basic shapes and forms': "All complex objects can be broken down into basic geometric shapes. Master these to build more complex drawings.",
            'Perspective principles': "Understanding how objects appear smaller as they recede into the distance creates realistic depth in your artwork.",
            'Value and shading': "Using light and dark values creates the illusion of three-dimensional form and adds depth to your drawings.",
            'Proportions and anatomy': "Understanding the relationships between different parts of your subject ensures accurate representation.",
            'Wet-on-wet techniques': "Applying paint to wet paper creates soft, flowing effects perfect for backgrounds and atmospheric elements.",
            'Color mixing and theory': "Understanding how colors interact helps you create harmonious palettes and achieve the exact hues you want.",
            'Brush control and strokes': "Different brush techniques create various textures and effects, from smooth washes to detailed line work.",
            'Fat over lean principle': "Applying thicker paint over thinner layers prevents cracking and ensures proper drying in oil painting.",
            'Canvas preparation': "Properly preparing your surface ensures paint adhesion and longevity of your artwork.",
            'Fast-drying properties': "Acrylics dry quickly, allowing for rapid layering but requiring quick decision-making in your painting process.",
            'Digital brush settings': "Customizing your digital brushes can mimic traditional media or create unique digital effects.",
            'Layer management': "Organizing your digital artwork in layers allows for easy editing and non-destructive changes.",
            'Rule of thirds': "Dividing your canvas into thirds both horizontally and vertically creates balanced, visually appealing compositions.",
            'Golden ratio': "This mathematical proportion creates naturally pleasing compositions that guide the viewer's eye.",
            'Leading lines': "Using lines to direct the viewer's attention creates dynamic, engaging compositions.",
            'Focal points': "Establishing a clear center of interest helps viewers understand and engage with your artwork.",
            'Balance and symmetry': "Distributing visual weight evenly creates stable, harmonious compositions.",
            'Color wheel basics': "The color wheel is the foundation for understanding color relationships and creating harmonious palettes.",
            'Primary, secondary, and tertiary colors': "Understanding these color categories helps you mix any color you need.",
            'Warm vs cool colors': "Warm colors advance while cool colors recede, creating depth and mood in your artwork.",
            'Complementary colors': "Colors opposite on the color wheel create vibrant contrast and visual interest.",
            'Analogous color schemes': "Using colors next to each other on the color wheel creates harmonious, unified palettes."
        }
        return explanations.get(concept, "This fundamental concept is essential for developing your artistic skills and understanding.")

    def _generate_steps(self, guide_type):
        """Generate step-by-step process"""
        steps_templates = {
            'drawing': [
                {'title': 'Gather Materials', 'description': 'Start with quality pencils (2H, HB, 2B, 6B), eraser, and smooth paper. Having the right tools makes learning easier.', 'tips': 'Invest in a good eraser - it\'s your best friend for corrections.'},
                {'title': 'Warm Up', 'description': 'Spend 5-10 minutes doing simple exercises like drawing circles, straight lines, and basic shapes. This loosens your hand and improves control.', 'tips': 'Don\'t skip warm-ups - they improve your drawing quality significantly.'},
                {'title': 'Choose Your Subject', 'description': 'Start with simple objects like fruit, cups, or basic geometric shapes. Avoid complex subjects until you master fundamentals.', 'tips': 'Use real objects rather than photos when possible for better understanding of form.'},
                {'title': 'Block In Basic Shapes', 'description': 'Lightly sketch the basic geometric shapes that make up your subject. Don\'t worry about details yet.', 'tips': 'Use light pressure - these are just guidelines that you\'ll refine.'},
                {'title': 'Add Details and Shading', 'description': 'Once your basic shapes are accurate, add details and use shading to create form and depth.', 'tips': 'Work from general to specific - build up your drawing in layers.'}
            ],
            'watercolor': [
                {'title': 'Prepare Your Materials', 'description': 'Set up your watercolor paper, paints, brushes, and water containers. Tape your paper to a board to prevent warping.', 'tips': 'Use 100% cotton paper for best results.'},
                {'title': 'Create a Color Palette', 'description': 'Mix your colors on a palette before painting. Start with a limited palette of 3-5 colors.', 'tips': 'Less is more - a limited palette often creates more harmonious paintings.'},
                {'title': 'Apply Initial Washes', 'description': 'Start with light, transparent washes to establish your basic shapes and values.', 'tips': 'Let each wash dry completely before adding the next layer.'},
                {'title': 'Build Up Layers', 'description': 'Add progressively darker and more detailed layers, allowing each to dry between applications.', 'tips': 'Work from light to dark - it\'s easier to darken than to lighten watercolor.'},
                {'title': 'Add Final Details', 'description': 'Use smaller brushes and more concentrated paint for final details and highlights.', 'tips': 'Use white paper for highlights rather than white paint.'}
            ],
            'composition': [
                {'title': 'Choose Your Format', 'description': 'Decide on your canvas or paper orientation (portrait, landscape, or square) based on your subject and intended impact.', 'tips': 'Consider how your format will affect the viewer\'s experience.'},
                {'title': 'Establish Focal Point', 'description': 'Decide what the main subject or area of interest will be. This should be the first thing that catches the viewer\'s eye.', 'tips': 'Use contrast, size, or placement to make your focal point stand out.'},
                {'title': 'Apply Rule of Thirds', 'description': 'Divide your canvas into thirds both horizontally and vertically. Place important elements along these lines or at their intersections.', 'tips': 'Don\'t always center your subject - off-center placement is often more dynamic.'},
                {'title': 'Create Visual Flow', 'description': 'Use lines, shapes, and colors to guide the viewer\'s eye through your composition in a logical path.', 'tips': 'Leading lines should point toward your focal point, not away from it.'},
                {'title': 'Balance Elements', 'description': 'Distribute visual weight evenly across your composition to create harmony and stability.', 'tips': 'Balance doesn\'t mean symmetry - you can balance a large object with several smaller ones.'}
            ]
        }
        
        return steps_templates.get(guide_type, steps_templates['drawing'])

    def _get_exercises(self, guide_type):
        """Get practice exercises for the guide type"""
        if guide_type == 'drawing':
            return self.exercises['beginner']
        elif guide_type in ['watercolor', 'oil', 'acrylic']:
            return [
                'Practice creating smooth washes on scrap paper',
                'Mix and create a color wheel with your paints',
                'Paint a simple still life focusing on values',
                'Experiment with different brush techniques',
                'Create a landscape using only 3 colors'
            ]
        elif guide_type == 'digital':
            return [
                'Practice using different brush settings',
                'Create artwork using only basic shapes',
                'Experiment with layer blending modes',
                'Practice digital color mixing',
                'Create a simple character design'
            ]
        elif guide_type == 'composition':
            return [
                'Take photos of interesting compositions in your environment',
                'Sketch thumbnail compositions before starting artwork',
                'Practice arranging simple objects in different ways',
                'Study and analyze compositions in famous artworks',
                'Create multiple versions of the same subject with different compositions'
            ]
        else:
            return self.exercises['beginner']

    def _generate_common_mistakes(self, guide_type):
        """Generate common mistakes for the guide type"""
        mistakes_templates = {
            'drawing': [
                {'title': 'Pressing too hard', 'description': 'Using heavy pressure makes it difficult to erase and creates harsh lines. Start light and build up gradually.'},
                {'title': 'Skipping fundamentals', 'description': 'Jumping into complex subjects without mastering basic shapes and forms leads to frustration and poor results.'},
                {'title': 'Not using reference', 'description': 'Drawing from imagination without understanding how things actually look results in unrealistic artwork.'},
                {'title': 'Rushing the process', 'description': 'Taking time to plan and build your drawing step by step produces much better results than rushing to finish.'}
            ],
            'watercolor': [
                {'title': 'Using too much paint', 'description': 'Watercolor is about transparency. Using too much pigment creates muddy, opaque results.'},
                {'title': 'Not letting layers dry', 'description': 'Adding wet paint to wet paint creates uncontrolled blending that can ruin your painting.'},
                {'title': 'Overworking areas', 'description': 'Constantly going back over the same area creates muddy colors and damages the paper surface.'},
                {'title': 'Using poor quality paper', 'description': 'Low-quality paper doesn\'t absorb paint properly and can\'t handle multiple washes.'}
            ],
            'composition': [
                {'title': 'Centering everything', 'description': 'Placing all elements in the center creates static, boring compositions. Use the rule of thirds instead.'},
                {'title': 'Ignoring negative space', 'description': 'Negative space is just as important as positive space. Don\'t fill every inch of your canvas.'},
                {'title': 'No clear focal point', 'description': 'Without a clear focal point, viewers don\'t know where to look and quickly lose interest.'},
                {'title': 'Poor visual flow', 'description': 'Elements that don\'t guide the eye create confusing, unengaging compositions.'}
            ]
        }
        
        return mistakes_templates.get(guide_type, mistakes_templates['drawing'])

    def _generate_resources(self, guide_type):
        """Generate additional resources"""
        resources = [
            "Art books and instructional videos",
            "Online art communities and forums",
            "Local art classes and workshops",
            "Museum visits to study master artworks",
            "Art supply stores for materials and advice"
        ]
        
        if guide_type == 'digital':
            resources.extend([
                "Digital art software tutorials",
                "Online courses on platforms like Skillshare or Udemy",
                "Digital art communities on social media"
            ])
        
        return resources

    def _generate_conclusion(self, guide_type):
        """Generate conclusion for the guide"""
        conclusions = {
            'drawing': "Remember that drawing is a skill that develops with practice. Don't be discouraged by early attempts - every artist starts somewhere. Focus on the fundamentals, practice regularly, and most importantly, enjoy the process of learning and creating.",
            'watercolor': "Watercolor can be challenging but incredibly rewarding. Embrace the medium's unique properties and don't fight against them. With patience and practice, you'll develop the control and understanding needed to create beautiful watercolor paintings.",
            'oil': "Oil painting offers incredible depth and versatility. Take your time to learn proper techniques and materials. The investment in learning will pay off in the quality and longevity of your artwork.",
            'acrylic': "Acrylic paint is perfect for artists who want to work quickly and experiment freely. Use its fast-drying properties to your advantage and don't be afraid to try new techniques and approaches.",
            'digital': "Digital art opens up endless creative possibilities. Take advantage of the medium's flexibility while developing strong fundamental skills. The best digital artists understand traditional art principles.",
            'composition': "Good composition is the foundation of successful artwork. Practice these principles regularly, and they'll become second nature. Remember that rules can be broken, but understanding them first helps you break them effectively.",
            'color_theory': "Color is one of the most powerful tools in your artistic arsenal. Understanding color theory will improve every aspect of your artwork. Practice mixing and using colors regularly to develop your color sense."
        }
        
        return conclusions.get(guide_type, conclusions['drawing'])

    def _generate_fallback_guide(self, title):
        """Generate a fallback guide if the main generation fails"""
        return f"""# {title}

## Introduction
This guide will help you develop your artistic skills and understanding. Art is a journey of continuous learning and practice.

## Key Steps
1. **Start with the basics** - Master fundamental techniques before moving to advanced concepts
2. **Practice regularly** - Even 15 minutes a day can make a significant difference
3. **Study other artists** - Learn from both contemporary and historical masters
4. **Experiment freely** - Don't be afraid to try new techniques and approaches
5. **Get feedback** - Share your work with others and be open to constructive criticism

## Practice Exercises
- Draw or paint from life regularly
- Experiment with different materials and techniques
- Study and replicate artwork you admire
- Keep a sketchbook for daily practice
- Join art communities for inspiration and feedback

## Tips for Success
- Be patient with your progress
- Focus on the process rather than just the result
- Don't compare your work to others unfairly
- Celebrate small improvements
- Keep learning and growing

Remember: Every artist was once a beginner. The key is consistent practice and a willingness to learn from both successes and mistakes."""

    def _get_estimated_time(self, guide_type):
        """Get estimated time for completing the guide"""
        time_estimates = {
            'drawing': '2-3 hours',
            'watercolor': '3-4 hours',
            'oil': '4-6 hours',
            'acrylic': '2-3 hours',
            'digital': '2-4 hours',
            'painting': '3-5 hours',
            'composition': '1-2 hours',
            'color_theory': '2-3 hours'
        }
        return time_estimates.get(guide_type, '2-3 hours')

    def _get_difficulty(self, guide_type):
        """Get difficulty level for the guide"""
        difficulty_levels = {
            'drawing': 'Beginner to Intermediate',
            'watercolor': 'Intermediate',
            'oil': 'Intermediate to Advanced',
            'acrylic': 'Beginner to Intermediate',
            'digital': 'Beginner to Intermediate',
            'painting': 'Intermediate',
            'composition': 'All Levels',
            'color_theory': 'All Levels'
        }
        return difficulty_levels.get(guide_type, 'Beginner to Intermediate')

    def _get_quick_tips(self, guide_type):
        """Get quick tips for the guide type"""
        tips = [
            "Practice regularly, even if just for 15 minutes a day",
            "Don't be afraid to make mistakes - they're part of learning",
            "Study the work of artists you admire",
            "Keep a sketchbook for daily practice",
            "Experiment with different materials and techniques"
        ]
        
        # Add specific tips based on guide type
        if guide_type == 'drawing':
            tips.extend([
                "Start with basic shapes before adding details",
                "Use light strokes for initial sketches",
                "Practice drawing from life whenever possible"
            ])
        elif guide_type in ['watercolor', 'oil', 'acrylic']:
            tips.extend([
                "Test colors on scrap paper first",
                "Work from light to dark",
                "Clean your brushes thoroughly after use"
            ])
        elif guide_type == 'digital':
            tips.extend([
                "Learn keyboard shortcuts to speed up your workflow",
                "Use layers to organize your work",
                "Save your work frequently"
            ])
        
        return tips[:8]  # Return max 8 tips