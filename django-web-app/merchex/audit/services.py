from .models import AuditLog


def log_action(*, merchant, actor, action, entity, summary, before=None, after=None):
    return AuditLog.objects.create(
        merchant=merchant,
        actor=actor,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(entity.pk),
        summary=summary,
        before=before,
        after=after,
    )
