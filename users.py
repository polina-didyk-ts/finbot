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
