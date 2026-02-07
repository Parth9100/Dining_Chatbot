"""
Notification Services Module
Handles SMS (Twilio) and Email notifications for booking confirmations.
"""

import json
import smtplib
import urllib.request
import urllib.error
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class TwilioSMS:
    """
    Send SMS notifications using Twilio API.
    
    Features:
    - Booking confirmations
    - Cancellation notices
    - Reminder messages
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with config file path."""
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent / "config.json"
        
        self.account_sid = None
        self.auth_token = None
        self.phone_number = None
        self.enabled = False
        
        self._load_config()
    
    def _load_config(self):
        """Load Twilio configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                twilio_config = config.get('twilio', {})
                self.account_sid = twilio_config.get('account_sid')
                self.auth_token = twilio_config.get('auth_token')
                self.phone_number = twilio_config.get('phone_number')
                self.enabled = twilio_config.get('enabled', False)
                
                # Validate config
                if self.account_sid and not self.account_sid.startswith('YOUR_'):
                    if self.auth_token and not self.auth_token.startswith('YOUR_'):
                        self.enabled = True
        except Exception as e:
            print(f"Warning: Could not load Twilio config: {e}")
    
    def send_sms(self, to_number: str, message: str) -> Tuple[bool, str]:
        """
        Send an SMS message.
        
        Args:
            to_number: Recipient phone number (E.164 format: +1234567890)
            message: Message content
            
        Returns:
            Tuple of (success, message/error)
        """
        if not self.enabled:
            return False, "Twilio SMS is not enabled. Configure in config.json"
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            
            # Prepare form data
            data = {
                'From': self.phone_number,
                'To': to_number,
                'Body': message
            }
            
            # URL encode the data
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            
            # Create Basic Auth header
            credentials = base64.b64encode(
                f"{self.account_sid}:{self.auth_token}".encode('utf-8')
            ).decode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=encoded_data,
                headers={
                    'Authorization': f'Basic {credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            return True, f"SMS sent! SID: {result.get('sid', 'unknown')}"
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return False, f"Twilio Error: {error_body}"
        except Exception as e:
            return False, f"SMS Error: {str(e)}"
    
    def send_booking_confirmation(self, to_number: str, booking: Dict[str, Any]) -> Tuple[bool, str]:
        """Send booking confirmation SMS."""
        message = (
            f"🍽️ Reservation Confirmed!\n"
            f"Booking ID: {booking['booking_id']}\n"
            f"Table: {booking['table_id']}\n"
            f"Date: {booking['date']}\n"
            f"Time: {booking['time_slot']}\n"
            f"Party: {booking['party_size']} guests\n"
            f"Thank you!"
        )
        return self.send_sms(to_number, message)
    
    def send_cancellation_notice(self, to_number: str, booking: Dict[str, Any]) -> Tuple[bool, str]:
        """Send cancellation confirmation SMS."""
        message = (
            f"❌ Booking Cancelled\n"
            f"Booking ID: {booking['booking_id']}\n"
            f"Date: {booking['date']}\n"
            f"Time: {booking['time_slot']}\n"
            f"We hope to see you again!"
        )
        return self.send_sms(to_number, message)


class EmailNotification:
    """
    Send email notifications using SMTP.
    
    Features:
    - HTML formatted booking confirmations
    - Cancellation notices
    - Rich email templates
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with config file path."""
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent / "config.json"
        
        self.smtp_server = None
        self.smtp_port = 587
        self.sender_email = None
        self.sender_password = None
        self.enabled = False
        
        self._load_config()
    
    def _load_config(self):
        """Load email configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                email_config = config.get('email', {})
                self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
                self.smtp_port = email_config.get('smtp_port', 587)
                self.sender_email = email_config.get('sender_email')
                self.sender_password = email_config.get('sender_password')
                self.enabled = email_config.get('enabled', False)
                
                # Validate config
                if self.sender_email and not self.sender_email.startswith('your-'):
                    if self.sender_password and not self.sender_password.startswith('your-'):
                        self.enabled = True
        except Exception as e:
            print(f"Warning: Could not load email config: {e}")
    
    def send_email(self, to_email: str, subject: str, 
                   body_text: str, body_html: str = None) -> Tuple[bool, str]:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            
        Returns:
            Tuple of (success, message/error)
        """
        if not self.enabled:
            return False, "Email is not enabled. Configure in config.json"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email
            
            # Attach text part
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
            
            # Attach HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, f"Email sent to {to_email}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Email authentication failed. Check credentials."
        except Exception as e:
            return False, f"Email Error: {str(e)}"
    
    def _create_booking_html(self, booking: Dict[str, Any]) -> str:
        """Create HTML template for booking confirmation."""
        return f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #4CAF50; color: white; padding: 20px; text-align: center;">
                <h1>🍽️ Reservation Confirmed!</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2>Booking Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Booking ID:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{booking['booking_id']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Table:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{booking['table_id']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Date:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{booking['date']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Time:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{booking['time_slot']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Party Size:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{booking['party_size']} guests</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><strong>Name:</strong></td>
                        <td style="padding: 10px;">{booking.get('customer_name', 'Guest')}</td>
                    </tr>
                </table>
            </div>
            <div style="padding: 20px; text-align: center; color: #666;">
                <p>Thank you for your reservation!</p>
                <p>We look forward to seeing you.</p>
            </div>
        </body>
        </html>
        '''
    
    def send_booking_confirmation(self, to_email: str, booking: Dict[str, Any]) -> Tuple[bool, str]:
        """Send booking confirmation email."""
        subject = f"🍽️ Reservation Confirmed - {booking['booking_id']}"
        
        body_text = (
            f"Reservation Confirmed!\n\n"
            f"Booking ID: {booking['booking_id']}\n"
            f"Table: {booking['table_id']}\n"
            f"Date: {booking['date']}\n"
            f"Time: {booking['time_slot']}\n"
            f"Party Size: {booking['party_size']} guests\n"
            f"Name: {booking.get('customer_name', 'Guest')}\n\n"
            f"Thank you for your reservation!"
        )
        
        body_html = self._create_booking_html(booking)
        
        return self.send_email(to_email, subject, body_text, body_html)
    
    def send_cancellation_notice(self, to_email: str, booking: Dict[str, Any]) -> Tuple[bool, str]:
        """Send cancellation confirmation email."""
        subject = f"❌ Booking Cancelled - {booking['booking_id']}"
        
        body_text = (
            f"Booking Cancelled\n\n"
            f"Your reservation has been cancelled:\n"
            f"Booking ID: {booking['booking_id']}\n"
            f"Date: {booking['date']}\n"
            f"Time: {booking['time_slot']}\n\n"
            f"We hope to see you again soon!"
        )
        
        return self.send_email(to_email, subject, body_text)


class NotificationService:
    """
    Unified notification service combining SMS and Email.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize all notification channels."""
        self.sms = TwilioSMS(config_path)
        self.email = EmailNotification(config_path)
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of all notification channels."""
        return {
            'sms_enabled': self.sms.enabled,
            'email_enabled': self.email.enabled
        }
    
    def send_booking_notification(self, booking: Dict[str, Any],
                                   phone: str = None, 
                                   email: str = None) -> Dict[str, Tuple[bool, str]]:
        """
        Send booking confirmation via all available channels.
        
        Args:
            booking: Booking details
            phone: Optional phone number
            email: Optional email address
            
        Returns:
            Dictionary with results for each channel
        """
        results = {}
        
        if phone and self.sms.enabled:
            results['sms'] = self.sms.send_booking_confirmation(phone, booking)
        
        if email and self.email.enabled:
            results['email'] = self.email.send_booking_confirmation(email, booking)
        
        return results
    
    def send_cancellation_notification(self, booking: Dict[str, Any],
                                        phone: str = None,
                                        email: str = None) -> Dict[str, Tuple[bool, str]]:
        """Send cancellation notice via all available channels."""
        results = {}
        
        if phone and self.sms.enabled:
            results['sms'] = self.sms.send_cancellation_notice(phone, booking)
        
        if email and self.email.enabled:
            results['email'] = self.email.send_cancellation_notice(email, booking)
        
        return results


# Test function
def main():
    """Test notification services."""
    service = NotificationService()
    
    print("Notification Service Status:")
    print(f"  SMS: {'Enabled' if service.sms.enabled else 'Disabled'}")
    print(f"  Email: {'Enabled' if service.email.enabled else 'Disabled'}")
    
    # Test booking
    test_booking = {
        'booking_id': 'BK123456',
        'table_id': 'T003',
        'date': '2026-02-08',
        'time_slot': '19:00-20:00',
        'party_size': 4,
        'customer_name': 'Test User'
    }
    
    print("\nTest Booking:")
    print(f"  {test_booking}")


if __name__ == "__main__":
    main()
