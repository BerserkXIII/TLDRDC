"""
Test Suite: PERSISTENCIA (guardar_partida, cargar_partida)

Especificación: TLDRDC_for_testing/especificaciones/ESPECIFICACION_PERSISTENCIA.md
Total tests: 15 (P1.1-P1.6, P2.1-P2.8, P3.1)

Guía de lectura: docs/Workshop/PROCESO_ESPECIFICACION_A_TESTS.md
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

# Setup sys.path para importar desde TLDRDC_for_testing/ (raíz del proyecto)
test_dir = Path(__file__).parent.parent.parent
code_dir = test_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import funciones a testear (se mockearán en conftest)
try:
    from TLDRDC_Prueba1 import guardar_partida, cargar_partida
except ImportError:
    # Fallback si falla import directo
    guardar_partida = Mock()
    cargar_partida = Mock()


# ==============================================================================
# FIXTURES COMPARTIDAS
# ==============================================================================

@pytest.fixture
def personaje_test():
    """Personaje mínimo válido para persistencia"""
    return {
        "nombre": "TestPlayer",
        "vida": 10,
        "fuerza": 5,
        "destreza": 5,
        "armadura": 0,
        "pociones": 6,
        "nivel": 1,
        "armas": {"daga": {"daño": 2, "tipo": "sutil"}},
    }


@pytest.fixture
def estado_test(personaje_test):
    """Estado global mínimo válido"""
    return {
        "personaje": personaje_test.copy(),
        "armas_jugador": {"daga": {"daño": 2, "tipo": "sutil"}},
        "ruta_jugador": [],
        "eventos_superados": 0,
        "bolsa_eventos": [1, 2, 3],
        "bolsa_exploracion": [],
        "pasos_nivel2": [],
        "pasos_secretos": [],
        "veces_guardado": 0,
        "_c01": 5,
    }


@pytest.fixture
def tmp_save_dir(tmp_path):
    """Directorio temporal para guardados (mock de AppData/TLDRDC)"""
    save_dir = tmp_path / "TLDRDC"
    save_dir.mkdir()
    return save_dir


@pytest.fixture
def mock_alerta():
    """Mock de función alerta() para validar llamadas"""
    with patch('TLDRDC_Prueba1.alerta') as mock:
        yield mock


# ==============================================================================
# TESTS: guardar_partida() [P1.1 - P1.6]
# ==============================================================================

class TestGuardarPartida:
    """Suite P1.x: Función guardar_partida(personaje)"""

    def test_P1_1_guardar_partida_exitosa(self, personaje_test, estado_test, tmp_save_dir, mock_alerta):
        """
        Spec: P1.1 - Guardar partida exitosa
        
        Valida que:
        - Archivo guardado.json se crea
        - JSON es válido (parseable)
        - Contiene el nombre del personaje
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    
                    # ACT
                    guardar_partida(personaje_test)
                    
                    # ASSERT
                    assert ruta_guardado.exists(), "Archivo guardado.json no existe"
                    
                    # Validar JSON
                    with open(ruta_guardado, "r", encoding="utf-8") as f:
                        data = json.load(f)  # Si falla, JSON inválido
                    
                    assert data["personaje"]["nombre"] == "TestPlayer"
                    mock_alerta.assert_not_called()

    def test_P1_2_json_contiene_estado_global_completo(self, personaje_test, estado_test, tmp_save_dir):
        """
        Spec: P1.2 - JSON contiene estado global COMPLETO
        
        Valida que el JSON guardado contiene TODOS estos 10 campos:
        - personaje, armas_jugador, ruta_jugador, eventos_superados
        - bolsa_eventos, bolsa_exploracion, pasos_nivel2, pasos_secretos
        - veces_guardado, _c01
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    
                    # ACT
                    guardar_partida(personaje_test)
                    
                    # ASSERT
                    with open(ruta_guardado, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    campos_requeridos = {
                        "personaje", "armas_jugador", "ruta_jugador", "eventos_superados",
                        "bolsa_eventos", "bolsa_exploracion", "pasos_nivel2", "pasos_secretos",
                        "veces_guardado", "_c01"
                    }
                    assert campos_requeridos.issubset(data.keys()), \
                        f"Faltan campos: {campos_requeridos - set(data.keys())}"

    def test_P1_3_integridad_de_datos(self, tmp_save_dir, estado_test):
        """
        Spec: P1.3 - Integridad de datos (valores correctos)
        
        Valida que los valores guardados coinciden exactamente con los entrada
        """
        # ARRANGE
        personaje = {
            "nombre": "TestPlayer",
            "vida": 15,
            "fuerza": 7,
            "destreza": 3,
            "armadura": 2,
            "pociones": 4,
            "nivel": 2,
            "armas": {"daga": {"daño": 2, "tipo": "sutil"}, "maza": {"daño": 5, "tipo": "pesada"}},
        }
        estado_test["personaje"] = personaje
        ruta_guardado = tmp_save_dir / "guardado.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    
                    # ACT
                    guardar_partida(personaje)
                    
                    # ASSERT
                    with open(ruta_guardado, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    assert data["personaje"]["vida"] == 15
                    assert data["personaje"]["fuerza"] == 7
                    assert data["personaje"]["destreza"] == 3
                    assert data["personaje"]["armas"]["maza"]["daño"] == 5

    def test_P1_4_fichero_temporal_se_limpia(self, personaje_test, estado_test, tmp_save_dir):
        """
        Spec: P1.4 - Fichero temporal se elimina tras éxito (atomic write)
        
        Valida que:
        - guardado_tmp.json se crea durante proceso
        - Pero desaparece después (reemplazado atómicamente)
        - guardado.json final existe y es válido
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        ruta_temp = tmp_save_dir / "guardado_tmp.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    
                    # ACT
                    guardar_partida(personaje_test)
                    
                    # ASSERT
                    assert ruta_guardado.exists(), "guardado.json no existe"
                    assert not ruta_temp.exists(), "guardado_tmp.json aún existe (no se limpió)"
                    
                    # Validar que guardado.json es válido
                    with open(ruta_guardado, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    assert len(data) > 0

    def test_P1_5_encriptacion_utf8(self, personaje_test, estado_test, tmp_save_dir):
        """
        Spec: P1.5 - Archivo guardado con encoding UTF-8
        
        Valida que caracteres especiales (acentos, caracteres latinos) se guardan correctamente
        """
        # ARRANGE
        personaje_utf8 = personaje_test.copy()
        personaje_utf8["nombre"] = "Jugador_Español"  # Ñ representa encoding UTF-8
        ruta_guardado = tmp_save_dir / "guardado.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    
                    # ACT
                    guardar_partida(personaje_utf8)
                    
                    # ASSERT
                    with open(ruta_guardado, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    assert data["personaje"]["nombre"] == "Jugador_Español"

    def test_P1_6_error_emite_alerta_sin_crash(self, personaje_test, estado_test, mock_alerta):
        """
        Spec: P1.6 - Error durante escritura emite alerta sin crash
        
        Valida que si algo falla (IOError), se captura y emite alerta,
        sin lanzar excepción no capturada
        """
        # ARRANGE
        # Mock open() para forzar IOError
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                
                # ACT (no debe lanzar excepción)
                try:
                    guardar_partida(personaje_test)
                    guardó_sin_crash = True
                except Exception as e:
                    guardó_sin_crash = False
                    excepcion = e
                
                # ASSERT
                assert guardó_sin_crash, f"Excepción no capturada: {excepcion if 'excepcion' in locals() else 'Unknown'}"
                mock_alerta.assert_called()  # alerta() debe ser llamado
                assert "Error al guardar" in str(mock_alerta.call_args) or "error" in str(mock_alerta.call_args).lower()


# ==============================================================================
# TESTS: cargar_partida() [P2.1 - P2.8]
# ==============================================================================

class TestCargarPartida:
    """Suite P2.x: Función cargar_partida()"""

    def test_P2_1_cargar_partida_exitosa(self, personaje_test, estado_test, tmp_save_dir):
        """
        Spec: P2.1 - Cargar partida exitosa
        
        Valida que:
        - Retorna dict personaje
        - Contiene campos esperados
        - No es None
        """
        # ARRANGE: crear archivo guardado válido
        ruta_guardado = tmp_save_dir / "guardado.json"
        datos_guardados = {
            "personaje": personaje_test,
            "armas_jugador": estado_test["armas_jugador"],
            "ruta_jugador": estado_test["ruta_jugador"],
            "eventos_superados": 0,
            "bolsa_eventos": [1, 2, 3],
            "bolsa_exploracion": [],
            "pasos_nivel2": [],
            "pasos_secretos": [],
            "veces_guardado": 0,
            "_c01": 5,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            with patch.dict('TLDRDC_Prueba1.estado', clear=True):
                
                # ACT
                personaje_cargado = cargar_partida()
                
                # ASSERT
                assert personaje_cargado is not None
                assert isinstance(personaje_cargado, dict)
                assert personaje_cargado["nombre"] == "TestPlayer"
                assert personaje_cargado["vida"] == 10

    def test_P2_2_restaura_estado_global_completo(self, personaje_test, estado_test, tmp_save_dir):
        """
        Spec: P2.2 - Restaura estado global COMPLETO
        
        Valida que todos los campos de estado se restauran correctamente
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        datos_guardados = {
            "personaje": personaje_test,
            "armas_jugador": {"daga": {"daño": 2}},
            "ruta_jugador": ["n", "s", "e"],
            "eventos_superados": 15,
            "bolsa_eventos": [1, 5, 8],
            "bolsa_exploracion": ["text1", "text2"],
            "pasos_nivel2": ["d", "i"],
            "pasos_secretos": ["secret1"],
            "veces_guardado": 3,
            "_c01": 42,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        estado_mock = {}
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            with patch.dict('TLDRDC_Prueba1.estado', estado_mock, clear=True):
                
                # ACT
                cargar_partida()
                
                # ASSERT: verificar que estado fue restaurado
                import TLDRDC_Prueba1
                assert TLDRDC_Prueba1.estado["_c01"] == 42
                assert TLDRDC_Prueba1.estado["eventos_superados"] == 15
                assert TLDRDC_Prueba1.estado["bolsa_eventos"] == [1, 5, 8]
                assert TLDRDC_Prueba1.estado["pasos_nivel2"] == ["d", "i"]
                assert TLDRDC_Prueba1.estado["veces_guardado"] == 3

    def test_P2_3_archivo_no_existe_retorna_none(self, tmp_save_dir, mock_alerta):
        """
        Spec: P2.3 - Archivo no existe → retorna None
        
        Valida que si no hay guardado.json, retorna None y emite alerta
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        assert not ruta_guardado.exists(), "Archivo no debería existir"
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            
            # ACT
            resultado = cargar_partida()
            
            # ASSERT
            assert resultado is None
            mock_alerta.assert_called()
            assert "No hay partida" in str(mock_alerta.call_args) or "no existe" in str(mock_alerta.call_args).lower()

    def test_P2_4_migracion_eventos_superados_lista_a_int(self, personaje_test, tmp_save_dir):
        """
        Spec: P2.4 - Migración: eventos_superados lista → int (backward compatibility)
        
        Valida que si guardado antiguo (pre-v0.6) tiene eventos_superados como lista,
        se convierte a int 0 sin crash
        """
        # ARRANGE: guardado antiguo con eventos_superados como lista
        ruta_guardado = tmp_save_dir / "guardado.json"
        datos_guardados = {
            "personaje": personaje_test,
            "armas_jugador": {},
            "ruta_jugador": [],
            "eventos_superados": [1, 2, 3],  # LISTA, no int (formato antiguo)
            "bolsa_eventos": [],
            "bolsa_exploracion": [],
            "pasos_nivel2": [],
            "pasos_secretos": [],
            "veces_guardado": 0,
            "_c01": 0,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            with patch.dict('TLDRDC_Prueba1.estado', clear=True):
                
                # ACT (no debe crash)
                resultado = cargar_partida()
                
                # ASSERT
                assert resultado is not None, "Cargó con éxito"
                import TLDRDC_Prueba1
                assert isinstance(TLDRDC_Prueba1.estado["eventos_superados"], int)
                assert TLDRDC_Prueba1.estado["eventos_superados"] == 0

    def test_P2_5_json_corrupto_emite_alerta(self, tmp_save_dir, mock_alerta):
        """
        Spec: P2.5 - JSON corrupto → retorna None + alerta
        
        Valida que si JSON es inválido, se captura JSONDecodeError
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            f.write("{vida: 10}")  # JSON inválido (sin comillas)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            
            # ACT
            resultado = cargar_partida()
            
            # ASSERT
            assert resultado is None
            mock_alerta.assert_called()

    def test_P2_6_campos_requeridos_ausentes(self, tmp_save_dir, mock_alerta):
        """
        Spec: P2.6 - Campos requeridos ausentes
        
        Valida que si falta campo requerido (ej: "vida"), retorna None
        """
        # ARRANGE: personaje sin "vida"
        ruta_guardado = tmp_save_dir / "guardado.json"
        datos_guardados = {
            "personaje": {
                "nombre": "TestPlayer",
                # "vida": MISSING
                "fuerza": 5,
                "destreza": 5,
                "pociones": 6,
                "nivel": 1,
                "armas": {},
            },
            "armas_jugador": {},
            "ruta_jugador": [],
            "eventos_superados": 0,
            "bolsa_eventos": [],
            "bolsa_exploracion": [],
            "pasos_nivel2": [],
            "pasos_secretos": [],
            "veces_guardado": 0,
            "_c01": 0,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            
            # ACT
            resultado = cargar_partida()
            
            # ASSERT
            assert resultado is None
            mock_alerta.assert_called()
            assert "incompleto" in str(mock_alerta.call_args).lower() or "dañado" in str(mock_alerta.call_args).lower()

    def test_P2_7_sincroniza_armas_desde_estado(self, personaje_test, tmp_save_dir):
        """
        Spec: P2.7 - Sincroniza armas desde estado a personaje
        
        Valida que armas_jugador (del estado) se copian a personaje["armas"]
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        personaje_test_sin_armas = personaje_test.copy()
        personaje_test_sin_armas["armas"] = {}  # Sin armas
        
        datos_guardados = {
            "personaje": personaje_test_sin_armas,
            "armas_jugador": {
                "daga": {"daño": 2, "tipo": "sutil"},
                "maza": {"daño": 5, "tipo": "pesada"},
            },
            "ruta_jugador": [],
            "eventos_superados": 0,
            "bolsa_eventos": [],
            "bolsa_exploracion": [],
            "pasos_nivel2": [],
            "pasos_secretos": [],
            "veces_guardado": 0,
            "_c01": 0,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            with patch.dict('TLDRDC_Prueba1.estado', clear=True):
                
                # ACT
                personaje_cargado = cargar_partida()
                
                # ASSERT
                assert personaje_cargado["armas"]["daga"]["daño"] == 2
                assert personaje_cargado["armas"]["maza"]["daño"] == 5

    def test_P2_8_validacion_campos_minimos(self, tmp_save_dir, mock_alerta):
        """
        Spec: P2.8 - Validación de campos mínimos
        
        Valida que faltan campos requeridos: {nombre, vida, fuerza, destreza, pociones, nivel}
        """
        # ARRANGE: personaje falta multiple campos
        ruta_guardado = tmp_save_dir / "guardado.json"
        datos_guardados = {
            "personaje": {
                "nombre": "Test",
                # "vida": MISSING
                # "fuerza": MISSING
                "destreza": 5,
                # "pociones": MISSING
                "nivel": 1,
                "armas": {},
            },
            "armas_jugador": {},
            "ruta_jugador": [],
            "eventos_superados": 0,
            "bolsa_eventos": [],
            "bolsa_exploracion": [],
            "pasos_nivel2": [],
            "pasos_secretos": [],
            "veces_guardado": 0,
            "_c01": 0,
        }
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(datos_guardados, f)
        
        with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
            
            # ACT
            resultado = cargar_partida()
            
            # ASSERT
            assert resultado is None
            mock_alerta.assert_called()


# ==============================================================================
# TESTS DE INTEGRACIÓN ADICIONALES (opcionales)
# ==============================================================================

class TestIntegracionPersistencia:
    """Tests de integración: guardar → cargar → verificar"""

    def test_ciclo_completo_guardar_cargar(self, personaje_test, estado_test, tmp_save_dir):
        """
        Test integración: Guardar partida → Cargar partida → Verificar datos intactos
        
        Valida que un ciclo completo de guardado y cargado preserva todos los datos
        """
        # ARRANGE
        ruta_guardado = tmp_save_dir / "guardado.json"
        
        with patch('TLDRDC_Prueba1.CARPETA_SAVE', str(tmp_save_dir)):
            with patch('TLDRDC_Prueba1.RUTA_SAVE', str(ruta_guardado)):
                
                # ACT 1: Guardar
                with patch.dict('TLDRDC_Prueba1.estado', estado_test, clear=False):
                    guardar_partida(personaje_test)
                
                # ACT 2: Cargar
                with patch.dict('TLDRDC_Prueba1.estado', clear=True):
                    personaje_cargado = cargar_partida()
                    import TLDRDC_Prueba1
                    estado_cargado = TLDRDC_Prueba1.estado.copy()
                
                # ASSERT
                assert personaje_cargado["nombre"] == personaje_test["nombre"]
                assert personaje_cargado["vida"] == personaje_test["vida"]
                assert estado_cargado["_c01"] == estado_test["_c01"]
                assert estado_cargado["eventos_superados"] == estado_test["eventos_superados"]
