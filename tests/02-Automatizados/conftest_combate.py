# ════════════════════════════════════════════════════════════════════
# FIXTURES ESPECÍFICAS PARA TESTS DE COMBATE
# ════════════════════════════════════════════════════════════════════
"""
Fixtures compartidas SOLO para tests de combate (COMBATE_JUGADOR, COMBATE_ENEMIGO, COMBATE_LOOP).

Transferida desde QA_project/tests/02-Automatizados/
Adaptada para TLDRDC/tests/02-Automatizados/

Evita contaminar conftest.py (raíz) manteniendo fixtures combate-específicas aquí.
pytest descubre este conftest automáticamente en esta carpeta.

Uso en tus tests:
    def test_ejemplo(personaje_combate, enemigo_combate, estado_global_combate):
        # Fixtures ya inyectadas y mockadas
        ...
"""

import pytest
from unittest.mock import Mock, patch

# ════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL FIXTURES (Combate-específico)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def estado_global_combate():
    """Estado global completo para combate, con armas y sistema cargado."""
    return {
        "armas_jugador": {
            "daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"},
            "espada": {"daño": 3, "golpe": 85, "tipo": "pesada"},
            "martillo": {"daño": 5, "golpe": 75, "stun": 3, "tipo": "pesada"},
            "cimitarra": {"daño": 5, "golpe": 75, "tipo": "mixta"},
        },
        "ruta_jugador": [],
        "eventos_superados": 0,
        "veces_guardado": 0,
        "_c01": 0,
        "bolsa_eventos": list(range(1, 21)),
        "bolsa_exploracion": list(range(1, 16)),
        "pasos_nivel2": [],
        "pasos_secretos": [],
    }


# ════════════════════════════════════════════════════════════════════
# PERSONAJE COMBATE FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def personaje_combate(estado_global_combate):
    """Personaje configurado para combate (con armas, stats balanceados)."""
    return {
        "nombre": "jugador",
        "vida": 10,
        "vida_max": 25,
        "fuerza": 5,
        "destreza": 5,
        "pociones": 6,
        "pociones_max": 10,
        "armadura": 2,
        "armadura_max": 5,
        "armas": estado_global_combate["armas_jugador"].copy(),
        "_huyo_combate": False,
        "_efectos_temporales": {},
        "stun": 0,
        # Campos secretos para integridad
        "moscas": 0,
        "brazos": 0,
        "sombra": 0,
        "sangre": 0,
        "_pw": 0,
        "tiene_llave": False,
        "rencor": False,
        "hitos_brazos_reclamados": [],
        "evento_brazos_final_completado": False,
        "evento_brazos_segundo_completado": False,
        "bolsa_acecho": [1, 2, 3],
        "_x9f": False,
    }


@pytest.fixture
def personaje_combate_bajo_vida(personaje_combate):
    """Personaje combate con vida crítica."""
    p = personaje_combate.copy()
    p["vida"] = 2
    return p


@pytest.fixture
def personaje_combate_agil():
    """Personaje con destreza máxima (fuerza mínima)."""
    return {
        "nombre": "agil",
        "vida": 10,
        "vida_max": 25,
        "fuerza": 1,
        "destreza": 20,
        "pociones": 6,
        "pociones_max": 10,
        "armadura": 2,
        "armadura_max": 5,
        "armas": {"daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"}},
        "_huyo_combate": False,
        "_efectos_temporales": {},
        "stun": 0,
    }


@pytest.fixture
def personaje_combate_fuerte():
    """Personaje con fuerza máxima (destreza mínima)."""
    return {
        "nombre": "fuerte",
        "vida": 10,
        "vida_max": 25,
        "fuerza": 20,
        "destreza": 1,
        "pociones": 6,
        "pociones_max": 10,
        "armadura": 2,
        "armadura_max": 5,
        "armas": {"martillo": {"daño": 5, "golpe": 75, "stun": 3, "tipo": "pesada"}},
        "_huyo_combate": False,
        "_efectos_temporales": {},
        "stun": 0,
    }


# ════════════════════════════════════════════════════════════════════
# ENEMIGO COMBATE FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def enemigo_combate():
    """Enemigo estándar para combate."""
    return {
        "nombre": "Larvas de Sangre",
        "vida": 10,
        "vida_max": 10,
        "daño": (1, 2),
        "esquiva": 17,
        "jefe": False,
        "armadura": 0,
        "stun": 0,
        "sangrado": 0,
        "habilidades": [],
        "_efectos_temporales": {},
    }


@pytest.fixture
def enemigo_jefe():
    """Jefe para combate (vida alta, habilidades)."""
    return {
        "nombre": "Forrix",
        "vida": 30,
        "vida_max": 30,
        "daño": (3, 8),
        "esquiva": 20,
        "jefe": True,
        "armadura": 2,
        "stun": 0,
        "sangrado": 0,
        "habilidades": ["reducir_armadura", "damage_boost"],
        "_efectos_temporales": {},
    }


@pytest.fixture
def enemigo_debil():
    """Enemigo débil para combate (baja vida)."""
    return {
        "nombre": "Rata",
        "vida": 3,
        "vida_max": 3,
        "daño": (1, 1),
        "esquiva": 10,
        "jefe": False,
        "armadura": 0,
        "stun": 0,
        "sangrado": 0,
        "habilidades": [],
        "_efectos_temporales": {},
    }


# ════════════════════════════════════════════════════════════════════
# MOCKS COMBATE-ESPECÍFICOS
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_emitir():
    """Mock para emitir() — enviar eventos UI."""
    return Mock(return_value=None)


@pytest.fixture
def mock_leer_input_combate():
    """Mock para leer_input() — lectura de acción en combate."""
    return Mock(return_value="daga")


@pytest.fixture
def mock_pedir_input():
    """Mock para pedir_input() — entrada bruta."""
    return Mock(return_value="test")


@pytest.fixture
def mock_random_randint():
    """Mock para random.randint() — rolls de combate."""
    return Mock(return_value=100)


# NOTA: mock_alerta y mock_sistema ya están en conftest.py (raíz)
# Los tests de combate inyectan esas fixtures automáticamente desde conftest.py


# ════════════════════════════════════════════════════════════════════
# PATCHES COMBINADOS (Reducen boilerplate en tests)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def patches_combate_basico(mock_emitir, mock_sistema, mock_alerta):
    """Patch básico: emitir, sistema, alerta ya mockados."""
    with patch('TLDRDC_Prueba1.emitir', mock_emitir), \
         patch('TLDRDC_Prueba1.sistema', mock_sistema), \
         patch('TLDRDC_Prueba1.alerta', mock_alerta):
        yield {
            "emitir": mock_emitir,
            "sistema": mock_sistema,
            "alerta": mock_alerta,
        }


@pytest.fixture
def patches_combate_completo(mock_emitir, mock_sistema, mock_alerta, 
                              mock_leer_input_combate, mock_pedir_input, mock_random_randint):
    """Patch completo: todos los mocks para turno_jugador."""
    with patch('TLDRDC_Prueba1.emitir', mock_emitir), \
         patch('TLDRDC_Prueba1.sistema', mock_sistema), \
         patch('TLDRDC_Prueba1.alerta', mock_alerta), \
         patch('TLDRDC_Prueba1.leer_input', mock_leer_input_combate), \
         patch('TLDRDC_Prueba1.pedir_input', mock_pedir_input), \
         patch('TLDRDC_Prueba1.random.randint', mock_random_randint):
        yield {
            "emitir": mock_emitir,
            "sistema": mock_sistema,
            "alerta": mock_alerta,
            "leer_input": mock_leer_input_combate,
            "pedir_input": mock_pedir_input,
            "randint": mock_random_randint,
        }
