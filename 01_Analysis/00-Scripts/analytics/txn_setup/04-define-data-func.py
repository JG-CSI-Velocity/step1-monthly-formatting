def load_transaction_file(filepath):
    """
    Load a debit card transaction file
    """
    filepath = Path(filepath)
    
    # Skip the metadata header line, read tab-delimited data
    df = pd.read_csv(filepath, sep='\t', skiprows=1, header=None, low_memory=False)
    
    # Assign column names based on the file definition document
    df.columns = [
        'transaction_date',      # Date of Transaction (MM/DD/YYYY)
        'primary_account_num',   # Primary account number (hashed)
        'transaction_type',      # PIN, SIG, ACH, CHK
        'amount',               # Transaction amount
        'mcc_code',             # Merchant Category Code
        'merchant_name',        # Merchant name
        'terminal_location_1',  # Terminal location/address
        'terminal_location_2',  # Additional location info
        'terminal_id',          # Terminal ID
        'merchant_id',          # Merchant ID  
        'institution',          # Institution number
        'card_present',         # Y/N indicator
        'transaction_code'      # Transaction code
    ][:len(df.columns)]  # Only use as many names as there are columns
    
    # Add metadata
    df['source_file'] = filepath.name
    
    return df

# Load TXN files from the trailing 12-month window (set by 02-file-config.py)
# files_to_load = recent dated files + unparsed files (can't exclude what we can't date)
transaction_files = []
print(f"Loading {len(files_to_load)} transaction files...\n")

for file_path in sorted(files_to_load):
    df = load_transaction_file(file_path)
    transaction_files.append(df)
    print(f"  Loaded: {file_path.name} ({len(df):,} rows)")

print(f"\n{'='*50}")
print(f"Total transactions loaded: {sum(len(df) for df in transaction_files):,}")
