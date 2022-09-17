#!/bin/bash
pyv="$(python -V 2>&1)"
if ! [[ $pyv =~ ^"Python 3.10."* ]];
then
	echo Python version must be 3.10
	exit 1
fi
	
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
