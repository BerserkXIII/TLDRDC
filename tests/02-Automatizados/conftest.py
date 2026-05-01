# ════════════════════════════════════════════════════════════════════
# TALLER DE TESTS TLDRDC — FIXTURES COMPARTIDAS
# ════════════════════════════════════════════════════════════════════
"""
Fixtures reutilizables para todos los tests unitarios.

Transferida desde QA_project/tests/02-Automatizados/
Adaptada para TLDRDC/tests/02-Automatizados/

Uso en tus tests:
    def test_ejemplo(personaje_base, estado_test):
        # personaje_base y estado_test ya están inyectados
        personaje_base["vida"] = 5
        assert personaje_base["vida"] == 5
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from collections import deque
import sys
import os

# Setup sys.path to import from code/TLDRDC_Prueba1
# From tests/02-Automatizados/ → ../../code/ (TLDRDC root/code)
_tests_dir = os.path.dirname(os.path.dirname(__file__))
_root_dir = os.path.dirname(_tests_dir)
_code_dir = os.path.join(_root_dir, "code")
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

# ════════════════════════════════════════════════════════════════════
# PERSONAJE FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def personaje_base():
    """Personaje estándar para tests. Modificable por cada test."""
    return {
        "nombre": "TestPlayer",
        "vida": 10,
        "vida_max": 25,
        "pociones": 6,
        "pociones_max": 10,
        "fuerza": 5,
        "destreza": 5,
        "armadura": 2,
        "armadura_max": 5,
        "nivel": 1,
        "armas": {},
        # Campos secretos (ver ESPECIFICACION_TLDRDC_CORE.md C2.5)
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
def personaje_vivo(personaje_base):
    """Personaje con vida máxima."""
    p = personaje_base.copy()
    p["vida"] = p["vida_max"]
    return p

@pytest.fixture
def personaje_bajo_vida(personaje_base):
    """Personaje con vida crítica."""
    p = personaje_base.copy()
    p["vida"] = 2
    return p

@pytest.fixture
def personaje_muerto(personaje_base):
    """Personaje KO (vida 0)."""
    p = personaje_base.copy()
    p["vida"] = 0
    return p

# ════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def estado_test():
    """Estado global del juego para tests."""
    return {
        "armas_jugador": {},
        "ruta_jugador": [],
        "eventos_superados": 0,
        "veces_guardado": 0,
        "_c01": 0,
        "bolsa_eventos": list(range(1, 21)),
        "bolsa_exploracion": list(range(1, 16)),
        "pasos_nivel2": [],
        "pasos_secretos": [],
    }

@pytest.fixture
def estado_con_armas(estado_test):
    """Estado con algunas armas ya equipadas."""
    estado_test["armas_jugador"] = {
        "daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"},
        "espada": {"daño": 3, "golpe": 85, "tipo": "pesada"},
    }
    return estado_test

@pytest.fixture
def estado_bolsa_vacia(estado_test):
    """Estado con bolsas de eventos y exploración vacías."""
    estado_test["bolsa_eventos"] = []
    estado_test["bolsa_exploracion"] = []
    return estado_test

# ════════════════════════════════════════════════════════════════════
# ARMAS FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def armas_global():
    """Base de datos de armas disponibles."""
    return {
        "daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"},
        "espada": {"daño": 3, "golpe": 85, "tipo": "pesada"},
        "martillo": {"daño": 5, "golpe": 75, "stun": 3, "tipo": "pesada"},
        "porra": {"daño": 3, "golpe": 80, "sangrado": 1, "stun": 2},
        "maza": {"daño": 7, "golpe": 70, "stun": 4, "tipo": "pesada"},
        "lanza": {"daño": 5, "golpe": 80, "sangrado": 1, "tipo": "sutil"},
        "estoque": {"daño": 4, "golpe": 80, "sangrado": 2, "tipo": "sutil"},
        "cimitarra": {"daño": 5, "golpe": 75, "tipo": "mixta"},
        "Mano de Dios": {"daño": 2, "golpe": 75, "vida": 1, "sangrado": 2, "stun": 3, "tipo": "mixta"},
        "Hoz de Sangre": {"daño": 5, "golpe": 85, "vida": 1, "sangrado": 1, "tipo": "mixta"},
        "Hoja de la Noche": {"daño": 8, "golpe": 75, "vida": 2, "stun": 1, "tipo": "mixta"},
        "Hacha Maldita": {"daño": 7, "golpe": 75, "tipo": "pesada", "auto_daño": 1},
    }

# ════════════════════════════════════════════════════════════════════
# MOCK FIXTURES (Funciones narrativas)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_narrar():
    """Mock para narrar() — emitir texto narrativo."""
    return Mock(return_value=None)

@pytest.fixture
def mock_alerta():
    """Mock para alerta() — emitir advertencia."""
    return Mock(return_value=None)

@pytest.fixture
def mock_exito():
    """Mock para exito() — emitir mensaje de recompensa."""
    return Mock(return_value=None)

@pytest.fixture
def mock_sistema():
    """Mock para sistema() — emitir evento de sistema."""
    return Mock(return_value=None)

@pytest.fixture
def mock_preguntar():
    """Mock para preguntar() — emitir pregunta."""
    return Mock(return_value=None)

@pytest.fixture
def mock_leer_input():
    """Mock para leer_input() — recibir input del jugador."""
    return Mock(return_value="test_input")

@pytest.fixture
def mock_combate():
    """Mock para combate() — simular encuentro."""
    return Mock(return_value=None)

@pytest.fixture
def mock_enemigo_aleatorio():
    """Mock para enemigo_aleatorio() — generar enemigo."""
    def _mock_enemigo(nombre=None):
        return {
            "nombre": nombre or "Enemigo Test",
            "vida": 10,
            "vida_max": 10,
            "daño": [2, 5],
            "armadura": 0,
            "habilidades": [],
        }
    return Mock(side_effect=_mock_enemigo)

@pytest.fixture
def mock_fin_derrota():
    """Mock para fin_derrota() — activar derrota."""
    return Mock(return_value=None)

@pytest.fixture
def mock_random_choice():
    """Mock para random.choice() — selecciona un elemento de lista."""
    return Mock(return_value=None)

@pytest.fixture
def mock_random_choices():
    """Mock para random.choices() — selecciona múltiples elementos."""
    return Mock(return_value=None)

# ════════════════════════════════════════════════════════════════════
# REACTIVE FIXTURES (Observer pattern)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def personaje_reactivo(personaje_base):
    """Personaje con soporte para observadores (Observer pattern)."""
    class Personaje(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._watchers = {}
            self.activo = False
        
        def observe(self, field, callback):
            self._watchers[field] = callback
        
        def __setitem__(self, key, value):
            if self.get(key) != value:
                super().__setitem__(key, value)
                if self.activo and key in self._watchers:
                    self._watchers[key](value)
    
    p = Personaje(personaje_base)
    p.activo = True
    return p

# ════════════════════════════════════════════════════════════════════
# FILE FIXTURES (Persistencia)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_save_dir(tmp_path):
    """Directorio temporal para guardar partidas."""
    save_dir = tmp_path / "TLDRDC"
    save_dir.mkdir()
    return save_dir

@pytest.fixture
def save_file(tmp_save_dir):
    """Ruta a archivo de guardado temporal."""
    return tmp_save_dir / "guardado.json"

# ════════════════════════════════════════════════════════════════════
# THREADING FIXTURES
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def bridge_mock():
    """Mock simple de _Bridge para tests sin threading real."""
    class _BridgeMock:
        def __init__(self):
            self._valor = ""
        
        def esperar(self):
            return self._valor
        
        def recibir(self, texto):
            self._valor = texto
    
    return _BridgeMock()

# ════════════════════════════════════════════════════════════════════
# IMAGEN FIXTURES (UI Manager)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_png(tmp_path):
    """Crea PNG válido 100x100 rojo para tests."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        png_path = tmp_path / "test_valid.png"
        img.save(png_path)
        return str(png_path)
    except ImportError:
        # Si PIL no disponible, crear un archivo PNG manualmente
        # PNG header + minimal valid PNG structure
        png_path = tmp_path / "test_valid.png"
        with open(png_path, "wb") as f:
            # Escribir PNG mínimo válido (100x100)
            f.write(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d'
                b'\x08\x02\x00\x00\x00\xf6\x18\xff\xa0\x00\x00\x00\x19tEXtSoftware'
                b'\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x1dIDATx\xdab\xf0\xcf\xc0'
                b'\x00\x00\x03\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
        return str(png_path)

@pytest.fixture
def corrupt_png(tmp_path):
    """Crea archivo PNG corrupto para tests de error."""
    png_path = tmp_path / "corrupt.png"
    with open(png_path, "wb") as f:
        # PNG header válido pero data corrupta
        f.write(b"\x89PNG\r\n\x1a\n" + b"INVALID_CORRUPTED_DATA")
    return str(png_path)

# ════════════════════════════════════════════════════════════════════
# COMPOSITE FIXTURES (Todo junto)
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def game_context(personaje_base, estado_test, armas_global, 
                 mock_narrar, mock_alerta, mock_exito, mock_sistema,
                 mock_leer_input, mock_combate):
    """Contexto completo: personaje + estado + mocks inyectados."""
    return {
        "personaje": personaje_base,
        "estado": estado_test,
        "armas": armas_global,
        "mocks": {
            "narrar": mock_narrar,
            "alerta": mock_alerta,
            "exito": mock_exito,
            "sistema": mock_sistema,
            "leer_input": mock_leer_input,
            "combate": mock_combate,
        }
    }

# ════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════

def assert_personaje_valido(p):
    """Helper: verifica que personaje tenga campos requeridos."""
    requeridos = {"nombre", "vida", "vida_max", "fuerza", "destreza", "pociones", "nivel"}
    assert requeridos.issubset(p.keys()), f"Faltan campos: {requeridos - set(p.keys())}"
    assert p["vida"] <= p["vida_max"], "vida > vida_max"
    assert p["vida"] >= 0, "vida < 0"

def assert_stats_en_rango(p, min_val=1, max_val=20):
    """Helper: verifica que stats estén en rango."""
    for stat in ("fuerza", "destreza", "inteligencia"):
        if stat in p:
            assert min_val <= p[stat] <= max_val, f"{stat} fuera de rango"

# ════════════════════════════════════════════════════════════════════
# RE-EXPORTAR FIXTURES DE CONFTEST_COMBATE
# ════════════════════════════════════════════════════════════════════
# Los tests de combate necesitan fixtures combate-específicas
# (personaje_combate, enemigo_combate, estado_global_combate, etc.)
from conftest_combate import *  # noqa: F401, F403
