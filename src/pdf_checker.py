import os
import datetime
from pypdf import PdfReader
import logging
from multiprocessing import Pool, cpu_count

def check_file_worker(args):
    """
    Worker function to check a single file.
    Args:
        args: Tuple containing (file_path, file_name, file_mtime)
    Returns:
        The filename stem if corrupt, None otherwise.
    """
    file_path, file_name, _ = args
    
    if not is_valid_pdf(file_path):
        logging.warning(f"Corrupt PDF found: {file_name}")
        
        filename_stem = os.path.splitext(file_name)[0]
        
        # Remove -Rev...
        if "-Rev" in filename_stem:
            filename_stem = filename_stem.split("-Rev")[0]
            
        clean_number = filename_stem.split("-")[0] # Splits at -Rev
        clean_number = clean_number.split("_")[0] # Splits at _002
        
        return clean_number
    return None

def scan_directory(path: str, days_back: int, fecha_desde_str: str = None) -> list[str]:
    """
    Scans the directory for PDF files modified within the last `days_back` days.
    Checks if they are valid PDFs using multiprocessing.
    Returns a list of filename stems (no extension) that are corrupt.
    """
    logging.info(f"Scanning directory: {path} for files modified in last {days_back} days.")
    
    if not os.path.exists(path):
        logging.error(f"Directory not found: {path}")
        return []

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    
    # Overwrite cutoff if strict date provided
    if fecha_desde_str:
        try:
            cutoff_date = datetime.datetime.strptime(fecha_desde_str, "%d/%m/%Y")
        except ValueError:
            logging.warning(f"Invalid date format for fechadesde: {fecha_desde_str}. Using days check.")

    logging.info(f"Cutoff date: {cutoff_date}")

    files_to_check = []
    
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name.lower().endswith(".pdf") and entry.is_file():
                    # Check modification time
                    mtime_ts = entry.stat().st_mtime
                    mtime_dt = datetime.datetime.fromtimestamp(mtime_ts)
                    
                    if mtime_dt >= cutoff_date:
                        files_to_check.append((entry.path, entry.name, mtime_ts))
                        
    except Exception as e:
        logging.error(f"Error scanning directory: {e}")
        return []

    count_checked = len(files_to_check)
    logging.info(f"Found {count_checked} files to check. Starting multiprocessing pool...")

    corrupt_files = []
    
    # Use multiprocessing
    if files_to_check:
        
        # Use available CPUs or default to 8 if not detectable (though cpu_count usually works)
        num_processes = cpu_count()
        # logging.info(f"Using {num_processes} processes.") 
        
        with Pool(processes=num_processes) as pool:
            results = pool.map(check_file_worker, files_to_check)
            
        # Filter out None results
        corrupt_files = [res for res in results if res is not None]

    logging.info(f"Scan complete. Checked {count_checked} files. Found {len(corrupt_files)} corrupt.")
    return corrupt_files

def is_valid_pdf(file_path: str) -> bool:
    """
    Returns True if the PDF is valid, False otherwise.
    """
    try:
        # pypdf validation
        reader = PdfReader(file_path)
        # Try to read pages to ensure it's not actually broken content
        if len(reader.pages) > 0:
             # Basic check: try accessing the first page
            _ = reader.pages[0]
            return True
        return False
    except Exception:
        return False
