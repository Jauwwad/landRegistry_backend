"""
Email notification service for land transfers
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('MAIL_PORT', 587))
        self.smtp_username = os.getenv('MAIL_USERNAME')
        self.smtp_password = os.getenv('MAIL_PASSWORD')
        self.default_sender = os.getenv('MAIL_DEFAULT_SENDER')
        self.use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'

    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.default_sender
            msg['To'] = to_email

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_transfer_initiated_email(self, transfer, land, from_user, to_user):
        """Send email when a transfer is initiated"""
        subject = f"Land Transfer Initiated - {land.title}"
        
        # Email to recipient
        html_content = f"""
        <html>
        <body>
            <h2>🏢 Land Transfer Notification</h2>
            <p>Hello {to_user.first_name},</p>
            
            <p>A land transfer has been initiated for you:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>📋 Transfer Details</h3>
                <p><strong>Land:</strong> {land.title}</p>
                <p><strong>Property ID:</strong> {land.property_id}</p>
                <p><strong>Location:</strong> {land.location}</p>
                <p><strong>Area:</strong> {land.area} sq m</p>
                <p><strong>From:</strong> {from_user.first_name} {from_user.last_name}</p>
                <p><strong>Price:</strong> ${transfer.price:,.2f}</p>
                <p><strong>Status:</strong> Pending</p>
            </div>
            
            <p>The land owner will execute this transfer on the blockchain once ready.</p>
            
            <p>You will receive another notification when the transfer is completed.</p>
            
            <p>Best regards,<br>Land Registry System</p>
        </body>
        </html>
        """
        
        self.send_email(to_user.email, subject, html_content)
        
        # Email to sender
        sender_subject = f"Transfer Initiated - {land.title}"
        sender_html = f"""
        <html>
        <body>
            <h2>🏢 Transfer Initiated Successfully</h2>
            <p>Hello {from_user.first_name},</p>
            
            <p>Your land transfer has been initiated successfully:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>📋 Transfer Details</h3>
                <p><strong>Land:</strong> {land.title}</p>
                <p><strong>Property ID:</strong> {land.property_id}</p>
                <p><strong>To:</strong> {to_user.first_name} {to_user.last_name}</p>
                <p><strong>Price:</strong> ${transfer.price:,.2f}</p>
                <p><strong>Status:</strong> Pending</p>
            </div>
            
            <p>You can now execute this transfer from your dashboard to complete it on the blockchain.</p>
            
            <p>Best regards,<br>Land Registry System</p>
        </body>
        </html>
        """
        
        self.send_email(from_user.email, sender_subject, sender_html)

    def send_transfer_completed_email(self, transfer, land, from_user, to_user):
        """Send email when a transfer is completed"""
        subject = f"Land Transfer Completed - {land.title}"
        
        # Email to new owner
        html_content = f"""
        <html>
        <body>
            <h2>🎉 Land Transfer Completed!</h2>
            <p>Hello {to_user.first_name},</p>
            
            <p>Congratulations! The land transfer has been completed successfully on the blockchain:</p>
            
            <div style="background-color: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>✅ Completed Transfer</h3>
                <p><strong>Land:</strong> {land.title}</p>
                <p><strong>Property ID:</strong> {land.property_id}</p>
                <p><strong>Location:</strong> {land.location}</p>
                <p><strong>Area:</strong> {land.area} sq m</p>
                <p><strong>From:</strong> {from_user.first_name} {from_user.last_name}</p>
                <p><strong>Price:</strong> ${transfer.price:,.2f}</p>
                <p><strong>Blockchain TX:</strong> {transfer.blockchain_tx_hash}</p>
            </div>
            
            <p>You are now the verified owner of this land on the blockchain! 🏆</p>
            
            <p>You can view your new property in your dashboard.</p>
            
            <p>Best regards,<br>Land Registry System</p>
        </body>
        </html>
        """
        
        self.send_email(to_user.email, subject, html_content)
        
        # Email to previous owner
        sender_subject = f"Transfer Completed - {land.title}"
        sender_html = f"""
        <html>
        <body>
            <h2>✅ Land Transfer Completed</h2>
            <p>Hello {from_user.first_name},</p>
            
            <p>Your land transfer has been completed successfully on the blockchain:</p>
            
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>📋 Completed Transfer</h3>
                <p><strong>Land:</strong> {land.title}</p>
                <p><strong>Property ID:</strong> {land.property_id}</p>
                <p><strong>To:</strong> {to_user.first_name} {to_user.last_name}</p>
                <p><strong>Price:</strong> ${transfer.price:,.2f}</p>
                <p><strong>Blockchain TX:</strong> {transfer.blockchain_tx_hash}</p>
            </div>
            
            <p>The ownership has been successfully transferred on the blockchain.</p>
            
            <p>Thank you for using our land registry system!</p>
            
            <p>Best regards,<br>Land Registry System</p>
        </body>
        </html>
        """
        
        self.send_email(from_user.email, sender_subject, sender_html)

    def send_transfer_cancelled_email(self, transfer, land, from_user, to_user):
        """Send email when a transfer is cancelled"""
        subject = f"Land Transfer Cancelled - {land.title}"
        
        # Email to both parties
        for user in [from_user, to_user]:
            html_content = f"""
            <html>
            <body>
                <h2>❌ Land Transfer Cancelled</h2>
                <p>Hello {user.first_name},</p>
                
                <p>The land transfer has been cancelled:</p>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>❌ Cancelled Transfer</h3>
                    <p><strong>Land:</strong> {land.title}</p>
                    <p><strong>Property ID:</strong> {land.property_id}</p>
                    <p><strong>From:</strong> {from_user.first_name} {from_user.last_name}</p>
                    <p><strong>To:</strong> {to_user.first_name} {to_user.last_name}</p>
                    <p><strong>Price:</strong> ${transfer.price:,.2f}</p>
                    <p><strong>Status:</strong> Cancelled</p>
                </div>
                
                <p>The transfer has been cancelled and no blockchain transaction was executed.</p>
                
                <p>If you have any questions, please contact support.</p>
                
                <p>Best regards,<br>Land Registry System</p>
            </body>
            </html>
            """
            
            self.send_email(user.email, subject, html_content)

# Global instance
email_service = EmailService()