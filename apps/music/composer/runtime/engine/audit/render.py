from .report import AuditReport


def render_report(report: AuditReport) -> str:
    return "\n".join(str(r) for r in report.iter_records())
