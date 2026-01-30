import configparser
import logging
import os
import sys
from collections import defaultdict

# Add src to path if needed, though structure implies checking from root
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pdf_checker import scan_directory
from src.db_client import DBClient
from src.email_sender import EmailSender

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_check.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    logging.info("Starting Auto Check Albaran...")
    
    # 1. Load Config
    config = configparser.ConfigParser()
    config_path = 'config.ini'
    if not os.path.exists(config_path):
        logging.error("config.ini not found!")
        res = config.read(config_path)
        if not res:
             logging.error("Failed to read config.ini")
             return

    config.read(config_path)

    try:
        pdf_path = config['GENERAL']['carpeta_pdf']
        days_back = int(config['GENERAL']['dias_atras'])
        fecha_desde = config['GENERAL'].get('fechadesde', None)
        
        dsn_name = config['DATABASE']['dsn_name']
        db_user = config['DATABASE']['user']
        db_password = config['DATABASE']['password']
        
        smtp_server = config['EMAIL']['servidor_smtp']
        smtp_port = int(config['EMAIL']['puerto_smtp'])
        sender_email = config['EMAIL']['remitente']
        use_tls = config['EMAIL'].getboolean('usar_tls')
        debug_email = config['EMAIL'].get('debug_email', None)
        central_recipients = config['EMAIL']['destinatarios_central'].split(',')
        if debug_email:
             logging.info(f"DEBUG MODE ACTIVE: All emails (Central + Centers) will be sent to {debug_email}")
             central_recipients = [debug_email]
        
        # Load Center > Email, Name Mapping
        center_emails = {}
        center_names = {}
        if 'CENTROS' in config:
            for key in config['CENTROS']:
                center_emails[key] = config['CENTROS'][key]
        
        if 'NOMBRES_CENTROS' in config:
            for key in config['NOMBRES_CENTROS']:
                center_names[key] = config['NOMBRES_CENTROS'][key]
                
    except KeyError as e:
        logging.error(f"Missing configuration key: {e}")
        return

    # 2. Check PDFs
    corrupt_files = scan_directory(pdf_path, days_back, fecha_desde)
    
    if not corrupt_files:
        logging.info("No corrupt files found. Process finished.")
        return

    logging.info(f"Found {len(corrupt_files)} corrupt files.")
    
    # 4. Query DB for Details
    details = []
    try:
        db_client = DBClient(dsn_name, db_user, db_password)
        details = db_client.get_albaran_details(corrupt_files)
    except Exception as e:
        logging.error(f"Failed to query database: {e}")
        # Proceed with empty details to at least notify central about files
    
    # Identify Missing Files (Not found in DB)
    # DB keys are uppercase now (COD_BARRAS matches filename stem)
    found_ids = set()
    if details:
        for r in details:
            # Handle potential Decimal/clean types
            val = str(r.get('COD_BARRAS', r.get('cod_barras', ''))).split('.')[0] 
            found_ids.add(val)

    missing_files = [f for f in corrupt_files if f not in found_ids]
    
    if missing_files:
        logging.warning(f"Files found on disk but NOT in DB: {missing_files}")

    # 3. Notify Central
    # We pass both lists so Central knows what's going on
    email_client = EmailSender(smtp_server, smtp_port, use_tls, sender_email)
    # Append note about missing files to central report logic (requires modifying send_central_report signature or just appending here? 
    # Let's keep signature simple and just pass 'corrupt_files' but maybe we log it.
    # Ideally we'd tell Central which ones failed DB check.
    # For now, let's just stick to the original list for Central, but user knows to check logs.
    email_client.send_central_report(central_recipients, corrupt_files)

    if not details:
        logging.warning("No details found in DB for the corrupt files.")
        return

    # 5. Group by Center and Notify
    grouped_data = defaultdict(list)
    for record in details:
        # Assuming 'ALM' is the center code from DB
        # Handle Decimal values by converting to int then str to remove .0
        raw_alm = record.get('ALM', '')
        try:
             # If it's a decimal like 160.00, this makes it '160'
             center_code = str(int(float(raw_alm)))
        except (ValueError, TypeError):
             center_code = str(raw_alm).strip()
             
        grouped_data[center_code].append(record)

    for center_code, records in grouped_data.items():
        # Look for email in config mapping
        recipient = center_emails.get(center_code)
        
        if not recipient:
             # Try removing leading zeros (just in case config has '60')
             recipient = center_emails.get(center_code.lstrip('0'))
        
        if not recipient:
             # Try adding leading zeros (DB has '60', config has '060')
             recipient = center_emails.get(center_code.zfill(3))

        # Get Center Name
        # Try all variants: exact, stripped, filled
        center_name = center_names.get(center_code)
        if not center_name:
             center_name = center_names.get(center_code.lstrip('0'))
        if not center_name:
             center_name = center_names.get(center_code.zfill(3))
             
        if not center_name:
             center_name = f"CENTRO {center_code}"
             
        if recipient:
            if debug_email:
                 recipient = debug_email
            
            logging.info(f"Sending report to {center_name} ({recipient}) with {len(records)} items.")
            email_client.send_center_report(recipient, records, center_name)
        else:
            logging.warning(f"No email configured for Center {center_code}. Skipping notification for this center.")

    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()
