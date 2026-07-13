import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Serviço de envio de emails.
    
    Suporta múltiplos provedores:
    - SendGrid (recomendado para produção)
    - SMTP (Gmail, Outlook, etc.)
    - Console (desenvolvimento)
    """
    
    def __init__(self):
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self):
        """Inicializa o provedor de email baseado nas configurações"""
        
        # Tenta SendGrid primeiro (produção)
        if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
            try:
                import sendgrid
                self.sendgrid_client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("Email service initialized with SendGrid")
                return "sendgrid"
            except ImportError:
                logger.warning("SendGrid library not installed. Install with: pip install sendgrid")
        
        # Fallback para SMTP
        if hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST:
            logger.info("Email service initialized with SMTP")
            return "smtp"
        
        # Fallback para console (desenvolvimento)
        logger.warning("No email provider configured. Emails will be printed to console.")
        return "console"
    
    async def send_password_reset(self, to_email: str, reset_link: str, user_name: str) -> bool:
        """Envia email de reset de senha"""
        subject = "Redefina sua senha - Quintou"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4F46E5; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Redefinição de Senha</h2>
                <p>Olá, {user_name}!</p>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta Quintou.</p>
                <p>Clique no botão abaixo para criar uma nova senha:</p>
                <a href="{reset_link}" class="button">Redefinir Senha</a>
                <p>Ou copie e cole este link no seu navegador:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p><strong>Este link expira em 1 hora.</strong></p>
                <p>Se você não solicitou esta redefinição, ignore este email.</p>
                <div class="footer">
                    <p>Equipe Quintou<br>
                    Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Olá, {user_name}!
        
        Recebemos uma solicitação para redefinir a senha da sua conta Quintou.
        
        Clique no link abaixo para criar uma nova senha:
        {reset_link}
        
        Este link expira em 1 hora.
        
        Se você não solicitou esta redefinição, ignore este email.
        
        Equipe Quintou
        """
        
        return await self._send_email(to_email, subject, html_content, text_content)
    
    async def send_booking_confirmation(
        self, 
        to_email: str, 
        user_name: str, 
        space_title: str, 
        booking_date: str, 
        total_price: float
    ) -> bool:
        """Envia email de confirmação de reserva"""
        subject = f"Reserva Confirmada - {space_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .booking-details {{ 
                    background-color: #f5f5f5; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎉 Reserva Confirmada!</h2>
                <p>Olá, {user_name}!</p>
                <p>Sua reserva foi confirmada com sucesso!</p>
                <div class="booking-details">
                    <h3>{space_title}</h3>
                    <p><strong>Data:</strong> {booking_date}</p>
                    <p><strong>Valor Total:</strong> R$ {total_price:.2f}</p>
                </div>
                <p>Você pode visualizar todos os detalhes da sua reserva no aplicativo Quintou.</p>
                <div class="footer">
                    <p>Equipe Quintou<br>
                    Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Olá, {user_name}!
        
        Sua reserva foi confirmada com sucesso!
        
        Espaço: {space_title}
        Data: {booking_date}
        Valor Total: R$ {total_price:.2f}
        
        Você pode visualizar todos os detalhes da sua reserva no aplicativo Quintou.
        
        Equipe Quintou
        """
        
        return await self._send_email(to_email, subject, html_content, text_content)
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """Envia email usando o provedor configurado"""
        
        try:
            if self.provider == "sendgrid":
                return await self._send_via_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == "smtp":
                return await self._send_via_smtp(to_email, subject, html_content, text_content)
            else:  # console
                return await self._send_via_console(to_email, subject, html_content, text_content)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def _send_via_sendgrid(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """Envia email via SendGrid"""
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        from_email = Email(settings.EMAIL_FROM, "Quintou")
        to = To(to_email)
        content = Content("text/html", html_content)
        
        mail = Mail(from_email, to, subject, content)
        mail.add_content(Content("text/plain", text_content))
        
        response = self.sendgrid_client.send(mail)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully to {to_email} via SendGrid")
            return True
        else:
            logger.error(f"SendGrid returned status {response.status_code}")
            return False
    
    async def _send_via_smtp(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """Envia email via SMTP"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = to_email
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email} via SMTP")
        return True
    
    async def _send_via_console(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """Imprime email no console (desenvolvimento)"""
        print("\n" + "="*80)
        print("📧 EMAIL (CONSOLE MODE)")
        print("="*80)
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-"*80)
        print(text_content)
        print("="*80 + "\n")
        
        logger.info(f"Email printed to console for {to_email}")
        return True
