from django.conf import settings
from django.db import models
from django.utils import timezone

class Measurement(models.Model):
	ID = models.BigAutoField(primary_key = True)
	date = models.DateTimeField()

class MeasurementSequence(models.Model):
	measurementID = models.IntegerField()
	waveLength = models.DecimalField(max_digits = 7, decimal_places = 3)
	intensity = models.DecimalField(max_digits = 13, decimal_places = 9)