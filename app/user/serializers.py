"""
Serializers for the user API View
"""

from django.contrib.auth import (
    get_user_model,
    authenticate,
)
from django.utils.translation import gettext as _


from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user project"""

    # json -> validate -> python object or model

    # tell django rest the model and fields
    class Meta:
        # which model am i representing
        model = get_user_model()
        # list of fields that are provided by the request
        fields = ['email','password','name']
        # extra meta data about the fields listed above
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    # override create method so that data is validated (min length), Raises validation error
    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    # intance = model insatnce that is being udpated
    # validated _data= data that is passed through the serializer validatioin
    def update(self, instance, validated_data):
        """Update and return user"""
        # remove password from the dictionary, default None
        password = validated_data.pop('password', None)
        # calls update method on the update user baseclass (existing method)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type':'password'},
        trim_whitespace = False,
    )

    # override validate method
    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')
        # django auth function
        user = authenticate(
            request = self.context.get('request'),
            username = email,
            password = password,
        )
        # if user did not get set
        if not user:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


