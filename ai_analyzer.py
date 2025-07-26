import cv2
import numpy as np
from PIL import Image
import os
import base64
from io import BytesIO
import json

class AIAnalyzer:
    def __init__(self):
        # Analysis templates for different aspects
        self.composition_templates = {
            'rule_of_thirds': 'The composition follows the rule of thirds well, creating a balanced and visually appealing layout.',
            'symmetrical': 'The symmetrical composition creates a sense of harmony and order.',
            'asymmetrical': 'The asymmetrical composition adds dynamic tension and visual interest.',
            'centered': 'The centered composition creates a strong focal point and sense of stability.',
            'diagonal': 'The diagonal composition adds movement and energy to the artwork.'
        }
        
        self.color_templates = {
            'warm': 'The warm color palette creates a sense of energy and passion.',
            'cool': 'The cool color palette evokes calmness and tranquility.',
            'complementary': 'The complementary colors create strong contrast and visual impact.',
            'analogous': 'The analogous colors create harmony and unity.',
            'monochromatic': 'The monochromatic approach creates depth through value variations.',
            'neutral': 'The neutral palette creates a sophisticated and timeless feel.'
        }
        
        self.technique_templates = {
            'realistic': 'The realistic technique shows excellent attention to detail and technical skill.',
            'impressionistic': 'The impressionistic style captures the essence and mood effectively.',
            'abstract': 'The abstract approach allows for creative interpretation and emotional expression.',
            'minimalist': 'The minimalist style emphasizes simplicity and essential elements.',
            'expressionistic': 'The expressionistic style conveys strong emotional content.'
        }
        
        self.style_templates = {
            'classical': 'The classical style demonstrates traditional artistic principles.',
            'modern': 'The modern approach shows contemporary artistic sensibilities.',
            'avant-garde': 'The avant-garde style pushes artistic boundaries and conventions.',
            'folk': 'The folk art style connects to cultural traditions and heritage.',
            'digital': 'The digital medium offers unique possibilities for artistic expression.'
        }
        
        self.artistic_styles = {
            'impressionist': 'Soft, visible brushstrokes with emphasis on light and color.',
            'expressionist': 'Bold, emotional use of color and form to convey feelings.',
            'cubist': 'Geometric abstraction with multiple perspectives.',
            'surrealist': 'Dreamlike imagery with unexpected juxtapositions.',
            'pop_art': 'Bold, bright colors with popular culture references.',
            'minimalist': 'Clean, simple forms with limited color palette.',
            'watercolor': 'Soft, transparent washes with flowing color transitions.',
            'oil_painting': 'Rich, textured surfaces with layered color application.'
        }
        
        self.color_palettes = {
            'sunset': ['#FF6B35', '#F7931E', '#FFD23F', '#F4A261', '#E76F51'],
            'ocean': ['#006994', '#1E90FF', '#87CEEB', '#4682B4', '#20B2AA'],
            'forest': ['#228B22', '#32CD32', '#006400', '#8FBC8F', '#556B2F'],
            'desert': ['#DEB887', '#F4A460', '#CD853F', '#D2691E', '#8B4513'],
            'neon': ['#FF1493', '#00FF00', '#00BFFF', '#FFD700', '#FF4500']
        }

    def analyze_artwork(self, image_path):
        """Analyze artwork and provide feedback"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'score': 0,
                    'feedback': 'Unable to load image for analysis.',
                    'composition': 'N/A',
                    'color_analysis': 'N/A',
                    'technique': 'N/A',
                    'style': 'N/A',
                    'tips': ['Ensure the image file is valid and accessible.']
                }
            
            # Convert to RGB for analysis
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Analyze different aspects
            composition_score, composition_feedback = self._analyze_composition(image_rgb)
            color_score, color_feedback = self._analyze_colors(image_rgb)
            technique_score, technique_feedback = self._analyze_technique(image_rgb)
            style_score, style_feedback = self._analyze_style(image_rgb)
            
            # Calculate overall score
            overall_score = (composition_score + color_score + technique_score + style_score) / 4
            
            # Generate tips
            tips = self._generate_tips(overall_score, composition_score, color_score, technique_score, style_score)
            
            return {
                'score': round(overall_score, 1),
                'feedback': f"Overall, this artwork shows {self._get_strength_level(overall_score)} artistic qualities.",
                'composition': composition_feedback,
                'color_analysis': color_feedback,
                'technique': technique_feedback,
                'style': style_feedback,
                'tips': tips
            }
            
        except Exception as e:
            return {
                'score': 0,
                'feedback': f'Error during analysis: {str(e)}',
                'composition': 'N/A',
                'color_analysis': 'N/A',
                'technique': 'N/A',
                'style': 'N/A',
                'tips': ['Please try uploading a different image.']
            }

    def redraw_artwork(self, image_path):
        """Apply artistic filters to create a redrawn version"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None, "Unable to load image for redrawing."
            
            # Apply artistic filters
            redrawn_image = self._apply_artistic_filters(image)
            
            # Save redrawn image
            output_path = image_path.replace('.', '_redrawn.')
            cv2.imwrite(output_path, redrawn_image)
            
            # Convert to base64 for display
            _, buffer = cv2.imencode('.jpg', redrawn_image)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return img_base64, "Artwork successfully redrawn with artistic enhancements!"
            
        except Exception as e:
            return None, f"Error during redrawing: {str(e)}"

    def _analyze_composition(self, image):
        """Analyze composition aspects"""
        height, width = image.shape[:2]
        
        # Simple composition analysis based on image dimensions and content
        aspect_ratio = width / height
        
        if 0.8 <= aspect_ratio <= 1.2:
            composition_type = 'centered'
            score = 8.5
        elif aspect_ratio > 1.5:
            composition_type = 'landscape'
            score = 7.5
        elif aspect_ratio < 0.7:
            composition_type = 'portrait'
            score = 7.5
        else:
            composition_type = 'balanced'
            score = 8.0
        
        feedback = self.composition_templates.get(composition_type, 
                                                f"The {composition_type} composition creates an interesting visual layout.")
        
        return score, feedback

    def _analyze_colors(self, image):
        """Analyze color aspects"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Calculate color statistics
        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])
        
        # Determine color palette type
        if s_mean < 50:
            color_type = 'neutral'
            score = 7.0
        elif h_mean < 30 or h_mean > 150:
            color_type = 'cool'
            score = 8.0
        elif 30 <= h_mean <= 90:
            color_type = 'warm'
            score = 8.0
        else:
            color_type = 'balanced'
            score = 8.5
        
        feedback = self.color_templates.get(color_type, 
                                          f"The {color_type} color palette creates an engaging visual experience.")
        
        return score, feedback

    def _analyze_technique(self, image):
        """Analyze technique aspects"""
        # Analyze image texture and edges
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        if edge_density > 0.1:
            technique_type = 'detailed'
            score = 8.5
        elif edge_density > 0.05:
            technique_type = 'balanced'
            score = 8.0
        else:
            technique_type = 'soft'
            score = 7.5
        
        feedback = self.technique_templates.get(technique_type, 
                                              f"The {technique_type} technique shows good artistic control.")
        
        return score, feedback

    def _analyze_style(self, image):
        """Analyze style aspects"""
        # Simple style analysis based on color variance and texture
        color_std = np.std(image, axis=(0, 1))
        avg_color_std = np.mean(color_std)
        
        if avg_color_std > 50:
            style_type = 'expressionistic'
            score = 8.0
        elif avg_color_std > 30:
            style_type = 'modern'
            score = 8.5
        else:
            style_type = 'classical'
            score = 7.5
        
        feedback = self.style_templates.get(style_type, 
                                          f"The {style_type} style demonstrates artistic vision.")
        
        return score, feedback

    def _generate_tips(self, overall_score, comp_score, color_score, tech_score, style_score):
        """Generate improvement tips based on scores"""
        tips = []
        
        if overall_score < 7.0:
            tips.append("Consider experimenting with different compositions to create more visual interest.")
            tips.append("Try varying your color palette to add more depth and emotion.")
            tips.append("Practice different techniques to expand your artistic range.")
        
        if comp_score < 7.0:
            tips.append("Study the rule of thirds and other composition principles.")
        
        if color_score < 7.0:
            tips.append("Experiment with color theory and different color harmonies.")
        
        if tech_score < 7.0:
            tips.append("Practice controlling your brushstrokes and mark-making.")
        
        if style_score < 7.0:
            tips.append("Explore different artistic styles to find your unique voice.")
        
        if not tips:
            tips.append("Great work! Continue refining your technique and exploring new ideas.")
            tips.append("Consider challenging yourself with more complex subjects.")
        
        return tips

    def _get_strength_level(self, score):
        """Get strength level description based on score"""
        if score >= 9.0:
            return "exceptional"
        elif score >= 8.0:
            return "strong"
        elif score >= 7.0:
            return "good"
        elif score >= 6.0:
            return "developing"
        else:
            return "basic"

    def _apply_artistic_filters(self, image):
        """Apply artistic filters to create redrawn version"""
        # Apply multiple filters for artistic effect
        result = image.copy()
        
        # 1. Enhance contrast
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 2. Add slight blur for painterly effect
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        # 3. Enhance saturation
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.2)  # Increase saturation
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # 4. Add subtle vignette effect
        rows, cols = result.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols/4)
        kernel_y = cv2.getGaussianKernel(rows, rows/4)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        
        for i in range(3):
            result[:, :, i] = result[:, :, i] * mask
        
        return result