from rest_framework import serializers
from .models import Atrakcja, Cennik

class AtrakcjaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atrakcja
        fields = '__all__'
       
class CennikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cennik
        fields = '__all__'