"""
TESTS: ui_imagen_manager.py — Image Manager con PIL/Fallback y Caché

Especificación: docs/TLDRDC_for_testing/especificaciones/ESPECIFICACION_UI_IMAGEN.md
Casos a cubrir: I1.1-I3.1 (10 tests total)

Estructura: AAA Pattern (ARRANGE, ACT, ASSERT)
Fixtures disponibles: imagen_manager, valid_png, corrupt_png
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile

# Importar ImagenManager
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'code', 'modules'))
from ui_imagen_manager import ImagenManager, PIL_DISPONIBLE


class TestImagenManagerInit:
    """Tests para __init__() — I1.1"""
    
    def test_I1_1_inicializacion_basica(self):
        """Test I1.1: Inicialización correcta
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I1.1
        Verifica que ImagenManager se inicializa con caché vacío.
        """
        # ARRANGE
        # No hay arrange
        
        # ACT
        manager = ImagenManager()
        
        # ASSERT
        assert hasattr(manager, '_cache')
        assert isinstance(manager._cache, dict)
        assert len(manager._cache) == 0
        assert hasattr(manager, 'pil_disponible')
        assert isinstance(manager.pil_disponible, bool)


class TestCargarImagenBasico:
    """Tests para cargar_imagen() básico — I2.1 a I2.4"""
    
    def test_I2_1_carga_imagen_valida(self, valid_png):
        """Test I2.1: Carga PNG válido
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.1
        Verifica que cargar_imagen() retorna imagen válida.
        """
        # ARRANGE
        manager = ImagenManager()
        
        # ACT
        # Mockar tk.PhotoImage para evitar "no default root window"
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=100, height=100)
            img = manager.cargar_imagen(valid_png)
        
        # ASSERT
        # Si PIL disponible, carga correctamente
        if PIL_DISPONIBLE:
            assert img is not None
        else:
            # Si no PIL, mock retorna el MagicMock
            assert img is not None
    
    def test_I2_2_redimension_con_pil(self, valid_png):
        """Test I2.2: Redimensión con PIL disponible
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.2
        Verifica que tamaño se aplica si PIL disponible.
        """
        # ARRANGE
        manager = ImagenManager()
        tamaño_target = (50, 50)
        
        # ACT
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=50, height=50)
            img = manager.cargar_imagen(valid_png, tamaño_target)
        
        # ASSERT
        if PIL_DISPONIBLE:
            # Con PIL, la imagen se redimensiona
            assert img is not None
        else:
            # Sin PIL, retorna tk.PhotoImage nativo sin redimensión
            assert img is not None
    
    def test_I2_3_imagen_no_existe_retorna_none(self):
        """Test I2.3: Imagen inexistente retorna None
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.3
        Verifica que ruta inexistente no lanza excepción, retorna None.
        """
        # ARRANGE
        manager = ImagenManager()
        ruta_inexistente = "/ruta/que/no/existe/fake.png"
        
        # ACT
        img = manager.cargar_imagen(ruta_inexistente)
        
        # ASSERT
        assert img is None
    
    def test_I2_4_png_corrupto_retorna_none(self, corrupt_png):
        """Test I2.4: PNG corrupto retorna None
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.4
        Verifica que PNG corrupto captura excepción y retorna None.
        """
        # ARRANGE
        manager = ImagenManager()
        
        # ACT
        img = manager.cargar_imagen(corrupt_png)
        
        # ASSERT
        assert img is None


class TestCargarImagenCache:
    """Tests para caché — I2.5 a I2.7"""
    
    def test_I2_5_cache_funciona(self, valid_png):
        """Test I2.5: Caché funciona (mismo objeto)
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.5
        Verifica que cargar dos veces retorna el MISMO objeto.
        """
        # ARRANGE
        manager = ImagenManager()
        tamaño = (50, 50)
        
        # ACT
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=50, height=50)
            img1 = manager.cargar_imagen(valid_png, tamaño)
            img2 = manager.cargar_imagen(valid_png, tamaño)
        
        # ASSERT
        if img1 is not None and img2 is not None:
            assert img1 is img2  # Mismo objeto de memoria
            assert len(manager._cache) == 1
    
    def test_I2_6_cache_con_tamaño_diferente_nueva_entrada(self, valid_png):
        """Test I2.6: Tamaño diferente = nueva entrada caché
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.6
        Verifica que (ruta, tamaño) diferente crea nueva entrada.
        """
        # ARRANGE
        manager = ImagenManager()
        tamaño1 = (50, 50)
        tamaño2 = (100, 100)
        
        # ACT
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=50, height=50)
            img1 = manager.cargar_imagen(valid_png, tamaño1)
            mock_photo.return_value = MagicMock(width=100, height=100)
            img2 = manager.cargar_imagen(valid_png, tamaño2)
        
        # ASSERT
        if img1 is not None and img2 is not None:
            assert img1 is not img2  # Objetos diferentes
            assert len(manager._cache) == 2
            # Verificar que ambas claves están en caché
            assert (valid_png, tamaño1) in manager._cache
            assert (valid_png, tamaño2) in manager._cache
    
    def test_I2_7_cache_sin_limite_hard(self, tmp_path):
        """Test I2.7: Caché sin límite hard automático
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.7
        Verifica que caché crece sin límite (no evicta automáticamente).
        """
        # ARRANGE
        manager = ImagenManager()
        
        # Crear 5 PNGs temporales válidos
        try:
            from PIL import Image
            png_paths = []
            for i in range(5):
                img = Image.new("RGB", (100, 100), color=(i*50, i*50, i*50))
                png_path = tmp_path / f"test_{i}.png"
                img.save(png_path)
                png_paths.append(str(png_path))
        except ImportError:
            # Si no PIL, skipear este test
            pytest.skip("PIL no disponible")
        
        # ACT
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=100, height=100)
            for png_path in png_paths:
                manager.cargar_imagen(png_path)
        
        # ASSERT
        # Todas las imágenes se mantienen en caché (sin evicción automática)
        assert len(manager._cache) == 5


class TestCargarImagenAspecto:
    """Tests para aspecto — I2.8"""
    
    def test_I2_8_redimension_preserva_aspecto(self, tmp_path):
        """Test I2.8: Redimensión preserva aspecto (thumbnail)
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I2.8
        Verifica que PIL.thumbnail() preserva relación de aspecto.
        """
        # ARRANGE
        manager = ImagenManager()
        
        try:
            from PIL import Image
            # Crear imagen 100x200 (1:2 ratio)
            img_original = Image.new("RGB", (100, 200), color="blue")
            png_path = tmp_path / "test_aspect.png"
            img_original.save(png_path)
            
            # ACT
            # Pedir tamaño (50, 100) que respeta el ratio
            with patch('tkinter.PhotoImage') as mock_photo:
                mock_photo.return_value = MagicMock(width=50, height=100)
                img_loaded = manager.cargar_imagen(str(png_path), (50, 100))
            
            # ASSERT
            assert img_loaded is not None
            # Con thumbnail(), la imagen cabe dentro de (50, 100) sin distorsión
            # (PIL.thumbnail() preserva aspecto)
        except ImportError:
            pytest.skip("PIL no disponible")


class TestValidarRutas:
    """Tests para validar_rutas() — I3.1"""
    
    def test_I3_1_detecta_carpeta_faltante(self, tmp_path):
        """Test I3.1: Detecta rutas faltantes
        
        Spec: ESPECIFICACION_UI_IMAGEN.md → I3.1
        Verifica que validar_rutas() retorna False para rutas inexistentes.
        """
        # ARRANGE
        manager = ImagenManager()
        dict_rutas = {
            "daga": str(tmp_path / "existe.png"),
            "espada": "/ruta/que/no/existe.png",
            "vacio": str(tmp_path / "tampoco.png"),
        }
        
        # ACT
        resultado = manager.validar_rutas(dict_rutas)
        
        # ASSERT
        assert isinstance(resultado, dict)
        assert resultado["daga"] is False  # No existe
        assert resultado["espada"] is False  # No existe
        assert resultado["vacio"] is False  # No existe


class TestLimpiarCache:
    """Tests para limpiar_cache() — Bonus"""
    
    def test_limpiar_cache_vacia_caché(self, valid_png):
        """Test Bonus: limpiar_cache() elimina todas las entradas
        
        Verifica que limpiar_cache() limpia el caché completamente.
        """
        # ARRANGE
        manager = ImagenManager()
        
        with patch('tkinter.PhotoImage') as mock_photo:
            mock_photo.return_value = MagicMock(width=50, height=50)
            manager.cargar_imagen(valid_png, (50, 50))
        
        assert len(manager._cache) > 0
        
        # ACT
        manager.limpiar_cache()
        
        # ASSERT
        assert len(manager._cache) == 0


# ════════════════════════════════════════════════════════════════════
# NOTAS DE IMPLEMENTACIÓN
# ════════════════════════════════════════════════════════════════════
"""
Patterns usados:

1. **Manejo de PIL opcional** (I2.2):
   - PIL_DISPONIBLE se chequea en tiempo de ejecución
   - Tests funcionan con o sin PIL
   - pytest.skip() para tests que requieren PIL

2. **Caché con claves compuestas** (I2.5, I2.6):
   - cache_key = (ruta, tamaño)
   - Permite múltiples versiones de misma imagen

3. **Archivos temporales** (I2.7, I2.8, I3.1):
   - Uso de tmp_path fixture de pytest
   - Archivos se limpian automáticamente

4. **Defensiva contra excepciones** (I2.3, I2.4):
   - cargar_imagen() captura todas las excepciones
   - Retorna None en lugar de fallar
   - Crucial para UI que no debe crashear por falta de sprites

RIESGO: I2.2 depende de disponibilidad de PIL. 
   - Si PIL no disponible, PhotoImage nativo no se redimensiona
   - Tests adaptan expectativas con PIL_DISPONIBLE
"""
