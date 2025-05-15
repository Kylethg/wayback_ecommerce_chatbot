"""
Tests for the WaybackClient class.
"""

import unittest
import datetime
from unittest.mock import patch, MagicMock
from app.components.wayback_client import WaybackClient
from app.utils.error_handling import WaybackError, SnapshotNotFoundError

class TestWaybackClient(unittest.TestCase):
    """Test cases for the WaybackClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = WaybackClient(cache_enabled=False)
        self.test_url = "example.com"
        self.test_date = datetime.date(2023, 1, 1)
    
    @patch('app.components.wayback_client.requests.get')
    def test_find_snapshot_for_date_success(self, mock_get):
        """Test finding a snapshot with successful API response"""
        # Mock the response from the Wayback Machine API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            ["timestamp", "original"],  # Header row
            ["20230101123456", "http://example.com"]  # Data row
        ]
        mock_get.return_value = mock_response
        
        # Call the method
        timestamp, original_url, found_date = self.client.find_snapshot_for_date(
            self.test_url, self.test_date
        )
        
        # Assert the results
        self.assertEqual(timestamp, "20230101123456")
        self.assertEqual(original_url, "http://example.com")
        self.assertEqual(found_date, self.test_date)
        
        # Assert the API was called with the correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertIn("example.com", call_args)
        self.assertIn("20230101", call_args)
    
    @patch('app.components.wayback_client.requests.get')
    def test_find_snapshot_for_date_no_results(self, mock_get):
        """Test finding a snapshot with no results"""
        # Mock the response from the Wayback Machine API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            ["timestamp", "original"]  # Header row only, no data
        ]
        mock_get.return_value = mock_response
        
        # Call the method
        timestamp, original_url, found_date = self.client.find_snapshot_for_date(
            self.test_url, self.test_date, max_offset=0  # No offset to simplify test
        )
        
        # Assert the results
        self.assertIsNone(timestamp)
        self.assertIsNone(original_url)
        self.assertIsNone(found_date)
    
    @patch('app.components.wayback_client.requests.get')
    def test_find_snapshot_for_date_api_error(self, mock_get):
        """Test finding a snapshot with API error"""
        # Mock the response from the Wayback Machine API
        mock_get.side_effect = Exception("API Error")
        
        # Call the method
        timestamp, original_url, found_date = self.client.find_snapshot_for_date(
            self.test_url, self.test_date, max_offset=0  # No offset to simplify test
        )
        
        # Assert the results
        self.assertIsNone(timestamp)
        self.assertIsNone(original_url)
        self.assertIsNone(found_date)
    
    @patch('app.components.wayback_client.requests.get')
    def test_get_snapshot_content_success(self, mock_get):
        """Test getting snapshot content with successful API response"""
        # Mock the response from the Wayback Machine
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        # Call the method
        content = self.client.get_snapshot_content("20230101123456", "http://example.com")
        
        # Assert the results
        self.assertEqual(content, "<html><body>Test content</body></html>")
        
        # Assert the API was called with the correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertIn("20230101123456", call_args)
        self.assertIn("example.com", call_args)
    
    @patch('app.components.wayback_client.requests.get')
    def test_get_snapshot_content_invalid_content(self, mock_get):
        """Test getting snapshot content with invalid content"""
        # Mock the response from the Wayback Machine
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Not HTML content"  # Too short and no HTML tag
        mock_get.return_value = mock_response
        
        # Call the method
        content = self.client.get_snapshot_content("20230101123456", "http://example.com")
        
        # Assert the results
        self.assertIsNone(content)
    
    @patch('app.components.wayback_client.requests.get')
    def test_get_snapshot_content_api_error(self, mock_get):
        """Test getting snapshot content with API error"""
        # Mock the response from the Wayback Machine
        mock_get.side_effect = Exception("API Error")
        
        # Call the method
        content = self.client.get_snapshot_content("20230101123456", "http://example.com")
        
        # Assert the results
        self.assertIsNone(content)
    
    def test_get_wayback_url(self):
        """Test generating a Wayback Machine URL"""
        # Call the method
        url = self.client.get_wayback_url("20230101123456", "http://example.com")
        
        # Assert the results
        self.assertEqual(url, "https://web.archive.org/web/20230101123456/http://example.com")

if __name__ == '__main__':
    unittest.main()