from enum import Enum


LENGTH_NAME_ORGANIZATION = 200
LENGTH_EMAIL = 100
LENGTH_NAME_USER = 100
LENGTH_PHONE = 30
LENGTH_TITLE_DEAL = 200
LENGTH_TITLE_TASK = 200


class MemberRole(str, Enum):
    """Роли участников организации."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class Permission(str, Enum):
    """Права доступа по сущностям."""

    ALL_PERMISSIONS = "all_permissions"

    # Организация
    READ_ORGANIZATION = "read_organization"
    WRITE_ORGANIZATION = "write_organization"

    # Настройки организации
    READ_ORG_SETTINGS = "read_org_settings"
    WRITE_ORG_SETTINGS = "write_org_settings"

    # Контакты
    READ_CONTACT = "read_contact"
    WRITE_CONTACT = "write_contact"

    # Сделки
    READ_DEAL = "read_deal"
    WRITE_DEAL = "write_deal"

    # Задачи
    READ_TASK = "read_task"
    WRITE_TASK = "write_task"

    # Активности
    READ_ACTIVITY = "read_activity"
    WRITE_ACTIVITY = "write_activity"


class Currency(str, Enum):
    """Валюты."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"


class StatusDeal(str, Enum):
    """Статусы сделки."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"

    def get_activity_change(
        self,
        new_status: "StatusDeal"
    ) -> tuple[str, dict]:
        """
        Определяет, какой тип активности создавать при изменении статуса.
        Возвращает (activity_type, payload)
        """
        payload = {"old_status": self.value, "new_status": new_status.value}

        if new_status in [StatusDeal.WON, StatusDeal.LOST]:
            return ("system", {**payload, "message": "Deal closed"})
        else:
            return ("status_change", payload)


class StageDeal(str, Enum):
    """Стадии сделки."""

    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED = "closed"

    def get_activity_change(
        self,
        new_stage: "StageDeal"
    ) -> tuple[str, dict]:
        payload = {"old_stage": self.value, "new_stage": new_stage.value}

        if new_stage == StageDeal.CLOSED:
            return ("system", {**payload, "message": "Stage closed"})
        else:
            return ("stage_change", payload)


class ActivityType(str, Enum):
    """Типы активности."""

    COMMENT = "comment"
    STATUS_CHANGE = "status_change"
    STAGE_CHANGE = "stage_change"
    TASK_CREATED = "task_created"
    SYSTEM = "system"
