#!/usr/bin/env python
"""Comprehensive integration tests - run via: python manage.py test tests.comprehensive_test"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.core.management import execute_from_command_line
execute_from_command_line(["manage.py", "test", "tests.comprehensive_test"])
