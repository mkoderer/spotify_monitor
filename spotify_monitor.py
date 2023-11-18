import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler
import logging
import yaml
from mergedeep import merge, Strategy
import schedule
import time

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
log = logging.getLogger()

last_execution = None

auth_cache = {}

last_song = {}

def get_all(sp, function, *arg):
    log.info("Call get_all with function: %s" % function)
    func = getattr(sp, function)
    result = func(*arg)
    while result.get("next"):
        log.debug("Next page for call %s" % function)
        res = sp.next(result)
        merge(result, res, strategy=Strategy.ADDITIVE)
    return result


def auth(account, config):
    """Handles the authentication for the various accounts
    """
    global auth_cache
    if account["Username"] in auth_cache:
        return auth_cache[account["Username"]]

    handler = CacheFileHandler(username=account["Username"])
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=account.get("ClientId"),
            client_secret=account["Secret"],
            redirect_uri=account.get("RedirectUrl"),
            cache_handler=handler,
            open_browser=config.get("OpenBrowser"),
            scope="user-read-recently-played user-read-currently-playing"))
    log.info("Authenicated with user %s" % account["Username"])
    auth_cache[account["Username"]] = sp
    return sp

def monitor_playing_song(sp, username):
    global last_song
    log.debug(f'Monitor Account')
    played_track = sp.current_user_playing_track()
    if played_track:
        track = played_track.get("item")
        name = track["name"]
        artist_names = ""
        for artist in track["artists"]:
            artist_names += artist["name"] + " "
        explicit = ""
        if track["explicit"]:
            explicit = "XXX"
        if not username in last_song or not last_song[username] == f'{name}-{artist_names}':
            log.info(f'Playing song from {username}: {name} / {artist_names} | {explicit}')
            last_song[username] = f'{name}-{artist_names}'


def main(args, history = False):
    global last_execution
    with open(args.config_file) as f:
        config = yaml.full_load(f)
    log.setLevel(config.get("LogLevel"))

    # Check if there is a song played currently
    for account in config.get("accounts"):
        sp = auth(account, config)
        cur_track = sp.current_user_playing_track()
        if cur_track and cur_track.get("is_playing"):
            if not schedule.get_jobs(tag=account["Username"]):
                log.info(f'Account {account["Username"]} is currently playing. Scheduling monitor every {args.monitor_frequency} seconds')
                job = schedule.every(args.monitor_frequency).seconds.do(monitor_playing_song, sp, account["Username"])
                job.tags = {account["Username"]}
        else:
            jobs = schedule.get_jobs(tag=account["Username"])
            for job in jobs:
                schedule.cancel_job(job)
                log.info(f'Account {account["Username"]} has stopped playing')

    if history:
    # Check history
        for account in config.get("accounts"):
            sp = auth(account, config)
            tracks = get_all(sp, "current_user_recently_played", 50, last_execution)
            log.debug(tracks)
            for tr in tracks.get("items"):
                played_at = tr["played_at"]
                track = tr["track"]
                name = track["name"]
                artist_names = ""
                for artist in track["artists"]:
                    artist_names += artist["name"] + " "
                explicit = ""
                if track["explicit"]:
                    explicit = "XXX"
                log.info(f'Played from {account["Username"]} at {played_at}: {name} / {artist_names} | {explicit}')
    last_execution = int(time.time()) - 60

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spotify playlist sync')
    parser.add_argument('--config-file', "-c",
                        help='Config file (default config.yaml)',
                        default="config.yaml")
    parser.add_argument('--frequency', '-f',
                        default=1,
                        help='Frequency for the general check in minutes')
    parser.add_argument('--monitor-frequency', '-m',
                        default=5,
                        help='Monitor frequency while playing in seconds')
    args = parser.parse_args()

    main(args, True)
    schedule.every(args.frequency).minutes.do(main, args=args)
    log.info("Run every %s minutes from now" % args.frequency)
    while True:
        schedule.run_pending()
        time.sleep(1)
