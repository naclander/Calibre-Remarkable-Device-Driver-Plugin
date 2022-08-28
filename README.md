I am no longer actively maintainig this plugin myself, but I will continue to accept patches if anyone contributes improvements. 

Sync your books to Remarkable with Calibre
==========================================================
This Calibre plugin implements Calibre's [Device Plugin](https://manual.calibre-ebook.com/plugins.html#module-calibre.devices.interface), 
making the Remarkable  Tablet a device Calibre can communicate with, similar to other supported Ebook readers. 
This plugin creates the folders and files within the Remarkable file structure, such that they are viewable using the 
Remarkable interface. It does not  simply copy files over in the filesystem, but integrates with the Calibre Document 
Format, thanks to [remarkable-fs](https://github.com/nick8325/remarkable-fs).

Requirements
------------
This plugin relies on SSH communication between the machine running Calibre, and the Remarkable tablet. Please ensure
that you can successfully SSH to your Remarkable tablet.

Installation
------------
Download the zipped version of this plugin, and install it in Calibre via the Plugin interface.

If you are a developer, you can install the source version of this plugin by running `calibre-customize -b` from the
root directory of this project to install the source code plugin directly. See 
`calibre-customize --help` for more detail.

Configuration
-------------
Clicking on the plugin from Calibre's plugin interface brings up the settings box where you will see several values
you can customize:

| Parameter     | Description                                                                                                                       | Default Value   |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------|-----------------|
| Remarkable IP | IP Address of Remarkable Tablet                                                                                                   | `"10.11.99.1"`  |
| Books Path    | Path where you would like Calibre to transfer your books to on the device ( Folders will be created if they do not exist )        | `"/"`           |
| Metadata Path | Location of calibre metadata file which is stored on the device                                                                   | `"/home/root/"` |
| Password      | If not using SSH key, the SSH password for the Remarkable user                                                                    | `""`            |

Usage
-----
Once the plugin is installed and configured, the plugin should work automatically. At Calibre startup, the plugin will attempt to find your Remarkable device, and ssh to it. If it succeeds you should see "Device" button at the top which shows your books on your Remarkable Tablet. 

To send a book to your Remarkable Tablet, right click on the book, select "send to device" and then "send to main memory". The book will transfer and you should now see your book in the Device tab. If you want to remove a book, go to the Device tab, right click on the book and select to remove it.

If you start Calibre and you don't see the Device tab, most likely Calibre was not able to find or connect to your Remarkable tablet. Try running Calibre in debug using `calibre-debug -g` and see the messages in the console regarding trying to connect to the device.

Development
-----------
Git clone this repository. First run `create-plugin-zip.sh` in order to install the local dependencies. After making
the desired changes, run `calibre-customize -b ./ && calibre-debug -g ` from the  root project directory to install the
latest version of this plugin and launch Calibre.

Ensure all plugin functionality still works and submit a patch.

This repo contains a submodule for remarkable-fs. Unfortunately the version of remarkable-fs in pypy and the current
source on the master branch are not in sync. I would ideally have liked to require remarkable-fs as a dependency and have
the user install the pip version. However, because the current pypy version is out of date and because have remarkable-fs
included in the zipped plugin makes installation simpler for users I've decided just to include it in this repo. It is
the responsibility of this repo to keep the remarkable-fs submodule up to date. I would like to eventually stop
including this submodule, and have a requirement of installing it with pip like other normal dependencies.

Architecture
------------
This plugin sends files and creates folders by using `remarkable-fs` under the hood. Files and folders are created via
Remarkable's custom format, which makes them viewable in the default Remarkable UI. This means you will not be able to
see them in the Linux filesystem directly.

To keep track of which books have been synced on the device, we create a `.calbire.json` metadata file which stores the
Calibre state on the device. We try and maintain this file in sync with the state in Calibre.

Bugs
----
Yes.

Thanks
------
[Calibre](https://github.com/kovidgoyal/calibre) for making a great ebook manager.

[remarkable-fs](https://github.com/nick8325/remarkable-fs) for implementing a great API for 
communication with the Remarkable tablet.

All developers in the Remarkable community.
