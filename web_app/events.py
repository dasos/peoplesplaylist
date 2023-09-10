# from web_app import system, data
import logging
from threading import Lock
from app import socketio
from flask_socketio import emit

import spotify

count = {"skip": 0, "keep": 0}


track_thread = 0
watcher_thread = None
thread_lock = Lock()
watcher_lock = Lock()


@socketio.event
def connect():
    global watcher_thread
    track_data = spotify.get_current_track()

    emit("now-playing", track_data)
    emit("vote", count)

    with thread_lock:
        if watcher_thread is None:
            watcher_thread = socketio.start_background_task(watcher)


@socketio.event
def vote(msg):
    count[msg["for"]] = count[msg["for"]] + 1

    logger = logging.getLogger("peoplesplaylist.vote")
    logger.info(f"Current votes: {count}")

    emit("vote", count, broadcast=True)


def watcher():
    """Runs every 30 seconds. If there are no track threads AND
    something is playing, start a new track thread"""

    global watcher_lock

    logger = logging.getLogger("peoplesplaylist.watcher")
    while True:
        logger.debug("Watcher is watching")
        if track_thread == 0:
            track_data = spotify.get_current_track()
            if "is_playing" in track_data and track_data["is_playing"] is True:
                with watcher_lock:
                    if track_thread == 0:  # Check again
                        logger.debug("Triggered new tracks")
                        new_track()
                    else:
                        logger.debug("Avoided making new threads!")
            else:
                logger.debug("Nothing playing")
        else:
            logger.debug(f"All good. Number of track threads: {track_thread}")

        socketio.sleep(30)


# Runs when a new track is started. May also be called by the watcher
def new_track():
    global thread_lock, count, NO_VOTES

    logger = logging.getLogger("peoplesplaylist.wait_for_voting")

    logger.info("New track detected, waiting for a second")
    socketio.sleep(1)

    count = {"skip": 0, "keep": 0}
    socketio.emit("vote", count)

    track_data = spotify.get_current_track()
    socketio.emit("now-playing", spotify.get_current_track())

    track_remaining = track_data["track_remaining"]
    track_remaining = max(
        track_remaining, 1000
    )  # It might be that it takes a second or two to start the next song, this avoids 0

    voting_remaining = track_data["voting_remaining"]

    # We will start a new thread for track and voting
    with thread_lock:
        # These threads will run
        socketio.start_background_task(wait_for_new_track, track_remaining)
        if voting_remaining > 0:
            socketio.start_background_task(wait_for_voting, voting_remaining)


def wait_for_voting(timer):
    global thread_lock, track_thread, count
    timer = timer / 1000

    logger = logging.getLogger("peoplesplaylist.wait_for_voting")
    logger.info(f"Voting timer, waiting for {timer} seconds")

    socketio.sleep(timer)
    logger.debug("Voting timer awake")

    if count["skip"] > count["keep"]:
        print(count)
        logger.info("Skip votes won! Next track...")
        spotify.skip()

        # Start the threads
        new_track()


def wait_for_new_track(timer):
    global track_thread, thread_lock

    # Count that I'm starting
    with thread_lock:
        track_thread = track_thread + 1

    logger = logging.getLogger("peoplesplaylist.wait_for_new_track")
    logger.debug(f"I'm thread number: {track_thread}")

    timer = timer / 1000
    logger.info(f"New tracker timer, waiting for {timer} seconds")

    socketio.sleep(timer)
    logger.debug("New track timer awake")
    # It could be a new track right now (or it could be the end of 30 secs)
    # If it is a new track, we want to reset votes anyway, and we'll end up starting the timer for the votes

    track_data = spotify.get_current_track()
    socketio.emit("now-playing", track_data)

    # This will probably be right at the end of the song, and the next one hasn't actually quite started yet
    if track_data["voting_remaining"] > 25000 or track_data["track_remaining"] < 5000:
        logger.debug("Track thread ended, new track detected")

        # This will start up new threads
        new_track()
    else:
        logger.debug(track_data)
        logger.debug("Track thread ended *without* detecting a new track")

    # Count that I'm ending
    with thread_lock:
        track_thread = track_thread - 1
