"""Support for Foobar2k api provided by beefweb https://github.com/hyperblast/beefweb."""

from collections import namedtuple
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDevice, PLATFORM_SCHEMA)

# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/media_player/const.py
from homeassistant.components.media_player.const import (
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_PLAY_MEDIA, SUPPORT_STOP, SUPPORT_PLAY, SUPPORT_SHUFFLE_SET, SUPPORT_SEEK,
    SUPPORT_PAUSE, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET, SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK,
    MEDIA_TYPE_MUSIC, ATTR_APP_NAME, ATTR_MEDIA_ALBUM_ARTIST, ATTR_MEDIA_ALBUM_NAME, ATTR_MEDIA_DURATION, ATTR_MEDIA_PLAYLIST,
    ATTR_MEDIA_SHUFFLE, ATTR_MEDIA_TITLE, ATTR_MEDIA_TRACK, ATTR_MEDIA_VOLUME_MUTED, SUPPORT_SELECT_SOURCE, SUPPORT_SELECT_SOUND_MODE,
    ATTR_SOUND_MODE, ATTR_SOUND_MODE_LIST)

from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PORT, CONF_TIMEOUT, STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING, STATE_UNKNOWN, STATE_IDLE)

from custom_components.foobar2k.foobar2k import (
    PLAYBACK_MODE_DEFAULT, PLAYBACK_MODE_REPEAT_PLAYLIST, PLAYBACK_MODE_REPEAT_TRACK, PLAYBACK_MODE_RANDOM,
    PLAYBACK_MODE_SHUFFLE_TRACKS, PLAYBACK_MODE_SHUFFLE_ALBUMS, PLAYBACK_MODE_SHUFFLE_FOLDERS)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 2

SUPPORT_FOOBAR_PLAYER = \
    SUPPORT_NEXT_TRACK | \
    SUPPORT_PAUSE | \
    SUPPORT_PLAY | \
    SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_SELECT_SOURCE | \
    SUPPORT_SELECT_SOUND_MODE | \
    SUPPORT_SHUFFLE_SET | \
    SUPPORT_STOP | \
    SUPPORT_VOLUME_MUTE |  \
    SUPPORT_VOLUME_SET
# SUPPORT_SEEK | \

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_PORT): cv.port,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Foobar 2k platform."""
    from custom_components.foobar2k.foobar2k import Foobar2k

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    timeout = config.get(CONF_TIMEOUT)

    fb2k_service = Foobar2k(
        host=host, port=port, timeout=timeout)

    add_entities([Foobar2kDevice(hass, fb2k_service, name)])


class Foobar2kDevice(MediaPlayerDevice):

    def __init__(self, hass, fb2k, name):
        """Initialize the device."""
        self.hass = hass
        self._name = name
        self._state = STATE_UNKNOWN
        self._service = fb2k
        self._title = None
        self._artist = None
        self._album = None
        self._album_art = None
        self._isMuted = False
        self._volume = 0
        self._track_position = None
        self._track_duration = None
        self._shuffle = False
        self._current_playlist = None
        self._current_sound_mode = None
        self._playlists = []
        self._sound_mode_list = self._service.playback_modes

    def update(self):
        self._service.update()
        self._isMuted = self._service.isMuted
        self._volume = self._service.volume
        self._shuffle = self._service.isShuffle
        self._playlists = self._service.playlists
        self._current_playlist = self._service.current_playlist
        self._current_sound_mode = self._service.get_playback_mode_description(
            self._service.playback_mode)
        if (self.state == STATE_PLAYING):
            self._album_art = self._service.album_art
            self._title = self._service.title
            self._artist = self._service.artist
            self._album = self._service.album
            self._track_position = self._service.track_position
            self._track_duration = self._service.track_duration
            # self._last_update = dt_util.utcnow()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        current_state = self._service.state
        if (current_state == STATE_PLAYING or current_state == STATE_PAUSED):
            self._state = current_state
        else:
            self._state = STATE_IDLE
        _LOGGER.debug("Current State {0}".format(self._state))

        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        supported_features = SUPPORT_FOOBAR_PLAYER
        return supported_features

    @property
    def shuffle(self):
        """Boolean if shuffling is enabled."""
        return self._shuffle

    @property
    def is_volume_muted(self):
        return self._isMuted

    @property
    def volume_level(self):
        """Volume level of the media player (0 to 1)."""
        return float(self._volume) / 100

    @property
    def media_title(self):
        """Title of current playing track."""
        return self._title

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_artist(self):
        """Artist of current playing track."""
        return self._artist

    @property
    def media_album_name(self):
        """Album name of current playing track."""
        return self._album

    @property
    def media_duration(self):
        """Return the duration of current playing media in seconds."""
        _LOGGER.debug("[Media_Player_FB2K] media_duration Called {0}".format(
            self._track_duration))
        return self._track_duration

    @property
    def media_position(self):
        """Return the position of current playing media in seconds."""
        _LOGGER.debug("[Media_Player_FB2K] media_position Called {0}".format(
            self._track_position))
        return self._track_position

    # @property
    # def media_position_updated_at(self):
    #     """When was the position of the current playing media valid."""
    #     return self._last_update

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        _LOGGER.debug("[Media_Player_FB2K] Album ART")
        return self._album_art

    @property
    def source(self):
        """Return  current source name."""
        return self._current_playlist

    # @property
    # def media_playlist(self):
    #     """Title of Playlist currently playing."""
    #     _LOGGER.debug(
    #         "[Media_Player_FB2K] media_playlist {0}".format(self._playlists))
    #     if (self._playlists == None or self._playlists == {} or self._current_playlist_id == None):
    #         _LOGGER.debug("[Media_Player_FB2K] media_playlist == NoName")
    #         return None
    #     else:
    #         name = self._playlists.get(self._current_playlist_id)
    #         _LOGGER.debug(
    #             "[Media_Player_FB2K] media_playlist {0}".format(name))
    #     return name

    @property
    def source_list(self):
        """List of available input sources."""
        _LOGGER.debug("[Media_Player_FB2K] Property Source_List")
        if (self._playlists == {} or self._playlists == []):
            return ["Empty"]
        else:
            return list(self._playlists.keys())

    @property
    def sound_mode(self):
        return self._current_sound_mode

    @property
    def sound_mode_list(self):
        return self._sound_mode_list

    # @property
    # def should_poll(self):
    #     """Return True if entity has to be polled for state."""
    #     return True

    def media_play_pause(self):
        """Send the media player the command for play/pause."""
        _LOGGER.debug("[Media_Player_FB2K] Play / Pause Called")
        self._service.toggle_play_pause()

    def media_pause(self):
        """Send the media player the command for play/pause if playing."""
        _LOGGER.debug("[Media_Player_FB2K] Pause Called")
        if (self.state == STATE_PLAYING):
            _LOGGER.debug("[Media_Player_FB2K] Pausing")
            media_play_pause()

    def media_stop(self):
        """Send the media player the stop command."""
        _LOGGER.debug("[Media_Player_FB2K] Stop Called")
        self._service.stop()

    def media_play(self):
        """Send the media player the command to play at the current playlist."""
        _LOGGER.debug("[Media_Player_FB2K] Play Called")
        self._service.play()

    def media_next_track(self):
        """Send the media player the command to play the next song"""
        _LOGGER.debug("[Media_Player_FB2K] Next Track Called")
        self._service.play_next()

    def media_previous_track(self):
        """Send the media player the command to play the previous song"""
        _LOGGER.debug("[Media_Player_FB2K] Previous Track Called")
        self._service.play_previous()

    def mute_volume(self, mute):
        """Mute the volume."""
        _LOGGER.debug("[Media_Player_FB2K] Mute Called")
        self._service.toggle_mute()

    def set_volume_level(self, volume):
        """Send the media player the command for setting the volume."""
        _LOGGER.debug("[Media_Player_FB2K] set_volume_level Called {0}".format(volume))
        self._service.set_volume(volume * 100)

    # def media_seek(self, position):
    #     """Send the media player a command for seeking new position in track."""
    #     self._service.set_position(position)

    def set_shuffle(self, shuffle):
        """Send the media player the command for setting the shuffle mode."""
        _LOGGER.debug("[Media_Player_FB2K] set_shuffle Called **{0}**".format(shuffle))
        mode = PLAYBACK_MODE_RANDOM if shuffle else PLAYBACK_MODE_DEFAULT
        self._service.set_playback_mode(self._service.get_playback_mode_description(mode))

    def select_source(self, source):
        _LOGGER.debug("[Media_Player_FB2K] Setting source {0}".format(source))
        if (source == self._current_playlist):
            return

        playlist_id = self._playlists.get(source)
        self._service.set_playlist_play(playlist_id, 0)
        self._current_playlist = source

    def select_sound_mode(self, sound_mode):
      """Switch the sound mode of the entity."""
      _LOGGER.debug("[Media_Player_FB2K] Sound Mode {0}".format(sound_mode))
      self._service.set_playback_mode(sound_mode)
