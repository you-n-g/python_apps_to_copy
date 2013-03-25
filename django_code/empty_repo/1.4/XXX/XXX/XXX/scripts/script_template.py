#!/usr/bin/env python
#!-*- coding:utf8 -*-
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from django.core.management import setup_environ
import settings
setup_environ(settings)

if __name__ == '__main__':
    #main()
