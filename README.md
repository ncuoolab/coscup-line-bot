# coscup-line-bot

## How to deploy

### Requirements

* python 3.5

### Install Dependency

```
pip install -r /path/to/requirements.txt
```

* Install custom wit
```
pip uninstall wit
pip install https://github.com/eternnoir/pywit/archive/master.zip
```

### Configuration

Coscup line bot will use these env. Please make sure you setup these value:

```
CHANNEL_MID = 'Your line bot's channel mid'
CHANNEL_ID = 'Your line bot's channel id'
CHANNEL_SECRET = 'Your line bot's channel secret'
WIT_ZHTW_TOKEN = 'Your wit.ai app token'
SHEET_CREDENTIAL_PATH = 'Your Google app credential path'
SHEET_NAME = 'Your Google spreadsheet name'
DEBUG = '1' # If DEBUG env is '1' will set logger's level to debug else INFO.
```

### Run

```
python server.py
```