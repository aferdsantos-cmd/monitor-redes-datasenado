"""
Pacote de Conectores Reais, Neutralidade Lexical e Orquestração Multi-Plataforma (Fases 02 e 03).
"""

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    BUILTIN_EXTENDED_THEMES,
    RawCollectedManifestation,
    enrich_settings_with_dynamic_themes,
    register_custom_theme,
)
from src.collectors.daily_radar_collector import (
    DailyLegislativeRadarCollector,
    DailyTopicRadarItem,
    SENATE_COMMITTEES_LEXICON,
)
from src.collectors.instagram_facebook_collector import (
    MetaInstagramFacebookCollector,
    fix_meta_mojibake_utf8,
)
from src.collectors.phase02_medallion_pipeline import Phase02MedallionOrchestrator
from src.collectors.phase03_six_platforms_orchestrator import (
    MonitoringWindowSpec,
    Phase03SixPlatformsOrchestrator,
    filter_manifestations_by_spec,
    VALID_PLATFORMS,
)
from src.collectors.telegram_collector import TelegramPublicChannelCollector
from src.collectors.tiktok_collector import TikTokResearchCollector
from src.collectors.whatsapp_collector import WhatsAppPublicGroupsExportCollector
from src.collectors.x_twitter_collector import XTwitterCollector
from src.collectors.youtube_collector import YouTubeOfficialCollector

__all__ = [
    "BaseLexicallyNeutralCollector",
    "BUILTIN_EXTENDED_THEMES",
    "RawCollectedManifestation",
    "enrich_settings_with_dynamic_themes",
    "register_custom_theme",
    "YouTubeOfficialCollector",
    "TelegramPublicChannelCollector",
    "XTwitterCollector",
    "MetaInstagramFacebookCollector",
    "fix_meta_mojibake_utf8",
    "TikTokResearchCollector",
    "WhatsAppPublicGroupsExportCollector",
    "DailyLegislativeRadarCollector",
    "DailyTopicRadarItem",
    "SENATE_COMMITTEES_LEXICON",
    "MonitoringWindowSpec",
    "filter_manifestations_by_spec",
    "VALID_PLATFORMS",
    "Phase02MedallionOrchestrator",
    "Phase03SixPlatformsOrchestrator",
]
