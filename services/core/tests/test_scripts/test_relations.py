"""Tests of the report of model relations between modules."""

from typing import Any, Final

from django.apps.registry import Apps
from django.db import models

from scripts.relations import RelationReport

_CARE: Final = 'server.apps.care'
_ACCOUNTS: Final = 'server.apps.accounts'
_LABEL: Final = 'care'


def _model(registry: Apps, name: str, label: str, **fields: Any) -> type:
    """Declares a model of the app with the given label in a registry."""
    meta = type('Meta', (), {'app_label': label, 'apps': registry})
    return type(
        name,
        (models.Model,),
        {'__module__': f'{_CARE}.models', 'Meta': meta, **fields},
    )


def test_reports_relation_to_another_module() -> None:
    registry = Apps([_CARE, _ACCOUNTS])
    post = _model(registry, 'Post', _LABEL)
    _model(
        registry,
        'Line',
        'accounts',
        post=models.ForeignKey(post, on_delete=models.CASCADE),
    )

    problems = list(RelationReport(registry).problems())

    assert problems == ['accounts.Line.post refers to care.Post']


def test_accepts_relations_inside_a_module() -> None:
    registry = Apps([_CARE])
    post = _model(registry, 'Post', _LABEL)
    _model(
        registry,
        'Comment',
        _LABEL,
        post=models.ForeignKey(post, on_delete=models.CASCADE),
    )

    problems = list(RelationReport(registry).problems())

    assert not problems


def test_accepts_framework_relations_to_modules() -> None:
    registry = Apps([_CARE, 'django.contrib.admin'])
    post = _model(registry, 'Post', _LABEL)
    _model(
        registry,
        'Entry',
        'admin',
        post=models.ForeignKey(post, on_delete=models.CASCADE),
    )

    problems = list(RelationReport(registry).problems())

    assert not problems
