from __future__ import annotations

from enum import StrEnum


class QualityGrade(StrEnum):
    """整图级图纸质量分级。只表示图纸本身的质量，不代表结果可以免核。"""

    CLEAR = "清晰"
    AVERAGE = "一般"
    POOR = "差"


QUALITY_GRADE_DISCLAIMER = "图纸质量分级只表示图纸本身的质量，不代表结果可以免核。"
LOW_QUALITY_MARK_TEXT = "低质量图，结果不可靠"
ASSEMBLY_OUT_OF_SCOPE_TEXT = "装配图、爆炸图不在处理范围。请上传单个零件的零件图。"
POOR_GRADE_ADVISE_TEXT = (
    "这张零件图的图纸质量分级为「差」，系统不会自动预填，建议走人工看图，"
    "以免给出看起来很自信的错结果。若你确信这张图可读，可以显式选择仍然继续；"
    "该结果将永久携带「低质量图，结果不可靠」标记。"
)
