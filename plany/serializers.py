from rest_framework import serializers
from .models import PlanZwiedzania

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanZwiedzania
        fields = '__all__'
