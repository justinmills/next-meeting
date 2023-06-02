Meeting Joiner
===

Script to join the online meeting you're supposed to be in.

This works by scraping your Google Calendar looking for meetings with video
links and finding the one that is currently happening, or is about to start in a
few minutes. It then launches that meeting.

Right now there is only support for meetings with zoom links.


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
* Do prerequisites of the [python quickstart
  guide](https://developers.google.com/calendar/quickstart/python) for Google Calendar.
  Particularly the part about creating [credentials]
  (https://developers.google.com/workspace/guides/create-credentials) - I created an
  [API Key](https://console.cloud.google.com/apis/credentials?project=autolaunchzoom-1601670988869).
  Save this file as `credentials.json`. NOTE: This file is marked as gitignore to
  prevent you from accidentally checking in secret values.

  As an alternative, you can take the `credentials.json` file from an existing machine (say your personal computer) where you created the Google app to another machine (say your work computer). In order for this to work, you need to add the other user's email to the list of test users. To do this, go to the [API's and Services \ OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) page and a) make sure the Publishing status is "Testing" and b) add the other user's email address to the list of Test users. Once this is done they should be able to continue on.
  
* Run it!
  ```shell
  pipenv run list
  ```

The first time you will be prompted to login and authenticate against the Google
Calendar API. Your credentials will be stored locally in `token.pickle` (again ignored
by git).

Subsequent times, it'll print out the next few events and then print out the event it's
about to join you to. It will always try to join you to a zoom meeting even if the next
meeting is some time out from now.
