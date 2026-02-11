#!/usr/bin/env python3
import zipfile
import xml.etree.ElementTree as ET
import datetime
import sys
import os

def excel_date_to_date(serial):
    """Convert Excel serial date to datetime.date"""
    # Excel base date is 1899-12-30 (or 1900-01-01 with bug)
    if serial == '':
        return None
    try:
        # Convert to int
        serial = float(serial)
        # Excel for Mac uses 1904 date system? Assuming 1900
        if serial < 60:
            # Adjust for Excel's bug where 1900 is incorrectly considered a leap year
            serial += 1
        base = datetime.datetime(1899, 12, 30)
        delta = datetime.timedelta(days=serial)
        return base + delta
    except:
        return None

def read_esigelec_xlsx(filename):
    students = []
    try:
        with zipfile.ZipFile(filename, 'r') as z:
            # Get shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                with z.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    for si in root.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        t = si.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                        if t is not None:
                            text = t.text
                            if text is not None:
                                shared_strings.append(text.strip())
                            else:
                                shared_strings.append('')
            # Get first sheet
            sheet_files = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]
            if not sheet_files:
                print(f"No sheet found in {filename}")
                return students
            
            with z.open(sheet_files[0]) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                
                # Assume first row is header
                if len(rows) < 1:
                    return students
                
                # Parse header
                header = []
                cells = rows[0].findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                for cell in cells:
                    if cell.get('t') == 's':
                        idx_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if idx_elem is not None:
                            idx = int(idx_elem.text)
                            val = shared_strings[idx] if idx < len(shared_strings) else ''
                        else:
                            val = ''
                    else:
                        v = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        val = v.text if v is not None else ''
                    header.append(val)
                
                print(f"Header: {header}")
                
                # Find column indices
                nom_idx = -1
                prenom_idx = -1
                email_idx = -1
                dob_idx = -1
                for i, h in enumerate(header):
                    h_lower = str(h).lower()
                    if 'nom' in h_lower and 'prénom' not in h_lower:
                        nom_idx = i
                    elif 'prénom' in h_lower:
                        prenom_idx = i
                    elif '邮箱' in h or 'mail' in h_lower:
                        email_idx = i
                    elif 'date de naissance' in h_lower:
                        dob_idx = i
                
                print(f"Indices: nom={nom_idx}, prenom={prenom_idx}, email={email_idx}, dob={dob_idx}")
                
                # Process data rows
                for row in rows[1:]:  # skip header
                    cells = row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                    row_vals = [''] * len(header)
                    
                    for i, cell in enumerate(cells):
                        col_idx = i
                        if col_idx >= len(header):
                            continue
                        if cell.get('t') == 's':
                            idx_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if idx_elem is not None:
                                try:
                                    idx = int(idx_elem.text)
                                    val = shared_strings[idx] if idx < len(shared_strings) else ''
                                except:
                                    val = ''
                            else:
                                val = ''
                        else:
                            v = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            val = v.text if v is not None else ''
                        row_vals[col_idx] = val
                    
                    # Extract values
                    nom = row_vals[nom_idx] if nom_idx != -1 and nom_idx < len(row_vals) else ''
                    prenom = row_vals[prenom_idx] if prenom_idx != -1 and prenom_idx < len(row_vals) else ''
                    email = row_vals[email_idx] if email_idx != -1 and email_idx < len(row_vals) else ''
                    dob_str = row_vals[dob_idx] if dob_idx != -1 and dob_idx < len(row_vals) else ''
                    
                    # Create full name
                    if nom or prenom:
                        full_name = f"{nom} {prenom}".strip()
                    else:
                        # Try to find name in other columns
                        full_name = ''
                    
                    # Calculate age from dob
                    age = ''
                    if dob_str:
                        dob_date = excel_date_to_date(dob_str)
                        if dob_date:
                            today = datetime.date.today()
                            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                            age = str(age)
                    
                    # Only add if we have at least a name or email
                    if full_name or email:
                        students.append({
                            'school': 'ESIGELEC',
                            'full_name': full_name,
                            'age': age,
                            'email': email,
                            'raw_data': row_vals
                        })
                        
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    return students

if __name__ == '__main__':
    filepath = '/Users/yangyan/Downloads/同步空间/HelenOA/Esigelec/liste d\'étudiant 2023.xlsx'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    students = read_esigelec_xlsx(filepath)
    print(f"Found {len(students)} students")
    
    # Print first few
    for i, s in enumerate(students[:10]):
        print(f"{i+1}: {s}")
    
    # Write to CSV
    import csv
    output_path = '/Users/yangyan/.openclaw/workspace/esigelec_students.csv'
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['school', 'full_name', 'age', 'email', 'notes'])
        writer.writeheader()
        for s in students:
            writer.writerow({
                'school': s['school'],
                'full_name': s['full_name'],
                'age': s['age'],
                'email': s['email'],
                'notes': ''
            })
    
    print(f"Written to {output_path}")