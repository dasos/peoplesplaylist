from flask import Blueprint, request, url_for, redirect

import logging

import spotipy


# Spotify is being authenticated and the token is stored globally, in a file
# This prevents being reauthed every time the app is started
cache_handler = spotipy.cache_handler.CacheFileHandler()

spotify = None

bp = Blueprint("spotify", __name__, url_prefix="/spotify/")

INVALID_TRACK = {"artist": "Bob Smith", "title": "Dance dance dance", "valid": False}

VOTE_TIME = 30


@bp.route("/")
def index():
    logger = logging.getLogger("peoplesplaylist.current_track")
    redirect_uri = url_for("spotify.index", _external=True)

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="user-read-currently-playing,user-modify-playback-state",
        redirect_uri=redirect_uri,
        show_dialog=True,
    )

    logging.debug("Got auth_manager")

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        logging.debug("Got access token, redirecting")
        return redirect("/")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        logging.debug("Not logged in")
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()

        return f'<h2><a href="{auth_url}">Sign in</a></h2><p>Remember, {redirect_uri} must be in the Spotify app settings'

    # Step 3. Signed in, display data
    logging.debug("Signed in OK")
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    logger.log(5, f"Spotify data: {spotify.me()}")  # Lower than debug :)
    return f'<h2>Hi {spotify.me()["display_name"]}! </h2> Now playing: {spotify.current_user_playing_track()}'


def get_spotify():
    global spotify

    logger = logging.getLogger("peoplesplaylist.get_spotify")

    if spotify is not None:
        return spotify

    auth_manager = spotipy.oauth2.SpotifyOAuth()
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        logger.debug("Not logged in")
        return

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return spotify


def get_current_track():
    logger = logging.getLogger("peoplesplaylist.current_track")

    spotify = get_spotify()

    if spotify is None:
        return INVALID_TRACK

    data = spotify.current_user_playing_track()
    if data is None:
        logger.debug("Not playing")
        return INVALID_TRACK

    logger.log(5, data)  # Lower than debug :)

    return {
        "artist": ", ".join([str(x["name"]) for x in data["item"]["artists"]]),
        "title": data["item"]["name"],
        "duration": data["item"]["duration_ms"],
        "track_remaining": max(0, data["item"]["duration_ms"] - data["progress_ms"]),
        "voting_remaining": max(0, (VOTE_TIME * 1000 - data["progress_ms"])),
        "progress": data["progress_ms"],
        "is_playing": data["is_playing"],
        "image_url": data["item"]["album"]["images"][0]["url"],
        "valid": True,
    }


def skip():
    logger = logging.getLogger("peoplesplaylist.current_track")

    spotify = get_spotify()

    if spotify is None:
        return INVALID_TRACK

    logger.info("Skipping track")
    spotify.next_track()
    return True
