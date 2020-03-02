import os
import smtplib
from email.MIMEText import MIMEText

def send_mail(subject, message_text, recipient=None, sender='rtools.notifier'):
    """
    Send an e-mail. Works from within the theochem network.

    Parameters
    ----------
    subject : str
        The mail subject

    message_text : str
        The main body text

    recipient : str (default=None)
        Specify the recipient email adress. Defaults to
        <user>@theo.chemie.tu-muenchen.de.

    sender : str (default='rtools.notifier')
        The sender address for the mail.
    """
    if recipient is None:
        recipient = "{}".format(os.environ["USER"])
    server = smtplib.SMTP('mail', 25)
    msg = MIMEText(message_text)
    msg['Content-Type'] = "text/plain; charset=utf-8"
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    server.sendmail(sender, recipient, msg.as_string())
