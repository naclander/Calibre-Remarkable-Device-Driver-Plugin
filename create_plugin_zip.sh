#!/bin/bash
set -euxo pipefail
# Helper script to generate the plugin zip file which can be directly
# installed by Calibre
rm -rf ./calibre-remarkable-device-driver-plugin.zip ./target

mkdir target
cp __init__.py config.py LICENSE plugin-import-name-remarkable_plugin.txt target/
pushd ./target
# Include all the dependencies in the zip archive
pip install git+https://github.com/nick8325/remarkable-fs -t ./
zip -r ../calibre-remarkable-device-driver-plugin.zip ./ -x ".*" "*.pyc"
popd
