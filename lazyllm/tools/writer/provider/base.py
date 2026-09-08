from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..data_models.multimodal import MediaAssetLibrary
from ..data_models.revision import PatchSet
from ..data_models.task import InputResource, TargetDocument
from ..data_models.writer_ir import WriterDocument, WriterStage


WriterProviderCapability = Literal[
    'load', 'create', 'replace', 'append', 'patch', 'revision_check', 'media',
]


class WriterProviderCapabilities(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    load: bool = False
    create: bool = False
    replace: bool = False
    append: bool = False
    patch: bool = False
    revision_check: bool = False
    media: bool = False


class WriterProviderCapabilityError(RuntimeError):
    code = 'PROVIDER_CAPABILITY_UNSUPPORTED'
    retryable = False

    def __init__(self, provider: str, capability: WriterProviderCapability):
        self.provider = provider
        self.capability = capability
        super().__init__(provider, capability)

    def __str__(self) -> str:
        return f'Writer provider {self.provider!r} does not support {self.capability!r}.'


class WriterProviderBase(ABC):
    '''Read and persist Writer content through one external document provider.'''

    provider: str = ''
    capabilities = WriterProviderCapabilities()

    def __init__(self, adapters=None):
        self.adapters = adapters or {}

    def require_capability(self, capability: WriterProviderCapability) -> None:
        if not getattr(self.capabilities, capability):
            raise WriterProviderCapabilityError(
                self.provider or type(self).__name__, capability,
            )

    @classmethod
    @abstractmethod
    def matches(cls, locator: str) -> bool:
        '''Return whether locator belongs to this provider.'''
        raise NotImplementedError

    @abstractmethod
    def resolve(self, locator: str) -> TargetDocument:
        '''Convert a provider locator into the existing target document model.'''
        raise NotImplementedError

    @abstractmethod
    def load_document(
        self,
        target: TargetDocument,
        *,
        stage: WriterStage = 'final',
    ) -> dict:
        '''Load a provider document and return its existing Writer representation.'''
        raise NotImplementedError

    def create_document(self, title: str, parent_uri: str = '') -> TargetDocument:
        '''Create an empty provider document.'''
        raise NotImplementedError(
            f'{self.provider or type(self).__name__} does not support create_document().')

    def document_image_resources(
        self,
        document: WriterDocument,
    ) -> tuple[list[InputResource], list[str]]:
        '''Return provider image resources and non-fatal discovery warnings.'''
        return [], []

    def download_document_image(
        self,
        document: WriterDocument,
        resource: InputResource,
    ) -> bytes | None:
        '''Return provider image bytes, or defer ordinary URIs to shared loading.'''
        # None delegates ordinary file/HTTP resources to the shared materializer.
        return None

    @abstractmethod
    def replace_document(
        self,
        content: WriterDocument | str,
        target: TargetDocument,
        *,
        media_assets: MediaAssetLibrary | None = None,
    ) -> dict:
        '''Replace an existing provider document.'''
        raise NotImplementedError

    def append_document(
        self,
        content: WriterDocument | str,
        target: TargetDocument,
        *,
        media_assets: MediaAssetLibrary | None = None,
    ) -> dict:
        '''Append content to an existing provider document.'''
        raise NotImplementedError(
            f'{self.provider or type(self).__name__} does not support append_document().')

    def apply_patch_to_document(
        self,
        patch_set: PatchSet,
        source_document: WriterDocument,
        target: TargetDocument,
        *,
        media_assets: MediaAssetLibrary | None = None,
    ) -> dict:
        '''Apply a structured patch to an existing provider document.'''
        raise NotImplementedError(
            f'{self.provider or type(self).__name__} does not support structured patches.')


__all__ = [
    'WriterProviderBase',
    'WriterProviderCapabilities',
    'WriterProviderCapability',
    'WriterProviderCapabilityError',
]
