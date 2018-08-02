from api import serializers

def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': serializers.UserSerializer(user, context={'request': request}).data
    }