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

# Default NAICS codes relevant to MRO/industrial distribution and safety/PPE product lines
NAICS_DESCRIPTIONS = {
    "423840": "Industrial Supplies Merchant Wholesalers",
    "423610": "Electrical Apparatus & Wiring Supplies Merchant Wholesalers",
    "423710": "Hardware Merchant Wholesalers",
    "423720": "Plumbing & Heating Equipment Merchant Wholesalers",
    "423830": "Industrial Machinery & Equipment Merchant Wholesalers",
    "423850": "Service Establishment Equipment Merchant Wholesalers",
    "423450": "Medical, Dental & Hospital Equipment Merchant Wholesalers",
    "339113": "Surgical Appliance & Supplies Manufacturing (Safety/PPE)",
    "332510": "Hardware Manufacturing",
    "561210": "Facilities Support Services",
    "811310": "Commercial & Industrial Machinery Repair",
    "238290": "Other Building Equipment Contractors",
    "315990": "Apparel Accessories & Other Apparel Manufacturing (Protective)",
    "424690": "Other Chemical & Allied Products Merchant Wholesalers",
    "423990": "Other Miscellaneous Durable Goods Merchant Wholesalers",
}

DEFAULT_NAICS_CODES = list(NAICS_DESCRIPTIONS.keys())

# Authorized small-business federal resellers (partner network), with their
# self-reported set-aside/socioeconomic certifications.
RESELLER_PARTNERS = [
    {"name": "ADA Supplies", "website": "adasupply.com", "set_asides": ["WOSB", "DBE"]},
    {"name": "Aviate Enterprises, Inc.", "website": "aviateinc.com", "set_asides": ["SDVOSB", "HUBZONE"]},
    {"name": "BahFed", "website": "bahfed.com", "set_asides": ["SDVOSB", "DBE", "HUBZONE", "8A"]},
    {"name": "Black Box Safety", "website": "blackboxsafety.com", "set_asides": ["SDVOSB"]},
    {"name": "Document Imaging Dimensions, Inc.", "website": "fssibpa.com", "set_asides": ["SB"]},
    {"name": "Eastern Power Technologies", "website": "easternpowertech.com", "set_asides": ["WOSB"]},
    {"name": "Green Ramp Group", "website": "greenrampgroup.com", "set_asides": ["SDVOSB"]},
    {"name": "The Jahnda Group", "website": "jahnda.com", "set_asides": ["SDVOSB", "8A", "DBE"]},
    {"name": "Premier and Companies", "website": "premiersupplies.com", "set_asides": ["SB"]},
    {"name": "SPS Industrial, Inc.", "website": "spsindustrial.com", "set_asides": ["SDVOSB"]},
    {"name": "Supply Chimp", "website": "supplychimp.com", "set_asides": ["SB"]},
    {"name": "United Commercial Supply", "website": "ucs-supply.com", "set_asides": ["SDVOSB"]},
    {"name": "WECsys, LLC", "website": "wecsysllc.com", "set_asides": ["WOSB"]},
    {"name": "Wrigglesworth Enterprises, Inc.", "website": "wesourceusa.com", "set_asides": ["WOSB"]},
]
