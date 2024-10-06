# Free Speech to Text using Python

I am trying to publish it online through Heroku
You can clone this respiratory and run it locally

## Installation
- You will need Python to run
  
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install libraries.

```bash
pip install SpeechRecognition
pip install pydub
pip install flask
```

## Usage
1. Create virtual environment
   ```bash
   cd <The directory of where you place this respiratory in>
   python -m venv venv
```
2. Activate the virtual environment
- Windows:

```bash
   venv\Scripts\activate
```

- MacOS/Linus:
   ```bash
   source venv/bin/activate
```
3. Install all libraries above using pip inside the virtual environment
4. Run the application
   ```bash
   python app.py
```
5. Go to your browser and type in
      ```bash
   http://127.0.0.1:5000/
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
