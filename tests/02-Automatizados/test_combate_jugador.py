# ════════════════════════════════════════════════════════════════════
# TESTS: COMBATE_JUGADOR (T1-T2)
# ════════════════════════════════════════════════════════════════════
"""
Tests para calcular_daño(arma, personaje) y turno_jugador(personaje, enemigo).

Total: 16 tests
- T1: calcular_daño (6 tests)
- T2: turno_jugador (10 tests — didáctico simplificado)

Notas:
  - T2 enfocado en diferenciadores de comportamiento
  - Integración completa probada en COMBATE_LOOP (T5-T7)
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Agregar ruta de código a sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'code'))

# Importar funciones del monolito
from TLDRDC_Prueba1 import calcular_daño, turno_jugador


# ════════════════════════════════════════════════════════════════════
# PARTE 1: CALCULAR_DAÑO (6 tests)
# ════════════════════════════════════════════════════════════════════

class TestCalcularDaño:
    """Tests para función calcular_daño(arma, personaje)."""

    def test_t1_1_daño_base_sin_tipo(self):
        """T1.1: Daño base sin tipo de arma."""
        arma = {"daño": 3}
        personaje = {"fuerza": 10, "destreza": 10}
        
        resultado = calcular_daño(arma, personaje)
        
        assert resultado == 3

    def test_t1_2_sutil_destreza_baja(self):
        """T1.2: Tipo sutil con destreza baja."""
        arma = {"daño": 2, "tipo": "sutil"}
        personaje = {"destreza": 4}
        
        resultado = calcular_daño(arma, personaje)
        
        assert resultado == 4  # 2 + (4//2)

    def test_t1_3_sutil_destreza_alta(self):
        """T1.3: Tipo sutil con destreza alta."""
        arma = {"daño": 2, "tipo": "sutil"}
        personaje = {"destreza": 10}
        
        resultado = calcular_daño(arma, personaje)
        
        assert resultado == 7  # 2 + (10//2)

    def test_t1_4_pesada_fuerza(self):
        """T1.4: Tipo pesada con bonificación de fuerza."""
        arma = {"daño": 5, "tipo": "pesada"}
        personaje = {"fuerza": 8}
        
        resultado = calcular_daño(arma, personaje)
        
        assert resultado == 9  # 5 + (8//2)

    def test_t1_5_mixta_fuerza_y_destreza(self):
        """T1.5: Tipo mixta con fuerza y destreza."""
        arma = {"daño": 5, "tipo": "mixta"}
        personaje = {"fuerza": 6, "destreza": 9}
        
        resultado = calcular_daño(arma, personaje)
        
        assert resultado == 10  # 5 + ((6+9)//3)

    def test_t1_6_builds_extremos(self):
        """T1.6: Máxima representación de stats (extremos ágil vs fuerte)."""
        # Build ágil: alta destreza, baja fuerza
        arma_sutil = {"daño": 2, "tipo": "sutil"}
        p_agil = {"destreza": 20, "fuerza": 1}
        
        d1 = calcular_daño(arma_sutil, p_agil)
        assert d1 == 12  # 2 + (20//2)
        
        # Build fuerte: alta fuerza, baja destreza
        arma_pesada = {"daño": 5, "tipo": "pesada"}
        p_fuerte = {"destreza": 1, "fuerza": 20}
        
        d2 = calcular_daño(arma_pesada, p_fuerte)
        assert d2 == 15  # 5 + (20//2)


# ════════════════════════════════════════════════════════════════════
# PARTE 2: TURNO_JUGADOR (8 tests — Simplificado Didáctico)
# ════════════════════════════════════════════════════════════════════

class TestTurnoJugadorSimplificado:
    """Tests para turno_jugador(personaje, enemigo) — versión didáctica."""

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_1_ataque_exitoso(self, mock_alerta, mock_sistema, mock_emitir, 
                                   mock_randint, mock_leer):
        """T2.1: Ataque exitoso reduce vida enemigo."""
        # Setup: Importar el módulo para acceder a estado
        import TLDRDC_Prueba1
        
        # Cargar armas al estado global
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"},
        }
        
        personaje_combate = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo_combate = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.return_value = "daga"
        mock_randint.return_value = 80  # Golpe exitoso (< 95%)
        
        resultado, stance = turno_jugador(personaje_combate, enemigo_combate)
        
        assert resultado == "ataque"
        assert enemigo_combate["vida"] < 10

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_2_ataque_falla(self, mock_alerta, mock_sistema, mock_emitir,
                                mock_randint, mock_leer):
        """T2.2: Ataque falla cuando roll > probabilidad golpe."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "baja": {"daño": 2, "golpe": 10, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.return_value = "baja"
        mock_randint.return_value = 11  # Falla (>10%)
        
        turno_jugador(personaje, enemigo)
        
        assert enemigo["vida"] == 10  # Sin daño

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.pedir_input')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_3_pocion_sana(self, mock_alerta, mock_sistema, mock_emitir,
                               mock_pedir, mock_leer):
        """T2.3: Poción sana +4 vida."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 6, "vida_max": 10,
            "fuerza": 5, "destreza": 5, "pociones": 2, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.side_effect = ["p", "daga"]
        mock_pedir.return_value = None
        
        turno_jugador(personaje, enemigo)
        
        assert personaje["pociones"] == 1
        assert personaje["vida"] == 10

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_4_pocion_bloqueada(self, mock_alerta, mock_sistema, mock_emitir,
                                    mock_leer):
        """T2.4: Poción bloqueada sin pociones."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 5, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 0, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.side_effect = ["p", "daga"]
        
        turno_jugador(personaje, enemigo)
        
        assert mock_alerta.called
        assert personaje["vida"] == 5

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_5_huida_exitosa(self, mock_alerta, mock_sistema, mock_emitir,
                                 mock_randint, mock_leer):
        """T2.5: Huida exitosa cuando 1d20+destreza ≥ 15."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {}
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.return_value = "h"
        mock_randint.return_value = 10  # 10+5=15, éxito
        
        resultado, stance = turno_jugador(personaje, enemigo)
        
        assert resultado == "huida"

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_6_huida_falla(self, mock_alerta, mock_sistema, mock_emitir,
                               mock_randint, mock_leer):
        """T2.6: Huida falla cuando 1d20+destreza < 15."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 2, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.side_effect = ["h", "daga"]
        mock_randint.return_value = 5  # 5+2=7, falla
        
        resultado, stance = turno_jugador(personaje, enemigo)
        
        assert resultado == "ataque"  # Continúa turno
        assert mock_alerta.called

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_7_stance_bloquear(self, mock_alerta, mock_sistema, mock_emitir,
                                   mock_randint, mock_leer):
        """T2.7: Stance bloquear toggle."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.side_effect = ["bl", "daga"]
        mock_randint.return_value = 80
        
        turno_jugador(personaje, enemigo)
        
        assert mock_sistema.called

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_8_stance_esquivar(self, mock_alerta, mock_sistema, mock_emitir,
                                   mock_randint, mock_leer):
        """T2.8: Stance esquivar toggle."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "daga": {"daño": 2, "golpe": 95, "tipo": "sutil"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.side_effect = ["esq", "daga"]
        mock_randint.return_value = 80
        
        turno_jugador(personaje, enemigo)
        
        assert mock_sistema.called
        assert any("esquiva" in str(call) for call in mock_sistema.call_args_list)

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_9_sin_stance(self, mock_alerta, mock_sistema, mock_emitir,
                              mock_randint, mock_leer):
        """T2.9: Sin stance (ataque normal sin modificadores)."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "espada": {"daño": 3, "golpe": 85, "tipo": "pesada"},
        }
        
        personaje = {
            "nombre": "jugador", "vida": 10, "vida_max": 25,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.return_value = "espada"
        mock_randint.return_value = 80  # Éxito
        
        resultado, stance = turno_jugador(personaje, enemigo)
        
        assert resultado == "ataque"
        assert stance is None  # Sin stance
        assert enemigo["vida"] == 5  # Daño con bonificación pesada: 10 - (3 + 5//2)

    @patch('TLDRDC_Prueba1.leer_input')
    @patch('TLDRDC_Prueba1.random.randint')
    @patch('TLDRDC_Prueba1.emitir')
    @patch('TLDRDC_Prueba1.sistema')
    @patch('TLDRDC_Prueba1.alerta')
    def test_t2_10_efectos_arma(self, mock_alerta, mock_sistema, mock_emitir,
                                mock_randint, mock_leer):
        """T2.10: Efectos de arma (sangrado, stun, vida) aplicados."""
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["armas_jugador"] = {
            "combo": {"daño": 5, "golpe": 100, "sangrado": 2, "stun": 3, "vida": 1, "tipo": "sutil"}
        }
        
        personaje = {
            "nombre": "jugador", "vida": 5, "vida_max": 10,
            "fuerza": 5, "destreza": 5, "pociones": 6, "pociones_max": 10,
            "armadura": 2, "armadura_max": 5,
            "_huyo_combate": False, "_efectos_temporales": {}, "stun": 0,
        }
        enemigo = {
            "nombre": "Larvas", "vida": 10, "vida_max": 10,
            "daño": (1, 2), "esquiva": 0, "jefe": False, "armadura": 0,
            "stun": 0, "sangrado": 0, "habilidades": [],
            "_efectos_temporales": {},
        }
        
        mock_leer.return_value = "combo"
        mock_randint.return_value = 2  # Para stun: 2 <= 3, activa stun
        
        turno_jugador(personaje, enemigo)
        
        assert enemigo["sangrado"] == 2
        assert enemigo["stun"] >= 1
        assert personaje["vida"] == 6  # Lifesteal: 5 + 1

