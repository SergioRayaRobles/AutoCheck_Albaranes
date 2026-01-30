import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Dict, Any

class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, use_tls: bool, sender_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.sender_email = sender_email

    def _send_email(self, to_emails: List[str], subject: str, body_text: str, body_html: str = None):
        if not to_emails:
            logging.warning("No recipients provided for email.")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(to_emails)

        part1 = MIMEText(body_text, "plain")
        msg.attach(part1)
        
        if body_html:
            part2 = MIMEText(body_html, "html")
            msg.attach(part2)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                # If authentication is needed, it would go here. 
                # Config didn't specify auth, assuming internal relay based on config.ini example.
                server.sendmail(self.sender_email, to_emails, msg.as_string())
            logging.info(f"Email sent to {to_emails}: {subject}")
        except Exception as e:
            logging.error(f"Failed to send email to {to_emails}: {e}")

    def send_central_report(self, recipients: List[str], corrupt_files: List[str]):
        """
        Sends the list of corrupted files to Central Systems.
        """
        subject = f"Informe de Albaranes PDF Corruptos - {len(corrupt_files)} detectados"
        
        body_text = "Se han detectado los siguientes archivos PDF corruptos o ilegibles:\n\n"
        for f in corrupt_files:
            body_text += f"- {f}\n"
            
        body_text += "\nPor favor, revise estos archivos."
        
        self._send_email(recipients, subject, body_text)

    def send_center_report(self, recipient: str, check_data: List[Dict[str, Any]], center_name: str = ""):
        """
        Sends the report to a specific center with the details of their albaranes.
        """
        if not check_data:
            return

        # Subject as requested: "Listado de Albaranes Dañados - {CENTER_NAME}"
        subject = f"Listado de Albaranes Dañados - {center_name}" if center_name else "Listado de Albaranes Dañados"

        # Headers based on user request example
        # Cod.Barras  ALM     Nº int  Fecha     ****    Prov  Div Proveedor                           ** Albaran  Flag
        
        header = f"{'Cod.Barras':<12} {'ALM':<4} {'Nº int':<8} {'Fecha':<9} {'****':<6} {'Prov':<6} {'Div':<4} {'Proveedor':<40} {'**':<3} {'Albaran':<9} {'Flag':<4}"
        separator = "-" * len(header)
        
        rows = []
        for row in check_data:
            # Safely get values and format
            line = f"{str(row.get('COD_BARRAS', '')):<12} {str(row.get('ALM', '')):<4} {str(row.get('NUM_INT', '')):<8} " \
                   f"{str(row.get('FECHA', '')):<9} {str(row.get('CUENTA_MAYOR', '')):<6} {str(row.get('PROV_CODIGO', '')):<6} " \
                   f"{str(row.get('DIVISION', '')):<4} {str(row.get('PROVEEDOR_DESC', ''))[:39]:<40} {str(row.get('SERIE', '')):<3} " \
                   f"{str(row.get('ALBARAN', '')):<9} {str(row.get('FLAG', '')):<4}"
            rows.append(line)

        body_text = f"{header}\n{separator}\n" + "\n".join(rows)
        body_text += "\n\nPor favor, vuelva a escanear estos documentos."

        # Optional HTML version could be added here for better rendering in modern clients
        html_rows = ""
        for row in check_data:
             html_rows += f"<tr><td>{row.get('COD_BARRAS', '')}</td><td>{row.get('ALM', '')}</td><td>{row.get('NUM_INT', '')}</td>" \
                          f"<td>{row.get('FECHA', '')}</td><td>{row.get('CUENTA_MAYOR', '')}</td><td>{row.get('PROV_CODIGO', '')}</td>" \
                          f"<td>{row.get('DIVISION', '')}</td><td>{row.get('PROVEEDOR_DESC', '')}</td><td>{row.get('SERIE', '')}</td>" \
                          f"<td>{row.get('ALBARAN', '')}</td><td>{row.get('FLAG', '')}</td></tr>"

        body_html = f"""
        <html>
        <head>
        <style>
        table {{ border-collapse: collapse; width: 100%; font-family: monospace; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        </style>
        </head>
        <body>
        <h3>Listado de Albaranes Dañados</h3>
        <table>
        <tr>
            <th>Cod.Barras</th><th>ALM</th><th>Nº int</th><th>Fecha</th><th>****</th><th>Prov</th><th>Div</th><th>Proveedor</th><th>**</th><th>Albaran</th><th>Flag</th>
        </tr>
        {html_rows}
        </table>
        <p>Por favor, vuelva a escanear estos documentos.</p>
        </body>
        </html>
        """

        self._send_email([recipient], subject, body_text, body_html)
