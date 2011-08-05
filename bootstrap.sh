#!/bin/bash

# FIX: Make this /bin/sh?

if [[ $USER != "root" ]] ; then
    echo "fatal: You need to be root."
    exit 1
fi

apt-get install python-apt

./machine.py setup

