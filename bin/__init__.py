#!/usr/env python3
# -*- coding: utf-8 -*-
# main.py


from bs4 import BeautifulSoup
import requests
from config.hianime import configure
import shutil


url=configure['baseurl']
columns = shutil.get_terminal_size().columns
text = "Welcome to pyanime"
print(text.center(columns))