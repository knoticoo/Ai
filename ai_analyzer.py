import cv2
import numpy as np
from PIL import Image
import torch
from transformers import pipeline
import os
import base64
from io import BytesIO
import json

class AIAnalyzer:
    def __init__(self):
        """Initialize AI analyzer with free local models"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize image classification model for art analysis
        try:
            self.classifier = pipeline(
                "image-classification",
                model="microsoft/resnet-50",
                device=self.device
            )
        except:
            # Fallback to a simpler approach if model loading fails
            self.classifier = None
        
        # Art analysis templates
        self.art_analysis_templates = {
            'composition': [
                "The composition shows {aspect} - this creates {effect}",
                "Consider {suggestion} to improve the composition",
                "The focal point is {position}, which {impact}"
            ],
            'color': [
                "The color palette uses {colors} which creates {mood}",
                "Color harmony is {quality} - try {suggestion}",
                "The contrast between {color1} and {color2} is {effect}"
            ],
            'technique': [
                "The technique shows {skill_level} - focus on {improvement}",
                "Brush strokes are {characteristic} - experiment with {variation}",
                "The medium handling is {quality} - practice {exercise}"
            ],
            'style': [
                "This style resembles {artistic_movement} - study {artists}",
                "The artistic approach is {description} - explore {direction}",
                "Style consistency is {level} - develop {aspect}"
            ]
        }
        
        self.art_styles = [
            "Realistic", "Impressionist", "Abstract", "Expressionist", 
            "Surrealist", "Cubist", "Minimalist", "Pop Art", "Digital Art",
            "Watercolor", "Oil Painting", "Sketch", "Mixed Media"
        ]
        
        self.color_palettes = [
            "Warm tones (reds, oranges, yellows)",
            "Cool tones (blues, greens, purples)",
            "Monochromatic",
            "Complementary colors",
            "Analogous colors",
            "Triadic colors",
            "Neutral palette"
        ]

    def analyze_artwork(self, image_path):
        """
        Analyze artwork and provide feedback
        Returns: (feedback_text, score)
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            image_array = np.array(image)
            
            # Basic image analysis
            analysis = self._basic_image_analysis(image_array)
            
            # Generate comprehensive feedback
            feedback = self._generate_feedback(analysis)
            
            # Calculate score based on analysis
            score = self._calculate_score(analysis)
            
            return feedback, score
            
        except Exception as e:
            print(f"Error analyzing artwork: {e}")
            return "Unable to analyze artwork at this time. Please try again.", 0.5

    def _basic_image_analysis(self, image_array):
        """Perform basic image analysis"""
        analysis = {}
        
        # Convert to different color spaces
        if len(image_array.shape) == 3:
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
            hsv = None
        
        # Analyze composition
        analysis['composition'] = self._analyze_composition(gray)
        
        # Analyze colors
        if hsv is not None:
            analysis['colors'] = self._analyze_colors(hsv, image_array)
        
        # Analyze technique
        analysis['technique'] = self._analyze_technique(gray)
        
        # Analyze style
        analysis['style'] = self._analyze_style(image_array)
        
        return analysis

    def _analyze_composition(self, gray_image):
        """Analyze composition using edge detection and rule of thirds"""
        height, width = gray_image.shape
        
        # Edge detection
        edges = cv2.Canny(gray_image, 50, 150)
        edge_density = np.sum(edges > 0) / (height * width)
        
        # Rule of thirds analysis
        third_h = height // 3
        third_w = width // 3
        
        # Check if main elements align with rule of thirds
        top_third = np.sum(gray_image[:third_h, :]) / (third_h * width)
        middle_third = np.sum(gray_image[third_h:2*third_h, :]) / (third_h * width)
        bottom_third = np.sum(gray_image[2*third_h:, :]) / (third_h * width)
        
        # Determine focal point
        focal_point = "center" if middle_third > (top_third + bottom_third) / 2 else "off-center"
        
        return {
            'edge_density': edge_density,
            'focal_point': focal_point,
            'rule_of_thirds': abs(middle_third - (top_third + bottom_third) / 2),
            'balance': self._calculate_balance(gray_image)
        }

    def _analyze_colors(self, hsv_image, rgb_image):
        """Analyze color composition"""
        # Extract color channels
        h, s, v = cv2.split(hsv_image)
        
        # Calculate color statistics
        hue_mean = np.mean(h)
        saturation_mean = np.mean(s)
        value_mean = np.mean(v)
        
        # Determine color palette
        if saturation_mean < 50:
            palette = "Neutral palette"
        elif hue_mean < 30 or hue_mean > 150:
            palette = "Cool tones (blues, greens, purples)"
        else:
            palette = "Warm tones (reds, oranges, yellows)"
        
        # Calculate color contrast
        contrast = np.std(v)
        
        return {
            'hue_mean': hue_mean,
            'saturation_mean': saturation_mean,
            'value_mean': value_mean,
            'palette': palette,
            'contrast': contrast,
            'color_variety': len(np.unique(h))
        }

    def _analyze_technique(self, gray_image):
        """Analyze drawing/painting technique"""
        # Calculate texture using local binary patterns
        texture_score = self._calculate_texture(gray_image)
        
        # Analyze brush stroke patterns
        stroke_pattern = self._analyze_strokes(gray_image)
        
        # Calculate detail level
        detail_level = self._calculate_detail_level(gray_image)
        
        return {
            'texture_score': texture_score,
            'stroke_pattern': stroke_pattern,
            'detail_level': detail_level,
            'technique_quality': (texture_score + detail_level) / 2
        }

    def _analyze_style(self, image_array):
        """Analyze artistic style"""
        # Simple style classification based on image characteristics
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Calculate style indicators
        edge_density = np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size
        color_variety = len(np.unique(image_array.reshape(-1, image_array.shape[-1]), axis=0)) if len(image_array.shape) == 3 else 1
        
        # Determine style based on characteristics
        if edge_density > 0.1:
            if color_variety > 100:
                style = "Expressionist"
            else:
                style = "Sketch"
        elif color_variety > 200:
            style = "Digital Art"
        elif color_variety < 50:
            style = "Minimalist"
        else:
            style = "Realistic"
        
        return {
            'detected_style': style,
            'edge_density': edge_density,
            'color_variety': color_variety
        }

    def _calculate_balance(self, gray_image):
        """Calculate visual balance of the image"""
        height, width = gray_image.shape
        left_half = gray_image[:, :width//2]
        right_half = gray_image[:, width//2:]
        
        left_mean = np.mean(left_half)
        right_mean = np.mean(right_half)
        
        return 1 - abs(left_mean - right_mean) / 255

    def _calculate_texture(self, gray_image):
        """Calculate texture score using local variance"""
        kernel = np.ones((5, 5), np.float32) / 25
        smooth = cv2.filter2D(gray_image, -1, kernel)
        texture = cv2.absdiff(gray_image, smooth)
        return np.mean(texture) / 255

    def _analyze_strokes(self, gray_image):
        """Analyze brush stroke patterns"""
        # Detect directional patterns
        sobelx = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate stroke direction
        direction = np.arctan2(sobely, sobelx)
        direction_consistency = np.std(direction)
        
        if direction_consistency < 0.5:
            return "Consistent"
        elif direction_consistency < 1.0:
            return "Varied"
        else:
            return "Random"

    def _calculate_detail_level(self, gray_image):
        """Calculate detail level using frequency analysis"""
        # Apply FFT to analyze frequency content
        f_transform = np.fft.fft2(gray_image)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        # High frequency content indicates detail
        detail_score = np.mean(magnitude_spectrum)
        return min(detail_score / 10, 1.0)

    def _generate_feedback(self, analysis):
        """Generate comprehensive feedback based on analysis"""
        feedback_parts = []
        
        # Composition feedback
        comp = analysis['composition']
        if comp['edge_density'] > 0.05:
            feedback_parts.append("Strong composition with clear focal points. The edge density suggests good definition.")
        else:
            feedback_parts.append("Consider adding more definition and contrast to strengthen the composition.")
        
        if comp['focal_point'] == 'center':
            feedback_parts.append("The focal point is centered - experiment with off-center compositions for more dynamic results.")
        
        # Color feedback
        if 'colors' in analysis:
            colors = analysis['colors']
            feedback_parts.append(f"Color palette: {colors['palette']}. ")
            if colors['contrast'] < 50:
                feedback_parts.append("Consider increasing contrast for more visual impact.")
            else:
                feedback_parts.append("Good contrast levels create visual interest.")
        
        # Technique feedback
        tech = analysis['technique']
        if tech['detail_level'] > 0.7:
            feedback_parts.append("Excellent attention to detail. The technique shows careful execution.")
        elif tech['detail_level'] > 0.4:
            feedback_parts.append("Good detail level. Consider refining specific areas for more impact.")
        else:
            feedback_parts.append("Focus on adding more detail and texture to enhance the artwork.")
        
        # Style feedback
        style = analysis['style']
        feedback_parts.append(f"Style detected: {style['detected_style']}. ")
        if style['color_variety'] > 100:
            feedback_parts.append("Rich color variety shows good artistic range.")
        else:
            feedback_parts.append("Consider exploring more color variations to expand your palette.")
        
        # Improvement suggestions
        suggestions = [
            "Practice different brush stroke techniques to add variety.",
            "Experiment with different color harmonies.",
            "Study composition principles like rule of thirds.",
            "Try different artistic styles to develop your unique voice.",
            "Focus on value relationships for better depth."
        ]
        
        feedback_parts.append(f"\n\nSuggestions for improvement:\n" + "\n".join(suggestions[:3]))
        
        return " ".join(feedback_parts)

    def _calculate_score(self, analysis):
        """Calculate overall score based on analysis"""
        score = 0.5  # Base score
        
        # Composition score (25%)
        comp = analysis['composition']
        score += 0.25 * (comp['balance'] * 0.5 + min(comp['edge_density'] * 10, 1.0) * 0.5)
        
        # Color score (25%)
        if 'colors' in analysis:
            colors = analysis['colors']
            color_score = min(colors['contrast'] / 100, 1.0) * 0.5 + min(colors['color_variety'] / 200, 1.0) * 0.5
            score += 0.25 * color_score
        
        # Technique score (25%)
        tech = analysis['technique']
        score += 0.25 * tech['technique_quality']
        
        # Style score (25%)
        style = analysis['style']
        style_score = min(style['color_variety'] / 100, 1.0) * 0.5 + (1 - style['edge_density']) * 0.5
        score += 0.25 * style_score
        
        return min(score, 1.0)

    def redraw_artwork(self, image_path):
        """
        Create an AI-redrawn version of the artwork
        Returns: base64 encoded image
        """
        try:
            # Load original image
            original_image = Image.open(image_path)
            
            # For now, we'll create a stylized version using basic image processing
            # In a full implementation, you could use diffusion models like Stable Diffusion
            
            # Convert to numpy array
            img_array = np.array(original_image)
            
            # Apply artistic filters
            redrawn = self._apply_artistic_filters(img_array)
            
            # Convert back to PIL Image
            redrawn_image = Image.fromarray(redrawn)
            
            # Convert to base64 for web display
            buffer = BytesIO()
            redrawn_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error redrawing artwork: {e}")
            return None

    def _apply_artistic_filters(self, image_array):
        """Apply artistic filters to create a redrawn version"""
        if len(image_array.shape) == 3:
            # Color image
            # Apply edge enhancement
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Create stylized version
            stylized = cv2.stylization(image_array, sigma_s=60, sigma_r=0.4)
            
            # Add edge overlay
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            result = cv2.addWeighted(stylized, 0.8, edges_colored, 0.2, 0)
            
            return result
        else:
            # Grayscale image
            # Apply pencil sketch effect
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(image_array, -1, kernel)
            
            return sharpened