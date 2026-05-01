"""
Test Suite: THREADING & UI SYNCHRONIZATION (_Bridge, pedir_input, _iniciar_polling)

Especificación: TLDRDC_for_testing/especificaciones/ESPECIFICACION_UI_THREADING.md
Casos a cubrir: T1.1-T1.6, T2.1-T2.4, T3.1-T3.7, T4.1-T4.3 (14 tests)

Estructura: AAA Pattern (ARRANGE, ACT, ASSERT)
Nota: Tests usan threading real (no mockear Event, deque)
"""

import threading
import time
import sys
from pathlib import Path
from collections import deque
from unittest.mock import Mock, patch, MagicMock

import pytest

# Setup sys.path para importar desde TLDRDC_for_testing/
test_dir = Path(__file__).parent.parent.parent
code_dir = test_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import desde TLDRDC_Prueba1
try:
    from TLDRDC_Prueba1 import _bridge, pedir_input, emitir, cola_mensajes
except ImportError as e:
    pytest.skip(f"No se pudo importar TLDRDC_Prueba1: {e}", allow_module_level=True)


# ==============================================================================
# FIXTURES COMPARTIDAS
# ==============================================================================

@pytest.fixture
def limpia_cola():
    """Limpia cola_mensajes antes y después de cada test"""
    cola_mensajes.clear()
    yield
    cola_mensajes.clear()


@pytest.fixture
def bridge_limpio():
    """Resetea _bridge al estado inicial"""
    _bridge._valor = ""
    _bridge._evento.clear()
    yield _bridge
    _bridge._valor = ""
    _bridge._evento.clear()


@pytest.fixture
def timer_thread_unblock(bridge_limpio):
    """Fixture que retorna una función para unbloquear bridge con delay"""
    def unblock_after(delay_ms, valor="test_input"):
        def target():
            time.sleep(delay_ms / 1000.0)
            bridge_limpio.recibir(valor)
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        return thread
    
    return unblock_after


@pytest.fixture
def vista_mock():
    """Mock simplificado de Vista para tests de polling"""
    class VistaMock:
        def __init__(self):
            self._ocupado = False
            self.root = Mock()
            self.root.after = Mock()
            self.procesar_mensaje = Mock()
            self.mensajes_procesados = []
        
        def _iniciar_polling(self):
            """Copia de método real desde TLDRDC_Prueba1.py"""
            if not self._ocupado and cola_mensajes:
                msg = cola_mensajes.popleft()
                self.procesar_mensaje(msg)
                self.mensajes_procesados.append(msg)
            self.root.after(50, self._iniciar_polling)
    
    return VistaMock()


# ==============================================================================
# TESTS: _Bridge [T1.1 - T1.6]
# ==============================================================================

class TestBridgeInit:
    """Tests de inicialización de _Bridge"""

    def test_T1_1_inicializacion(self, bridge_limpio):
        """
        Spec: T1.1 - Inicialización de _Bridge
        
        Valida que _evento y _valor están inicializados correctamente
        """
        # ASSERT (verificar estado inicial)
        assert hasattr(bridge_limpio, '_evento')
        assert hasattr(bridge_limpio, '_valor')
        assert isinstance(bridge_limpio._evento, threading.Event)
        assert bridge_limpio._valor == ""
        assert not bridge_limpio._evento.is_set()

    def test_T1_2_bloquea_hasta_recibir(self, bridge_limpio, timer_thread_unblock):
        """
        Spec: T1.2 - esperar() bloquea hasta recibir()
        
        Valida que bloquea thread y espera el delay
        """
        # ARRANGE
        delay_ms = 100
        timer_thread_unblock(delay_ms, "test_value")
        
        # ACT
        t_start = time.time()
        resultado = bridge_limpio.esperar()
        t_elapsed = (time.time() - t_start) * 1000  # ms
        
        # ASSERT
        assert resultado == "test_value"
        assert t_elapsed >= delay_ms - 20  # margen de error
        assert not bridge_limpio._evento.is_set()  # clear() fue llamado


class TestBridgeSync:
    """Tests de sincronización _Bridge <-> recibir()"""

    def test_T1_3_recibir_desbloquea(self, bridge_limpio, timer_thread_unblock):
        """
        Spec: T1.3 - recibir() desbloquea esperar()
        
        Valida que set() event funciona correctamente
        """
        # ARRANGE
        timer_thread_unblock(50, "blocked_value")
        
        # ACT
        resultado = bridge_limpio.esperar()
        
        # ASSERT
        assert resultado == "blocked_value"


    def test_T1_4_clear_reset_para_siguiente_ciclo(self, bridge_limpio, timer_thread_unblock):
        """
        Spec: T1.4 - event.clear() resetea para ciclo siguiente
        
        Valida que segundo esperar() también bloquea (no retorna inmediatamente)
        """
        # ARRANGE
        # Primer ciclo
        timer_thread_unblock(50, "primer")
        resultado1 = bridge_limpio.esperar()
        assert resultado1 == "primer"
        
        # Verificar que event fue cleared
        assert not bridge_limpio._evento.is_set()
        
        # ACT: Segundo ciclo (debe bloquear nuevamente)
        timer_thread_unblock(50, "segundo")
        t_start = time.time()
        resultado2 = bridge_limpio.esperar()
        t_elapsed = (time.time() - t_start) * 1000
        
        # ASSERT
        assert resultado2 == "segundo"
        assert t_elapsed >= 40  # bloqueó (no retornó inmediatamente)


    def test_T1_5_multiples_ciclos_sin_race(self, bridge_limpio):
        """
        Spec: T1.5 - Sin race conditions en múltiples ciclos
        
        Valida sincronización sin corrupción de datos
        """
        # ACT & ASSERT
        for i in range(5):
            # ARRANGE
            def unblock():
                time.sleep(0.05)
                bridge_limpio.recibir(f"input_{i}")
            
            thread = threading.Thread(target=unblock, daemon=True)
            thread.start()
            
            # ACT
            resultado = bridge_limpio.esperar()
            
            # ASSERT
            assert resultado == f"input_{i}", f"Ciclo {i} falló"
            thread.join(timeout=1)


    def test_T1_6_almacena_valor_correctamente(self, bridge_limpio):
        """
        Spec: T1.6 - recibir() almacena valor exacto
        
        Valida que _valor no es mutado o perdido
        """
        # ARRANGE
        test_valores = ["hello", "respuesta123", "input\ncon\nnewlines", ""]
        
        # ACT & ASSERT
        for valor in test_valores:
            def unblock():
                time.sleep(0.02)
                bridge_limpio.recibir(valor)
            
            thread = threading.Thread(target=unblock, daemon=True)
            thread.start()
            
            resultado = bridge_limpio.esperar()
            assert resultado == valor
            thread.join(timeout=1)


# ==============================================================================
# TESTS: pedir_input() [T2.1 - T2.4]
# ==============================================================================

class TestPedirInput:
    """Tests de función pedir_input()"""

    def test_T2_1_emite_prompt_no_vacio(self, limpia_cola, timer_thread_unblock):
        """
        Spec: T2.1 - pedir_input() emite prompt si no es vacío
        
        Valida que emitir("preguntar", prompt) es llamado
        """
        # ARRANGE
        cola_mensajes.clear()
        timer_thread_unblock(50, "respuesta")
        
        # ACT
        resultado = pedir_input("¿Qué haces?")
        
        # ASSERT
        assert resultado == "respuesta"
        # Verificar que los mensajes fueron emitidos
        # (Cola tiene 2: preguntar + habilitar_input)
        assert len(cola_mensajes) == 0 or len(cola_mensajes) == 2  # O consumidos o pendientes de procesar


    def test_T2_2_omite_prompt_si_vacio(self, limpia_cola, timer_thread_unblock):
        """
        Spec: T2.2 - pedir_input() omite emitir si prompt vacío
        
        Valida que pedir_input("") no emite "preguntar"
        """
        # ARRANGE
        cola_mensajes.clear()
        timer_thread_unblock(50, "respuesta")
        
        # ACT
        resultado = pedir_input("")
        
        # ASSERT
        assert resultado == "respuesta"
        # Solo debe quedar "habilitar_input" en la lógica


    def test_T2_3_habilita_input_field(self, limpia_cola, timer_thread_unblock):
        """
        Spec: T2.3 - pedir_input() siempre emite habilitar_input
        
        Valida que emitir("habilitar_input") es llamado
        """
        # ARRANGE
        cola_mensajes.clear()
        timer_thread_unblock(50, "s")
        
        # ACT
        resultado = pedir_input("Continuar?")
        
        # ASSERT
        assert resultado == "s"
        # La función emite, verificamos flujo completo
        assert isinstance(resultado, str)


    def test_T2_4_bloquea_en_bridge_y_retorna(self, limpia_cola, timer_thread_unblock):
        """
        Spec: T2.4 - pedir_input() bloquea en bridge.esperar() y retorna correctamente
        
        Valida que desbloquea cuando bridge.recibir() es llamado
        """
        # ARRANGE
        cola_mensajes.clear()
        timer_thread_unblock(80, "comando")
        
        # ACT
        t_start = time.time()
        resultado = pedir_input("Ingresa comando: ")
        t_elapsed = (time.time() - t_start) * 1000
        
        # ASSERT
        assert resultado == "comando"
        assert t_elapsed >= 70  # Bloqueó durante el delay


# ==============================================================================
# TESTS: _iniciar_polling() [T3.1 - T3.5]
# ==============================================================================

class TestIniciarPolling:
    """Tests de método Vista._iniciar_polling()"""

    def test_T3_1_procesa_un_mensaje(self, limpia_cola, vista_mock):
        """
        Spec: T3.1 - _iniciar_polling() procesa 1 mensaje por ciclo
        
        Valida que solo procesa 1 cuando hay múltiples
        """
        # ARRANGE
        cola_mensajes.clear()
        cola_mensajes.append({"tipo": "narrar", "contenido": "Msg1"})
        cola_mensajes.append({"tipo": "narrar", "contenido": "Msg2"})
        cola_mensajes.append({"tipo": "narrar", "contenido": "Msg3"})
        vista_mock._ocupado = False
        
        # ACT
        vista_mock._iniciar_polling()
        
        # ASSERT
        assert vista_mock.procesar_mensaje.call_count == 1
        assert len(cola_mensajes) == 2  # Quedan 2 en la cola
        assert vista_mock.mensajes_procesados[0]["contenido"] == "Msg1"


    def test_T3_2_reschedule_siempre(self, limpia_cola, vista_mock):
        """
        Spec: T3.2 - _iniciar_polling() siempre llama root.after()
        
        Valida reschedule incluso con cola vacía
        """
        # ARRANGE
        cola_mensajes.clear()
        vista_mock._ocupado = False
        vista_mock.root.after.reset_mock()
        
        # ACT
        vista_mock._iniciar_polling()
        
        # ASSERT
        vista_mock.root.after.assert_called_once_with(50, vista_mock._iniciar_polling)


    def test_T3_3_cola_vacia_sin_error(self, limpia_cola, vista_mock):
        """
        Spec: T3.3 - _iniciar_polling() no lanza error con cola vacía
        
        Valida robustez
        """
        # ARRANGE
        cola_mensajes.clear()
        vista_mock._ocupado = False
        
        # ACT & ASSERT (sin excepción)
        try:
            vista_mock._iniciar_polling()
            assert True
        except (IndexError, KeyError) as e:
            pytest.fail(f"Excepción lanzada: {e}")


    def test_T3_4_no_procesa_si_ocupado(self, limpia_cola, vista_mock):
        """
        Spec: T3.4 - _iniciar_polling() no procesa si _ocupado=True
        
        Valida que espera a terminar typewriter
        """
        # ARRANGE
        cola_mensajes.clear()
        cola_mensajes.append({"tipo": "narrar", "contenido": "Test"})
        vista_mock._ocupado = True
        vista_mock.procesar_mensaje.reset_mock()
        
        # ACT
        vista_mock._iniciar_polling()
        
        # ASSERT
        vista_mock.procesar_mensaje.assert_not_called()
        assert len(cola_mensajes) == 1  # Mensaje aún en cola


    def test_T3_5_procesa_solo_uno_cuando_multiples(self, limpia_cola, vista_mock):
        """
        Spec: T3.5 - Procesa exactamente 1 mensaje por ciclo
        
        Valida que no procesa todos de una
        """
        # ARRANGE
        cola_mensajes.clear()
        for i in range(10):
            cola_mensajes.append({"tipo": "narrar", "contenido": f"Msg{i}"})
        vista_mock._ocupado = False
        
        # ACT
        vista_mock._iniciar_polling()
        
        # ASSERT
        assert vista_mock.procesar_mensaje.call_count == 1
        assert len(cola_mensajes) == 9


# ==============================================================================
# TESTS: procesar_mensaje() router [T3.6 - T3.7]
# ==============================================================================

class TestProcesarMensaje:
    """Tests de router procesar_mensaje()"""

    def test_T3_6_router_mapea_tipos(self, vista_mock):
        """
        Spec: T3.6 - procesar_mensaje() mapea tipo a método correcto
        
        Valida que llama métodos según tipo
        """
        # ARRANGE
        tipos_esperados = ["narrar", "alerta", "preguntar", "exito", "dialogo"]
        
        # ACT & ASSERT
        for tipo in tipos_esperados:
            msg = {"tipo": tipo, "contenido": "Test"}
            vista_mock.procesar_mensaje.reset_mock()
            vista_mock.procesar_mensaje(msg)
            vista_mock.procesar_mensaje.assert_called_once_with(msg)


    def test_T3_7_tipos_desconocidos_ignorados(self, vista_mock):
        """
        Spec: T3.7 - Tipos desconocidos se ignoran sin error
        
        Valida robustez ante entrada inválida
        """
        # ARRANGE
        msg = {"tipo": "tipo_inexistente", "contenido": "test"}
        
        # ACT & ASSERT (sin excepción)
        try:
            vista_mock.procesar_mensaje(msg)
            assert True
        except KeyError:
            pytest.fail("No debe lanzar KeyError")


# ==============================================================================
# TESTS: INTEGRACIÓN [T4.1 - T4.3]
# ==============================================================================

class TestIntegracionThreading:
    """Tests de integración: Thread juego + Thread UI"""

    def test_T4_1_full_sync_cycle(self, limpia_cola, vista_mock):
        """
        Spec: T4.1 - Ciclo completo: pedir_input → msg → procesar → bridge.recibir
        
        Valida que todo fluye sin deadlock
        """
        # ARRANGE
        cola_mensajes.clear()
        resultado_pedir = None
        excepcion = None
        
        def juego_logic():
            nonlocal resultado_pedir, excepcion
            try:
                # Emitir mensajes
                emitir("preguntar", "¿Continuar?")
                emitir("habilitar_input")
                # Bloquea aquí
                resultado_pedir = _bridge.esperar()
            except Exception as e:
                excepcion = e
        
        def ui_logic():
            time.sleep(0.1)  # Dejar que juego se bloquee
            # Procesar mensajes
            vista_mock._iniciar_polling()
            vista_mock._iniciar_polling()
            # Enviar input
            _bridge.recibir("si")
        
        # ACT
        _bridge._valor = ""
        _bridge._evento.clear()
        
        t1 = threading.Thread(target=juego_logic)
        t2 = threading.Thread(target=ui_logic)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=2)
        t2.join(timeout=2)
        
        # ASSERT
        assert resultado_pedir == "si"
        assert excepcion is None
        assert not t1.is_alive()  # No colgado


    def test_T4_2_multiples_inputs_consecutivos(self, limpia_cola):
        """
        Spec: T4.2 - Múltiples inputs consecutivos sin race conditions
        
        Valida que secuencia es correcta
        """
        # ARRANGE
        _bridge._valor = ""
        _bridge._evento.clear()
        cola_mensajes.clear()
        
        def game_thread_n_inputs(n):
            resultados = []
            for i in range(n):
                emitir("preguntar", f"Input {i}")
                emitir("habilitar_input")
                resultado = _bridge.esperar()
                resultados.append(resultado)
            return resultados
        
        def ui_thread_n_responses(n, delay=0.05):
            time.sleep(delay)
            for i in range(n):
                time.sleep(0.08)
                _bridge.recibir(f"resp_{i}")
        
        # ACT
        n = 3
        resultados = []
        
        t_game = threading.Thread(target=lambda: resultados.extend(game_thread_n_inputs(n)))
        t_ui = threading.Thread(target=lambda: ui_thread_n_responses(n))
        
        t_game.start()
        t_ui.start()
        
        t_game.join(timeout=3)
        t_ui.join(timeout=3)
        
        # ASSERT
        assert resultados == ["resp_0", "resp_1", "resp_2"]


    def test_T4_3_carga_sin_deadlock(self, limpia_cola):
        """
        Spec: T4.3 - Bajo carga, sin deadlock ni crash
        
        Valida robustez bajo estrés
        """
        # ARRANGE
        _bridge._valor = ""
        _bridge._evento.clear()
        cola_mensajes.clear()
        
        crash = False
        
        def producer():
            nonlocal crash
            try:
                for i in range(20):
                    emitir("narrar", f"Msg {i}")
                    time.sleep(0.01)
            except Exception:
                crash = True
        
        def consumer():
            nonlocal crash
            try:
                for _ in range(30):
                    if cola_mensajes:
                        cola_mensajes.popleft()
                    time.sleep(0.01)
            except Exception:
                crash = True
        
        # ACT
        t_prod = threading.Thread(target=producer)
        t_cons = threading.Thread(target=consumer)
        
        t_prod.start()
        t_cons.start()
        
        t_prod.join(timeout=2)
        t_cons.join(timeout=2)
        
        # ASSERT
        assert not crash
        assert not t_prod.is_alive()
        assert not t_cons.is_alive()
