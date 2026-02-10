# PDF-TOOLS

## BUILD VENV
### WINDOWS
`python -m venv venv-pdf-tools`
### LINUX
`python3 -m venv venv-pdf-tools`

## ACTIVE VENV
### WINDOWS
`.\venv-pdf-tools\Scripts\activate`
### LINUX
`source venv-pdf-tools/bin/activate`

## DEACTIVE VENV
`deactivate`

## INSTALL DEPENDENCIES
`pip install -r requirements.txt`
`sudo apt install ghostscript`

## RUNNING APP
`streamlit run app.py --server.address 0.0.0.0 --server.port 8502`

## OTHERS
`py --list // for check version python`

`pip cache purge`