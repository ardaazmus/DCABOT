"""Bounded, rule-based explanations over existing read-only projections.

This module describes already-authoritative statuses and outcomes. It does not
recalculate economics, create actions, or change the state that it explains.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol


MAX_EXPLANATION_ITEMS = 1_024


class _ActionLike(Protocol):
    bar_index: int
    role: str


class _HistoricalResultLike(Protocol):
    execution_status: str
    application_code: str | None
    position_status: str
    actions: tuple[_ActionLike, ...]
    summary: dict[str, object]


class _ReplayResultLike(Protocol):
    outcomes: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class ReadOnlyExplanation:
    """One deterministic explanation with no economic authority fields."""

    code: str
    severity: str
    title: str
    message: str
    source: str
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", MappingProxyType(dict(self.context)))


_HISTORICAL_STATUS = {
    "COMPLETED": ReadOnlyExplanation(
        code="HISTORICAL_COMPLETED",
        severity="INFO",
        title="Tarihsel koşu tamamlandı",
        message="Backend sonucu doğrulanmış kapalı bar kapsamı için üretildi; bu açıklama yeni hesap yapmaz.",
        source="execution_status",
    ),
    "INDETERMINATE": ReadOnlyExplanation(
        code="HISTORICAL_INDETERMINATE",
        severity="WARNING",
        title="Tarihsel koşu tamamlanmadı",
        message="Backend sonucu belirsiz olarak işaretledi; final ekonomik sonuç iddiası üretilmiyor.",
        source="execution_status",
    ),
}

_REPLAY_OUTCOME = {
    "ACCEPTED": ("INFO", "Gözlem kabul edildi", "Public gözlem replay sınırında kabul edildi."),
    "DUPLICATE": ("INFO", "Tekrarlı gözlem", "Aynı gözlem daha önce kabul edildiği için yeniden uygulanmadı."),
    "CONFLICT": ("ERROR", "Çakışan gözlem", "Aynı kimlik için farklı içerik görüldü; fail-closed sınır uygulandı."),
    "OUT_OF_ORDER": ("WARNING", "Sıra dışı gözlem", "Gözlem event zamanı sırasıyla uyumlu olmadığı için kabul edilmedi."),
    "SEQUENCE_GAP": ("WARNING", "Gözlem aralığında boşluk", "Gözlem akışında süreksizlik görüldü; ekonomik geçiş yapılmadı."),
    "STALE": ("WARNING", "Gözlem akışı güncel değil", "Stale sınırı nedeniyle gözlem kabul edilmedi."),
    "RESYNC_REQUIRED": ("WARNING", "Yeniden eşitleme gerekli", "Replay devam etmeden önce açık bir resync gerekir."),
    "WRONG_SCOPE": ("ERROR", "Kapsam dışı gözlem", "Gözlem kaynak, ürün veya stream kapsamıyla eşleşmedi."),
    "MISSING_SEQUENCE": ("ERROR", "Sıra bilgisi eksik", "Gerekli kaynak sıra bilgisi bulunmadığı için gözlem kabul edilmedi."),
    "CAPACITY_EXCEEDED": ("ERROR", "Kapasite sınırı aşıldı", "Bounded replay kapasitesi aşıldığı için yeni gözlem kabul edilmedi."),
    "FAILED": ("ERROR", "Public gözlem akışı başarısız", "Akış fail-closed durumda; yeni ekonomik veya canlı işlem iddiası yok."),
}


def explain_historical_result(result: _HistoricalResultLike) -> tuple[ReadOnlyExplanation, ...]:
    """Explain an existing historical result without reading its economics."""

    _validate_historical_result(result)
    explanations = [_HISTORICAL_STATUS[result.execution_status]]
    if result.application_code == "AMBIGUOUS_OHLC_PATH":
        explanations.append(
            ReadOnlyExplanation(
                code="AMBIGUOUS_OHLC_PATH",
                severity="WARNING",
                title="OHLC içi sıra kesin değil",
                message="Aynı bar içinde birden fazla geçerli olay sırası olabileceği için backend final commit üretmedi.",
                source="application_code",
            )
        )
    for index, action in enumerate(result.actions):
        explanations.append(
            ReadOnlyExplanation(
                code="ACTION_RECORDED",
                severity="INFO",
                title="Backend aksiyonu kaydedildi",
                message="Bu kayıt backend sonucundaki mevcut action snapshot’ını açıklar; yeni fill veya hesap üretmez.",
                source=f"actions[{index}]",
                context={"bar_index": action.bar_index, "role": action.role},
            )
        )
    if result.position_status == "OPEN_AT_END":
        explanations.append(
            ReadOnlyExplanation(
                code="POSITION_OPEN_AT_END",
                severity="WARNING",
                title="Pozisyon dönem sonunda açık",
                message="Backend pozisyonu açık bıraktı; bu projection forced close veya kapanış hesabı eklemez.",
                source="position_status",
            )
        )
    funding_status = _result_status(result, "funding_status")
    mark_status = _result_status(result, "mark_status")
    if funding_status != "NOT_MODELED" or mark_status != "NOT_AVAILABLE":
        raise ValueError("Bu projection yalnız mevcut tarihsel sınır durumlarını açıklar.")
    explanations.extend(
        (
            ReadOnlyExplanation(
                code="FUNDING_NOT_MODELED",
                severity="WARNING",
                title="Funding modellenmedi",
                message="Mevcut backend sonucu funding hesabı içermez; açıklama bunu değiştirmez.",
                source="funding_status",
            ),
            ReadOnlyExplanation(
                code="MARK_NOT_AVAILABLE",
                severity="WARNING",
                title="Exchange mark mevcut değil",
                message="Mevcut backend sonucu exchange mark verisi içermez; açıklama unrealized değer üretmez.",
                source="mark_status",
            ),
        )
    )
    return tuple(explanations)


def explain_public_replay(result: _ReplayResultLike) -> tuple[ReadOnlyExplanation, ...]:
    """Explain bounded public replay outcomes without live or economic claims."""

    if not isinstance(result.outcomes, tuple) or len(result.outcomes) > MAX_EXPLANATION_ITEMS:
        raise ValueError("Public replay outcome kapsamı geçersiz.")
    explanations: list[ReadOnlyExplanation] = []
    for index, outcome in enumerate(result.outcomes):
        value = getattr(outcome, "value", None)
        if value not in _REPLAY_OUTCOME:
            raise ValueError("Bilinmeyen public replay outcome açıklanamaz.")
        severity, title, message = _REPLAY_OUTCOME[value]
        explanations.append(
            ReadOnlyExplanation(
                code=f"OBSERVATION_{value}",
                severity=severity,
                title=title,
                message=message,
                source=f"outcomes[{index}]",
                context={"outcome_index": index},
            )
        )
    return tuple(explanations)


def _validate_historical_result(result: _HistoricalResultLike) -> None:
    if result.execution_status not in _HISTORICAL_STATUS:
        raise ValueError("Bilinmeyen historical execution status açıklanamaz.")
    if result.application_code not in {None, "AMBIGUOUS_OHLC_PATH"}:
        raise ValueError("Bilinmeyen historical application code açıklanamaz.")
    if result.execution_status == "COMPLETED" and result.application_code is not None:
        raise ValueError("Tamamlanmış sonuç belirsizlik application code’u taşıyamaz.")
    if result.position_status not in {"CLOSED", "OPEN_AT_END"}:
        raise ValueError("Bilinmeyen position status açıklanamaz.")
    funding_status = _result_status(result, "funding_status")
    mark_status = _result_status(result, "mark_status")
    if funding_status != "NOT_MODELED" or mark_status != "NOT_AVAILABLE":
        raise ValueError("Bu projection yalnız mevcut tarihsel sınır durumlarını açıklar.")
    if not isinstance(result.actions, tuple) or len(result.actions) > MAX_EXPLANATION_ITEMS:
        raise ValueError("Historical action kapsamı geçersiz.")
    for action in result.actions:
        if type(action.bar_index) is not int or action.bar_index < 1:
            raise ValueError("Historical action bar index geçersiz.")
        if not isinstance(action.role, str) or not action.role or len(action.role) > 128:
            raise ValueError("Historical action role geçersiz.")


def _result_status(result: _HistoricalResultLike, name: str) -> object:
    value = getattr(result, name, None)
    if value is not None:
        return value
    summary = getattr(result, "summary", None)
    if not isinstance(summary, dict):
        raise ValueError("Historical result status kaynağı geçersiz.")
    value = summary.get(name)
    if value is not None:
        return value
    if summary.get("model") == "historical_ohlcv_partial_fixed_v1":
        fixed_status = {
            "funding_status": "NOT_MODELED",
            "mark_status": "NOT_AVAILABLE",
        }
        if name in fixed_status:
            return fixed_status[name]
    raise ValueError("Historical result status kaynağı eksik.")
