from django.db import models

# Create your models here.
class SensorData(models.Model):
    node_id = models.IntegerField()
    temperature = models.FloatField()
    smoke = models.FloatField()
    humidity = models.FloatField()
    x = models.FloatField(null=True, blank=True)
    y = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=10)  # SAFE / WARNING / FIRE

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Node {self.node_id} - {self.status}"