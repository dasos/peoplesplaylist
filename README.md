
# peoplesplaylist

The Peoples Playlist is a Python3 web app that controls a Spotify player. It is used at a party, to give the people there a little bit of control over the playlist. In short, it lets those people, at specific points, decide if the next track is to be played or skipped.

## What does it look like?

### Desktop view

<img src="desktop.png" width="600"/>

### Mobile view

<img src="mobile.png" width="300"/>

## How does it work?

It used flask-socketio to allow for instant updates between server and client. At this point, websockets aren't actually used, but it may in the future.

## Get it running

### Spotify

You will need to register an app at [the Spotify developers site](https://developer.spotify.com/) Get the client id and client secret, specify a call back (which will be something like https://<ip>/spotify) and pass them as environment variables.

### Docker

The easiest way is to take the Docker Compose file, modify it to include your Spotify config, and then execute it. 

    docker-compose -f docker-compose.yml up

It will then be available at port 5000 by default. If you are running it on your local machine, it is http://localhost:5000 Note it will run across the network.

### Log in to Spotify

Once you can connect to the front-end, navigate to https://<ip>/spotify in your browser. Then log in. Then play something, and the standard front end should show it!

## Development, or local install

### Dependancies
Python 3, plus the modules in requirements.txt

### How to run a development server
Assumption is a Ubuntu machine.

Install the dependancies:

    pip3 install -r requirements.txt

Set the variables:

    export SPOTIPY_CLIENT_ID="<client id>"
	export SPOTIPY_CLIENT_SECRET="<client secret>"
    export SPOTIPY_REDIRECT_URI=http://<ip>:5000/spotify/'
    export FLASK_DEBUG=true

Execute:

    python3 web_app/app.py

### Code standards

Auto-formatting is achieved using Black:

    python3 -m black .

And making sure you follow PEP 8 is done with Flake8, with the adjustments that Black recommend.

    python3 -m flake8 web_app