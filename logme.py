#!/usr/bin/env python

"""logme: Simplest diary program"""

__author__ = "Mirat Can Bayrak"
__copyright__ = "Copyright 2016, Planet Earth"


from datetime import datetime
from googleapiclient.http import MediaIoBaseUpload
from io import StringIO
import pickle
from os import mkdir
from os.path import expanduser, join, exists
import argparse
import subprocess
from tempfile import NamedTemporaryFile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


CONFIG_DIR = expanduser('~/.config/logme/')

if not exists(CONFIG_DIR):
    mkdir(CONFIG_DIR)

def get_drive_service():
    """
    Returns google drive service with valid credentials.
    """
    creds = None
    token_path = join(CONFIG_DIR, 'token.pickle')
    if exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            scopes = [
                'https://www.googleapis.com/auth/drive.metadata.readonly',
                'https://www.googleapis.com/auth/drive.file'
            ]
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def parse_args():
    """
    Parses arguments from command line.
    """
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
    """
    Opens vim editor and returns what's written in it.
    """
    with NamedTemporaryFile('r') as tfile:
        subprocess.call(["vim", tfile.name])
        with open(tfile.name, 'r') as sfile:
            story = sfile.read()
    return story


def get_story(cmd_line_args):
    """
    Returns story from editor or command line.
    """
    if cmd_line_args.use_editor:
        return get_story_from_editor()
    return cmd_line_args.story

DAY_FILE_PATTERN = '%m-%d.txt'
DAY_TITLE_PATTERN = '%Y/%m/%d/ - %A\n'

DRIVE = get_drive_service()
NOW = datetime.now()
REMOTE_APP_DIR = 'MyLogs'

FILE_NAME = datetime.strftime(NOW, DAY_FILE_PATTERN)

def get_or_create_remote_dir():
    """
    Tries to get or create remote directory.
    """
    try:
        return DRIVE.files().list(
            pageSize=1, fields="files(id, name)",
            q="mimeType='application/vnd.google-apps.folder' and " \
            f"name='{REMOTE_APP_DIR}' and trashed=false"
        ).execute()['files'][0]['id']
    except (KeyError, IndexError):
        file_metadata = {
            'name': REMOTE_APP_DIR,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        return DRIVE.files().create(
            body=file_metadata, fields='id').execute()['id']

def get_or_create_remote_log_file(remote_dir_id, content):
    try:
        return False, DRIVE.files().list(
            pageSize=1, fields="files(id, name)",
            q=f"mimeType='text/plain' and '{remote_dir_id}' in parents and " \
              f"name='{FILE_NAME}' and trashed=false"
        ).execute()['files'][0]['id']
    except IndexError:
        media = MediaIoBaseUpload(
            StringIO(content), mimetype='plain/text',
        )

        return True, DRIVE.files().create(
            body={'name': FILE_NAME, 'mimetype': 'text/plain'},
            media_body=media,
            fields='id'
        ).execute()

cmd_line_args = parse_args()
story = get_story(cmd_line_args)
remote_dir_id = get_or_create_remote_dir()
print(get_or_create_remote_log_file(remote_dir_id, story))
"""
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
"""
