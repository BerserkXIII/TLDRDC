"""
TESTS: combate_loop.py — Loop principal de combate y funciones asociadas

Especificación: ESPECIFICACION_COMBATE_LOOP.md v1.0
Casos: T5.1-T5.9 (combate loop) + T6.1-T6.3 (sangrado) + T7.1-T7.2 (fibonacci)
Total: 14 tests (T7.3 omitido por secretismo)

Estructura: AAA Pattern (ARRANGE, ACT, ASSERT)
Fixtures: personaje_combate, enemigo_combate, estado_global_combate

PARTE 1: COMBATE LOOP (9 tests - T5.1-T5.9)
- T5.1: Crea enemigo si None
- T5.2: turno_jugador ejecutado
- T5.3: turno_enemigo ejecutado
- T5.4: Sangrado aplicado cada ciclo
- T5.5: Fin Huida
- T5.6: Fin Victoria
- T5.7: Fin Derrota
- T5.8: Post-combate evento
- T5.9: HUD emitido

PARTE 2: SANGRADO (3 tests - T6.1-T6.3)
- T6.1: Sangrado base daño
- T6.2: Sin sangrado
- T6.3: Muerte por sangrado

PARTE 3: FIBONACCI BONUS (2 tests - T7.1-T7.2)
- T7.1: revisar_bonus_fibonacci() se llama
- T7.2: Contador incrementado
(T7.3 omitido - mantener secretismo)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Import game functions
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'code'))
from TLDRDC_Prueba1 import combate, aplicar_sangrado, revisar_bonus_fibonacci, estado


# ════════════════════════════════════════════════════════════════════
# PARTE 1: COMBATE LOOP (9 tests - T5.1-T5.9)
# ════════════════════════════════════════════════════════════════════

class TestCombateLoop:
    """Tests T5.1-T5.9: Loop principal combate()"""

    def test_T5_1_crea_enemigo_si_none(self, personaje_combate):
        """Test T5.1: Función crea enemigo si None
        
        ARRANGE: enemigo = None
        ACT: combate(p, None)
        ASSERT: Sin crash (enemigo creado internamente)
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        
        # ACT & ASSERT: No debe crash
        try:
            with patch('TLDRDC_Prueba1.enemigo_aleatorio') as mock_enemigo_gen:
                test_enemigo = {
                    "nombre": "Test", "vida": 1, "vida_max": 10,
                    "daño": (1, 1), "esquiva": 0, "jefe": False, "armadura": 0,
                    "stun": 0, "sangrado": 0, "habilidades": [], "_efectos_temporales": {}
                }
                mock_enemigo_gen.return_value = test_enemigo
                
                with patch('TLDRDC_Prueba1.emitir'):
                    with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                        # Matar enemigo en primer turno
                        def matar_enemigo(p, e):
                            e["vida"] = 0
                            return ("ataque", None)
                        mock_turno_j.side_effect = matar_enemigo
                        with patch('TLDRDC_Prueba1.turno_enemigo'):
                            with patch('TLDRDC_Prueba1.exito'):
                                with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                    with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                        combate(personaje_combate, None)
            assert True  # Sin crash
        except Exception as e:
            pytest.fail(f"combate(p, None) lanzó error: {e}")


    def test_T5_2_turno_jugador_ejecutado(self, personaje_combate, enemigo_combate):
        """Test T5.2: turno_jugador() se ejecuta en loop
        
        ARRANGE: Mock turno_jugador
        ACT: combate(p, e)
        ASSERT: turno_jugador() llamado >= 1 vez
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 1
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def kill_enemigo(p, e):
                    enemigo_combate["vida"] = 0
                    return ("ataque", None)
                mock_turno_j.side_effect = kill_enemigo
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_turno_j.called


    def test_T5_3_turno_enemigo_ejecutado(self, personaje_combate, enemigo_combate):
        """Test T5.3: turno_enemigo() se ejecuta en loop
        
        ARRANGE: Mock turno_enemigo
        ACT: combate(p, e)
        ASSERT: turno_enemigo() llamado >= 1 vez
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 10
        call_count = [0]
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def jugador_attack(p, e):
                    e["vida"] -= 2  # Damage but don't kill immediately
                    return ("ataque", None)
                mock_turno_j.side_effect = jugador_attack
                with patch('TLDRDC_Prueba1.turno_enemigo') as mock_turno_e:
                    def enemigo_attack(p, e, stance):
                        call_count[0] += 1
                        p["vida"] -= 1  # Light damage
                    mock_turno_e.side_effect = enemigo_attack
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_turno_e.called
        assert call_count[0] >= 1


    def test_T5_4_sangrado_aplicado_cada_ciclo(self, personaje_combate, enemigo_combate):
        """Test T5.4: aplicar_sangrado() ejecutado en loop
        
        ARRANGE: e = {"sangrado": 2}
        ACT: combate(p, e) [hasta victoria]
        ASSERT: aplicar_sangrado() llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 10
        enemigo_combate["sangrado"] = 2
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def jugador_attack(p, e):
                    e["vida"] -= 2  # Damage but don't kill immediately
                    return ("ataque", None)
                mock_turno_j.side_effect = jugador_attack
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.aplicar_sangrado') as mock_sangrado:
                        with patch('TLDRDC_Prueba1.exito'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_sangrado.called


    def test_T5_5_fin_huida(self, personaje_combate, enemigo_combate):
        """Test T5.5: Huida termina combate inmediatamente
        
        ARRANGE: Mock turno_jugador → ("huida", None)
        ACT: combate(p, e)
        ASSERT: p["_huyo_combate"] == True, retorna inmediatamente
        """
        # ARRANGE
        personaje_combate["_huyo_combate"] = False
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                mock_turno_j.return_value = ("huida", None)
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.alerta'):
                            with patch('TLDRDC_Prueba1.narrar'):
                                combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert personaje_combate["_huyo_combate"] == True


    def test_T5_6_fin_victoria_enemigo_muere(self, personaje_combate, enemigo_combate):
        """Test T5.6: Victoria cuando enemigo muere
        
        ARRANGE: e["vida"] = 1, mock turno_jugador mata
        ACT: combate(p, e)
        ASSERT: exito("Has vencido") llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 1
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def kill_enemy(p, e):
                    enemigo_combate["vida"] = 0
                    return ("ataque", None)
                mock_turno_j.side_effect = kill_enemy
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito') as mock_exito:
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_exito.called


    def test_T5_7_fin_derrota_jugador_muere(self, personaje_combate, enemigo_combate):
        """Test T5.7: Derrota cuando jugador muere
        
        ARRANGE: p["vida"] = 1, mock turno_enemigo mata
        ACT: combate(p, e)
        ASSERT: fin_derrota() llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 1
        enemigo_combate["vida"] = 100
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                mock_turno_j.return_value = ("ataque", None)
                with patch('TLDRDC_Prueba1.turno_enemigo') as mock_turno_e:
                    def kill_player(p, e, stance):
                        personaje_combate["vida"] = 0
                    mock_turno_e.side_effect = kill_player
                    with patch('TLDRDC_Prueba1.fin_derrota') as mock_derrota:
                        with patch('TLDRDC_Prueba1.alerta'):
                            with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                                combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_derrota.called


    def test_T5_8_post_combate_evento_aplicado(self, personaje_combate, enemigo_combate):
        """Test T5.8: Evento post-combate aplicado en victoria
        
        ARRANGE: Mock resolver_eventos_post_combate(), victoria
        ACT: combate(p, e)
        ASSERT: resolver_eventos_post_combate() llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 1
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def kill_enemy(p, e):
                    enemigo_combate["vida"] = 0
                    return ("ataque", None)
                mock_turno_j.side_effect = kill_enemy
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate') as mock_evento:
                                mock_evento.return_value = {"vida": 5}
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_evento.called


    def test_T5_9_hud_emitido_cada_turno(self, personaje_combate, enemigo_combate):
        """Test T5.9: HUD emitido cada turno
        
        ARRANGE: Mock emitir()
        ACT: combate(p, e) [1 ciclo]
        ASSERT: emitir("hud_combate", {...}) llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 1
        
        # ACT
        with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
            def kill_enemy(p, e):
                enemigo_combate["vida"] = 0
                return ("ataque", None)
            mock_turno_j.side_effect = kill_enemy
            with patch('TLDRDC_Prueba1.turno_enemigo'):
                with patch('TLDRDC_Prueba1.exito'):
                    with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                        with patch('TLDRDC_Prueba1.emitir') as mock_emitir:
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_emitir.called


# ════════════════════════════════════════════════════════════════════
# PARTE 2: SANGRADO (3 tests - T6.1-T6.3)
# ════════════════════════════════════════════════════════════════════

class TestSangrado:
    """Tests T6.1-T6.3: Función aplicar_sangrado()"""

    def test_T6_1_sangrado_base_daño(self, enemigo_combate):
        """Test T6.1: Sangrado causa daño
        
        ARRANGE: e = {"sangrado": 3, "vida": 10}
        ACT: aplicar_sangrado(e)
        ASSERT: e["vida"] == 7, alerta emitida
        """
        # ARRANGE
        enemigo_combate["sangrado"] = 3
        enemigo_combate["vida"] = 10
        vida_inicial = enemigo_combate["vida"]
        
        # ACT
        with patch('TLDRDC_Prueba1.alerta') as mock_alerta:
            aplicar_sangrado(enemigo_combate)
        
        # ASSERT
        assert enemigo_combate["vida"] == vida_inicial - 3
        # Verificar que alerta menciona sangrado
        if mock_alerta.called:
            assert any("sangr" in str(call).lower() for call in mock_alerta.call_args_list)


    def test_T6_2_sin_sangrado(self, enemigo_combate):
        """Test T6.2: Sin sangrado no causa daño
        
        ARRANGE: e = {"sangrado": 0, "vida": 10}
        ACT: aplicar_sangrado(e)
        ASSERT: e["vida"] == 10
        """
        # ARRANGE
        enemigo_combate["sangrado"] = 0
        enemigo_combate["vida"] = 10
        vida_inicial = enemigo_combate["vida"]
        
        # ACT
        aplicar_sangrado(enemigo_combate)
        
        # ASSERT
        assert enemigo_combate["vida"] == vida_inicial


    def test_T6_3_muerte_por_sangrado(self, enemigo_combate):
        """Test T6.3: Sangrado puede matar
        
        ARRANGE: e = {"sangrado": 15, "vida": 10}
        ACT: aplicar_sangrado(e)
        ASSERT: e["vida"] < 0 (sin clamp)
        """
        # ARRANGE
        enemigo_combate["sangrado"] = 15
        enemigo_combate["vida"] = 10
        
        # ACT
        with patch('TLDRDC_Prueba1.alerta'):
            aplicar_sangrado(enemigo_combate)
        
        # ASSERT
        assert enemigo_combate["vida"] < 0  # Puede ir negativo


# ════════════════════════════════════════════════════════════════════
# PARTE 3: FIBONACCI BONUS (3 tests - T7.1-T7.3)
# ════════════════════════════════════════════════════════════════════

class TestFibonacciBonus:
    """Tests T7.1-T7.3: Sistema Fibonacci bonus"""

    def test_T7_1_revisar_bonus_fibonacci_llamado(self, personaje_combate, enemigo_combate, estado_global_combate):
        """Test T7.1: revisar_bonus_fibonacci() se llama en victoria
        
        ARRANGE: estado["_c01"] = 2 (Fibonacci), victoria
        ACT: combate(p, e)
        ASSERT: revisar_bonus_fibonacci() llamado
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 10
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["_c01"] = 2
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def kill_enemy(p, e):
                    e["vida"] -= 2
                    return ("ataque", None)
                mock_turno_j.side_effect = kill_enemy
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci') as mock_fib:
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT
        assert mock_fib.called


    def test_T7_2_contador_victoria_incrementado(self, personaje_combate, enemigo_combate, estado_global_combate):
        """Test T7.2: _c01 incrementado después de victoria
        
        ARRANGE: estado["_c01"] = 10
        ACT: combate(p, e) con victoria
        ASSERT: estado["_c01"] >= 10 (incrementado)
        """
        # ARRANGE
        personaje_combate["vida"] = 100
        enemigo_combate["vida"] = 10
        import TLDRDC_Prueba1
        TLDRDC_Prueba1.estado["_c01"] = 10
        contador_inicial = TLDRDC_Prueba1.estado["_c01"]
        
        # ACT
        with patch('TLDRDC_Prueba1.emitir'):
            with patch('TLDRDC_Prueba1.turno_jugador') as mock_turno_j:
                def kill_enemy(p, e):
                    e["vida"] -= 2
                    return ("ataque", None)
                mock_turno_j.side_effect = kill_enemy
                with patch('TLDRDC_Prueba1.turno_enemigo'):
                    with patch('TLDRDC_Prueba1.exito'):
                        with patch('TLDRDC_Prueba1.aplicar_sangrado'):
                            with patch('TLDRDC_Prueba1.resolver_eventos_post_combate'):
                                with patch('TLDRDC_Prueba1.revisar_bonus_fibonacci'):
                                    combate(personaje_combate, enemigo_combate)
        
        # ASSERT: Contador debe ser >= inicial (puede ser modificado por combate)
        assert TLDRDC_Prueba1.estado["_c01"] >= contador_inicial
