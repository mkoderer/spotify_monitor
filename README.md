# spotify_monitor
Monitors listened songs.

## Setup

1. Create a transfer playlist in spotify and share it across the accounts
2. Create [developer accounts](https://developer.spotify.com/) for all the accounts where the marked songs should be synced
3. Copy ``config.yaml.sample`` to ``config.yaml``
4. Adapt username, access key and secret (first account shoule be the user of the tranfer playlist)
5. Create venv `python3 -mvenv .venv && source .venv/bin/activate`
6. `pip install -r requirements.txt`
7. Run `python3 spotify_monitor.py`


## Cache files
The refresh tokens are stored locally for each username. Please ensure that the usernames are unique.
