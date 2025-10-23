# Lotografia Backend

## Feature list
- [ ] user account functionality 
- [ ] user-defined projects with files on persistent storage
- [ ] sending large files to the user personal storage
- [ ] ability to view sent files in some editor (e.g. Portree)
- [ ] basic processing workflow allowing for creation of measurable dense point cloud with interchangable processing backend (some kind of interface between)





## Description
Backend service for Lotografia application built with FastAPI and NiceGUI.

## Requirements
- Python 3.8+


## Installation
1. Clone the repository
```bash
git clone https://github.com/yourusername/lotografia-back.git
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
Create `.venv` file in the root directory and add necessary environment variables.

## Running the application
```bash
uvicorn main:app --reload
```

For NiceGUI interface:
```bash
python main.py
```

## API Documentation
API documentation is automatically generated and available at `/docs` or `/redoc` after starting the server.

## Contributing
Read CONTRIBUTING.md for detailed information about contribution guidelines and change submission process.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

