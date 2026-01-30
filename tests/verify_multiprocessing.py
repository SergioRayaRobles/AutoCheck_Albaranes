import os
import sys
import shutil
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pdf_checker import scan_directory

def create_dummy_pdf(path, is_valid=True):
    if is_valid:
        # Minimal valid PDF
        content = (b"%PDF-1.0\n"
                   b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
                   b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n"
                   b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000111 00000 n\n"
                   b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF")
    else:
        content = b"This is not a PDF, just random text."
    
    with open(path, 'wb') as f:
        f.write(content)

def main():
    test_dir = os.path.join(os.path.dirname(__file__), "temp_test_pdfs")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    print(f"Created temp directory: {test_dir}")

    try:
        # Create 5 valid PDFs
        for i in range(5):
            create_dummy_pdf(os.path.join(test_dir, f"valid_{i}.pdf"), is_valid=True)
        
        # Create 5 corrupt PDFs
        corrupt_names = []
        for i in range(5):
            name = f"999000{i}-Rev(1.00).pdf"
            path = os.path.join(test_dir, name)
            create_dummy_pdf(path, is_valid=False)
            corrupt_names.append(f"999000{i}")

        print("Created 5 valid and 5 corrupt PDFs.")
        
        # Run scan
        print("Running scan_directory...")
        start_time = time.time()
        # Scan with 1 day back (files created just now)
        found_corrupt = scan_directory(test_dir, days_back=1)
        end_time = time.time()
        
        print(f"Scan finished in {end_time - start_time:.4f} seconds.")
        print(f"Found corrupt files: {found_corrupt}")
        
        # Verify
        found_set = set(found_corrupt)
        expected_set = set(corrupt_names)
        
        if found_set == expected_set:
            print("SUCCESS: All corrupt files identified correctly.")
        else:
            print(f"FAILURE: Expected {expected_set}, but got {found_set}")
            # Ensure failure is propagated
            sys.exit(1)

    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("Cleaned up temp directory.")

if __name__ == "__main__":
    main()
