"""Pydantic schemas for the P2S MVP 0 data contract."""

from p2s_core.models.asset_plan import (
    AssetPlanBundle,
    AssetPlanQualityReport,
    RenderPlan,
    SceneAssetPlan,
    TTSPlan,
    VisualAssetPlan,
)
from p2s_core.models.claim import PaperClaim
from p2s_core.models.common import EvidenceSpan, SuggestedFix, VisualIdentityProfile
from p2s_core.models.extraction_result import ClaimExtractionResult, ClaimReviewBundle
from p2s_core.models.extraction import (
    EvidenceMatchReport,
    EvidenceMatchReportBundle,
    ExtractedFigure,
    ExtractedSection,
    ExtractedTable,
    ExtractionQualityReport,
    RealPaperSmokeReport,
)
from p2s_core.models.paper import ExtractedPaper, PaperChunk, PaperSection
from p2s_core.models.persona import PersonaProfile, VRMProfile, VoiceProfile
from p2s_core.models.presentation import (
    NarrativeArcItem,
    NarrativePlan,
    PresentationPlan,
    PresentationProfile,
    PresentationReviewBundle,
    PresentationScene,
    ScenesBundle,
)
from p2s_core.models.project_state import (
    CodeVersion,
    STAGE_NAMES,
    ExtractionState,
    ProjectSettings,
    ProjectSource,
    ProjectState,
    StageState,
    default_stages,
)
from p2s_core.models.review import GateDecision, ReviewResult
from p2s_core.models.rewrite import SceneRewritePatch, SceneRewriteResult
from p2s_core.models.scene import (
    AssetPolicy,
    AssetTypeHint,
    BackgroundMode,
    PresenterMode,
    Scene,
    SceneDraft,
    VisualFocus,
    VisualType,
    VoiceDirection,
    visual_type_values,
)
from p2s_core.models.style import StyleProfile

__all__ = [
    "AssetPlanBundle",
    "AssetPlanQualityReport",
    "EvidenceSpan",
    "EvidenceMatchReport",
    "EvidenceMatchReportBundle",
    "ExtractionState",
    "ExtractedFigure",
    "ExtractedPaper",
    "ExtractedSection",
    "ExtractedTable",
    "ExtractionQualityReport",
    "GateDecision",
    "ClaimExtractionResult",
    "ClaimReviewBundle",
    "CodeVersion",
    "PaperChunk",
    "PaperClaim",
    "PaperSection",
    "NarrativeArcItem",
    "NarrativePlan",
    "PersonaProfile",
    "PresentationPlan",
    "PresentationProfile",
    "PresentationReviewBundle",
    "PresentationScene",
    "ProjectSettings",
    "ProjectSource",
    "ProjectState",
    "ReviewResult",
    "RealPaperSmokeReport",
    "RenderPlan",
    "STAGE_NAMES",
    "Scene",
    "SceneAssetPlan",
    "SceneDraft",
    "ScenesBundle",
    "SceneRewritePatch",
    "SceneRewriteResult",
    "StageState",
    "StyleProfile",
    "SuggestedFix",
    "TTSPlan",
    "AssetPolicy",
    "AssetTypeHint",
    "BackgroundMode",
    "PresenterMode",
    "VRMProfile",
    "VisualFocus",
    "VisualIdentityProfile",
    "VisualAssetPlan",
    "VisualType",
    "VoiceDirection",
    "VoiceProfile",
    "default_stages",
    "visual_type_values",
]
