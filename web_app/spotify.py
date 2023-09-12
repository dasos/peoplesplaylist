from flask import (
    Blueprint,
    request,
    url_for,
    redirect,
    current_app,
    has_request_context,
)

import logging

import spotipy

import os

import json

# These are global variables that we'll use when we are outside of a request context
cache_path = None
redirect_uri = None

bp = Blueprint("spotify", __name__, url_prefix="/spotify/")

VOTE_TIME = 30


@bp.route("/")
def index():
    logger = logging.getLogger("peoplesplaylist.spotify")
    
    print(f'logger level: {logger.getEffectiveLevel}')

    auth_manager = get_auth_manager()
    logger.debug(f"Got auth_manager, uing cache file here: {auth_manager.cache_handler.cache_path}")

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        token = auth_manager.get_access_token(request.args.get("code"))

        # Explicitly save the token. This shouldn't be necessary
        # cache_handler.save_token_to_cache(token)

        s = spotipy.Spotify(auth_manager=auth_manager)

        # print(cache_handler.get_cached_token())

        logger.debug("Got access token, redirecting")
        return redirect("/spotify")

    if not auth_manager.validate_token(auth_manager.cache_handler.get_cached_token()):
        logger.debug("Not logged in")
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()

        return (
            f'<h2><a href="{auth_url}">Sign in</a></h2>'
            f"<p>Remember, {redirect_uri} must be in the Spotify app settings"
        )

    # Step 3. Signed in, display data
    logger.debug("Signed in OK")
    s = spotipy.Spotify(auth_manager=auth_manager)
    logger.debug(f"Spotify profile data: {spotify.me()}")
    return (
        f'<h2>Hi {s.me()["display_name"]}!</h2>'
        f"My profile: <pre>{json.dumps(s.me(), indent=2)}</pre>"        
        f"Now playing: <pre>{json.dumps(s.current_user_playing_track(), indent=2)}"
    )


def get_auth_manager():
    global cache_path, redirect_uri

    logger = logging.getLogger("peoplesplaylist.get_auth_manager")

    if has_request_context():
        cache_path = current_app.config.get("SPOTIPY_CACHE")
        redirect_uri = url_for("spotify.index", _external=True)

    # We can't continue without a cache_path
    # We'll need to wait for someone to hit the login page
    if cache_path is None:
        logger.debug("No cache_path, cannot continue")
        return None

    # Work around containers mounting directories, not files
    cache_file = os.path.join(cache_path, "cache_file")
    logger.debug(f"Adjusted cache path to be {cache_file}")

    # Spotify is being authenticated and the token is stored globally, in a file
    # This prevents being reauthed every time the app is started
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=cache_file)

    return spotipy.oauth2.SpotifyOAuth(
        scope="user-read-currently-playing,user-modify-playback-state",
        redirect_uri=redirect_uri,
        show_dialog=True,
        cache_handler=cache_handler,
    )


def get_spotify():

    logger = logging.getLogger("peoplesplaylist.get_spotify")

    auth_manager = get_auth_manager()

    if auth_manager is None:
        logger.warning("No cache file is available, which means we aren't logged in")
        logger.error("Go to <url>/spotify to authenticate")
        return None

    try:
        if not auth_manager.validate_token(
            auth_manager.cache_handler.get_cached_token()
        ):
            logger.warning("Not logged in")
            return None
    except Exception as e:
        logger.error("Exception when trying to auth")
        logger.error(e)
        return None

    return spotipy.Spotify(auth_manager=auth_manager)


def get_current_track():
    logger = logging.getLogger("peoplesplaylist.current_track")

    s = get_spotify()

    if s is None:
        return {"valid": False}

    t = s.current_user_playing_track()
    if t is None:
        logger.debug("Not playing")
        return {"valid": False}

    logger.log(5, t)  # Lower than debug :)

    p = {}
    if t["context"]["type"] == "playlist":
        try:
            p = s.playlist(
                t["context"]["uri"], fields="collaborative,external_urls,name"
            )
        except SpotifyException as e:
            logger.warning(f"Caught an exception when trying to get playlist information: {e}")
            pass

    return {
        "artist": ", ".join([str(x["name"]) for x in t["item"]["artists"]]),
        "title": t["item"]["name"],
        "duration": t["item"]["duration_ms"],
        "track_remaining": max(0, t["item"]["duration_ms"] - t["progress_ms"]),
        "voting_remaining": max(0, (VOTE_TIME * 1000 - t["progress_ms"])),
        "progress": t["progress_ms"],
        "is_playing": t["is_playing"],
        "image_url": t["item"]["album"]["images"][0]["url"],
        "playlist": {
            "collaborative": p.get("collaborative"),
            "uri": p.get("external_urls", {}).get("spotify"),
            "name": p.get("name"),
        },
        "valid": True,
    }


def skip():
    logger = logging.getLogger("peoplesplaylist.skip")

    s = get_spotify()

    if s is None:
        return {"valid": False}

    logger.info("Skipping track")
    s.next_track()
    return True
