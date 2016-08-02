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
pip uninstall wit linebot
pip install https://github.com/eternnoir/pywit/archive/master.zip https://github.com/tp6vup54/line-bot-sdk-python/archive/master.zip
```

### Configuration

Coscup line bot will use these env. Please make sure you setup these value:

```
CHANNEL_MID = 'Your line bot's channel mid'
CHANNEL_ID = 'Your line bot's channel id'
CHANNEL_SECRET = 'Your line bot's channel secret'
CHANNEL_TOKEN = 'Your line bot's channel token if you got a business connection bot'
BOT_TYPE = 'TRIAL' or 'BUSINESS' depends on your bot type, usually be 'TRIAL'
WIT_ZHTW_TOKEN = 'Your wit.ai app token'
SHEET_CREDENTIAL_PATH = 'Your Google app credential path'
SHEET_NAME = 'Your Google spreadsheet name'
ADMIN_ID = 'Id to login backend'
ADMIN_PWD = 'Pwd to login backend'
DEBUG = '1' # If DEBUG env is '1' will set logger's level to debug else INFO.
```

### Run

```
python server.py
```