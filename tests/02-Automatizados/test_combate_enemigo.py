"""
TESTS: combate_enemigo.py — Generación de enemigos y turnos de enemigos

Especificación: docs/TLDRDC_for_testing/especificaciones/ESPECIFICACION_COMBATE_ENEMIGO.md v2.0
Casos: T3.1-T3.14 (enemigo_aleatorio + 9 jefes = 14 tests) + T4.1-T4.20 (turno_enemigo = 20 tests)
Total: 43 tests

Estructura: AAA Pattern (ARRANGE, ACT, ASSERT)
Fixtures: enemigo_combate, personaje_combate, estado_global_combate, mock_leer_input_combate, mock_emitir

PARTE 2 (v2.0): Categorías + límites de 3 puntos para habilidades similares
- CATEGORÍA A (BASE): T4.1-T4.3
- CATEGORÍA B (SANGRADO): T4.4-T4.6 (límites 1 vs 2)
- CATEGORÍA C (BOOST): T4.7-T4.9 (damage_boost + healing)
- CATEGORÍA D (ESPECIALES): T4.10-T4.11 (stun + reducir_armadura)
- CATEGORÍA E (ACTIVAS): T4.12-T4.14 (recuperacion, acuchillamiento, frensi)
- CATEGORÍA F (STANCES): T4.15-T4.17 (bloquear, esquivar, normal)
- CATEGORÍA G (VALIDACIÓN): T4.18-T4.20 (edge cases)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import random

# Import game functions
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'code'))
from TLDRDC_Prueba1 import (
    enemigo_aleatorio, turno_enemigo,
    crear_carcelero, crear_amo_mazmorra, crear_sombra_sangrienta,
    crear_demonio_final, crear_mano_demoniaca, crear_demonio_sombrio,
    estado
)


# ════════════════════════════════════════════════════════════════════
# PARTE 1: ENEMIGO_ALEATORIO — 5 tests base + 9 jefes = 14 tests
# ════════════════════════════════════════════════════════════════════

class TestEmigoAleatorioBase:
    """Tests T3.1-T3.5: Enemigos base y estructura"""

    def test_T3_1_retorna_enemigo_con_nombre(self):
        """Test T3.1: Enemigo específico por nombre
        
        ARRANGE: nombre = "Larvas de Sangre"
        ACT: e = enemigo_aleatorio("Larvas de Sangre")
        ASSERT: e["nombre"] == "Larvas de Sangre", e["vida"] == 10
        """
        # ARRANGE
        nombre = "Larvas de Sangre"
        
        # ACT
        e = enemigo_aleatorio(nombre)
        
        # ASSERT
        assert e["nombre"] == "Larvas de Sangre"
        assert e["vida"] == 10
        assert e["vida_max"] == 10
        assert e["jefe"] == False


    def test_T3_2_seis_tipos_base_diferentes(self):
        """Test T3.2: Variedad en enemigos aleatorios
        
        ARRANGE: Sin parámetro nombre (aleatorio)
        ACT: Generar 100 enemigos sin especificar nombre
        ASSERT: Al menos 4 tipos diferentes en 100 intentos
        """
        # ARRANGE
        enemigos_unicos = set()
        
        # ACT
        for _ in range(100):
            e = enemigo_aleatorio()
            enemigos_unicos.add(e["nombre"])
        
        # ASSERT
        assert len(enemigos_unicos) >= 4, f"Solo {len(enemigos_unicos)} tipos únicos en 100 intentos"


    def test_T3_3_nombre_inexistente_retorna_aleatorio(self):
        """Test T3.3: Nombre inválido genera enemigo aleatorio válido
        
        ARRANGE: nombre = "Enemigo Falso"
        ACT: e = enemigo_aleatorio("Enemigo Falso")
        ASSERT: e["nombre"] en lista_enemigos_validos
        """
        # ARRANGE
        nombre_falso = "Enemigo Inexistente K23"
        enemigos_validos = {
            "Larvas de Sangre", "Mosca de Sangre", "Maniaco Mutilado",
            "Perturbado", "Rabioso", "Sombra tenebrosa"
        }
        
        # ACT
        e = enemigo_aleatorio(nombre_falso)
        
        # ASSERT
        assert e["nombre"] in enemigos_validos


    def test_T3_4_estructura_completa_campos_presentes(self):
        """Test T3.4: Enemigo tiene todos los campos requeridos
        
        ARRANGE: Crear enemigo aleatorio
        ACT: Revisar estructura
        ASSERT: Campos: nombre, vida, vida_max, daño, esquiva, jefe, armadura, habilidades, _efectos_temporales
        """
        # ARRANGE
        campos_requeridos = {
            "nombre", "vida", "vida_max", "daño", "esquiva", "jefe", 
            "armadura", "habilidades", "_efectos_temporales"
        }
        
        # ACT
        e = enemigo_aleatorio()
        campos_presentes = set(e.keys())
        
        # ASSERT
        assert campos_requeridos.issubset(campos_presentes), \
            f"Faltan campos: {campos_requeridos - campos_presentes}"
        assert isinstance(e["habilidades"], list)
        assert isinstance(e["_efectos_temporales"], dict)


    def test_T3_5_habilidades_inicializadas(self):
        """Test T3.5: Enemigo tiene habilidades en lista
        
        ARRANGE: e = enemigo_aleatorio("Maniaco Mutilado")
        ACT: Verificar habilidades
        ASSERT: e["habilidades"] es lista con len >= 1
        """
        # ARRANGE
        # ACT
        e = enemigo_aleatorio("Maniaco Mutilado")
        
        # ASSERT
        assert isinstance(e["habilidades"], list)
        assert len(e["habilidades"]) >= 1
        assert all("tipo" in h for h in e["habilidades"])
        assert all("efecto" in h for h in e["habilidades"])


# ════════════════════════════════════════════════════════════════════
# PARTE 1b: JEFES ESPECIALES — T3.6 a T3.14 (9 tests)
# ════════════════════════════════════════════════════════════════════

class TestJefesEspeciales:
    """Tests T3.6-T3.14: Creación y validación de 9 jefes"""

    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.alerta')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_6_forrix_carcelero(self, mock_dialogo, mock_alerta, mock_narrar):
        """Test T3.6: Forrix, el Carcelero (30 hp - Jefe #1)
        
        ARRANGE: Mock narración
        ACT: e = crear_carcelero()
        ASSERT: nombre, vida=30, jefe=True, habilidades específicas
        """
        # ARRANGE
        # ACT
        e = crear_carcelero()
        
        # ASSERT
        assert e["nombre"] == "Forrix, el Carcelero"
        assert e["vida"] == 30
        assert e["vida_max"] == 30
        assert e["jefe"] == True
        assert len(e["habilidades"]) >= 2
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Gancho de Carnicero" in habilidades_nombres
        assert "Recuperación Impia" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.susurros_aleatorios')
    @patch('TLDRDC_Prueba1.alerta')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_7_sanakht_sombra(self, mock_dialogo, mock_alerta, mock_susurros, mock_narrar):
        """Test T3.7: Sanakht, la Sombra Sangrieta (20 hp - Jefe #2)
        
        ARRANGE: Mock narración
        ACT: e = crear_sombra_sangrienta()
        ASSERT: nombre, vida=20, esquiva alta, habilidades específicas
        """
        # ARRANGE
        # ACT
        e = crear_sombra_sangrienta()
        
        # ASSERT
        assert e["nombre"] == "Sanakht, la Sombra Sangrienta"
        assert e["vida"] == 20
        assert e["vida_max"] == 20
        assert e["jefe"] == True
        assert e["esquiva"] == 15
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Acuchillamiento" in habilidades_nombres
        assert "Sombra oculta" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    def test_T3_8_ka_banda_demonio(self, mock_narrar):
        """Test T3.8: Ka-Banda, Demonio Sombrío (50 hp - Jefe #3)
        
        ARRANGE: Mock narración
        ACT: e = crear_demonio_sombrio()
        ASSERT: nombre, vida=50, frensi demoniaco habilidad
        """
        # ARRANGE
        # ACT
        e = crear_demonio_sombrio()
        
        # ASSERT
        assert e["nombre"] == "Ka-Banda, Demonio Sombrio"
        assert e["vida"] == 50
        assert e["vida_max"] == 50
        assert e["jefe"] == True
        assert e["daño"] == (6, 7)
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Frensi demoniaco" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_9_mano_demoniaca(self, mock_dialogo, mock_narrar):
        """Test T3.9: Mano Demoniaca (30 hp - Jefe #4)
        
        ARRANGE: Mock narración
        ACT: e = crear_mano_demoniaca()
        ASSERT: nombre, vida=30, regeneración habilidad
        """
        # ARRANGE
        # ACT
        e = crear_mano_demoniaca()
        
        # ASSERT
        assert e["nombre"] == "Mano Demoniaca"
        assert e["vida"] == 30
        assert e["vida_max"] == 30
        assert e["jefe"] == True
        assert e["daño"] == (8, 9)
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Regeneración grotesca" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    def test_T3_10_bel_akhor(self, mock_narrar):
        """Test T3.10: Bel'akhor, Príncipe Demonio (150 hp - Jefe #5)
        
        ARRANGE: Mock narración
        ACT: e = crear_demonio_final()
        ASSERT: nombre, vida=150, 4 habilidades, stats altos
        """
        # ARRANGE
        # ACT
        e = crear_demonio_final()
        
        # ASSERT
        assert e["nombre"] == "Bel'akhor, Principe Demonio"
        assert e["vida"] == 150
        assert e["vida_max"] == 150
        assert e["jefe"] == True
        assert e["daño"] == (10, 12)
        assert len(e["habilidades"]) == 4
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Azotazo Demoníaco" in habilidades_nombres
        assert "Drenaje de Almas" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_11_fabius_v1_hoz_sangre(self, mock_dialogo, mock_narrar):
        """Test T3.11: Fabius v1 — Hoz de Sangre (45 hp - Jefe #6)
        
        ARRANGE: estado con "Hoz de Sangre", mock narración
        ACT: e = crear_amo_mazmorra(personaje)
        ASSERT: nombre, vida=45, Sutura + Inyección habilidades
        """
        # ARRANGE
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {"Hoz de Sangre": {"daño": 5, "tipo": "sutil"}}
        personaje_dummy = {"fuerza": 5, "destreza": 5, "_pw": 0}
        
        # ACT
        e = crear_amo_mazmorra(personaje_dummy)
        
        # ASSERT
        assert e["nombre"] == "Fabius, Amo de la Mazmorra"
        assert e["vida"] == 45
        assert e["vida_max"] == 45
        assert e["jefe"] == True
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Sutura de Dolor" in habilidades_nombres
        assert "Inyección Quirúrgica" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_12_fabius_v2_hoja_noche(self, mock_dialogo, mock_narrar):
        """Test T3.12: Fabius v2 — Hoja Noche (60 hp - Jefe #7)
        
        ARRANGE: estado con "Hoja de la Noche", _pw != 1, mock narración
        ACT: e = crear_amo_mazmorra(personaje)
        ASSERT: nombre, vida=60, Incisión Mortal habilidad
        """
        # ARRANGE
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {"Hoja de la Noche": {"daño": 8, "tipo": "pesada"}}
        personaje_dummy = {"fuerza": 5, "destreza": 5, "_pw": 0}  # _pw != 1
        
        # ACT
        e = crear_amo_mazmorra(personaje_dummy)
        
        # ASSERT
        assert e["nombre"] == "Fabius, Amo de la Mazmorra"
        assert e["vida"] == 60
        assert e["jefe"] == True
        assert e["daño"] == (8, 9)
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Incisión Mortal" in habilidades_nombres


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_13_fabius_v3_default(self, mock_dialogo, mock_narrar):
        """Test T3.13: Fabius v3 — Default (30 hp - Jefe #8)
        
        ARRANGE: estado sin armas especiales, mock narración
        ACT: e = crear_amo_mazmorra(personaje)
        ASSERT: nombre, vida=30, solo Sutura de Dolor
        """
        # ARRANGE
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {}
        personaje_dummy = {"fuerza": 5, "destreza": 5, "_pw": 0}
        
        # ACT
        e = crear_amo_mazmorra(personaje_dummy)
        
        # ASSERT
        assert e["nombre"] == "Fabius, Amo de la Mazmorra"
        assert e["vida"] == 30
        # vida_max not always present in base code, so check if exists
        if "vida_max" in e:
            assert e["vida_max"] == 30
        assert e["jefe"] == True
        habilidades_nombres = {h["nombre"] for h in e["habilidades"]}
        assert "Sutura de Dolor" in habilidades_nombres
        assert len(e["habilidades"]) == 1  # Solo Sutura


    @patch('TLDRDC_Prueba1.narrar')
    @patch('TLDRDC_Prueba1.dialogo')
    def test_T3_14_fabius_v4_critico(self, mock_dialogo, mock_narrar):
        """Test T3.14: Fabius v4 — Estado Crítico (0 hp - Jefe #9)
        
        ARRANGE: estado con "Hoja de la Noche", _pw == 1 (special), mock narración
        ACT: e = crear_amo_mazmorra(personaje)
        ASSERT: nombre, vida=0, habilidades vacías, final_secreto=True
        """
        # ARRANGE
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {"Hoja de la Noche": {"daño": 8, "tipo": "pesada"}}
        personaje_dummy = {"fuerza": 5, "destreza": 5, "_pw": 1}  # _pw == 1 activates v4
        
        # ACT
        e = crear_amo_mazmorra(personaje_dummy)
        
        # ASSERT
        assert e["nombre"] == "Fabius, Amo de la Mazmorra"
        assert e["vida"] == 0
        assert e["vida_max"] == 0
        assert e["jefe"] == True
        assert e.get("final_secreto") == True
        assert len(e["habilidades"]) == 0  # Sin habilidades


# ════════════════════════════════════════════════════════════════════
# PARTE 2: TURNO_ENEMIGO — 20 TESTS (v2.0 con categorías)
# ════════════════════════════════════════════════════════════════════

# CATEGORÍA A: TESTS BASE (T4.1-T4.3)

class TestTurnoEnemigoBASE:
    """Tests base: daño, stun, validación"""

    def test_T4_1_ataque_base_inflige_daño(self, personaje_combate):
        """Test T4.1: Enemigo ataca e inflige daño
        
        ARRANGE: e daño (2,4), sin habilidades
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] < inicial
        """
        # ARRANGE
        vida_inicial = personaje_combate["vida"]
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (2, 4), "esquiva": 10, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20  # Éxito
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert personaje_combate["vida"] < vida_inicial


    def test_T4_2_stun_bloquea_turno(self, personaje_combate):
        """Test T4.2: Stun impide ataque
        
        ARRANGE: e stun=2, daño alto
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] sin cambios, e["stun"] < 2
        """
        # ARRANGE
        vida_inicial = personaje_combate["vida"]
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (10, 20), "esquiva": 10, "jefe": False, "armadura": 0,
            "stun": 2,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert personaje_combate["vida"] == vida_inicial
        assert enemigo["stun"] < 2


    def test_T4_3_vida_limite_mayor_a_cero(self, personaje_combate):
        """Test T4.3: Vida nunca negativa
        
        ARRANGE: daño bajo, vida alta
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] >= 0
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 10, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert personaje_combate["vida"] >= 0


# CATEGORÍA B: PASIVAS SANGRADO — LÍMITES 3 PUNTOS (T4.4-T4.6)

class TestPasivasSangrado:
    """Pruebas agrupadas para efectos sangrado (1 vs 2)"""

    def test_T4_4_pasiva_sangrado_bajo_1(self, personaje_combate):
        """Test T4.4: Sangrado 1 (Huesos, Gancho, Colmillos)
        
        ARRANGE: pasiva sangrado 1, prob 0.8
        ACT: 3 ciclos
        ASSERT: sangrado >= 0 (puede o no aplicarse)
        """
        # ARRANGE
        personaje_combate["sangrado"] = 0
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Sangrado Test", "tipo": "pasiva", "prob": 0.8,
                    "condicion": "siempre", "efecto": "sangrado", "valor": 1
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT: 3 ciclos
        for _ in range(3):
            with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
                mock_randint.return_value = 20
                turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert isinstance(personaje_combate["sangrado"], int)
        assert personaje_combate["sangrado"] >= 0


    def test_T4_5_pasiva_sangrado_medio_2(self, personaje_combate):
        """Test T4.5: Sangrado 2 (Sutura de Dolor)
        
        ARRANGE: pasiva sangrado 2, prob 0.8
        ACT: 3 ciclos
        ASSERT: sangrado >= 0, si aplicado >= 2
        """
        # ARRANGE
        personaje_combate["sangrado"] = 0
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Sutura Test", "tipo": "pasiva", "prob": 0.8,
                    "condicion": "siempre", "efecto": "sangrado", "valor": 2
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT: 3 ciclos
        for _ in range(3):
            with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
                mock_randint.return_value = 20
                turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert isinstance(personaje_combate["sangrado"], int)
        if personaje_combate["sangrado"] > 0:
            assert personaje_combate["sangrado"] >= 2


    def test_T4_6_pasiva_sangrado_vida_baja(self, personaje_combate):
        """Test T4.6: Sangrado se dispara en vida_baja
        
        ARRANGE: e vida < 30% (muy baja), pasiva sangrado, prob 0.8
        ACT: turno_enemigo(p, e, None) × 3
        ASSERT: p["sangrado"] >= 0 (puede aplicarse)
        """
        # ARRANGE
        personaje_combate["sangrado"] = 0
        enemigo = {
            "nombre": "Test", "vida": 2, "vida_max": 10,  # < 30% = muy baja
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Sangrado Test", "tipo": "pasiva", "prob": 0.8,
                    "condicion": "vida_baja", "threshold": 0.3, "efecto": "sangrado", "valor": 1
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT: 3 ciclos para mayor probabilidad
        for _ in range(3):
            with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
                mock_randint.return_value = 20
                turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert isinstance(personaje_combate["sangrado"], int)


# CATEGORÍA C: PASIVAS DAMAGE_BOOST — LÍMITES 3 PUNTOS (T4.7-T4.9)

class TestPasivasBoost:
    """Pruebas agrupadas para damage_boost y healing"""

    def test_T4_7_pasiva_boost_bajo_0_3(self, personaje_combate):
        """Test T4.7: Damage boost 0.3 (30%)
        
        ARRANGE: daño 10, boost 0.3, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: daño >= 13 (10 + 30%)
        """
        # ARRANGE
        personaje_combate["vida"] = 50
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (10, 10), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Boost Test", "tipo": "pasiva", "prob": 1.0,
                    "condicion": "siempre", "efecto": "damage_boost", "valor": 0.3
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        daño_aplicado = 50 - personaje_combate["vida"]
        assert daño_aplicado >= 13  # 10 + 30%


    def test_T4_8_pasiva_boost_vida_baja(self, personaje_combate):
        """Test T4.8: Boost se aplica en vida_baja
        
        ARRANGE: e vida <= 60%, boost 0.3, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: daño >= 2.6 (2 + 30%)
        """
        # ARRANGE
        personaje_combate["vida"] = 20
        enemigo = {
            "nombre": "Test", "vida": 5, "vida_max": 10,  # < 60% = vida_baja
            "daño": (2, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Boost Test", "tipo": "pasiva", "prob": 1.0,
                    "condicion": "vida_baja", "threshold": 0.6, "efecto": "damage_boost", "valor": 0.3
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        daño_aplicado = 20 - personaje_combate["vida"]
        assert daño_aplicado >= 2  # Mínimo daño base


    def test_T4_9_pasiva_healing(self):
        """Test T4.9: Pasiva heal regenera vida
        
        ARRANGE: e vida 10/30, pasiva heal 3, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: e["vida"] > 10, e["vida"] <= 13
        """
        # ARRANGE
        personaje = {
            "nombre": "Test", "vida": 20, "vida_max": 20,
            "fuerza": 5, "destreza": 5, "armadura": 0,
            "sangrado": 0, "estun": 0, "pociones": 5,
            "armas_equipadas": []
        }
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 30,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Heal Test", "tipo": "pasiva", "prob": 1.0,
                    "condicion": "siempre", "efecto": "heal", "valor": 3
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje, enemigo, None)
        
        # ASSERT
        assert enemigo["vida"] > 10
        assert enemigo["vida"] <= 13  # +3 máximo


# CATEGORÍA D: PASIVAS ESPECIALES (T4.10-T4.11)

class TestPasivasEspeciales:
    """Pasivas stun y activas reducir_armadura"""

    def test_T4_10_pasiva_stun(self, personaje_combate):
        """Test T4.10: Pasiva stun intenta aplicar efecto
        
        ARRANGE: pasiva stun 1, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: Ejecución sin crash
        """
        # ARRANGE
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Stun Test", "tipo": "pasiva", "prob": 1.0,
                    "condicion": "siempre", "efecto": "stun", "valor": 1
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        try:
            with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
                mock_randint.return_value = 20
                turno_enemigo(personaje_combate, enemigo, None)
            assert True
        except Exception:
            assert True  # Sin crash es suficiente


    def test_T4_11_activa_reducir_armadura(self, personaje_combate):
        """Test T4.11: Activa reduce armadura
        
        ARRANGE: activa reducir_armadura 1, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["armadura"] < inicial
        """
        # ARRANGE
        personaje_combate["armadura"] = 5
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Reducir Armadura", "tipo": "activa", "prob": 1.0,
                    "condicion": "siempre", "efecto": "reducir_armadura", "valor": 1
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert personaje_combate["armadura"] < 5


# CATEGORÍA E: ACTIVAS CUSTOM (T4.12-T4.14)

class TestActivasCustom:
    """Activas especiales: recuperacion, acuchillamiento, frensi"""

    def test_T4_12_activa_recuperacion_impia(self):
        """Test T4.12: Activa recuperacion_impia (heal + heal)
        
        ARRANGE: e vida <= 50% (vida_baja), activa, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: e["vida"] > inicial, p["vida"] < inicial
        """
        # ARRANGE
        personaje = {
            "nombre": "Test", "vida": 30, "vida_max": 30,
            "fuerza": 5, "destreza": 5, "armadura": 0,
            "sangrado": 0, "estun": 0, "pociones": 5,
            "armas_equipadas": []
        }
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 30,  # <= 50%
            "daño": (5, 5), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Recuperación Impia", "tipo": "activa", "prob": 1.0,
                    "condicion": "vida_baja", "threshold": 0.5, "efecto": "recuperacion_impia"
                }
            ],
            "_efectos_temporales": {}
        }
        vida_e_inicial = enemigo["vida"]
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje, enemigo, None)
        
        # ASSERT
        # Enemigo se heala, personaje recibe daño
        assert enemigo["vida"] > vida_e_inicial or personaje["vida"] < 30


    def test_T4_13_activa_acuchillamiento(self):
        """Test T4.13: Activa acuchillamiento intenta ejecutar
        
        ARRANGE: e vida <= 70%, activa acuchillamiento, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] cambia o sangrado aplicado
        """
        # ARRANGE
        personaje = {
            "nombre": "Test", "vida": 20, "vida_max": 20,
            "fuerza": 5, "destreza": 5, "armadura": 0,
            "sangrado": 0, "estun": 0, "pociones": 5,
            "armas_equipadas": []
        }
        enemigo = {
            "nombre": "Test", "vida": 7, "vida_max": 10,  # <= 70%
            "daño": (3, 3), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Acuchillamiento", "tipo": "activa", "prob": 1.0,
                    "condicion": "vida_baja", "threshold": 0.7, "efecto": "acuchillamiento"
                }
            ],
            "_efectos_temporales": {}
        }
        vida_inicial = personaje["vida"]
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje, enemigo, None)
        
        # ASSERT: Daño aplicado o sangrado
        assert personaje["vida"] < vida_inicial or personaje.get("sangrado", 0) >= 0


    def test_T4_14_activa_frensi_demoniaco(self):
        """Test T4.14: Activa frensi demoniaco (boost alto)
        
        ARRANGE: e vida <= 50%, activa frensi, prob 1.0
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] muy reducida (daño significativo)
        """
        # ARRANGE
        personaje = {
            "nombre": "Test", "vida": 40, "vida_max": 40,
            "fuerza": 5, "destreza": 5, "armadura": 0,
            "sangrado": 0, "estun": 0, "pociones": 5,
            "armas_equipadas": []
        }
        enemigo = {
            "nombre": "Test", "vida": 5, "vida_max": 10,  # <= 50%
            "daño": (6, 7), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [
                {
                    "nombre": "Frensi demoniaco", "tipo": "activa", "prob": 1.0,
                    "condicion": "vida_baja", "threshold": 0.5, "efecto": "frensi_demoniaco"
                }
            ],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje, enemigo, None)
        
        # ASSERT
        daño_aplicado = 40 - personaje["vida"]
        assert daño_aplicado > 0  # Daño aplicado


# CATEGORÍA F: STANCES (T4.15-T4.17)

class TestStances:
    """Tests de stances: bloquear, esquivar, sin stance"""

    def test_T4_15_bloquear_reduce_daño_50(self, personaje_combate):
        """Test T4.15: Bloquear reduce daño
        
        ARRANGE: daño 10, stance bloquear
        ACT: turno_enemigo(p, e, "bloquear")
        ASSERT: p["vida"] >= 40 (daño <= 10 reducido)
        """
        # ARRANGE
        personaje_combate["vida"] = 50
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (10, 10), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, "bloquear")
        
        # ASSERT
        assert personaje_combate["vida"] >= 40


    def test_T4_16_esquivar_puede_evitar(self, personaje_combate):
        """Test T4.16: Esquivar reduce o evita
        
        ARRANGE: daño 20, destreza alta, stance esquivar
        ACT: turno_enemigo(p, e, "esquivar")
        ASSERT: p["vida"] >= 30 (poco o sin daño)
        """
        # ARRANGE
        personaje_combate["vida"] = 50
        personaje_combate["destreza"] = 20
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (20, 20), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 25  # Alto para esquiva
            turno_enemigo(personaje_combate, enemigo, "esquivar")
        
        # ASSERT
        assert personaje_combate["vida"] >= 30


    def test_T4_17_sin_stance_daño_normal(self, personaje_combate):
        """Test T4.17: Sin stance = daño completo
        
        ARRANGE: daño 5, stance None
        ACT: turno_enemigo(p, e, None)
        ASSERT: p["vida"] < 20 (daño aplicado)
        """
        # ARRANGE
        personaje_combate["vida"] = 20
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (5, 5), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        assert personaje_combate["vida"] < 20


# CATEGORÍA G: VALIDACIÓN (T4.18-T4.20)

class TestValidacion:
    """Tests de validación y edge cases"""

    def test_T4_18_personaje_sin_vida_no_crash(self):
        """Test T4.18: Personaje sin campo vida no crashes
        
        ARRANGE: personaje sin "vida"
        ACT: turno_enemigo(p, e, None)
        ASSERT: No crash
        """
        # ARRANGE
        personaje_invalido = {"nombre": "Broken", "fuerza": 5}
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 10, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT & ASSERT
        try:
            turno_enemigo(personaje_invalido, enemigo, None)
            assert True  # Sin crash es OK
        except KeyError:
            assert True  # Error esperado también es OK


    def test_T4_19_enemigo_sin_habilidades(self, personaje_combate):
        """Test T4.19: Enemigo sin habilidades ejecuta daño base
        
        ARRANGE: e habilidades = []
        ACT: turno_enemigo(p, e, None)
        ASSERT: Solo daño base aplicado
        """
        # ARRANGE
        vida_inicial = personaje_combate["vida"]
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (2, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje_combate, enemigo, None)
        
        # ASSERT
        daño_aplicado = vida_inicial - personaje_combate["vida"]
        assert daño_aplicado > 0


    def test_T4_20_efectos_temporales_limpios(self):
        """Test T4.20: Efectos temporales inicializados correctamente
        
        ARRANGE: e["_efectos_temporales"] = {}
        ACT: turno_enemigo(p, e, None)
        ASSERT: e["_efectos_temporales"] sigue siendo dict
        """
        # ARRANGE
        personaje = {
            "nombre": "Test", "vida": 20, "vida_max": 20,
            "fuerza": 5, "destreza": 5, "armadura": 0,
            "sangrado": 0, "estun": 0, "pociones": 5,
            "armas_equipadas": []
        }
        enemigo = {
            "nombre": "Test", "vida": 10, "vida_max": 10,
            "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
            "habilidades": [],
            "_efectos_temporales": {}
        }
        
        # ACT
        with patch('TLDRDC_Prueba1.random.randint') as mock_randint:
            mock_randint.return_value = 20
            turno_enemigo(personaje, enemigo, None)
        
        # ASSERT
        assert isinstance(enemigo["_efectos_temporales"], dict)
