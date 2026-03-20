# Velocity Pipeline Setup

## M: Drive Structure

```
M:\ARS\
  00_Formatting\
    run.py
    00-Scripts\
    01-Data-Ready for Formatting\
    02-Data-Ready for Analysis\
  01_Analysis\
    run.py
    00-Scripts\
  02_Presentations\
  03_Config\
    clients_config.json
  04_Logs\
  05_UI\
    app.py
    index.html
```

## First-Time Setup

### 1. Install Python packages

```
pip install loguru rich pydantic pydantic-settings openpyxl python-pptx matplotlib numpy pandas fastapi uvicorn
```

### 2. Clone the repo into 00-Scripts

```
M:
cd \ARS\00_Formatting\00-Scripts
git clone https://github.com/JG-CSI-Velocity/ars-production-pipeline.git .
```

### 3. Copy the UI to 05_UI

```
xcopy M:\ARS\00_Formatting\00-Scripts\ui M:\ARS\05_UI\ /E /I
```

### 4. Copy analysis scripts to 01_Analysis

```
xcopy M:\ARS\00_Formatting\00-Scripts\01_Analysis M:\ARS\01_Analysis\ /E /I
```

## Running

### Step 1: Format ODD files

```
cd M:\ARS\00_Formatting\00-Scripts\00_Formatting
python run.py --month 2026.03 --csm James --client 1200
```

### Step 2: Run analysis + generate PPTX

```
cd M:\ARS\01_Analysis
python run.py --month 2026.03 --csm James --client 1200
```

### Launch the UI

```
cd M:\ARS\05_UI
python app.py
```

Then open http://localhost:8000

### Run all clients (batch)

```
cd M:\ARS\00_Formatting\00-Scripts\00_Formatting
python run.py --month 2026.03 --csm James
```

## Updating

```
cd M:\ARS\00_Formatting\00-Scripts
git pull
```

Then re-copy to 01_Analysis and 05_UI if needed.
