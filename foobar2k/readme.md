# foobar2000 Media Player for Home Assistant

A Home Assistant Python library to control [foobar2000](http://www.foobar2000.org/) media player from within Home Assistant. It relies on [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb).

## Setup

* Copy the contents of the `foobar2k` directory to your `custom_components` folder in Home Assistant. Configuration is now via UI only. Provide the url and port where Foobar 2000 is running.
* The foobar2k media player should work with any media player front end. It has been tested with the excellent [Minimalistic media card](https://github.com/kalkih/mini-media-player). The settings I use are:
 ```yaml
    - type: custom:mini-media-player
      entity: media_player.my_foobar_server
      volume_stateless: false
      artwork: full-cover-fit
      source: icon
      sound_mode: full
      hide:
         name: true
         icon: true   
         shuffle: false
         sound_mode: false
```

## Thank you

Big thanks to `ed0zer-projects` who first created a foobar2000 player for Home Assistant. They used `foo_httpcontrol` but I wanted to go with the REST API as supplied by [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb). In any case I used `ed0zer-projects` implementation as a high level guide. Also thank you `HyperBlast` for the REST Api to foobar2000.
