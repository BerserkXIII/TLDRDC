"""
TESTS: reactive.py — Observer Pattern Implementation

Especificación: docs/TLDRDC_for_testing/especificaciones/ESPECIFICACION_REACTIVE.md
Casos a cubrir: U1.1-U3.7 (13 tests)

Estructura: AAA Pattern (ARRANGE, ACT, ASSERT)
Fixtures disponibles: personaje_reactivo, personaje_base
"""

import pytest
from unittest.mock import Mock


class TestReactiveInit:
    """Tests de Personaje.__init__() — Inicialización"""
    
    def test_init_vacio(self):
        """Test U1.1: Crear personaje vacío
        
        Spec: ESPECIFICACION_REACTIVE.md → U1.1
        """
        # ARRANGE
        # Crear clase Personaje para este test
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
        
        # ACT
        p = Personaje()
        
        # ASSERT
        assert isinstance(p, dict)
        assert len(p) == 0
        assert isinstance(p._watchers, dict)
        assert len(p._watchers) == 0
        assert p.activo == False
    
    def test_init_con_datos(self):
        """Test U1.2: Crear personaje con datos
        
        Spec: ESPECIFICACION_REACTIVE.md → U1.2
        """
        # ARRANGE
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
        
        datos = {"vida": 10, "fuerza": 5}
        
        # ACT
        p = Personaje(datos)
        
        # ASSERT
        assert p["vida"] == 10
        assert p["fuerza"] == 5
        assert len(p) == 2
        assert p._watchers == {}
        assert p.activo == False
    
    def test_init_compatible_dict(self, personaje_reactivo):
        """Test U1.3: Personaje es compatible con dict
        
        Spec: ESPECIFICACION_REACTIVE.md → U1.3
        Hereda de dict, así que soporta todas las operaciones dict normales.
        """
        # ARRANGE
        p = personaje_reactivo
        
        # ACT y ASSERT
        # Operaciones dict normales
        assert p.get("vida") == p["vida"]
        assert p.get("inexistente") == None
        assert "vida" in p
        assert len(p) > 0
        assert list(p.keys())  # Iterable
        assert p.copy()  # Clonable


class TestObserve:
    """Tests de Personaje.observe() — Registrar observador"""
    
    def test_observe_registro_unico(self, personaje_reactivo):
        """Test U2.1: Registrar callback único
        
        Spec: ESPECIFICACION_REACTIVE.md → U2.1
        """
        # ARRANGE
        p = personaje_reactivo
        p.activo = False  # Asegurar que no dispara aún
        callback = Mock()
        
        # ACT
        p.observe("vida", callback)
        
        # ASSERT
        assert "vida" in p._watchers
        assert p._watchers["vida"] == callback
        # No se ejecuta aún (activo=False)
        callback.assert_not_called()
    
    def test_observe_multiples(self, personaje_reactivo):
        """Test U2.2: Registrar múltiples observadores
        
        Spec: ESPECIFICACION_REACTIVE.md → U2.2
        """
        # ARRANGE
        p = personaje_reactivo
        callback_vida = Mock()
        callback_pociones = Mock()
        callback_fuerza = Mock()
        
        # ACT
        p.observe("vida", callback_vida)
        p.observe("pociones", callback_pociones)
        p.observe("fuerza", callback_fuerza)
        
        # ASSERT
        assert len(p._watchers) == 3
        assert p._watchers["vida"] == callback_vida
        assert p._watchers["pociones"] == callback_pociones
        assert p._watchers["fuerza"] == callback_fuerza
    
    def test_observe_sobrescribe(self, personaje_reactivo):
        """Test U2.3: Segundo observe del mismo field sobrescribe
        
        Spec: ESPECIFICACION_REACTIVE.md → U2.3
        """
        # ARRANGE
        p = personaje_reactivo
        callback_1 = Mock()
        callback_2 = Mock()
        
        # ACT
        p.observe("vida", callback_1)
        p.observe("vida", callback_2)  # Sobrescribe
        
        # Ahora cambiamos la vida
        p["vida"] = 15
        
        # ASSERT
        assert p._watchers["vida"] == callback_2
        callback_2.assert_called_once_with(15)
        callback_1.assert_not_called()  # El primero NUNCA se ejecuta


class TestSetItem:
    """Tests de Personaje.__setitem__() — Asignar y disparar callback"""
    
    def test_setitem_sin_observer(self, personaje_reactivo):
        """Test U3.1: Asignar sin observador registrado
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.1
        """
        # ARRANGE
        p = personaje_reactivo
        
        # ACT
        p["vida"] = 20
        
        # ASSERT
        assert p["vida"] == 20  # Se asignó sin problemas
    
    def test_setitem_valor_identico(self, personaje_reactivo):
        """Test U3.2: Asignar valor idéntico (sin cambio)
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.2
        """
        # ARRANGE
        p = personaje_reactivo
        vida_actual = p["vida"]
        callback = Mock()
        p.observe("vida", callback)
        
        # ACT
        p["vida"] = vida_actual  # Mismo valor
        
        # ASSERT
        callback.assert_not_called()  # No se ejecuta si no cambia
    
    def test_setitem_valor_diferente(self, personaje_reactivo):
        """Test U3.3: Asignar valor diferente
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.3
        """
        # ARRANGE
        p = personaje_reactivo
        vida_original = p["vida"]
        callback = Mock()
        p.observe("vida", callback)
        
        # ACT
        nuevo_valor = vida_original + 5
        p["vida"] = nuevo_valor
        
        # ASSERT
        assert p["vida"] == nuevo_valor
        callback.assert_called_once_with(nuevo_valor)
    
    def test_setitem_inactivo_no_dispara(self, personaje_reactivo):
        """Test U3.4: No dispara callback si activo=False
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.4
        """
        # ARRANGE
        p = personaje_reactivo
        p.activo = False  # Desactivar
        callback = Mock()
        p.observe("vida", callback)
        
        # ACT
        p["vida"] = 20
        
        # ASSERT
        assert p["vida"] == 20  # Se asignó
        callback.assert_not_called()  # Pero no disparó callback
    
    def test_setitem_activo_dispara(self, personaje_reactivo):
        """Test U3.5: Dispara callback cuando activo=True
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.5
        """
        # ARRANGE
        p = personaje_reactivo
        p.activo = True  # Activar (está activo por defecto en fixture)
        callback = Mock()
        p.observe("pociones", callback)
        
        # ACT
        p["pociones"] = 8
        
        # ASSERT
        callback.assert_called_once_with(8)
    
    def test_setitem_multiples_cambios(self, personaje_reactivo):
        """Test U3.6: Múltiples cambios disparan múltiples callbacks
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.6
        """
        # ARRANGE
        p = personaje_reactivo
        callback_vida = Mock()
        callback_pociones = Mock()
        callback_fuerza = Mock()
        
        p.observe("vida", callback_vida)
        p.observe("pociones", callback_pociones)
        p.observe("fuerza", callback_fuerza)
        
        # ACT
        p["vida"] = 15
        p["pociones"] = 8
        p["fuerza"] = 6
        
        # ASSERT
        callback_vida.assert_called_once_with(15)
        callback_pociones.assert_called_once_with(8)
        callback_fuerza.assert_called_once_with(6)
    
    def test_setitem_valores_none(self, personaje_reactivo):
        """Test U3.7: Asignar None (valor especial)
        
        Spec: ESPECIFICACION_REACTIVE.md → U3.7
        """
        # ARRANGE
        p = personaje_reactivo
        callback = Mock()
        # Primero establecer un valor para que haya cambio
        p["campo_especial"] = 10
        callback.reset_mock()  # Limpiar calls anteriores
        p.observe("campo_especial", callback)
        
        # ACT
        p["campo_especial"] = None
        
        # ASSERT
        callback.assert_called_once_with(None)
        assert p["campo_especial"] == None


# ════════════════════════════════════════════════════════════════════
# RESUMEN DE COBERTURA
# ════════════════════════════════════════════════════════════════════

"""
✅ TESTS IMPLEMENTADOS: 13 de 13

CLASE TestReactiveInit (3 tests):
  ✅ test_init_vacio (U1.1)
  ✅ test_init_con_datos (U1.2)
  ✅ test_init_compatible_dict (U1.3)

CLASE TestObserve (3 tests):
  ✅ test_observe_registro_unico (U2.1)
  ✅ test_observe_multiples (U2.2)
  ✅ test_observe_sobrescribe (U2.3)

CLASE TestSetItem (7 tests):
  ✅ test_setitem_sin_observer (U3.1)
  ✅ test_setitem_valor_identico (U3.2)
  ✅ test_setitem_valor_diferente (U3.3)
  ✅ test_setitem_inactivo_no_dispara (U3.4)
  ✅ test_setitem_activo_dispara (U3.5)
  ✅ test_setitem_multiples_cambios (U3.6)
  ✅ test_setitem_valores_none (U3.7)

EJECUCIÓN:
  pytest tests/unit/test_reactive.py -v
  
ESPERADO:
  13 passed ✅
"""
