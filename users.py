from typing import Optional, Dict, Any

USERS: Dict[int, Dict[str, Any]] = {
    696461653: {
        "name": "polyanakw",
        "sheet_tab": "Поля",
    },
    156994725: {
        "name": "KseniiaTsarik",
        "sheet_tab": "Ксюша",
    },
    396411418: {
        "name": "Marina_Marynych",
        "sheet_tab": "Марина",
    },
    591402904: {
        "name": "Molyya94",
        "sheet_tab": "Оля",
    },
    364129678: {
        "name": "sergeypevniy",
        "sheet_tab": "Сергій Певний",
    },
}


def get_user_config(telegram_user_id: int) -> Optional[Dict[str, Any]]:
    return USERS.get(int(telegram_user_id))


# Slack member ID -> config. A user who isn't listed gets their ID from the bot
# in the thread; add it here. Tab names refer to the 2027 spreadsheet.
SLACK_USERS: Dict[str, Dict[str, Any]] = {
    "U08986YDASJ": {"name": "polyanakw", "sheet_tab": "Поля"},
    "U07JY98C63B": {"name": "KseniiaTsarik", "sheet_tab": "Ксюша"},
    "U0603QMDX5Z": {"name": "Marina_Marynych", "sheet_tab": "Марина"},
    "U098804L10T": {"name": "Molyya94", "sheet_tab": "Оля"},
    "U04BJSMTP9Q": {"name": "sergeypevniy", "sheet_tab": "Сергій П."},
}


def get_slack_user_config(slack_user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not slack_user_id:
        return None
    return SLACK_USERS.get(slack_user_id)
