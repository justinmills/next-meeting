Zoom Meeting Joiner
===

Script to join the Zoom meeting you're supposed to be in.

This works by scraping your Google Calendar looking for meeting with zoom links and
finding the one currently going on, or if one is about to start in a few minutes,
picking that one.

## How to setup

**Note**: this has only been tested on the mac.

* Setup [pyenv](https://github.com/pyenv/pyenv)
* Setup [pipenv](https://github.com/pypa/pipenv)
* Optionally setup [direnv](https://direnv.net/)
* Activate (if requred) pyenv/pipenv for this directory
* Install all requirements:
  ```shell
  pipenv install --dev --ignore-pipfile
  ```
* Do step 1 of the [python quickstart
  guide](https://developers.google.com/calendar/quickstart/python) for Google Calendar.
  Save this file as `credentials.json`. NOTE: This file is marked as gitignore to
  prevent you from accidentally checking in secret values.
* Run it!
  ```shell
  python ./zoom.py
  ```

The first time you will be prompted to login and authenticate against the Google
Calendar API. Your credentials will be stored locally in `token.pickle` (again ignored
by git).

Subsequent times, it'll print out the next few events and then print out the event it's
about to join you to. It will always try to join you to a zoom meeting even if the next
meeting is some time out from now.
