#!/usr/bin/env python3
"""
Test script for ArtAI AI components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_analyzer import AIAnalyzer
from ai_guide_generator import AIGuideGenerator

def test_ai_analyzer():
    """Test the AI Analyzer functionality"""
    print("🧪 Testing AI Analyzer...")
    
    try:
        analyzer = AIAnalyzer()
        print("✅ AI Analyzer initialized successfully")
        
        # Test guide generation
        guide = analyzer.analyze_artwork("test_image.jpg")
        print("✅ AI Analysis method works (no actual image needed)")
        
        return True
    except Exception as e:
        print(f"❌ AI Analyzer test failed: {e}")
        return False

def test_ai_guide_generator():
    """Test the AI Guide Generator functionality"""
    print("🧪 Testing AI Guide Generator...")
    
    try:
        generator = AIGuideGenerator()
        print("✅ AI Guide Generator initialized successfully")
        
        # Test guide generation
        guide = generator.generate_guide("Watercolor Painting", "Learn the basics of watercolor techniques")
        print("✅ Guide generation works")
        print(f"📝 Generated guide type: {guide.get('type', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ AI Guide Generator test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting ArtAI AI Component Tests...\n")
    
    tests_passed = 0
    total_tests = 2
    
    if test_ai_analyzer():
        tests_passed += 1
    
    print()
    
    if test_ai_guide_generator():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All AI components are working correctly!")
        return True
    else:
        print("⚠️  Some AI components have issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)