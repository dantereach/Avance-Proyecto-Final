"""
Tests para el protocolo de mensajes.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.message_protocol import (
    create_request,
    create_response,
    create_heartbeat,
    create_announcement,
    serialize_message,
    deserialize_message,
    validate_request,
    validate_response,
    MessageType,
    CommandType,
    ResponseStatus
)


class TestMessageProtocol:
    """Tests para el protocolo de mensajes."""

    def test_create_request(self):
        """Test de creación de request."""
        request = create_request(CommandType.LIST_PROCESSES, {'param': 'value'})
        
        assert request['type'] == MessageType.REQUEST
        assert request['command'] == CommandType.LIST_PROCESSES
        assert request['params'] == {'param': 'value'}
        assert 'timestamp' in request

    def test_create_response_success(self):
        """Test de creación de response exitosa."""
        response = create_response(
            ResponseStatus.SUCCESS,
            data={'result': 'ok'},
            message='Success'
        )
        
        assert response['type'] == MessageType.RESPONSE
        assert response['status'] == ResponseStatus.SUCCESS
        assert response['data'] == {'result': 'ok'}
        assert response['message'] == 'Success'
        assert 'timestamp' in response

    def test_create_response_error(self):
        """Test de creación de response de error."""
        response = create_response(
            ResponseStatus.ERROR,
            error='Something went wrong'
        )
        
        assert response['status'] == ResponseStatus.ERROR
        assert response['error'] == 'Something went wrong'

    def test_create_heartbeat(self):
        """Test de creación de heartbeat."""
        heartbeat = create_heartbeat('server-123', {'load': 0.5})
        
        assert heartbeat['type'] == MessageType.HEARTBEAT
        assert heartbeat['server_id'] == 'server-123'
        assert heartbeat['metadata'] == {'load': 0.5}

    def test_create_announcement(self):
        """Test de creación de announcement."""
        announcement = create_announcement(
            'server-123',
            'localhost',
            9000,
            {'version': '1.0'}
        )
        
        assert announcement['type'] == MessageType.ANNOUNCEMENT
        assert announcement['server_id'] == 'server-123'
        assert announcement['host'] == 'localhost'
        assert announcement['port'] == 9000

    def test_serialize_deserialize(self):
        """Test de serialización y deserialización."""
        original = create_request(CommandType.PING)
        
        # Serializar
        data = serialize_message(original)
        assert isinstance(data, bytes)
        
        # Deserializar
        deserialized = deserialize_message(data)
        
        assert deserialized['type'] == original['type']
        assert deserialized['command'] == original['command']

    def test_validate_request_valid(self):
        """Test de validación de request válido."""
        request = create_request(CommandType.PING)
        assert validate_request(request) is True

    def test_validate_request_invalid(self):
        """Test de validación de request inválido."""
        invalid = {'type': 'request'}  # Falta command, params, timestamp
        assert validate_request(invalid) is False

    def test_validate_response_valid(self):
        """Test de validación de response válido."""
        response = create_response(ResponseStatus.SUCCESS)
        assert validate_response(response) is True

    def test_validate_response_invalid(self):
        """Test de validación de response inválido."""
        invalid = {'type': 'response'}  # Falta status, timestamp
        assert validate_response(invalid) is False

    def test_serialize_invalid(self):
        """Test de serialización de mensaje inválido."""
        # Objeto no serializable
        invalid = {'data': lambda x: x}
        
        with pytest.raises(ValueError):
            serialize_message(invalid)

    def test_deserialize_invalid(self):
        """Test de deserialización de datos inválidos."""
        invalid_data = b'not json'
        
        with pytest.raises(ValueError):
            deserialize_message(invalid_data)
