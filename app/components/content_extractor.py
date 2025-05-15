"""
HTML content extractor for the Wayback Ecommerce Chatbot.
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Any

class ContentExtractor:
    """Extract relevant ecommerce content from HTML"""
    
    def __init__(self):
        # Common ecommerce element classes and IDs
        self.promo_patterns = [
            'promo', 'promotion', 'banner', 'offer', 'discount', 
            'sale', 'deal', 'campaign', 'hero', 'slider'
        ]
        
        self.product_patterns = [
            'product', 'item', 'card', 'tile', 'listing'
        ]
        
        self.price_patterns = [
            'price', 'cost', 'amount', 'value', 'now', 'was'
        ]
        
        # Domain-specific extraction patterns
        self.domain_patterns = {
            "asos.com": {
                "promo_selectors": [".promotion-banner", ".discount-strip", ".hero__title"],
                "product_selectors": [".product-card", ".product-tile"],
                "hero_selectors": [".hero", ".homepage-hero", ".main-banner"]
            },
            "lookfantastic.com": {
                "promo_selectors": [".promo-banner", ".offer-strip", ".lf-banner__content"],
                "product_selectors": [".productBlock", ".product-list__item"],
                "hero_selectors": [".hero-banner", ".homepage-banner"]
            },
            # Default patterns for unknown sites
            "default": {
                "promo_selectors": [".promo", ".banner", ".offer", ".discount", ".sale", ".deal"],
                "product_selectors": [".product", ".item", ".card"],
                "hero_selectors": [".hero", ".banner", ".slider", ".carousel"]
            }
        }
    
    def extract_content(self, html_content: str, domain: str) -> Dict[str, List[str]]:
        """
        Extract relevant ecommerce content from HTML
        
        Args:
            html_content: HTML content as string
            domain: Domain name for domain-specific extraction
            
        Returns:
            Dictionary of extracted content by category
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_content = {
            "promotions": [],
            "products": [],
            "navigation": [],
            "hero_content": []
        }
        
        # Get the appropriate patterns for this domain
        domain_key = next((k for k in self.domain_patterns.keys() if k in domain), "default")
        patterns = self.domain_patterns[domain_key]
        
        # Extract promotions using domain-specific selectors
        for selector in patterns["promo_selectors"]:
            for element in soup.select(selector):
                text = element.get_text().strip()
                if text and len(text) > 3:  # Filter out empty or very short text
                    extracted_content["promotions"].append(text)
        
        # Extract hero content
        for selector in patterns["hero_selectors"]:
            for element in soup.select(selector):
                # Get text content
                text = element.get_text().strip()
                if text and len(text) > 5:
                    extracted_content["hero_content"].append(text)
                
                # Also get any images within hero sections
                for img in element.find_all('img', alt=True):
                    if len(img['alt']) > 5:
                        extracted_content["hero_content"].append(f"Hero image: {img['alt']}")
        
        # Extract featured products
        for selector in patterns["product_selectors"]:
            for element in soup.select(selector):
                product_info = {}
                
                # Try to extract product name
                name_element = element.find(['h3', 'h4', 'h5', '.name', '.title'])
                if name_element:
                    product_info["name"] = name_element.get_text().strip()
                
                # Try to extract price
                price_element = element.find(class_=lambda c: c and any(x in c.lower() for x in self.price_patterns))
                if price_element:
                    product_info["price"] = price_element.get_text().strip()
                
                if product_info:
                    extracted_content["products"].append(str(product_info))
        
        # Fallback extraction if specific selectors didn't yield results
        if not any(extracted_content.values()):
            print(f"Domain-specific extraction failed for {domain}, using fallback methods")
            extracted_content = self._fallback_extraction(soup)
        
        return extracted_content
    
    def _fallback_extraction(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Fallback extraction method when domain-specific extraction fails
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            Dictionary of extracted content by category
        """
        extracted_content = {
            "promotions": [],
            "products": [],
            "navigation": [],
            "hero_content": []
        }
        
        # Extract all headings
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if text and len(text) > 5:
                extracted_content["hero_content"].append(f"Heading: {text}")
        
        # Look for common promotional terms in any element
        promo_terms = ['off', 'save', 'discount', 'free', 'deal', 'offer', 'promotion', 'sale']
        for term in promo_terms:
            for element in soup.find_all(text=re.compile(term, re.IGNORECASE)):
                parent = element.parent
                if parent and parent.name not in ['script', 'style']:
                    text = parent.get_text().strip()
                    if text and len(text) < 200:  # Avoid large text blocks
                        extracted_content["promotions"].append(text)
        
        # Extract all images with meaningful alt text
        for img in soup.find_all('img', alt=True):
            if len(img['alt']) > 5 and not img['alt'].isspace():
                extracted_content["hero_content"].append(f"Image: {img['alt']}")
        
        return extracted_content
    
    def format_extracted_content(self, extracted_content: Dict[str, List[str]]) -> str:
        """
        Format extracted content for analysis
        
        Args:
            extracted_content: Dictionary of extracted content by category
            
        Returns:
            Formatted string of extracted content
        """
        formatted_content = []
        
        if extracted_content["hero_content"]:
            formatted_content.append("# HERO CONTENT")
            formatted_content.extend(extracted_content["hero_content"])
        
        if extracted_content["promotions"]:
            formatted_content.append("# PROMOTIONS")
            formatted_content.extend(extracted_content["promotions"])
        
        if extracted_content["products"]:
            formatted_content.append("# FEATURED PRODUCTS")
            formatted_content.extend(extracted_content["products"])
        
        if extracted_content["navigation"]:
            formatted_content.append("# NAVIGATION")
            formatted_content.extend(extracted_content["navigation"])
        
        # Add metadata about extraction success
        extraction_stats = {
            "hero_count": len(extracted_content["hero_content"]),
            "promo_count": len(extracted_content["promotions"]),
            "product_count": len(extracted_content["products"]),
            "navigation_count": len(extracted_content["navigation"])
        }
        formatted_content.append("# EXTRACTION METADATA")
        formatted_content.append(f"Elements found: {sum(extraction_stats.values())}")
        
        return "\n".join(formatted_content)