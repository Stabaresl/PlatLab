from dataclasses import dataclass

import pytest

from modules.shared.domain.base_entity import BaseEntity
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher


def test_base_entity_equality_by_id():
    entity_a = BaseEntity()
    entity_b = BaseEntity(id=entity_a.id)
    assert entity_a == entity_b


def test_domain_event_generates_id_and_timestamp():
    @dataclass(frozen=True, kw_only=True)
    class SampleEvent(DomainEvent):
        payload: str

    event = SampleEvent(payload="x")
    assert event.event_id is not None
    assert event.occurred_at is not None


def test_event_dispatcher_calls_registered_listener():
    @dataclass(frozen=True, kw_only=True)
    class SampleEvent(DomainEvent):
        payload: str

    dispatcher = EventDispatcher()
    received = []
    dispatcher.subscribe(SampleEvent, lambda e: received.append(e.payload))

    dispatcher.dispatch(SampleEvent(payload="hola"))

    assert received == ["hola"]


def test_validation_error_has_expected_code():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("dato invalido")

    assert exc_info.value.code == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_django_orm_is_reachable():
    """Confirma que pytest-django puede crear la BD de test y consultar el ORM."""
    from django.contrib.auth.models import User

    assert User.objects.count() == 0
    User.objects.create(username="smoke_test_user")
    assert User.objects.count() == 1
