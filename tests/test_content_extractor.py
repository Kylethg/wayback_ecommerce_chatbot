"""
Tests for the ContentExtractor class.
"""

import unittest
from app.components.content_extractor import ContentExtractor

class TestContentExtractor(unittest.TestCase):
    """Test cases for the ContentExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = ContentExtractor()
        
        # Sample HTML content for testing
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Ecommerce Site</title>
        </head>
        <body>
            <div class="hero-banner">
                <h1>Summer Sale</h1>
                <p>Up to 50% off selected items</p>
                <img src="banner.jpg" alt="Summer Sale Banner">
            </div>
            
            <div class="promo-banner">
                <p>Use code SUMMER20 for an extra 20% off</p>
            </div>
            
            <div class="product-card">
                <h3 class="name">Test Product 1</h3>
                <p class="price">$99.99</p>
                <p class="description">This is a test product</p>
            </div>
            
            <div class="product-card">
                <h3 class="name">Test Product 2</h3>
                <p class="price">$149.99</p>
                <p class="description">This is another test product</p>
            </div>
        </body>
        </html>
        """
    
    def test_extract_content_default_domain(self):
        """Test extracting content with default domain patterns"""
        # Extract content using the default domain patterns
        extracted_content = self.extractor.extract_content(self.sample_html, "unknown-domain.com")
        
        # Assert that content was extracted
        self.assertTrue(len(extracted_content["hero_content"]) > 0)
        self.assertTrue(len(extracted_content["promotions"]) > 0)
        self.assertTrue(len(extracted_content["products"]) > 0)
        
        # Check for specific content
        hero_content_text = "\n".join(extracted_content["hero_content"])
        self.assertIn("Summer Sale", hero_content_text)
        
        promotions_text = "\n".join(extracted_content["promotions"])
        self.assertIn("SUMMER20", promotions_text)
    
    def test_extract_content_specific_domain(self):
        """Test extracting content with domain-specific patterns"""
        # Add a test domain pattern
        self.extractor.domain_patterns["testdomain.com"] = {
            "promo_selectors": [".promo-banner"],
            "product_selectors": [".product-card"],
            "hero_selectors": [".hero-banner"]
        }
        
        # Extract content using the specific domain patterns
        extracted_content = self.extractor.extract_content(self.sample_html, "testdomain.com")
        
        # Assert that content was extracted
        self.assertTrue(len(extracted_content["hero_content"]) > 0)
        self.assertTrue(len(extracted_content["promotions"]) > 0)
        self.assertTrue(len(extracted_content["products"]) > 0)
        
        # Check for specific content
        hero_content_text = "\n".join(extracted_content["hero_content"])
        self.assertIn("Summer Sale", hero_content_text)
        
        promotions_text = "\n".join(extracted_content["promotions"])
        self.assertIn("SUMMER20", promotions_text)
    
    def test_fallback_extraction(self):
        """Test fallback extraction when domain-specific extraction fails"""
        # Create HTML with no matching selectors
        html_without_matches = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Ecommerce Site</title>
        </head>
        <body>
            <div class="no-match">
                <h1>Summer Sale</h1>
                <p>Up to 50% off selected items</p>
            </div>
            
            <div class="no-match-promo">
                <p>Use code SUMMER20 for an extra 20% off</p>
            </div>
        </body>
        </html>
        """
        
        # Extract content
        extracted_content = self.extractor.extract_content(html_without_matches, "unknown-domain.com")
        
        # The fallback extraction should still find the headings and promotional terms
        self.assertTrue(len(extracted_content["hero_content"]) > 0)
        
        # Check for specific content
        all_content = "\n".join([item for sublist in extracted_content.values() for item in sublist])
        self.assertIn("Summer Sale", all_content)
        self.assertIn("50% off", all_content)
    
    def test_format_extracted_content(self):
        """Test formatting extracted content"""
        # Create sample extracted content
        extracted_content = {
            "hero_content": ["Summer Sale", "Up to 50% off selected items"],
            "promotions": ["Use code SUMMER20 for an extra 20% off"],
            "products": ["{'name': 'Test Product 1', 'price': '$99.99'}", "{'name': 'Test Product 2', 'price': '$149.99'}"],
            "navigation": []
        }
        
        # Format the content
        formatted_content = self.extractor.format_extracted_content(extracted_content)
        
        # Assert that the formatted content contains the expected sections
        self.assertIn("# HERO CONTENT", formatted_content)
        self.assertIn("# PROMOTIONS", formatted_content)
        self.assertIn("# FEATURED PRODUCTS", formatted_content)
        self.assertIn("# EXTRACTION METADATA", formatted_content)
        
        # Assert that the formatted content contains the expected data
        self.assertIn("Summer Sale", formatted_content)
        self.assertIn("SUMMER20", formatted_content)
        self.assertIn("Test Product 1", formatted_content)
        self.assertIn("Elements found:", formatted_content)

if __name__ == '__main__':
    unittest.main()