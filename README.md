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
`sudo apt install ghostscript`
`sudo apt install tesseract-ocr poppler-utils`
`sudo apt install tesseract-ocr-ind`
`pip install -r requirements.txt`

## RUNNING APP
`streamlit run app.py --server.address 0.0.0.0 --server.port 8502`

## OTHERS
`py --list // for check version python`

`pip cache purge`


## USING DOCKER
`docker build -t pdf-tools .`

## RUNNING AFTER BUILD CONTAINER
`docker run -d --name pdf-tools -p 8502:8502 pdf-tools`

## USING DOCKER COMPOSE


