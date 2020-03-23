#!/bin/bash
chmod 755 ./run.py
pip3 install -./requirements.txt
mv ./config.py.example ./config.py
vim ./config.py
