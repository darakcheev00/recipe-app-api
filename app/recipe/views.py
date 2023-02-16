"""
Views for the recipes apis
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe
from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe api's"""

    serializer_class = serializers.RecipeSerializer
    querset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    # need to be authenticated to use api's

    def get_query_set(self):
        """Retrieve recipes for authed user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

