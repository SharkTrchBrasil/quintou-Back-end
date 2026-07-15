WIZARD_STEPS_CONFIG = {
    "SPACE": {
        "steps": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "step_3_fields": ["max_guests", "size_length", "size_width", "is_outdoor", "has_restroom", "is_ada_friendly"],
        "step_4_rules": ["allows_parties", "allows_smoking", "allows_pets", "allows_children", "allows_alcohol", "allows_loud_music", "allows_commercial"],
        "pricing_modes": ["PER_HOUR", "PER_DAY"],
    },
    "EQUIPMENT": {
        "steps": [0, 1, 2, 3, 6, 7, 8],  # Skip 4 (rules) e 5 (amenities)
        "step_3_fields": ["max_guests", "delivery_available", "delivery_fee", "delivery_radius_km"],
        "step_4_rules": [],
        "pricing_modes": ["PER_DAY", "FIXED"],
    },
    "SERVICE": {
        "steps": [0, 1, 2, 3, 6, 7, 8],  # Skip 4 (rules) e 5 (amenities)
        "step_2_mode": "service_area",  # Modo especial: área de atuação em vez de endereço fixo
        "step_3_fields": ["years_experience", "portfolio_url", "service_area_description"],
        "step_4_rules": [],
        "pricing_modes": ["PER_HOUR", "FIXED"],
    },
    "VEHICLE": {
        "steps": [0, 1, 2, 3, 4, 5, 6, 7, 8],  # Todos os steps, mas adaptados
        "step_3_fields": ["max_guests", "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_length_ft", "engine_hp", "has_captain", "requires_license", "embark_location"],
        "step_4_rules": ["allows_alcohol", "allows_smoking", "allows_children", "allows_pets", "allows_loud_music"],
        "pricing_modes": ["PER_HOUR", "PER_DAY"],
    },
}

WIZARD_LABELS = {
    "SPACE": {
        "step_1_title": "Dê um nome ao seu espaço",
        "step_2_title": "Onde fica o seu espaço?",
        "step_3_title": "Detalhes do espaço",
        "step_6_title": "Fotos do espaço",
        "step_8_price_label": "Valor por hora ou diária",
    },
    "EQUIPMENT": {
        "step_1_title": "Dê um nome ao seu equipamento",
        "step_2_title": "Qual é a sua localização?",
        "step_3_title": "Detalhes do equipamento",
        "step_6_title": "Fotos do equipamento",
        "step_8_price_label": "Valor da diária ou pacote",
    },
    "SERVICE": {
        "step_1_title": "Descreva o seu serviço",
        "step_2_title": "Onde você atende?",
        "step_3_title": "Sobre o seu serviço",
        "step_6_title": "Portfolio e fotos",
        "step_8_price_label": "Valor por hora ou pacote",
    },
    "VEHICLE": {
        "step_1_title": "Descreva a sua embarcação",
        "step_2_title": "Onde fica a embarcação?",
        "step_3_title": "Especificações",
        "step_6_title": "Fotos da embarcação",
        "step_8_price_label": "Valor por hora ou diária",
    },
}
