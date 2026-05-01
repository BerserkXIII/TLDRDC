"""
PARSER - Interactive Command Parser for UI Tester
==================================================

Processes user commands from Vista's input field.
Commands are validated against weapon/enemy lists from mocks.py

Commands (Phase 1):
    arma [nombre]    - Add weapon
    pociones [0-10]  - Change potion count
    status           - Show character state
    inventory        - List weapons
    help             - Show commands
    clear            - Clear text panel
    exit             - Exit tester
"""

from . import mocks
from .mocks import (
    personaje_global, estado, 
    ARMAS_NOMBRES, ARMAS_ABREVIATURAS,
    ENEMIGOS_NOMBRES, ENEMIGOS_ESPECIALES
)

def _log(texto, tipo="narrar"):
    """Helper to emit message to Vista queue (thread-safe).
    
    Accesses mocks.emitir as module reference (not direct import)
    so that injection from main.py is visible.
    """
    if mocks.emitir:
        mocks.emitir(tipo, texto)
    else:
        # Debug: if emitir is None, log to console
        print(f"[DEBUG] _log() FALLBACK: emitir=None, tipo={tipo}, texto={texto[:50]}")


class TesterParser:
    """
    Interactive parser for tester commands.
    Receives user input from Vista and processes it.
    """
    
    def __init__(self, vista, tldrdc_game):
        """
        Args:
            vista: Vista instance (UI controller)
            tldrdc_game: TLDRDC_Prueba1 module (contains game functions)
        """
        self.vista = vista
        self.tldrdc_game = tldrdc_game
        
        # Reference to game functions
        self.añadir_arma_func = getattr(tldrdc_game, 'añadir_arma', None)
        
        # Bind parser as Vista's input callback
        self.vista.parser_entry.bind("<Return>", self._handle_return)
        self.vista.parser_entry.config(state="normal")
        self.vista._input_activo = True
        self.vista.parser_entry.focus()
        
        self.mostrar_bienvenida()
    
    def _handle_return(self, event):
        """Handle Return key in entry widget (non-blocking)."""
        entrada = self.vista.parser_entry.get().strip()
        self.vista.parser_entry.delete(0, "end")
        
        if entrada:
            self.procesar_comando(entrada)
        return "break"  # Prevent default Enter behavior
    
    def mostrar_bienvenida(self):
        """Display welcome and initial help."""
        _log("\n" + "="*70, "narrar")
        _log("🎮 UI TESTER VISUAL - TLDRDC (FASE 1)", "narrar")
        _log("="*70, "narrar")
        _log("\nInterfaz gráfica cargada. Escribe comandos en el parser.", "narrar")
        _log("Escribe 'help' para ver todos los comandos disponibles.\n", "narrar")
        self.mostrar_ayuda()
    
    def procesar_comando(self, entrada_raw):
        """
        Process command from Vista parser entry.
        Called by _handle_return() when user presses Enter.
        """
        entrada = entrada_raw.strip().lower()
        if not entrada:
            return
        
        # Parse command and arguments
        partes = entrada.split(maxsplit=1)
        cmd = partes[0]
        args = partes[1] if len(partes) > 1 else ""
        
        # Dispatch command
        if cmd == "arma":
            self.cmd_arma(args)
        elif cmd == "pociones":
            self.cmd_pociones(args)
        elif cmd == "set":
            self.cmd_set(args)
        elif cmd == "combate":
            self.cmd_combate(args)
        elif cmd == "status":
            self.cmd_status()
        elif cmd == "inventory":
            self.cmd_inventory()
        elif cmd == "help":
            self.mostrar_ayuda()
        elif cmd == "clear":
            self.cmd_clear()
        elif cmd == "exit":
            _log("[*] Cerrando tester...", "alerta")
            self.vista.root.quit()
        else:
            _log(f"[?] Comando desconocido: '{cmd}'. Escribe 'help' para ayuda.", "alerta")
    
    def cmd_arma(self, arg):
        """
        Command: arma [nombre] - Add weapon to inventory.
        
        Calls original game function: añadir_arma(personaje, nombre)
        This triggers reactive updates: personaje_global["armas"] changes
        → Observer fires → Vista._on_armas_cambio() executes → Sprite updates
        """
        if not arg:
            _log("[!] Sintaxis: arma [nombre]", "alerta")
            _log(f"    Armas: {', '.join(ARMAS_NOMBRES[:6])}...", "alerta")
            return
        
        # Resolve weapon name (supports abbreviations)
        arma_input = arg.lower().strip()
        
        if arma_input in ARMAS_ABREVIATURAS:
            arma_nombre = ARMAS_ABREVIATURAS[arma_input]
        elif arma_input in ARMAS_NOMBRES:
            arma_nombre = arma_input
        else:
            # Fuzzy match
            matches = [a for a in ARMAS_NOMBRES if arma_input in a.lower()]
            if matches:
                arma_nombre = matches[0]
            else:
                _log(f"[✗] Arma '{arg}' no encontrada.", "alerta")
                weapons_str = ', '.join(ARMAS_NOMBRES)
                _log(f"    Válidas: {weapons_str}", "alerta")
                return
        
        # Call original game function
        if self.añadir_arma_func:
            try:
                self.añadir_arma_func(personaje_global, arma_nombre)
                _log(f"[✓] Arma '{arma_nombre}' procesada", "exito")
            except Exception as e:
                _log(f"[✗] Error: {e}", "alerta")
        else:
            _log("[✗] Función añadir_arma no disponible", "alerta")
    
    def cmd_pociones(self, arg):
        """
        Command: pociones [número] - Change potion count (0-10).
        
        Testing command only. Sets personaje_global["pociones"] directly.
        This triggers: personaje_global["pociones"] change
        → Observer fires → Vista._on_pociones_cambio() executes → Sprite updates
        """
        if not arg:
            num_actual = personaje_global.get("pociones", 0)
            _log(f"[*] Pociones actuales: {num_actual}", "narrar")
            return
        
        try:
            num = int(arg)
            if 0 <= num <= 10:
                personaje_global["pociones"] = num
                _log(f"[✓] Pociones: {num}", "exito")
            else:
                _log(f"[!] Las pociones deben estar entre 0 y 10", "alerta")
        except ValueError:
            _log(f"[!] Uso: pociones [número]", "alerta")
    
    def cmd_set(self, arg):
        """
        Command: set [variable] [valor] - Modify character variables.
        
        Testing command for Phase 2-3. Allows setting any personaje_global variable.
        Útil para testing de eventos y combates.
        
        Ejemplos:
            set vida 20
            set armadura 5
            set fuerza 10
            set eventos_superados 12
        """
        if not arg:
            self._mostrar_variables_settables()
            return
        
        partes = arg.split(maxsplit=1)
        if len(partes) < 2:
            _log("[!] Sintaxis: set [variable] [valor]", "alerta")
            self._mostrar_variables_settables()
            return
        
        var_nombre = partes[0].lower()
        var_valor = partes[1]
        
        # Variables válidas en personaje_global
        vars_validas = {
            "vida", "vida_max", "pociones", "pociones_max",
            "armadura", "armadura_max", "fuerza", "destreza",
            "nivel", "moscas", "brazos", "sombra", "sangre", "nombre"
        }
        
        # Variables válidas en estado
        vars_estado = {"eventos_superados"}
        
        try:
            if var_nombre in vars_validas:
                # Intentar convertir a int (para números)
                try:
                    valor = int(var_valor)
                except ValueError:
                    valor = var_valor  # Mantener como string si es nombre, etc.
                
                personaje_global[var_nombre] = valor
                _log(f"[✓] {var_nombre} = {valor}", "exito")
                
            elif var_nombre in vars_estado:
                valor = int(var_valor)
                estado[var_nombre] = valor
                _log(f"[✓] estado['{var_nombre}'] = {valor}", "exito")
                
            else:
                _log(f"[✗] Variable '{var_nombre}' no válida", "alerta")
                self._mostrar_variables_settables()
                
        except ValueError as e:
            _log(f"[✗] Error: No se puede convertir '{var_valor}' a número", "alerta")
    
    def _mostrar_variables_settables(self):
        """Display settable variables for testing."""
        _log("\n" + "─"*70, "narrar")
        _log("⚙️  VARIABLES MODIFICABLES (cmd: set [variable] [valor])", "narrar")
        _log("─"*70, "narrar")
        _log("\n📊 Personaje:", "narrar")
        _log("  vida, vida_max, pociones, pociones_max", "narrar")
        _log("  armadura, armadura_max, fuerza, destreza", "narrar")
        _log("  nivel, moscas, brazos, sombra, sangre, nombre", "narrar")
        _log("\n🎮 Estado:", "narrar")
        _log("  eventos_superados (contador para trigger de Forrix)", "narrar")
        _log("\n💡 Ejemplos:", "narrar")
        _log("  set vida 20", "narrar")
        _log("  set eventos_superados 13  (→ Trigger Forrix)", "narrar")
        _log("  set fuerza 8", "narrar")
        _log("─"*70 + "\n", "narrar")
    
    def cmd_combate(self, arg):
        """
        Command: combate [enemigo] - Start combat encounter (PHASE 2).
        
        Currently in preparation. Shows available enemies to test.
        In Phase 2, will execute full combat system with Queue-based input.
        
        Ejemplos:
            combate Forrix, el Carcelero
            combate Sanakht, la Sombra Sangrienta
            combate Larvas de Sangre
        """
        if not arg:
            self._mostrar_enemigos_combatibles()
            return
        
        enemigo_input = arg.strip()
        
        # Check if enemy exists (normal + special)
        todos_enemigos = ENEMIGOS_NOMBRES + list(ENEMIGOS_ESPECIALES.keys())
        
        if enemigo_input in todos_enemigos:
            _log(f"\n[⚠️  PHASE 2] Combate con '{enemigo_input}' en preparación", "alerta")
            stats = ENEMIGOS_ESPECIALES.get(enemigo_input, {})
            desc = stats.get('descripcion', 'Enemigo normal')
            _log(f"    Stats: {desc}", "narrar")
            _log(f"    [*] Implementar en Phase 2: cmd_combate(enemigo)\n", "narrar")
        else:
            # Fuzzy match
            matches = [e for e in todos_enemigos if enemigo_input.lower() in e.lower()]
            if matches:
                _log(f"[⚠️  Posible coincidencia: '{matches[0]}'", "alerta")
                _log(f"[*] Escribe 'combate {matches[0]}'", "narrar")
            else:
                _log(f"[✗] Enemigo '{arg}' no encontrado", "alerta")
                self._mostrar_enemigos_combatibles()
    
    def _mostrar_enemigos_combatibles(self):
        """Display all combatable enemies for testing."""
        _log("\n" + "─"*70, "narrar")
        _log("⚔️  ENEMIGOS DISPONIBLES PARA COMBATE (PHASE 2):", "narrar")
        _log("─"*70, "narrar")
        
        _log("\n🩸 NORMALES:", "narrar")
        for nombre in ENEMIGOS_NOMBRES:
            _log(f"  {nombre}", "narrar")
        
        _log("\n👹 JEFES:", "narrar")
        for nombre, stats in ENEMIGOS_ESPECIALES.items():
            desc = stats.get("descripcion", "")
            vida = stats.get("vida", 0)
            daño = stats.get("daño", (0, 0))
            _log(f"  {nombre:<40} [V:{vida} D:{daño}]", "narrar")
        
        _log("\n💡 Ejemplo: combate Forrix, el Carcelero", "narrar")
        _log("─"*70 + "\n", "narrar")
    
    def cmd_status(self):
        """
        Command: status - Show character state.
        """
        armas = personaje_global.get("armas", {})
        _log("\n" + "─"*70, "narrar")
        _log("📊 ESTADO DEL PERSONAJE:", "narrar")
        _log(f"  Nombre:     {personaje_global.get('nombre')}", "narrar")
        _log(f"  Vida:       {personaje_global.get('vida')}/{personaje_global.get('vida_max')}", "narrar")
        _log(f"  Pociones:   {personaje_global.get('pociones')}/{personaje_global.get('pociones_max')}", "narrar")
        _log(f"  Armadura:   {personaje_global.get('armadura')}/{personaje_global.get('armadura_max')}", "narrar")
        _log(f"  Fuerza:     {personaje_global.get('fuerza')}", "narrar")
        _log(f"  Destreza:   {personaje_global.get('destreza')}", "narrar")
        _log(f"  Nivel:      {personaje_global.get('nivel')}", "narrar")
        _log(f"  Eventos superados: {estado.get('eventos_superados')}", "narrar")
        if armas:
            _log(f"  Armas:      {list(armas.keys())}", "narrar")
        else:
            _log(f"  Armas:      (ninguna)", "narrar")
        _log("─"*70 + "\n", "narrar")
    
    def cmd_inventory(self):
        """
        Command: inventory - List current weapons.
        """
        armas = personaje_global.get("armas", {})
        _log("\n" + "─"*70, "narrar")
        _log("🔪 INVENTARIO DE ARMAS:", "narrar")
        if armas:
            for i, (nombre, stats) in enumerate(armas.items(), 1):
                _log(f"  {i}. {nombre}", "narrar")
        else:
            _log(f"  (vacío)", "narrar")
        _log("─"*70 + "\n", "narrar")
    
    def mostrar_ayuda(self):
        """Display available commands."""
        _log("─"*70, "narrar")
        _log("📘 COMANDOS DISPONIBLES (FASE 1 + PREVIEW FASE 2):", "narrar")
        _log("  arma [nombre]           Agrega un arma al inventario", "narrar")
        _log("  pociones [num]          Cambia pociones (0-10)", "narrar")
        _log("  set [var] [val]         Modifica variable de testing", "narrar")
        _log("  combate [enemigo]       Inicia combate (PHASE 2 prep)", "narrar")
        _log("  status                  Muestra estado del personaje", "narrar")
        _log("  inventory               Lista armas actuales", "narrar")
        _log("  clear                   Limpia panel de texto", "narrar")
        _log("  help                    Muestra esta ayuda", "narrar")
        _log("  exit                    Salir del tester", "narrar")
        _log("─"*70, "narrar")
        _log("\n💡 Ejemplos:", "narrar")
        _log("    arma daga", "narrar")
        _log("    pociones 5", "narrar")
        _log("    set vida 20", "narrar")
        _log("    set eventos_superados 13", "narrar")
        _log("    combate Forrix, el Carcelero", "narrar")
        _log("    status\n", "narrar")
    
    def cmd_clear(self):
        """Clear text panel by emitting multiple blank lines and separator."""
        _log("", "narrar")
        _log("─"*70, "separador")
        _log("", "narrar")
