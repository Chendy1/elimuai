"""Roles and the permission matrix. Code is the source of truth (ADR 0007); the `roles` table
mirrors the role names and a test keeps the two in sync."""

STUDENT = "student"
GUARDIAN = "guardian"
TEACHER = "teacher"
CURRICULUM_ADMIN = "curriculum_admin"
CONTENT_REVIEWER = "content_reviewer"
INSTITUTIONAL_PARTNER = "institutional_partner"
SUPER_ADMIN = "super_admin"

ALL_ROLES: tuple[str, ...] = (
    STUDENT,
    GUARDIAN,
    TEACHER,
    CURRICULUM_ADMIN,
    CONTENT_REVIEWER,
    INSTITUTIONAL_PARTNER,
    SUPER_ADMIN,
)

P_LEARNING_USE = "learning:use"
P_LEARNERS_MANAGE_OWN = "learners:manage_own"
P_CLASSES_MANAGE = "classes:manage"
P_ASSESSMENTS_CREATE = "assessments:create"
P_CURRICULUM_MANAGE = "curriculum:manage"
P_CONTENT_REVIEW = "content:review"
P_CONTENT_PUBLISH = "content:publish"
P_REPORTS_AGGREGATE_READ = "reports:aggregate:read"
P_INSTITUTIONS_MANAGE = "institutions:manage"
P_AI_CONFIGURE = "ai:configure"
P_USERS_READ = "users:read"
P_USERS_MANAGE_ROLES = "users:manage_roles"
P_AUDIT_READ = "audit:read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        P_LEARNING_USE,
        P_LEARNERS_MANAGE_OWN,
        P_CLASSES_MANAGE,
        P_ASSESSMENTS_CREATE,
        P_CURRICULUM_MANAGE,
        P_CONTENT_REVIEW,
        P_CONTENT_PUBLISH,
        P_REPORTS_AGGREGATE_READ,
        P_INSTITUTIONS_MANAGE,
        P_AI_CONFIGURE,
        P_USERS_READ,
        P_USERS_MANAGE_ROLES,
        P_AUDIT_READ,
    }
)

# Permissions that mean "act on my own things". Only the matching role grants them; being a
# super administrator does not make someone a guardian or a student.
OWN_SCOPED_PERMISSIONS: frozenset[str] = frozenset({P_LEARNING_USE, P_LEARNERS_MANAGE_OWN})

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    STUDENT: frozenset({P_LEARNING_USE}),
    GUARDIAN: frozenset({P_LEARNERS_MANAGE_OWN}),
    TEACHER: frozenset({P_CLASSES_MANAGE, P_ASSESSMENTS_CREATE}),
    CURRICULUM_ADMIN: frozenset({P_CURRICULUM_MANAGE, P_CONTENT_REVIEW, P_CONTENT_PUBLISH}),
    CONTENT_REVIEWER: frozenset({P_CONTENT_REVIEW}),
    # Aggregate, anonymised reporting only. Never individual learner data.
    INSTITUTIONAL_PARTNER: frozenset({P_REPORTS_AGGREGATE_READ}),
    SUPER_ADMIN: ALL_PERMISSIONS - OWN_SCOPED_PERMISSIONS,
}


def permissions_for(role: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(roles: list[str] | tuple[str, ...], permission: str) -> bool:
    return any(permission in permissions_for(r) for r in roles)
