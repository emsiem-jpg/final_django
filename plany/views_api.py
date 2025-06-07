from rest_framework import viewsets
from .models import PlanZwiedzania 
from .serializers import PlanSerializer

class PlanViewSet(viewsets.ModelViewSet):
    queryset = PlanZwiedzania.objects.all()
    serializer_class = PlanSerializer
