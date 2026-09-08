from pathlib import Path

import pytest

from lazyllm.tools.writer.provider import (
    FeishuWriterProvider,
    GitHubWriterProvider,
    NotionWriterProvider,
    WeChatWriterProvider,
    WriterProviderBase,
    WriterProviderCapabilityError,
)
from lazyllm.tools.writer.tools.resource_tools import WriterResourceTools


def test_optional_provider_capabilities_default_to_unsupported():
    assert WriterProviderBase.capabilities.model_dump() == {
        'load': False,
        'create': False,
        'replace': False,
        'append': False,
        'patch': False,
        'revision_check': False,
        'media': False,
    }


@pytest.mark.parametrize(
    ('provider_class', 'expected'),
    [
        (FeishuWriterProvider, {**dict.fromkeys(
            ('load', 'create', 'replace', 'append', 'patch', 'revision_check', 'media'), True,
        )}),
        (NotionWriterProvider, {**dict.fromkeys(
            ('load', 'create', 'replace', 'append', 'patch', 'revision_check', 'media'), True,
        )}),
        (GitHubWriterProvider, {
            'load': True, 'create': True, 'replace': True, 'append': True,
            'patch': False, 'revision_check': True, 'media': True,
        }),
        (WeChatWriterProvider, {
            'load': True, 'create': True, 'replace': True, 'append': False,
            'patch': True, 'revision_check': True, 'media': True,
        }),
    ],
)
def test_builtin_providers_declare_tested_capabilities(provider_class, expected):
    assert provider_class.capabilities.model_dump() == expected


def test_resource_create_requires_explicit_provider(tmp_path: Path):
    with pytest.raises(ValueError, match='adapter is required'):
        WriterResourceTools(artifact_store=str(tmp_path)).create_document('Document')


def test_resource_operation_rejects_unsupported_capability_before_provider_call(tmp_path: Path):
    with pytest.raises(WriterProviderCapabilityError) as captured:
        WriterResourceTools(artifact_store=str(tmp_path)).append_to_document(
            '# Document',
            {'adapter': 'wechat', 'doc_id': 'draft-1'},
        )

    assert captured.value.code == 'PROVIDER_CAPABILITY_UNSUPPORTED'
    assert captured.value.provider == 'wechat'
    assert captured.value.capability == 'append'
    assert captured.value.retryable is False
