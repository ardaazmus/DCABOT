"""Read-only why-no-trade explanation over local snapshots (F39).

Aggregates already-decided verdicts (bot pair scope, paper session, deal
status) into human reasons. It never opens positions, never overrides a
verdict, and never invents data — unknown inputs stay UNKNOWN.
"""
_TERMINAL_DEAL_STATUS = frozenset({"COMPLETED", "ABORTED", "FAILED"})


def explain_risk(
    *,
    pair_verdict: tuple[str, str] | None = None,
    paper: dict[str, object] | None = None,
    paper_requested: bool = False,
    deal: dict[str, object] | None = None,
    deal_requested: bool = False,
) -> dict[str, object]:
    """Explain whether a trade is currently blocked and why not."""
    reasons: list[dict[str, str]] = []
    if pair_verdict is not None:
        verdict, detail = pair_verdict
        if verdict == "ALLOWED":
            reasons.append({
                "code": "PAIR_ALLOWED",
                "severity": "INFO",
                "message": f"Pair serbest: {detail}.",
            })
        elif verdict == "BLOCKED_BLACKLIST":
            reasons.append({
                "code": "PAIR_BLOCKED",
                "severity": "BLOCKER",
                "message": f"Pair blacklistte, işlem açılmaz: {detail}.",
            })
        elif verdict == "NOT_IN_SCOPE":
            reasons.append({
                "code": "PAIR_OUT_OF_SCOPE",
                "severity": "BLOCKER",
                "message": f"Pair bot kapsamında değil: {detail}.",
            })
        else:
            reasons.append({
                "code": "PAIR_UNKNOWN",
                "severity": "BLOCKER",
                "message": "Pair kararı bilinmiyor; güvenli tarafta kalınıyor.",
            })
    if paper is not None:
        reasons.append({
            "code": "SESSION_ACTIVE",
            "severity": "INFO",
            "message": (
                f"Paper session {paper.get('session_id')} aktif "
                f"(nakit {paper.get('cash')})."
            ),
        })
    elif paper_requested:
        reasons.append({
            "code": "SESSION_UNKNOWN",
            "severity": "BLOCKER",
            "message": "Paper session bulunamadı; işlem açılamaz.",
        })
    if deal is not None:
        status = deal.get("status")
        if status in _TERMINAL_DEAL_STATUS:
            reasons.append({
                "code": "DEAL_TERMINAL",
                "severity": "WARNING",
                "message": f"Deal {status}; yeni olay eklenemez.",
            })
        else:
            reasons.append({
                "code": "DEAL_OPEN",
                "severity": "INFO",
                "message": f"Deal açık ({status}).",
            })
    elif deal_requested:
        reasons.append({
            "code": "DEAL_UNKNOWN",
            "severity": "BLOCKER",
            "message": "Deal bulunamadı; işlem açılamaz.",
        })
    if not reasons:
        reasons.append({
            "code": "NO_INPUT",
            "severity": "INFO",
            "message": "Açıklama için session, bot+symbol veya deal verin.",
        })
    return {
        "blocked": any(reason["severity"] == "BLOCKER" for reason in reasons),
        "reasons": reasons,
    }
