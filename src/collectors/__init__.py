"""
Pacote de Conectores Reais e Neutralidade Lexical da Fase 02.
"""

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
)
from src.collectors.youtube_collector import YouTubeOfficialCollector
from src.collectors.telegram_collector import TelegramPublicChannelCollector

__all__ = [
    "BaseLexicallyNeutralCollector",
    "RawCollectedManifestation",
    "YouTubeOfficialCollector",
    "TelegramPublicChannelCollector",
]
