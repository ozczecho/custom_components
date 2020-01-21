import requests
import logging
import json.tool
import time

_LOGGER = logging.getLogger(__name__)

# System const
POWER_ON = "ON"
POWER_OFF = "OFF"
STATE_PAUSED = "paused"
STATE_STOPPED = "stopped"
STATE_PLAYING = "playing"

# Api calls
GET_PLAYER_INFO = "/api/player"
GET_PLAYLIST_ITEMS = "/api/playlists/{0}/items/{1}"
GET_PLAYLISTS = "/api/playlists"
GET_ALBUM_ART = "/api/artwork/{0}/{1}"

POST_PLAYER = "/api/player"
POST_PLAYER_PLAY = "/api/player/play"
POST_PLAYER_STOP = "/api/player/stop"
POST_PLAYER_NEXT = "/api/player/next"
POST_PLAYER_PREVIOUS = "/api/player/previous"
POST_PLAYER_PAUSE = "/api/player/pause"
POST_PLAYER_PAUSE_TOGGLE = "/api/player/pause/toggle"
POST_PLAYER_RANDOM = "/api/player/random"
POST_PLAYER_PLAY_PLAYLIST = "/api/player/play/{0}/{1}"

PLAYBACK_MODE_DEFAULT = 0
PLAYBACK_MODE_REPEAT_PLAYLIST = 1
PLAYBACK_MODE_REPEAT_TRACK = 2
PLAYBACK_MODE_RANDOM = 3
PLAYBACK_MODE_SHUFFLE_TRACKS = 4
PLAYBACK_MODE_SHUFFLE_ALBUMS = 5
PLAYBACK_MODE_SHUFFLE_FOLDERS = 6

playback_modes = {
    PLAYBACK_MODE_DEFAULT: 'Default',
    PLAYBACK_MODE_REPEAT_PLAYLIST: 'Repeat Playlist',
    PLAYBACK_MODE_REPEAT_TRACK: 'Repeat Track',
    PLAYBACK_MODE_RANDOM: 'Random',
    PLAYBACK_MODE_SHUFFLE_TRACKS: 'Shuffle Tracks',
    PLAYBACK_MODE_SHUFFLE_ALBUMS: 'Shuffle Albums',
    PLAYBACK_MODE_SHUFFLE_FOLDERS: 'Shuffle Folders'
}

class Foobar2k:
    """Api access to Foobar 2000 Server"""

    def __init__(self, host, port, timeout):

        self._host = host
        self._port = port
        self._timeout = timeout
        self._base_url = "http://{host}:{port}".format(host=self._host, port=self._port)
        _LOGGER.debug("[Foobar2k] __init__  with {0}".format(self._base_url))

        self._title = ''
        self._state = STATE_STOPPED
        self._artist = ''
        self._album = ''
        self._volume = 50
        self._track_duration = 0
        self._track_position = 0
        self._isMuted = False
        self._min_volume = -100
        self._album_art_url = None
        self._current_playlist_id = None
        self._current_index = 0
        self._playlists = {}
        self._playback_mode = PLAYBACK_MODE_DEFAULT
        self._path = None 

    def send_get_command(self, command, data):
        """Send command via HTTP get to FB2K server."""

        res = requests.get("{base_url}{command}".format(
            base_url=self._base_url, command=command), data=data,
            timeout=self.timeout)
        if (res.status_code == 200 or res.status_code == 204):
            return res.text
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s to GET command at "
                "end point %s"), self._host, res.status_code, command)
            return None

    def send_post_command(self, command, data):
        """Send command via HTTP post to FB2K server."""

        res = requests.post("{base_url}{command}".format(
            base_url=self._base_url, command=command),
            data=data, timeout=self.timeout)
        if (res.status_code == 200 or res.status_code == 204):
            return res.text
        else:
            _LOGGER.error((
                "Host %s returned HTTP status code %s to POST command at "
                "end point %s"), self._host, res.status_code, command)
            return None

    def update(self):
        """Get the latest status information from FB2K server"""

        _LOGGER.debug("[Foobar2k] Doing update()")
        # Get current status of the FB2K server
        try:
            response = self.send_get_command(GET_PLAYER_INFO, data=None)
            self._power = POWER_ON
            _LOGGER.debug("[Foobar2k] Doing update() POWER ON")
        except ValueError:
            pass
        except requests.exceptions.RequestException:
            # On timeout and connection error, the device is probably off
            self._power = POWER_OFF
            _LOGGER.debug("[Foobar2k] Doing update() POWER OFF")
        else:
            # Get current status
            _LOGGER.debug("[Foobar2k] Doing update() Reading response")
            if (response is not None):
                data = json.loads(response)
                _LOGGER.debug("[Foobar2k] Doing update() Loaded response {0}".format(data))
                new_state = data["player"]["playbackState"]
                if (new_state != self._state):
                    _LOGGER.debug("[Foobar2k] Getting playlists")
                    self.set_playlists()
                    
                self._state = new_state
                self._playback_mode = data["player"]["playbackMode"]

                if 'activeItem' in data["player"]:
                    _LOGGER.debug("[Foobar2k] Doing update() Have activeItem")
                    if ('playlistId' in data["player"]["activeItem"]):
                        index = data["player"]["activeItem"]["index"]
                        if (index >= 0):
                            _LOGGER.debug("[Foobar2k] Doing update() Have index")
                            self._current_index = index
                            self._current_playlist_id = data["player"]["activeItem"]["playlistId"]
                            self._track_duration = data["player"]["activeItem"]["duration"]
                            self._track_position = data["player"]["activeItem"]["position"]
                            self._album_art_url = "{0}{1}".format(self._base_url, GET_ALBUM_ART.format(self._current_playlist_id, index))

                            currently = self.send_get_command(GET_PLAYLIST_ITEMS.format(
                                self._current_playlist_id, index), data='{"columns":["%artist%","%title%", "%track%", "%album%", "%path%"]}')
                            if (currently is not None):
                                _LOGGER.debug("[Foobar2k] Doing update() Have current song")
                                i = json.loads(currently)
                                _LOGGER.debug("Currently Playing {0} {1}".format(
                                    i["playlistItems"]["items"][0]["columns"][0], i["playlistItems"]["items"][0]["columns"][1]))
                                self._artist = i["playlistItems"]["items"][0]["columns"][0]
                                self._title = i["playlistItems"]["items"][0]["columns"][1]
                                self._album = i["playlistItems"]["items"][0]["columns"][3]
                                self._path = i["playlistItems"]["items"][0]["columns"][4]

                if 'volume' in data["player"]:
                    self._isMuted = data["player"]["volume"]["isMuted"]
                    self._volume = data["player"]["volume"]["value"]
                    self._min_volume = data["player"]["volume"]["min"]

                _LOGGER.debug("[Foobar2k] update {0} {1} {2} - {3}:{4}".format(self._artist, self._title, self._album, self._current_playlist_id, self._current_index))

            return True

    @property
    def host(self):
        """Return the host address."""
        return self._host

    @property
    def port(self):
        """Return the host port."""
        return self._port

    @property
    def timeout(self):
        """Return the timeout."""
        return self._timeout

    @property
    def isMuted(self):
        """Is Muted True / False."""
        return self._isMuted

    @property
    def isShuffle(self):
        """Is Shuffle True / False."""
        return self._playback_mode == PLAYBACK_MODE_RANDOM

    @property
    def volume(self):
        """Volume level."""
        return self._volume + abs(self._min_volume)

    @property
    def state(self):
        """Can be paused, stopped, playing"""
        _LOGGER.debug("[Foobar2k] State {0}".format(self._state))
        return self._state

    @property
    def power(self):
        """Can be on, off"""
        return self._power

    @property
    def title(self):
        """Song title"""
        return self._title

    @property
    def album(self):
        """Name of album"""
        return self._album

    @property
    def album_art(self):
        """ Album art work url"""
        return self._album_art_url

    @property
    def artist(self):
        """Name of artist"""
        return self._artist

    @property
    def track_position(self):
        """Playing position of the track"""
        return self._track_position

    @property
    def track_duration(self):
        """Duration of the Track"""
        return self._track_duration

    @property
    def playlists(self):
        """ Get a list of all playlists """
        return self._playlists

    @property
    def current_playlist(self):
        """Get the current playlist"""
        if (self._playlists == {}):
            return None
        else:
            for title, id in self._playlists.items():
                if (id == self._current_playlist_id):
                    return title
            return None

    @property
    def current_index(self):
        """Get the index of the current song"""
        return self._current_index

    @property
    def media_path(self):
        """Gets the full file path to the current media playing"""
        return self._path

    @property
    def playback_mode(self):
        """Get the current playback mode"""
        return self._playback_mode

    @property
    def playback_modes(self):
        """Get the current playback mode"""
        return list(playback_modes.values())

    def toggle_play_pause(self):
        """Toggle play pause media player."""
        _LOGGER.debug("[Foobar2k] In Play / Pause")
        if (self._power == POWER_ON):
            if (self._state == STATE_STOPPED):
                self.send_post_command(POST_PLAYER_PLAY_PLAYLIST.format(self._current_playlist_id, self._current_index), data=None)
            else:            
                self.send_post_command(POST_PLAYER_PAUSE_TOGGLE, data=None)

    def play(self):
        """Send play command to FB2K Server"""
        _LOGGER.debug("[Foobar2k] In Play")
        if (self._power == POWER_ON):
            response = None
            if (self._state == STATE_STOPPED):
                response = self.send_post_command(POST_PLAYER_PLAY_PLAYLIST.format(self._current_playlist_id, self._current_index), data=None)
            else:
                response = self.send_post_command(POST_PLAYER_PLAY, data=None)
            if (response is not None):
                self._state = STATE_PLAYING

    def stop(self):
        """Send stop command to FB2K Server"""
        _LOGGER.debug("[Foobar2k] In Stop. Current state is {0}".format(self._state))
        if (self._power == POWER_ON and self._state == STATE_PLAYING):
            self.send_post_command(POST_PLAYER_STOP, data=None)
            self._state = STATE_STOPPED
            _LOGGER.debug("[Foobar2k] State now is {0}".format(self._state))

    def play_next(self):
        """Send next command to FB2K Server"""
        _LOGGER.debug("[Foobar2k] In Next")
        if (self._power == POWER_ON):
            self.send_post_command(POST_PLAYER_NEXT, data=None)
            time.sleep(0.2)
            self.update()

    def play_previous(self):
        """Send previous command to FB2K Server"""
        _LOGGER.debug("[Foobar2k] In Previous")
        if (self._power == POWER_ON):
            self.send_post_command(POST_PLAYER_PREVIOUS, data=None)
            time.sleep(0.2)
            self.update()

    def toggle_mute(self):
        """Mute the volume."""
        _LOGGER.debug("[Foobar2k] In Toggle Mute")
        if (self._power == POWER_ON):
            mute = not self._isMuted
            data = json.dumps({"isMuted": mute})
            _LOGGER.debug("[Foobar2k] Toggle data {0}".format(data))
            self.send_post_command(POST_PLAYER, data=data)
            self._isMuted = mute

    def set_volume(self, volume):
        """Change the volume."""
        _LOGGER.debug("[Foobar2k] In Volume {0}".format(volume))
        if (self._power == POWER_ON):
            new_volume = self._min_volume + volume
            data = json.dumps({"volume": new_volume})
            _LOGGER.debug("[Foobar2k] Volume data {0}".format(data))
            self.send_post_command(POST_PLAYER, data=data)
            self._volume = new_volume

    def set_position(self, position):
        """Change the track playing position."""
        _LOGGER.debug("[Foobar2k] In Position {0}".format(position))
        if (self._power == POWER_ON):
            data = json.dumps({"position": position})
            _LOGGER.debug("[Foobar2k] Position data {0}".format(data))
            self.send_post_command(POST_PLAYER, data=data)
            self._track_position = position

    def set_playlists(self):
        """ Retrieve all available playlists from player"""
        _LOGGER.debug("[Foobar2k] Getting playlists")
        if (self._power == POWER_ON):
            playlists = {}
            response = self.send_get_command(GET_PLAYLISTS, data=None)
            data = json.loads(response)
            _LOGGER.debug("[Foobar2k] Have  playlists {0}".format(data))
            for pl in data["playlists"]:
                playlists[pl["title"]] = pl["id"]
                if (pl["isCurrent"]):
                    self._current_playlist_id = pl["id"]
            self._playlists = playlists

    def set_playlist_play(self, playlist_id, index):
        """ Set the playlist and song index"""
        self.send_post_command(POST_PLAYER_PLAY_PLAYLIST.format(playlist_id, index), data=None)
        self._current_playlist_id = playlist_id
        time.sleep(0.2)
        self.update()

    def set_playback_mode(self, new_mode):
        """Change the playback mode. Can be Default, Repeat (PlayList), Repeat (Track), Random, Shuffle (Tracks), Shuffle (Albums), Shuffle (Folders)"""
        _LOGGER.debug("[Foobar2k] In Set playback mode")
        if (self._power == POWER_ON):
            mode = PLAYBACK_MODE_DEFAULT
            for m in playback_modes:
                if (playback_modes[m] == new_mode):
                    mode = m
                    break

            data = json.dumps({"playbackMode": mode})
            _LOGGER.debug("[Foobar2k] PlaybackMode data {0}".format(data))
            self.send_post_command(POST_PLAYER, data=data)
            self._playback_mode = mode

    def get_playback_mode_description(self, mode):
        return playback_modes[mode]