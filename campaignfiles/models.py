# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class SourceType(models.Model):
	sourceType = models.CharField(max_length=30, unique=True)
