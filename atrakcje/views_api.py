from rest_framework import viewsets
from .models import Atrakcja, Cennik
from .serializers import AtrakcjaSerializer, CennikSerializer

class AtrakcjaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Atrakcja.objects.all()
    serializer_class = AtrakcjaSerializer

class CennikViewSet(viewsets.ModelViewSet):
    queryset = Cennik.objects.all()
    serializer_class = CennikSerializer
