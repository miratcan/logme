#!/usr/bin/env python

"""logme: Simplest diary program"""

__author__ = "Mirat Can Bayrak"
__copyright__ = "Copyright 2016, Planet Earth"


from datetime import datetime

import pickle
from os import mkdir
from os.path import expanduser, join, exists
import argparse
import subprocess
from tempfile import NamedTemporaryFile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
CONFIG_DIR = expanduser('~/.config/logme/')
TOKEN_PATH = join(CONFIG_DIR, 'token.pickle')

if not exists(CONFIG_DIR):
    mkdir(CONFIG_DIR)

def get_drive_service():
    creds = None
    if exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Diary program for your terminal.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--story', '-s', type=str, action='store',
        help='Your one line story to be saved.')
    group.add_argument(
        '--editor', '-e', dest='use_editor', action='store_true',
        help='Use editor to make multiline stories.')
    return parser.parse_args()


def get_story_from_editor():
    with NamedTemporaryFile('r') as tfile:
        subprocess.call(["vim", tfile.name])
        with open(tfile.name, 'r') as sfile:
            story = sfile.read()
    return story


args = parse_args()
if args.use_editor:
    story = get_story_from_editor()
else:
    story = args.story

DAY_FILE_PATTERN = '%m-%d.txt'
DAY_TITLE_PATTERN = '%Y/%m/%d/ - %A\n'

service = get_drive_service()
now = datetime.now()
REMOTE_APP_DIR =  'MyLogs'

file_name = datetime.strftime(now, DAY_FILE_PATTERN)


def get_or_create_remote_dir():
    try:
        root_folder = service.files().list(
            pageSize=10, fields="files(id, name)",
            q=f"mimeType='application/vnd.google-apps.folder' and " \
               "name='{REMOTE_APP_DIR}' and trashed=false"
        ).execute()['files'][0]['id']
    except (KeyError, IndexError):
        file_metadata = {
            'name': REMOTE_APP_DIR,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        root_folder = service.files().create(
            body=file_metadata, fields='id').execute()
    return root_folder

print(get_or_create_remote_dir())

if not exists(file_path):
    fp = open(file_path, 'w')
    title = datetime.strftime(now, DAY_TITLE_PATTERN)
    fp.write(title)
    fp.write('-' * (len(title) - 1) + '\n')
else:
    fp = open(file_path, 'a')
    timestamp = now.strftime("%H:%M")
    if args.use_editor:
        fp.write('%s: %s' % (timestamp, story.strip()))
    else:
        fp.write('%s: %s\n' % (timestamp, story.strip()))
fp.close()
