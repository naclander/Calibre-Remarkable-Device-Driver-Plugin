#!/bin/bash
# Helper script to generate the plugin zip file which can be directly 
# installed by Calibre
zip -r calibre-remarkable-device-driver-plugin.zip ./ -x ".*"
