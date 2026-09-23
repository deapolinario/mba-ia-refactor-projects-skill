import smtplib
from config import Config
from utils.helpers import utcnow


def _mask_email(email):
    """v2.2 - mascarar email em logs (fix Logs Sensíveis/PII)."""
    parts = email.split('@')
    if len(parts) != 2:
        return '***'
    return f"{parts[0][:2]}***@{parts[1]}"


class NotificationService:
    """
    NOTA (v2.2): esta classe não é instanciada em nenhum lugar do código
    atual (dead code, confirmado via auditoria). As credenciais hardcoded
    foram corrigidas mesmo assim, pois representavam um achado CRITICAL
    independente do uso. Ativar o envio de notificações reais está fora
    do escopo desta refatoração.
    """

    def __init__(self):
        self.notifications = []
        self.email_host = Config.EMAIL_HOST
        self.email_port = Config.EMAIL_PORT
        self.email_user = Config.EMAIL_USER
        self.email_password = Config.EMAIL_PASSWORD

    def send_email(self, to, subject, body):
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            print(f"Email enviado para {_mask_email(to)}")
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {str(e)}")
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow()
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
