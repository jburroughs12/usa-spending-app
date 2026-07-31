"""Reference configuration for federal contract search filters."""

SET_ASIDE_TYPES = [
    {"code": "SDVOSB", "name": "Service-Disabled Veteran-Owned Small Business"},
    {"code": "WOSB", "name": "Women-Owned Small Business"},
    {"code": "8A", "name": "8(a) Program"},
    {"code": "HUBZONE", "name": "HUBZone"},
    {"code": "SB", "name": "Small Business"},
]

SET_ASIDE_RECIPIENT_TYPES = {
    "SDVOSB": ["service_disabled_veterans_owned_business"],
    "8A": ["8a_program_participant"],
    "WOSB": ["women_owned_small_business"],
    "HUBZONE": ["historically_underutilized_business_zone"],
    "SB": ["small_business", "other_than_small_business"],
}
