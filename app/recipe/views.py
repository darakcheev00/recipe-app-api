"""
Views for the recipes apis
"""

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import (
    viewsets,
    mixins
)

from core.models import (
    Recipe, 
    Tag
)

from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe api's"""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    # need to be authenticated to use api's

    def get_queryset(self):
        """Retrieve recipes for authed user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')


    def get_serializer_class(self):
        # returns reference to the class
        """Return the serializer class for request"""
        # list is show all
        if self.action == 'list':
            return serializers.RecipeSerializer
        
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        # when we perfrom creation of a new object through this viewset, call this method too
        serializer.save(user=self.request.user)

# due to crud:
class TagViewSet(mixins.UpdateModelMixin,
                mixins.DestroyModelMixin,
                mixins.ListModelMixin, 
                viewsets.GenericViewSet):
    """Manage tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authed user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    