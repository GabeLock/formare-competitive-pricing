from __future__ import annotations

import os


def get_user_agent() -> str:
    contact = os.getenv("FORMARE_BOT_CONTACT_EMAIL", "configure-contato@formare.local")
    return (
        "FormarePriceIntelligenceBot/1.0 "
        f"(ethical public price monitoring; contact: {contact})"
    )

