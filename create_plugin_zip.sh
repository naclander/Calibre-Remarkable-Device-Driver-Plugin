#!/bin/bash
set -euxo pipefail
# Helper script to generate the plugin zip file which can be directly
# installed by Calibre
rm -rf ./calibre-remarkable-device-driver-plugin.zip ./remarkable-device-driver-plugins

# Include all the dependencies in the zip archive
pip install git+https://github.com/nick8325/remarkable-fs -t ./remarkable-device-driver-plugins

zip -r calibre-remarkable-device-driver-plugin.zip ./ -x ".*" "*.pyc"
