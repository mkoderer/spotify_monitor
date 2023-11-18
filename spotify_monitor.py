import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler
import logging
import yaml
from mergedeep import merge, Strategy
import schedule
import time


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARNING)
log = logging.getLogger()

last_execution = None

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
    handler = CacheFileHandler(username=account["Username"])
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=account.get("ClientId"),
            client_secret=account["Secret"],
            redirect_uri=account.get("RedirectUrl"),
            cache_handler=handler,
            open_browser=config.get("OpenBrowser"),
            scope="user-read-recently-played"))
    log.info("Authenicated with user %s" % account["Username"])

    return sp

def main(args):
    global last_execution
    with open(args.config_file) as f:
        config = yaml.full_load(f)
    log.setLevel(config.get("LogLevel"))
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
    last_execution = time.time_ns() - ( 5 * 60 * 1000 * 1000) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spotify playlist sync')
    parser.add_argument('--config-file', "-c",
                        help='Config file (default config.yaml)',
                        default="config.yaml")
    parser.add_argument('--daemon', "-d", action="store_true",
                        default=False,
                        help='Keep running and syncing')
    parser.add_argument('--frequency',
                        default=5,
                        help='Sync frequency in minutes')
    args = parser.parse_args()

    main(args)
    if args.daemon:
        schedule.every(args.frequency).seconds.do(main, args=args)
        log.info("Run every %s minutes from now" % args.frequency)
        while True:
            schedule.run_pending()
            time.sleep(10)
