# ================== MÓDULO DE EVENTOS Y EXPLORACIÓN ==================
"""
Módulo events: Sistema de eventos del dungeon crawler TLDRDC.

Contiene todas las funciones de eventos numerados (_evento_1 a _evento_20),
el router evento_aleatorio(), constantes de control, y funciones auxiliares
para el sistema de bolsa de eventos.

DEPENDENCIAS INYECTADAS (asignadas por TLDRDC_Prueba1.py después de importar):
  Funciones narrativas:
    - narrar(texto): emitir texto narrativo
    - alerta(texto): emitir advertencia
    - preguntar(texto): emitir pregunta
    - leer_input(prompt, personaje): leer input del jugador
    - dialogo(texto): emitir diálogo de personaje
    - exito(texto): emitir mensaje de recompensa
    - sistema(texto): emitir mensaje de sistema
    - emitir(tipo, contenido): encolar mensaje genérico
    - susurros_aleatorios(): emitir susurros aleatorios
  
  Funciones de combate:
    - combate(personaje, enemigo): iniciar combate
    - enemigo_aleatorio(nombre_opt): generar enemigo aleatorio
    - crear_carcelero(): crear enemigo jefe
  
  Funciones de procesamiento:
    - aplicar_evento(evento_dict, personaje): aplicar resultados de evento
  
  Variables globales:
    - estado: dict global de estado del juego
    - armas_global: dict de definiciones de armas
"""

import random

# ================== INYECCIÓN DE DEPENDENCIAS ==================
# Todas estas funciones/variables son asignadas por TLDRDC_Prueba1.py
# al importar este módulo, para evitar circular imports.

narrar = None
alerta = None
preguntar = None
leer_input = None
dialogo = None
exito = None
sistema = None
emitir = None
susurros_aleatorios = None
combate = None
enemigo_aleatorio = None
crear_carcelero = None
aplicar_evento = None

# Variables globales de estado (referencias)
estado = None
armas_global = None

# ================== BOLSA DE EVENTOS (AUXILIAR) ==================

def rellenar_bolsa_eventos():
    """Rellena la bolsa con todos los eventos disponibles"""
    estado["bolsa_eventos"] = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    random.shuffle(estado["bolsa_eventos"])  # Mezclamos para mayor aleatoriedad

def rellenar_bolsa_exploracion():
    """Rellena la bolsa con todos los textos de exploración disponibles"""
    estado["bolsa_exploracion"] = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    random.shuffle(estado["bolsa_exploracion"])  # Mezclamos para mayor aleatoriedad

def obtener_evento_de_bolsa():
    """Obtiene un evento de la bolsa, rellenándola si está vacía"""
    if not estado["bolsa_eventos"]:  # Si está vacía
        rellenar_bolsa_eventos()
    return estado["bolsa_eventos"].pop()  # Sacamos el último elemento

def obtener_texto_exploracion_de_bolsa():
    """Obtiene un texto de exploración de la bolsa, rellenándola si está vacía"""
    if not estado["bolsa_exploracion"]:  # Si está vacía
        rellenar_bolsa_exploracion()
    return estado["bolsa_exploracion"].pop()  # Sacamos el último elemento

# ================== EVENTOS Y EXPLORACIÓN ==================

eventos_jefe = 13

def _evento_1(personaje):
    while True:
        narrar("Avanzas por la oscuridad a tientas, con la humedad pegándose a tu piel como una segunda capa.")
        narrar("El aire sabe a moho y hierro viejo. Tu bota tropieza con algo duro que raspa la piedra.")
        narrar("Te agachas y pasas la mano por la superficie astillada.")
        narrar("Es madera hinchada por la humedad… un pequeño cofre deformado por el tiempo.")
        narrar("Algo dentro se desplaza con un sonido seco.")
        preguntar("¿Lo quieres abrir? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Rebuscas a tientas la cerradura. La madera cruje como si protestara.")
            narrar("Cuando levantas la tapa, un olor rancio escapa del interior.")
            narrar("Tus dedos recorren el contenido: fragmentos duros, mechones apelmazados, y algo húmedo que se deshace entre tus uñas.")
            cofre = random.choice(["poción", "vacío", "corte"])
            if cofre == "poción":
                narrar("Entre trozos de hueso y pelo apelmazado, tus dedos encuentran un frasco intacto.")
                narrar("El vidrio está frío, pero el líquido en su interior emite un leve calor reconfortante.")
                return {"pociones": 1}
            elif cofre == "corte":
                alerta("Algo se rompe bajo tu presión. Una punta oxidada se clava en tu palma antes de que puedas apartarte.")
                narrar("Retiras la mano con un gesto brusco. La herida arde… pero no parece profunda.")
                return {"vida": -1}
            else:
                narrar("Remueves los restos durante un rato.")
                narrar("Solo hay huesos pequeños, asquerosos gusanos y materia irreconocible.")
                narrar("Nada útil. Al menos esta vez sales intacto...")
                return {}
        elif resp in ["n", "no"]:
            narrar("Retiras la mano lentamente. En este lugar, abrir cosas cerradas rara vez trae algo bueno.")
            narrar("Dejas el cofre atrás y continúas avanzando, sintiendo su presencia a tu espalda.")
            accion = random.choices(
                ["sombra", "mutilado", "escape"],
                weights=[33, 33, 34],
                k=1
            )[0]
            if accion == "sombra":
                narrar("Notas un pinchazo repentino, como una aguja en tu nuca. ")
                alerta("Un susurro frío te roza. Al girarte, la oscuridad ya tiene forma.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
            elif accion == "mutilado":
                alerta("Oyes un arrastre húmedo detrás de ti. Un balbuceo demente y ahogado te sigue.")
                narrar("Algo parecido a medio cuerpo humano se arrastra por el pasillo.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
            else:
                narrar("El pasillo permanece en silencio. Esta vez, nadie te ha seguido.")
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_2(personaje):
    while True:
        narrar("Un líquido cálido empapa tu bota. Pisas sin querer un charco ancho y oscuro.")
        narrar("El hedor te golpea de frente: hierro viejo, carne podrida, algo que estuvo vivo hace muy poco, o hace muchisimo...")
        narrar("El asco te revuelve el estómago. Respiras por la boca, pero el sabor es casi peor.")
        narrar("El pasillo delante está en silencio. Demasiado silencio.")
        narrar("Alguien, o algo, ha estado aquí. Y no hace mucho.")
        tirada = random.randint(1, 25)
        if tirada <= personaje["destreza"]:
            narrar("Un instinto primitivo se te dispara antes de que tu mente procese nada.")
            narrar("Tu cuerpo ya lo sabe: una trampa. Te pegas a la pared y aguantas la respiración.")
            narrar("Unos pasos pesados, irregulares, al fondo...")
            narrar("Deambulan irregularmente. Esperas inmóvil que el sonido se desvanezca por completo.")
            salida = random.choices(["recuperar", "escapar"], weights=[35, 65], k=1)[0]
            if salida == "recuperar":
                narrar("Cuando los pasos se apagan, te atreves a moverte de nuevo, y encuentras algo entre la piedra húmeda.")
                narrar("Un frasco a medias, olvidado en un hueco de la pared. Reconoces el contenido, y lo agradeces.")
                narrar("Lo apuras a oscuras, de espaldas a la podredumbre. El calor baja por tu garganta y te reconforta.")
                narrar("La tensión se disipa, la calma te revitaliza. Un poco...")
                return {"vida": 1}
            else:
                narrar("Cuando los pasos se pierden del todo, te deslizas hacia el pasillo contrario.")
                narrar("No miras atrás. El charco queda a tu espalda, y tú sigues avanzando.")
                narrar("Estás demasiado concentrado en no vomitar, y el hedor te persigue un buen rato.")
                return {}
        else:
            narrar("Estás demasiado concentrado en no vomitar.")
            narrar("El hedor es tan denso que casi tiene peso. Tu mente se bloquea en el asco.")
            alerta("No oyes nada hasta que ya es demasiado tarde.")
            alerta("Algo emerge del fondo del pasillo. Corriendo directamente hacia ti.")
            combate(personaje, enemigo_aleatorio())
            return {}

def _evento_3(personaje):
    while True:
        narrar("Llegas a una sala con una hoguera con rescoldos aún encendidos. Alguien habrá estado aquí no hace mucho...")
        narrar("Las paredes están cubiertas de sangre y ganchos, y adviertes herramientas esparcidas por el suelo.")
        preguntar("¿Investigas la sala? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Remueves los restos ennegrecidos y apartas huesos rotos.")
            narrar("El aire huele a hierro y ceniza.")
            resultados = ["pocion", "sombra", "aleatorio", "nada"]
            if "maza" not in estado["armas_jugador"]:
                resultados.append("maza")
            resultado = random.choice(resultados)
            if resultado == "maza":
                narrar("Entre los utensilios de tortura descubres una 'maza' de acero.")
                narrar("Está cubierta de sangre seca, pero es pesada y no tiene mellas.")
                return {"armas": {"maza": {}}}
            elif resultado == "pocion":
                narrar("Encuentras un vial intacto entre la ceniza.")
                return {"pociones": 1}
            elif resultado == "sombra":
                alerta("La hoguera se oscurece de repente.")
                alerta("Una sombra se desprende de la pared y se abalanza sobre ti.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
            elif resultado == "aleatorio":
                alerta("Escuchas pasos detrás de ti. Algo emerge de la oscuridad.")
                combate(personaje, enemigo_aleatorio())
            else:
                narrar("Tras registrar la sala, solo encuentras restos inútiles.")
                narrar("Nada que merezca la pena conservar.")
            return {}
        elif resp in ["n", "no"]:
            narrar("Decides no rebuscar en este horror.")
            narrar("Quizás el dueño de la hoguera no tarde en volver. Será mejor seguir tu camino.")
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_4(personaje):
    while True:
        narrar("El pasillo está destrozado, como si hubieran arrastrado algo enorme en llamas.")
        narrar("Piedras sueltas, huesos calcinados y tablones rotos cubren el suelo.")
        narrar("El hedor a carne quemada y sangre vieja te hace toser involuntariamente.")
        narrar("A lo lejos distingues unas cajas apiladas.")
        narrar("Una figura encorvada rebusca entre ellas, murmurando para sí misma.")
        narrar("Su respiración irregular resuena como un jadeo humanoide mezclado con algo que no lo es del todo.")
        preguntar("¿Te acercas? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Te aproximas lentamente. Es un perturbado, sucio y cubierto de ceniza.")
            narrar("No te ataca. Balbucea y choca sus dientes. Su piel parece translúcida por el fuego reciente.")
            preguntar("¿Desconfías de él? (s/n)")
            decision = leer_input("> ", personaje)
            if decision in ["s", "si"]:
                narrar("No te fías. Te preparas para actuar antes de que pueda reaccionar.")
                narrar("Te parece inofensivo, pero no hay nada inofensivo aquí...")
                preguntar("¿Cómo actúas? (d) destreza  /  (f) fuerza")
                modo = leer_input("> ", personaje)
                if modo == "d":
                    if personaje["destreza"] <= 3:
                        narrar("Te abalanzas con rapidez. Agarras su maltrecha cabeza y la estampas contra la pared.")
                        alerta("No logras matarlo a la primera a pesar de la brecha en su cabeza, imaginas que por su resistencia al dolor.")
                        narrar("El maniaco lucha por su vida y en el forcejeo te clava sus uñas y apendices de hueso.")
                        narrar("Consigues apartarlo, desenvainar y atravesarle el pecho.")
                        narrar("Te ha hecho una buena herida, y el ruido seguro que atraerá a otros, así que decides marcharte.")
                        return {"vida": -1}
                    elif personaje["destreza"] <= 6:
                        narrar("A pesar de forcejear, consigues tirarlo al suelo y propinarle un tajo en el cuello.")
                        narrar("No ha sido limpio, pero has salido ileso. Mientras se desangra, tu rebuscas en su botín.")
                        narrar("El desgraciado queda en el suelo con espasmos. Entre las cajas encuentras una poción.")
                        return {"pociones": 1}
                    else:
                        if "cimitarra" in estado["armas_jugador"]:
                            narrar("Te mueves como una sombra: agarras su maltrecho cuello y lo partes.")
                            narrar("Un movimiento rápido y preciso acaba con él. Rebuscas en su botín sin preocuparte mucho.")
                            narrar("Encuentras dos pociones intactas entre las cajas.")
                            return {"pociones": 2}
                        else:
                            narrar("Te mueves como una sombra: agarras su maltrecho cuello y lo partes.")
                            narrar("El perturbado cae sin saber que lo ha matado. Resbuscas por las cajas, y das con una hoja curva y afilada.")
                            narrar("Entre los restos descubres una cimitarra.")
                            return {"armas": {"cimitarra": {}}}
                elif modo == "f":
                    if personaje["fuerza"] <= 3:
                        alerta("Intentas someterlo por la fuerza, pero es sorprendente su resistencia.")
                        narrar("Sus uñas rotas y sucias te marcan la piel mientras su mirada te hiela el alma.")
                        combate(personaje, enemigo_aleatorio("Perturbado"))
                        return {}
                    elif personaje["fuerza"] <= 6:
                        narrar("Te muerde y forcejea. Antes de morir, ves algo en sus ojos que te perturba.")
                        alerta("Lo reduces con brutalidad, pero en el esfuerzo sufres varios cortes. -2 vida.")
                        return {"vida": -2}
                    else:
                        if "maza" in estado["armas_jugador"]:
                            narrar("Haces chascar su cuello con un sonido húmedo. Rebuscas en su botín.")
                            narrar("Encuentras piezas de armadura aprovechables.")
                            return {"armadura": 2}
                        else:
                            narrar("De un golpe devastador acabas con él.")
                            narrar("Entre las cajas encuentras una pesada 'maza'.")
                            return {"armas": {"maza": {}}}
                else:
                    alerta("Respuesta no válida.")
                    continue
            else:
                narrar("Decides no arriesgarte. Te alejas lentamente sin darle la espalda.")
                narrar("Sientes que sus ojos vacíos te siguen, y un eco extraño de voces apagadas resuena detrás de ti.")
                if random.random() < 0.6:
                    alerta("De repente escuchas pasos apresurados tras de ti. El perturbado se lanza al ataque.")
                    combate(personaje, enemigo_aleatorio("Perturbado"))
                    return {}
                else:
                    narrar("El murmullo se desvanece. Consigues alejarte sin problemas.")
                    return {}
        elif resp in ["n", "no"]:
            narrar("Ignoras la figura y continúas por el pasillo.")
            narrar("El silencio vuelve a envolverte, y el hedor de muerte reciente te acompaña un instante más.")
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_5(personaje):
    while True:
        narrar("Este pasillo está lleno de cadáveres amontonados. Todos presentan signos de violencia.")
        narrar("Ves las bolsas y pertenencias de los muertos. Parece que se libró una sangrienta batalla, y no hace mucho...")
        preguntar("¿Rebuscas entre ellas? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["si", "s"]:
            chequeo_fuerza = random.randint(1, 25)
            if chequeo_fuerza <= personaje["fuerza"]:
                narrar("Tu constitución te permite revolver los cuerpos sin demasiado esfuerzo.")
                narrar("Trozos de carne, huesos rotos, brazos arrancados, ojos vacíos... una carnicería.")
                if "cimitarra" in estado["armas_jugador"]:
                    narrar("Rebuscas metódicamente entre las bolsas y alforjas desperdigadas.")
                    narrar("La mayoría están vacías o contienen restos irreconocibles.")
                    narrar("Hasta que notas el tacto familiar de un frasco intacto entre los jirones.")
                    narrar("Guardas la poción y te apartas de la masacre.")
                    return {"pociones": 1}
                else:
                    narrar("En el cadáver de lo que parece un soldado, tu mano tropieza con algo metálico y frío.")
                    narrar("Una hoja curva, pesada, con filo que no se ha oxidado a pesar de todo.")
                    narrar("La limpias en un trozo de tela y la guardas sin demora.")
                    return {"armas": {"cimitarra": {}}}
            else:
                narrar("Te cuesta revolver los pesados cadáveres. Algunos no parecen ni humanos...")
                narrar("Con el sobreesfuerzo, pierdes el equilibrio y caes de bruces entre los cuerpos mutilados.")
                alerta("Mientras apartas trozos de cuerpo, te clavas algo afilado en el costado. La herida arde.")
                if "cimitarra" in estado["armas_jugador"]:
                    narrar("Entre el dolor, sigues removiendo los restos con poca gracia.")
                    narrar("Nada de valor... salvo un frasco que ha sobrevivido intacto entre los escombros.")
                    narrar("Guardas la poción a duras penas y te marchas.")
                    return {"pociones": 1, "vida": -1}
                else:
                    narrar("Te has hecho un buen corte, asi que debe haber un arma por aqui...")
                    narrar("Una hoja curva, sólida, con un filo decente. No es el mejor momento para valorarla.")
                    narrar("La agarras y te incorporas. Ya habrá tiempo de limpiarla.")
                    return {"armas": {"cimitarra": {}}, "vida": -1}
        elif resp in ["no", "n"]:
            narrar("Decides no rebuscar y pasar rápido entre la masacre.")
            if "cimitarra" not in estado["armas_jugador"]:
                if random.random() < 0.55:
                    narrar("Cuando ya casi has cruzado el pasillo, algo capta tu atención en el suelo.")
                    narrar("Sobresaliendo bajo un cuerpo, el reflejo apagado de una hoja curva.")
                    preguntar("¿La coges? (s/n)")
                    resp2 = leer_input("> ", personaje)
                    if resp2 in ["s", "si"]:
                        chequeo_destreza = random.randint(1, 25)
                        if chequeo_destreza <= personaje["destreza"]:
                            narrar("Con un movimiento rápido apartas el cuerpo y la sacas de un tirón.")
                            narrar("La limpias en el pantalón y sigues sin detenerte.")
                            return {"armas": {"cimitarra": {}}}
                        else:
                            narrar("Al mover el cuerpo, varios cadáveres encima se derrumban con estruendo.")
                            alerta("Algo que estaba entre los muertos se revuelve y se lanza contra ti.")
                            combate(personaje, enemigo_aleatorio())
                            narrar("Tras el combate, recuperas el aliento y coges la hoja del suelo.")
                            narrar("No es el momento de ser exigente con cómo has conseguido las cosas.")
                            return {"armas": {"cimitarra": {}}}
                    elif resp2 in ["n", "no"]:
                        narrar("La dejas donde está. Ya tienes bastante con seguir vivo.")
                        return {}
                    else:
                        alerta("Respuesta no válida.")
                        return {}
                else:
                    return {}
            else:
                if random.random() < 0.45:
                    narrar("Esquivas el charco más grande y aceleras, pero algo brilla cerca de la pared.")
                    narrar("Un frasco intacto, medio tapado por un brazo sin cuerpo.")
                    preguntar("¿Lo coges? (s/n)")
                    resp2 = leer_input("> ", personaje)
                    if resp2 in ["s", "si"]:
                        if random.random() < 0.4:
                            narrar("Al agacharte a cogerlo, algo se mueve entre los cadáveres más cercanos.")
                            alerta("Un cuerpo que todavía no estaba del todo muerto se revuelve hacia ti.")
                            combate(personaje, enemigo_aleatorio())
                            narrar("Lo rematas y coges el frasco del suelo. Valió la pena.")
                            return {"pociones": 1}
                        else:
                            narrar("Lo agarras rápido y sigues andando sin mirar atrás.")
                            return {"pociones": 1}
                    elif resp2 in ["n", "no"]:
                        narrar("Demasiado arriesgado. Sigues tu camino y no miras atrás.")
                        return {}
                    else:
                        alerta("Respuesta no válida.")
                        return {}
                else:
                    return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_6(personaje):
    while True:
        narrar("El pasillo termina en una abertura baja. Al agacharte para cruzarla, la temperatura cae en seco.")
        narrar("La sala que se abre ante ti está bañada en una luz roja y pálida que no viene de ninguna antorcha.")
        narrar("El suelo, las paredes, hasta el techo: todo cubierto de sangre seca y coagulada en capas.")
        narrar("En el centro, un altar de piedra negra rezuma sangre fresca desde una grieta en su superficie.")
        narrar("La sangre cae despacio, sin prisa, como si el altar respirara.")
        narrar("En el fondo del charco escarlata que se forma a sus pies, algo brilla con destellos propios.")
        preguntar("¿Metes la mano en la fuente de sangre? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Te arrodillas ante el altar. El olor es metálico y dulzón, casi mareante.")
            narrar("Metes el brazo despacio. La sangre está caliente, demasiado caliente para ser de algo muerto.")
            narrar("Notas trozos informes entre el líquido, hasta que algo choca en tu mano. La sacas por instinto, pero algo tira de ti.")
            if random.random() < 0.5:
                narrar("Estiras con toda tu fuerza y consigues sacar el brazo. Tienes algún rasguño, pero nada serio.")
                narrar("Te das cuenta que has sacado algo. Una extraña gema escarlata. Tu mirada se pierde en sus destellos...")
                narrar("y sin darte cuenta la aprietas con fuerza en tu mano. Tanta fuerza que duele, pero te gusta...")
                narrar("Pulverizas la gema en tu mano y una bruma rojiza invade la sala. Se te mete por las fosas, los ojos, los oídos...")
                susurros_aleatorios()
                narrar("No entiendes nada de las voces, pero crees que hablan de ti.")
                narrar("Sientes cómo el polvo de la gema arde en tu sangre, pero el dolor te revigoriza.")
                return {"fuerza": 1, "vida": -1}
            else:
                alerta("Luchas con todo por sacar el brazo, pero sientes punzadas y golpes. Lo tienes destrozado... -3 vida.")
                narrar("Pero has conseguido mantener el puño cerrado y tienes algo...")
                narrar("Una extraña gema escarlata. Tu mirada se pierde en sus destellos...")
                narrar("y sin darte cuenta, a pesar de tu brazo magullado, la aprietas con fuerza en tu mano.")
                narrar("Pulverizas la gema y una bruma rojiza invade la sala. Se te mete por las fosas, los ojos, los oídos...")
                susurros_aleatorios()
                narrar("No entiendes nada, la cabeza te da vueltas...")
                narrar("Sientes cómo arden tus venas, y el dolor te revigoriza a pesar de tu estado.")
                return {"fuerza": 1, "vida": -2}
        elif resp in ["n", "no"]:
            narrar("Retrocedes un paso. Algo en ese brillo bajo la sangre te resulta demasiado tentador para ser inocente.")
            narrar("Rompes el contacto visual con el altar y te das la vuelta.")
            if random.random() < 0.50:
                narrar("Cuando llegas a la abertura de salida, oyes un chasquido de dientes a tu espalda.")
                narrar("No sabes desde cuándo había alguien en esa sala contigo.")
                alerta("Un perturbado emerge de entre las sombras del altar, mascullando algo ininteligible.")
                combate(personaje, enemigo_aleatorio("Perturbado"))
            return {}
        else:
            alerta("Respuesta no válida.")

def _evento_7(personaje):
    while True:
        narrar("El pasillo desemboca en una sala que debió ser una biblioteca.")
        narrar("Las estanterías se derrumban sobre sí mismas, aplastadas por décadas de humedad y abandono.")
        narrar("Pergaminos podridos cubren el suelo como hojas secas. El aire huele a ceniza y algo más difícil de nombrar.")
        narrar("En el centro, sobre un atril que permanece intacto entre la ruina general, hay un libro.")
        narrar("No está iluminado por ninguna fuente visible, y sin embargo emite un brillo dorado y frío.")
        narrar("Los símbolos de su portada no están grabados: se mueven, lentos, como si respiraran.")
        preguntar("Aunque el libro llama tu atención, algo te dice que podría ser peligroso. ¿Quieres leerlo? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Te acercas al atril. El libro parece más grande de cerca, como si ocupara más espacio del que debería.")
            narrar("En cuanto tus dedos rozan la cubierta, el frío te sube por el brazo hasta el hombro.")
            narrar("El libro se abre solo. Las páginas comienzan a pasar solas, cada vez más rápido, generando un viento que no debería existir.")
            narrar("Los símbolos saltan de las páginas y se clavan en tus ojos como esquirlas.")
            susurros_aleatorios()
            narrar("Las voces no vienen del libro. Vienen de dentro de tu cabeza, y conocen tu nombre.")
            if random.random() < 0.6:
                narrar("Cierras los ojos con fuerza. Aguantas. Dejas que las imágenes pasen sin intentar aferrarlas.")
                narrar("Cuando el libro se cierra de golpe, estás en el suelo, con la espalda contra el atril.")
                narrar("Tu cabeza zumba, los ojos arden, y tienes la senación de haberte asomado al abismo y haber visto algo que no deberías.")
                return {"vida": -1}
            else:
                narrar("Intentas procesar los símbolos, descifrarlos, pero son demasiados y van demasiado rápido.")
                narrar("Algo en tu mente cede con un crujido sordo. El dolor es blanco y total.")
                susurros_aleatorios()
                narrar("Cuando vuelves en ti, el libro está cerrado y el atril está vacío.")
                narrar("No recuerdas qué has visto, pero tu cuerpo lo sabe. Cada músculo está en alerta.")
                alerta("El coste ha sido alto. Pero algo ha quedado grabado donde antes no había nada.")
                return {"destreza": 1, "vida": -2}
        elif resp in ["n", "no"]:
            narrar("Apartas la mirada del libro antes de que los símbolos terminen de engancharte.")
            narrar("Retrocedes hacia la salida sin darle la espalda, pisando los pergaminos podridos con cuidado.")
            if random.random() < 0.6:
                narrar("Cuando cruzas el umbral, oyes cómo el libro se abre solo a tu espalda.")
                narrar("Un zumbido grave llena el pasillo, y el brillo dorado se cuela por la ranura de la puerta.")
                narrar("Aceleras el paso. Lo que sea que haya en ese libro, esta vez ha decidido dejarte marchar.")
                return {}
            else:
                narrar("Casi has salido cuando oyes un alarido desgarrado desde algún punto del pasillo.")
                dialogo("'¡NO LO TOQUES! ¡NO LO TOQUES! ¡NO LO TOQUES!'")
                narrar("Una figura encorvada irrumpe desde la oscuridad, los ojos en blanco, las manos extendidas.")
                narrar("No distingues si viene a proteger el libro o a alejarte de él.")
                combate(personaje, enemigo_aleatorio("Perturbado"))
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_8(personaje):
    while True:
        narrar("El pasillo huele a hierro viejo y a algo más dulce y putrefacto que no sabes nombrar.")
        narrar("A la luz que se cuela entre las grietas del techo, distingues una figura tumbada junto a la pared.")
        narrar("Un soldado. O lo que queda de uno.")
        narrar("La armadura que lleva está sucia, pero sigue en pie. Y tú no.")
        narrar("Unos chasquidos secos resuenan en algún punto del techo. No se acercan. Todavía.")
        preguntar("¿Revisas la armadura del soldado? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            hallazgo = random.choice(["cuero", "placas", "infestado"])
            if hallazgo == "cuero":
                narrar("Te arrodillas junto al cuerpo y empiezas a soltar correas y hebillas con los dedos sucios de sangre ajena.")
                narrar("La armadura de cuero está blanda por la humedad, pero las costuras aguantan.")
                narrar("Te la colocas por encima de lo que llevas. No es elegante, pero cubre lo que tiene que cubrir.")
                narrar("El soldado no protestó.")
                return {"armadura": 1}
            elif hallazgo == "placas":
                narrar("Bajo el manto sucio hay algo más sólido: placas de metal reforzadas, unidas con remaches que no han cedido.")
                narrar("Te cuesta un rato sacarlas sin hacer ruido, pero el trabajo vale la pena.")
                narrar("Cuando te la ajustas, sientes el peso nuevo repartirse por tu cuerpo. Incómodo. Tranquilizador.")
                return {"armadura": 2}
            elif hallazgo == "infestado":
                narrar("Cuando tus manos tocan el primer cierre, el cadáver se estremece.")
                narrar("No es un espasmo. Es algo que hay dentro.")
                alerta("La armadura revienta hacia fuera. Docenas de larvas pálidas explotan desde el torso del soldado.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                return {}
            else:
                return {}
        elif resp in ["n", "no"]:
            accion = random.choices(
                ["seguir", "mosca"],
                weights=[70, 30],
                k=1
            )[0]
            if accion == "seguir":
                narrar("Pasas junto al cadáver sin mirarlo demasiado. Algo en su postura no te gusta.")
                narrar("El olor te sigue varios metros, pegado al interior de la nariz, hasta que el siguiente pasillo lo diluye.")
                return {}
            elif accion == "mosca":
                narrar("Cuando te apartas del cadáver, el chasquido del techo se vuelve constante.")
                narrar("Luego para. El silencio es peor.")
                alerta("Un zumbido grave rompe el aire justo detrás de tu nuca. No hubo aviso.")
                combate(personaje, enemigo_aleatorio("Mosca de Sangre"))
                narrar("Cuando termina, el pasillo vuelve a estar en silencio.")
                narrar("El cadáver del soldado sigue en la misma posición. Como si nada.")
                if random.random() < 0.5:
                    alerta("Las mandíbulas de la mosca han destrozado lo que te protegía.")
                    return {"armadura": -2}
                else:
                    return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_9(personaje):
    while True:
        narrar("La sala tiene una sola antorcha, casi consumida, que tiembla sin corriente alguna que la mueva.")
        narrar("En el centro, un cadáver atravesado por una lanza que va de lado a lado del torso, los pies sin tocar el suelo.")
        narrar("El cuerpo parece intacto, no hay signos de lucha. Alguien lo puso ahí con cuidado. Con ceremonia.")
        narrar("Puedes ver todas las percenencias todavia en el sacrificio.")
        preguntar("¿Rebuscas en el cadáver? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            if "lanza" in estado["armas_jugador"]:
                narrar("El cadáver tiene ornamentos de hueso y simbolos tallados en la piel.")
                narrar("Rebuscando, encuentras un pequeño bulto cosido al forro interior de su ropa.")
                narrar("Lo abres con cuidado. Un frasco intacto, envuelto en tela, que alguien quiso proteger.")
                narrar("Lo guardas y te alejas del cuerpo colgante.")
                if random.random() < 0.5:
                    narrar("Cuando alcanzas la salida, oyes que algo cae detrás de ti.")
                    alerta("El cadáver ya no está en la lanza. Y algo en la oscuridad respira amenazante.")
                    combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                return {"pociones": 1}
            narrar("La lanza que lo atraviesa tiene buen metal. Hoja ancha, asta sin astillas.")
            narrar("Quien la clavó sabía lo que hacía. Y quien la forjó, también.")
            while True:
                preguntar("¿Intentas sacar la lanza? (s/n)")
                resp2 = leer_input("> ", personaje)
                if resp2 in ["s", "si"]:
                    chequeo_fuerza = random.randint(1, 25)
                    if chequeo_fuerza <= personaje["fuerza"]:
                        narrar("Apoyas un pie en el torso del cadáver para hacer palanca. Requiere dos intentos.")
                        narrar("La lanza sale con un sonido húmedo que te estremece.")
                        narrar("La limpias en el forro de su ropa y la sopesas. Sólida. Equilibrada.")
                        narrar("El cuerpo se desparrama por el suelo sin ceremonias.")
                        return {"armas": {"lanza": {}}}
                    else:
                        narrar("Tiras, giras, empujas. El cadáver se balancea pero la lanza no cede.")
                        narrar("Estás tan concentrado en el esfuerzo que no oyes los pasos hasta que ya están encima.")
                        dialogo("'¡NO TOQUES MI OFRENDA!'")
                        alerta("Un perturbado sale de las sombras del fondo, los ojos en blanco, la voz rota.")
                        combate(personaje, enemigo_aleatorio("Rabioso Perturbado"))
                        narrar("Cuando termina, la lanza sigue donde estaba. Ahora la sacas sin ningúna interrución.")
                        return {"armas": {"lanza": {}}}
                elif resp2 in ["n", "no"]:
                    if random.random() < 0.7:
                        narrar("Decides que no vale la pena disturbar esa macabra escena más de lo necesario.")
                        narrar("Sales de la sala sin hacer ruido. La antorcha se apaga sola cuando cruzas el umbral.")
                        return {}
                    else:
                        narrar("Cuando te das la vuelta para marcharte, la sombra ya estaba ahí.")
                        narrar("No sabes cuánto tiempo lleva observando.")
                        combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                        return {}
                else:
                    alerta("Respuesta no válida.")
                    continue
        elif resp in ["n", "no"]:
            accion = random.choices(
                ["seguir", "combate", "pocion"],
                weights=[40, 20, 40],
                k=1
            )[0]
            if accion == "seguir":
                narrar("Bordeas la sala pegado a la pared, sin acercarte al centro ni mirar demasiado.")
                narrar("Algo en la postura del cadáver te dice que no hay nada bueno en esa lanza.")
                narrar("Salud mental intacta, por una vez.")
                return {}
            elif accion == "combate":
                narrar("Cuando ya casi has cruzado la sala, algo cae desde el cuerpo colgante.")
                narrar("No es la lanza.")
                alerta("Una larva del tamaño de un antebrazo se descuelga del torso abierto y salta hacia ti.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                return {}
            elif accion == "pocion":
                narrar("Decides no acercarte al cuerpo, pero algo brilla en el suelo junto a la base de la lanza.")
                narrar("Un frasco que cayó de algún bolsillo, intacto entre la sangre coagulada.")
                narrar("Lo recoge con dos dedos y te lo guardas sin detenerte.")
                return {"pociones": 1}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_10(personaje):
    while True:
        narrar("El pasillo huele a algo que no es solo muerte: es más dulce, casi agradable, y caliente, reciente.")
        narrar("A unos metros, tumbado contra la pared, hay un cuerpo retorcido.")
        narrar("Algunos de sus miembros apuntan en direcciones equivocadas. La piel es de un gris verdoso, y esta lleno de costuras.")
        narrar("A su alrededor, varios frascos. La mayoría rotos. Unos pocos, no.")
        preguntar("¿Te acercas a por las pociones? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            if personaje["vida"] < 5:
                hallazgo = random.choices(
                    ["dos_pociones", "una_pocion", "ninguna"],
                    weights=[60, 30, 10],
                    k=1
                )[0]
                if hallazgo == "dos_pociones":
                    narrar("La necesidad puede más que el asco. Te agachas junto al cuerpo, los ojos en él, las manos buscando a ciegas.")
                    narrar("Sus cuencas vacías miran el techo. Las costuras de su torso parecen chirrían con cada respiración tuya.")
                    narrar("Recoges varios frascos. La mitad se agrietan al tocarlos, el vidrio demasiado fino para tanta violencia.")
                    narrar("Dos aguantan enteros. Los guardas sin mirar demasiado dónde los metes.")
                    return {"pociones": 2}
                elif hallazgo == "una_pocion":
                    narrar("Te arrodillas lo más lejos que puedes sin perder el alcance. El hedor es casi sólido.")
                    narrar("Tocas tres frascos. Dos estallan entre tus dedos, el líquido frío empapándote la mano.")
                    narrar("El tercero aguanta. Lo aprietas contra tu pecho y retrocedes.")
                    narrar("El cuerpo no se ha movido. Seguramente...")
                    return {"pociones": 1}
                elif hallazgo == "ninguna":
                    narrar("Extiendes la mano hacia el frasco más cercano.")
                    narrar("El cuerpo cambia de postura. Solo un poco. Solo lo suficiente.")
                    alerta("No está muerto. Lo sabías. Lo sabes. Pero necesitabas las pociones.")
                    narrar("Agarras en los frascos con dedos temblorosos. Todos rotos, agrietados, todos inútiles.")
                    narrar("Te alejas con las manos manchadas de líquido y rotos de vidrio.")
                    narrar("Antes de doblar la esquina, miras atrás. El cuerpo está exactamente donde estaba. Gira el cuello roto y sonríe.")
                    return {}
            elif personaje["vida"] >= 8:
                narrar("Te inclinas hacia el frasco más cercano.")
                alerta("El cuerpo lleva varios segundos mirándote. No te habías dado cuenta.")
                narrar("El mutilado se incorpora con un movimiento que no funciona como debería, las articulaciones cediendo en el orden equivocado.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                narrar("Registras lo que queda. Entre los restos, un frasco intacto.")
                narrar("Interesante que lo llevara encima. Quizás para mantenerse en pie el tiempo suficiente.")
                return {"pociones": 1}
            if random.random() < 0.3:
                alerta("El cadáver se estremece y se levanta entre espasmos, con movimientos horribles y descoordinados.")
                narrar("Sus ojos inyectados en sangre se clavan en ti mientras chasquea los dientes.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                narrar("Entre sus ropas encuentras un frasco intacto. Lo guardas sin pensar demasiado en cómo sobrevivió al combate.")
                return {"pociones": 1}
            else:
                narrar("A medio camino, lo ves. El pecho que sube y baja. Las manos que se cierran despacio.")
                narrar("No está muerto.")
                narrar("Retrocedes sin hacer ruido. El cuerpo no se mueve. Pero cuando llegas a la esquina y miras atrás, ya no está mirando al techo.")
                return {}
        elif resp in ["n", "no"]:
            accion = random.choices(
                ["seguir", "cadaver_vivo"],
                weights=[60, 40],
                k=1
            )[0]
            if accion == "seguir":
                narrar("Bordeas los frascos rotos con cuidado de no pisar ninguno.")
                narrar("El crujido del vidrio es lo último que quieres ahora mismo.")
                narrar("El cuerpo te sigue con los ojos hasta que doblas la esquina. O eso te parece.")
                return {}
            elif accion == "cadaver_vivo":
                narrar("Cuando le das la espalda, oyes un chirrido sordo. Como una articulación que se fuerza.")
                alerta("El mutilado se ha puesto en pie. No sabes cuánto rato llevas siendo observado.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_11(personaje):
    narrar("Llegas a una sala donde el suelo cruje bajo tus pies. Está todo lleno de sangre e insectos comiendo restos.")
    narrar("Sin darte cuenta, al pisar un caparazón de mosca, te hundes hasta la rodilla, y cuando luchas por liberarte, el suelo se rompe bajo ti.")
    narrar("Caes en un foso enorme, plagado de moscas y larvas que se retuercen entre sangre y restos putrefactos.")
    narrar("Estás cubierto de restos y sangre, y al levantarte vomitas lo que has tragado.")
    narrar("Te recuperas rápidamente. Los insectos están aletargados, pero no tardarán en advertir tu presencia.")
    chequeo = random.randint(1, 25)
    if chequeo > personaje["fuerza"] and chequeo > personaje["destreza"]:
        alerta("No consigues soportar el dolor y el asco, te sientes febril, mareado y angustiado.")
        alerta("Sientes un dolor punzante, te arrodillas, y sientes que algo te muerde... desde dentro del estómago...")
        aplicar_evento({"vida": -1}, personaje)
    narrar("Te das cuenta de que te encuentras en un nido de moscas y larvas de sangre.")
    narrar("No es un sitio seguro, pero entre toda la podredumbre ves cosas útiles.")
    while True:
        preguntar("¿Valdrá la pena explorarlo? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            salida = random.random()
            if salida < 0.4:
                narrar("Corres entre los pasillos del nido y encuentras una bóveda llena de huevas rojas con pulsantes criaturas negras dentro.")
                narrar("También hay restos de quitinas y caparazones resistentes en el suelo. Sabes cómo podrías usarlas para defenderte.")
                narrar("El crujido bajo tus botas es constante; cada paso aplasta formas blandas que estallan con un chasquido húmedo.")
                armadura_ganada = random.choice([1, 2])
                narrar(f"Recoges {armadura_ganada} piezas útiles de armadura.")
                return {"armadura": armadura_ganada}
            elif salida < 0.7:
                narrar("Mientras corres por los pasillos, resbalas y revientas una de las huevas rojas.")
                narrar("Te sumerges en un líquido sangriento y viscoso. Lo sientes distinto, no corrosivo, sino revigorizante...")
                narrar("El fluido tibio se adhiere a tu piel. Durante un instante crees oír latidos que no son los tuyos.")
                stat_subida = random.choice(["fuerza", "destreza"])
                if stat_subida == "fuerza":
                    narrar("Aprietas los puños instintivamente. Notas los músculos tensarse bajo la piel como cuerdas recién estiradas.")
                    return {"fuerza": 1}
                elif stat_subida == "destreza":
                    narrar("Tus movimientos se vuelven ligeros y precisos. Sientes el equilibrio perfecto incluso sobre la superficie viscosa.")
                    return {"destreza": 1}
            else:
                enemigo = random.choice(["larva", "mosca"])
                if enemigo == "larva":
                    alerta("Un chasquido húmedo resuena sobre tu cabeza. La carne del techo se abre como una herida reciente.")
                    alerta("De la grieta se descuelga una masa pálida y palpitante. Una enorme larva cae sobre ti.")
                    combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                    return {}
                elif enemigo == "mosca":
                    alerta("El zumbido se vuelve ensordecedor. Sombras vibrantes se arremolinan sobre ti.")
                    alerta("Una mosca monstruosa desciende en picado, sus alas golpeando el aire con furia enfermiza.")
                    combate(personaje, enemigo_aleatorio("Mosca de Sangre"))
                    return {}
        elif resp in ["n", "no"]:
            narrar("Decides no arriesgarte más. Intentas orientarte para salir del nido, evitando las zonas más densas de podredumbre.")
            narrar("El suelo palpita bajo tus botas. Oyes un zumbido que va creciendo... algo te ha localizado.")
            chequeo = random.random()
            if chequeo > max(personaje["destreza"], personaje["fuerza"]) / 10:
                alerta("Las larvas emergen de entre los restos putrefactos, bloqueando tu retirada.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                return {}
            else:
                narrar("Totalmente alarmado, sales corriendo. Dejas de oír los asquerosos zumbidos al alejarte.")
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_12(personaje):
    while True:
        narrar("Llevas un rato con esa sensación. No es un sonido concreto. Es la suma de varios:" \
        " el eco que no encaja, el silencio se come demasiado rápido tus pasos, un frío punzante en la nuca a pesar de tu capucha.")
        narrar("Algo te sigue. O te espera. La diferencia, en este lugar, no es mucha.")
        narrar("Tu mano ya está más cerca del arma de lo que recuerdas haberla puesto.")
        preguntar("¿Te giras a enfrentarlo? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Dejas de caminar.")
            narrar("Un paso. Dos. Te giras despacio, con el arma ya en la mano, los pies abiertos, el peso repartido.")
            narrar("El pasillo detrás de ti está vacío.")
            narrar("Durante tres segundos, no pasa nada. No ves nada. No oyes nada.")
            narrar("El silencio tiene una calidad particular. Como si algo contuviera el aliento.")
            tirada = random.choice(["sombra", "rabioso"])
            if tirada == "sombra":
                narrar("Luego la oscuridad entre dos antorchas se mueve, y entiendes que no era oscuridad.")
                narrar("Una risita seca surge de ningún sitio y de todos a la vez.")
                narrar("Las antorchas no se apagan. Solo se vuelven irrelevantes.")
                alerta("La sombra se desprende de la pared y avanza hacia ti con una forma que cambia según la miras.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                return {}
            elif tirada == "rabioso":
                narrar("Luego oyes la respiración. Rápida, irregular, cargada de algo que no es solo esfuerzo físico.")
                narrar("Y el impacto de pasos que no intentan disimularse. Que nunca lo intentaron.")
                alerta("El Rabioso dobla la esquina en plena carrera, los ojos en blanco, los puños ya apretados.")
                narrar("No te ha visto hasta ahora. Pero eso no importa. Ya te tiene.")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                return {}
        elif resp in ["n", "no"]:
            narrar("Aceleras el paso sin romper a correr. Correr hace ruido. Correr confirma que huyes.")
            narrar("El pasillo se alarga. Una intersección a la derecha, otra ruta posible.")
            narrar("El frío en la nuca no cede.")
            narrar("Tampoco desaparece cuando cambias de dirección. Lo que sea, ya sabe a dónde vas.")
            tirada = random.choice(["sombra", "rabioso"])
            if tirada == "sombra":
                narrar("Cuando doblas la esquina, la sombra ya está al otro lado.")
                narrar("No te ha perseguido. Te ha cortado el paso.")
                narrar("No tiene ojos visibles, pero sabes que te está mirando. Lo notas en la piel.")
                alerta("Se expande lentamente por las paredes como si fuera humo negro.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                return {}
            elif tirada == "rabioso":
                narrar("Cuando oyes el retumbar tras de ti, el miedo te puede. Rompes a correr.")
                narrar("Durante unos segundos, parece que funciona, pero tropiezas con algo y caes al suelo.")
                alerta("Oyes la voz rota de un Rabioso acercandose. Más rápido. Mucho más rápido.")
                narrar("El alarido llega antes que él. Y él llega antes de que puedas levantarte.")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_13(personaje):
    while True:
        narrar("La sala es amplia, demasiado para lo poco que hay en ella.")
        narrar("El suelo tiene marcas de arrastre que salen de la oscuridad del fondo y llegan hasta el centro.")
        narrar("Ves marcas que indican que han corrido ríos de sangre por este suelo.")
        narrar("En una estantería pegada a la pared, varios frascos. Algunos rotos, otros no.")
        preguntar("¿Coges alguno? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            tirada = random.random()
            if tirada < 0.6:
                narrar("Cruzas la sala con pasos rápidos y llegas a la estantería.")
                narrar("Tus dedos acaban de tocar el primer frasco cuando el ruido llega desde atrás.")
                dialogo("'¡NOOOOOO!'")
                narrar("Golpes secos, rítmicos, como alguien chocando su cabeza contra la piedra.")
                alerta("Un Rabioso irrumpe desde el pasillo lateral, la boca abierta, los ojos en ningún sitio.")                    
                combate(personaje, enemigo_aleatorio("Rabioso"))
                narrar("Cuando terminas el combate, la sala vuelve al silencio.")
                narrar("Rebuscas la estantería con calma. Entre los frascos rotos, uno aguanta intacto.")
                return {"pociones": 1}
            else:
                narrar("La sala parece vacía. Llegas a la estantería sin problemas.")
                narrar("Estás a punto de coger el primer frasco cuando oyes la respiración.")
                narrar("Lenta, entrecortada, como un fuelle roto. Viene del fondo.")
                alerta("Una figura se incorpora desde el suelo. Sus articulaciones se mueven en el orden equivocado.")
                narrar("Llevaba ahí tirado. Esperando, quizá. O simplemente sin poder moverse hasta ahora.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                narrar("Registras la zona con cuidado. Entre los restos y la sangre, dos frascos intactos.")
                return {"pociones": 2}
        elif resp in ["n", "no"]:
            tirada = random.random()
            if tirada < 0.3:
                narrar("Das media vuelta y empiezas a salir.")
                narrar("El silencio de la sala dura exactamente tres segundos.")
                alerta("Luego los golpes, un alarido y un Rabioso en el umbral.")
                dialogo("'¡NOOOOOO!'")
                narrar("No importa si vas a por las pociones o no. Ya te ha visto.")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                narrar("Entre los restos del caído, dos pociones que sobrevivieron al golpe.")
                return {"pociones": 2}
            elif tirada < 0.6:
                narrar("Decides no entrar. Retrocedes hacia el pasillo.")
                narrar("Un crujido metálico resuena arriba. Algo se mueve en la pasarela.")
                narrar("No tienes tiempo de mirar hacia arriba.")
                alerta("El Maniaco Mutilado cae desde la altura con un impacto sordo, justo delante de ti.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                narrar("Entre los restos del caído, dos pociones que sobrevivieron al golpe.")
                return {"pociones": 1}
            else:
                narrar("Decides no arriesgarte. Las pociones no merecen lo que probablemente hay en esa sala.")
                narrar("Bordeas la entrada sin mirar dentro y sigues avanzando.")
                narrar("Nadie te sigue. Esta vez.")
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_14(personaje):
    while True:
        narrar("A un lado del pasillo, una puerta de hierro rompe la monotonia de la piedra.")
        narrar("La puerta es pequeña, metálica, con barrotes gruesos que no encajan con el resto del corredor.")
        narrar("Alguien invirtió esfuerzo en hacerla resistente, pero por 'suerte' esta abierta.")
        narrar("Por entre los barrotes se filtra un olor a óxido, cuero quemado y algo más orgánico que prefieres no nombrar.")
        narrar("Al fondo, herramientas colgadas en la pared como trofeos. Algunas siguen en uso, a juzgar por el brillo.")
        preguntar("¿Entras a rebuscar? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Empujas la puerta. Cede con un chirrido que se extiende por el corredor más de lo que te gustaría.")
            narrar("El suelo de dentro está ennegrecido. Las manchas tienen formas que preferirías no reconocer.")
            narrar("Apartas cadenas, ganchos, sorteas una mesas volcadas y abres cajas y cajones que se resisten.")
            opciones = ["martillo", "combate", "nada", "daño"]
            if "martillo" in estado["armas_jugador"]:
                opciones.remove("martillo")
            tirada = random.choice(opciones)
            resultado = {}
            if tirada == "martillo":
                narrar("Colgado en la pared junto a una sierra sin dientes, hay un martillo de hierro macizo.")
                narrar("Tiene la cabeza ennegrecida, pero el mango está intacto y el equilibrio es bueno.")
                narrar("Quien lo usó aquí no lo usaba para clavar clavos.")
                narrar("Lo descuelgas y lo sopesas. Sólido. Útil.")
                resultado = {"armas": {"martillo": {}}}
            elif tirada == "combate":
                narrar("La estancia parece vacía. Demasiado vacía, con demasiado sitio para esconderse detrás de las sombras.")
                narrar("Notas el frío antes de ver nada. Un frío puntual, dirigido, que no viene del suelo ni de las paredes.")
                narrar("La sombra entre dos instrumentos colgados no se parece al resto de las sombras.")
                alerta("Se alarga por el suelo hacia ti antes de que puedas retroceder.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
            elif tirada == "daño":
                narrar("Apartas una mesa volcada para ver qué hay detrás.")
                narrar("El mecanismo es antiguo y está oxidado, pero sigue funcionando.")
                narrar("Un chasquido metálico, un movimiento de aire, y el dolor llega antes de que veas qué lo causó.")
                alerta("Un gancho de hierro se clava en tu costado y se retrae de golpe, dejando una herida profunda.")
                aplicar_evento({"vida": -1}, personaje)
            elif tirada == "nada":
                narrar("Rebuscas con cuidado entre todo el horror utilitario de la sala.")
                narrar("Nada sirve: demasiado pesado, demasiado dañado, demasiado específico para usos que no quieres imaginar.")
                narrar("Sales con las manos vacías y la sensación de que la sala te ha visto hacer el ridículo.")
                narrar("El chirrido de la puerta al cerrarla suena igual de acusador.")
            if random.random() < 0.7:
                narrar("Antes de salir, algo llama tu atención entre los restos: un frasco pequeño, casi oculto bajo un trapo.")
                narrar("Lo limpias en la manga sin examinar qué hay debajo del trapo. Lo guardas.")
                aplicar_evento({"pociones": 1}, personaje)
            return resultado
        elif resp in ["n", "no"]:
            narrar("Miras entre los barrotes el tiempo suficiente para decidir que no merece la pena.")
            narrar("Hay cosas útiles ahí dentro, seguramente. Pero hay otras cosas también.")
            narrar("Sigues tu camino. La puerta queda atrás. El olor, no.")
            if random.random() < 0.5:
                narrar("Un sonido a tu espalda. No viene de la sala de torturas.")
                narrar("Viene del corredor. De algo que estaba esperando a que te distrajeras.")
                combate(personaje, enemigo_aleatorio())
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_15(personaje):
    while True:
        narrar("El suelo ha cambiado de textura sin que te hayas dado cuenta.")
        narrar("Pegajoso, oscuro, con manchas que no son solo sangre seca.")
        narrar("Las paredes también. Una capa fina, casi translúcida, que recubre las grietas como si algo las hubiera sellado por dentro.")
        narrar("Cuando enfocas la vista, lo ves: miles de huevas del tamaño de una uña, pulsando.")
        preguntar("¿Cómo intentas atravesar el nido? (f)uerza / (d)estreza")
        resp = leer_input("> ", personaje)
        if resp == "probar":
            narrar("Acercas la mano lentamente a una de las huevas.")
            narrar("La textura es húmeda, cálida. Palpita como un corazón.")
            narrar("Y por un momento, algo... responde a tu toque. Una inteligencia colectiva, sin forma ni intención, solo hambre y crecimiento.")
            narrar("Las huevas explotan bajo tu tacto, pero hay docenas más. Cientos. Miles.")
            narrar("Comprendes que no puedes destruirlas. Solo atravesarlas.")
            if "vigor" not in personaje:
                personaje["vigor"] = 0
            personaje["vigor"] += 1
            narrar("Algo en ti ha despertado. Ahora sabes cómo moverse entre ellas.")
            preguntar("¿Cómo intentas atravesar el nido? (f)uerza / (d)estreza")
            resp = leer_input("> ", personaje)
        if resp in ["f", "fuerza"]:
            chequeo = random.randint(1, 25)
            if personaje["fuerza"] >= chequeo:
                narrar("No te molestas en rodearlas. Pisas fuerte, deliberadamente.")
                narrar("Las huevas estallan bajo tus botas con un sonido húmedo que preferirías olvidar.")
                narrar("Algo intenta aferrarse a tu tobillo. Lo sacudes. Sigue aferrado. Lo sacudes más fuerte.")
                narrar("Cruzas al otro lado chorreando linfa. Vivo. Eso cuenta.")
                return {}
            elif personaje["fuerza"] >= chequeo - 4:
                narrar("Empujas hacia adelante aplastando lo que hay bajo tus pies, pero el nido es más denso de lo que parece.")
                narrar("Algo explota a la altura de tu muslo. Luego otro. Luego varios a la vez.")
                alerta("Las larvas no esperan a caer al suelo.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                narrar("Las aplastas, las arrancas, las pisas. Pero hay demasiadas.")
                narrar("Sales del nido con la armadura perforada en varios sitios.")
                return {"armadura": -1}
            else:
                narrar("Intentas abrirte paso a la fuerza, pero el suelo cede bajo tu peso de un modo que no esperabas.")
                narrar("Te hundes hasta el tobillo en una masa de huevas reventadas. El olor es insoportable.")
                alerta("El zumbido llega antes que ellas. Las moscas ya están aquí.")
                combate(personaje, enemigo_aleatorio("Moscas de Sangre"))
                narrar("Sales arrastrándote, con la armadura perforada y el sabor de la sangre ajena en la boca.")
                narrar("El veneno de las larvas, contra todo pronóstico, te ha espabilado.")
                return {"vida": 1, "armadura": -1}
        elif resp in ["d", "destreza"]:
            chequeo = random.randint(1, 25)
            if personaje["destreza"] >= chequeo:
                narrar("Calculas cada paso antes de darlo.")
                narrar("Hay un patrón en la distribución del nido, huecos entre los cúmulos, franjas limpias.")
                narrar("Atraviesas en silencio, sin pisar nada, sin rozar las paredes.")
                narrar("Al otro lado, el suelo vuelve a ser piedra. Respiras.")
                return {}
            elif personaje["destreza"] >= chequeo - 4:
                narrar("Lo intentas con cuidado, pero a mitad del tramo una hueva revienta sola bajo tu pie.")
                narrar("El sonido es suficiente. Varias más responden al instante.")
                alerta("Las larvas salen disparadas antes de que puedas retroceder.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                return {}
            else:
                narrar("El primer paso parece seguro. El segundo también.")
                narrar("En el tercero, el suelo se mueve solo.")
                alerta("Caes de bruces sobre el nido. El impacto revienta docenas de huevas a la vez.")
                combate(personaje, enemigo_aleatorio("Moscas de Sangre"))
                narrar("Sales de allí entre arcadas y algo moviéndose todavía en tu ropa.")
                narrar("El veneno de las larvas, extrañamente, te ha reforzado.")
                return {"vida": 1}
        else:
            alerta("Respuesta no válida. (f) para fuerza, (d) para destreza.")
            continue

def _evento_16(personaje):
    while True:
        narrar("La puerta cede hacia dentro antes de que la empujes.")
        narrar("Una sala amplia. Estanterías metálicas combadas por el peso de años de abandono.")
        narrar("Tablas de madera podrida, yelmos aplastados, escudos partidos en dos. Una armería.")
        narrar("Huele a óxido viejo y a cuero que lleva demasiado tiempo húmedo.")
        narrar("Algo cruje en el fondo cuando entras. Probablemente el suelo. Probablemente...")
        narrar("Pero entre los escombros hay piezas que todavía parecen utiles. Que todavía tienen uso.")
        preguntar("¿Rebuscas en la habitación? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            opciones = ["placas", "rodela", "porra", "nada"]
            if "porra" in estado["armas_jugador"]:
                opciones.remove("porra")
            tirada = random.choice(opciones)
            if tirada == "placas":
                narrar("Detrás de una estantería volcada, asoman placas de metal unidas por correas de cuero.")
                narrar("Algunas tienen abolladuras profundas. Otras están intactas.")
                narrar("Las pruebas una a una. La mayoría encajan. Te las ajustas como puedes.")
                narrar("No es bonito, pero es sólido.")
                return {"armadura": 2}
            elif tirada == "rodela":
                narrar("En un gancho de la pared, colgada al revés, hay una rodela de hierro con el umbo intacto.")
                narrar("La descuelgas. Pesa bien, sin grietas, sin fisuras en el borde.")
                narrar("La ajustas al antebrazo. Te queda ajustada. Útil.")
                return {"armadura": 1}
            elif tirada == "porra":
                narrar("Entre dos estanterías volcadas, medio enterrada bajo escombros, sobresale un mango de hierro.")
                narrar("Tiras de él. Sale con resistencia, arrastrando cascotes.")
                narrar("Una porra. Cabeza maciza, mango corto, sin adornos. Fabricada para una sola cosa.")
                narrar("La sopesas. Directa. 'Honesta'.")
                return {"armas": {"porra": {}}}
            elif tirada == "nada":
                narrar("Mientras rebuscas, una de las estanterías se desploma.")
                alerta("El estruendo es ensordecedor, y temes que te hayan escuchado.")
                narrar("Piensas que pueden venir a por ti.")
                preguntar("¿Sales corriendo? (s/n)")
                resp = leer_input("> ", personaje)
                if resp in ["s", "si"]:
                    narrar("Sales corriendo de la armería con el estruendo todavía resonando en las paredes.")
                    narrar("Doblas un recodo y te pegas a la pared, conteniendo la respiración.")
                    narrar("Un minuto. Dos. Nada se mueve.")
                    narrar("El silencio vuelve. Sigues tu camino sin mirar atrás.")
                    return {}
                else:
                    narrar("Decides no correr y enfrentarte a lo que venga.")
                    narrar("Te quedas en medio de la sala preparado, pues no hay donde esconderse.")
                    alerta("¡MIS COSAS! ¡ALGUIEN HA TIRADO MIS COSAS!")
                    narrar("Oyes a alguien corriendo hacia la sala, y una figura destrozada entra a trompicones.")
                    dialogo("'¡TE MATARÉ! ¡LO HAS ROTO TODOOO!'")
                combate(personaje, enemigo_aleatorio("Perturbado"))
                recompensa = random.random()
                narrar("El cuerpo del perturbado cae entre todas las estanterías. Está todo empapado de sangre.")
                if recompensa < 0.3:
                    narrar("En un gancho de la pared, colgada al revés, hay una rodela de hierro con el umbo intacto.")
                    narrar("La descuelgas. Pesa bien, sin grietas, sin fisuras en el borde.")
                    narrar("La ajustas al antebrazo. Te queda ajustada. Útil.")
                    return {"armadura": 1}
                elif recompensa < 0.6:
                    narrar("Todas las armas están rotas, oxidadas o son peores que las tuyas.")
                    narrar("Pero encuentras una poción intacta entre los restos.")
                    return {"pociones": 1}
                else:
                    if "porra" in estado["armas_jugador"]:
                        narrar("Entre dos estanterías volcadas, medio enterrada bajo escombros, sobresale un mango de hierro.")
                        narrar("Tiras de él. Sale con resistencia, arrastrando cascotes.")
                        narrar("Una porra. Cabeza maciza, mango corto, sin adornos. Fabricada para una sola cosa.")
                        narrar("La sopesas. Directa. 'Honesta'.")
                        return {"pociones": 1}
                    narrar("Das con una 'porra' contundente entre los escombros.")
                    return {"armas": {"porra": {}}}
        elif resp in ["n", "no"]:
            narrar("Echas un vistazo desde el umbral y decides que no merece el tiempo.")
            narrar("Demasiado ruido para demasiado poco probable.")
            narrar("Sigues tu camino.")
            return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_17(personaje):
    while True:
        narrar("En medio del pasillo ves a lo que parece un hombre encadenado al suelo.")
        narrar("Por el cuello, las muñecas y los tobillos lo mantienen inmovil en la fria piedra.")
        narrar("La cabeza colgando hacia abajo. El pelo pegado a la cara. No se mueve.")
        narrar("Sus ropas están desgarradas, pero debajo hay piezas de equipo que todavía tienen forma.")
        narrar("No hay sangre en el suelo. Solo las cadenas, tensas, ancladas a la piedra del techo como si alguien hubiera planeado esto.")
        preguntar("¿Registras al hombre suspendido? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Te acercas despacio, atento a cada sonido.")
            narrar("Las cadenas rechinan levemente con tu peso en el suelo. El hombre no reacciona.")
            narrar("Extiendes la mano hacia sus ropas.")
            tirada = random.choice(["armadura", "pocion", "sombra", "rabioso"])
            if tirada == "armadura":
                narrar("Bajo los jirones hay correas de cuero cruzadas sobre el pecho, y bajo ellas, placas de metal remachadas.")
                narrar("Las sueltas con cuidado. El hombre oscila levemente con el movimiento, pero no más.")
                narrar("Las placas están dañadas pero son sólidas. Te las ajustas entre tus propias correas.")
                narrar("Cuando te alejas, las cadenas siguen crujiendo, como si el peso no hubiera cambiado del todo.")
                return {"armadura": 2}
            elif tirada == "pocion":
                narrar("El forro interior de su ropa está cosido con doble puntada en el pecho.")
                narrar("Hay algo dentro. Lo abres con cuidado. Un frasco pequeño, envuelto en tela encerada, intacto.")
                narrar("Alguien lo escondió para que no se encontrara fácilmente.")
                narrar("O para que solo lo encontrara alguien que supiera buscar.")
                return {"pociones": 1}
            elif tirada == "sombra":
                narrar("Cuando tus dedos tocan el primer cierre, sientes el frío.")
                narrar("No viene del cuerpo. Viene de las cadenas.")
                narrar("La sombra que proyecta el hombre sobre el suelo se mueve. Lentamente. Sin que la fuente de luz haya cambiado.")
                alerta("Las cadenas caen de golpe. El hombre cae. Pero la sombra no.")
                narrar("Se levanta del suelo y adquiere una forma que no es la del hombre que acaba de caer.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                return {}
            elif tirada == "rabioso":
                narrar("Cuando apartas el cuerpo, el ojo que queda visible está abierto.")
                narrar("Ha estado abierto todo el tiempo.")
                alerta("La boca se abre con un sonido líquido. Las cadenas se tensan. Se rompen.")
                narrar("No estaba muerto. Solo esperaba a que alguien se acercara lo suficiente.")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                return {}
        elif resp in ["n", "no"]:
            narrar("Bordeas al hombre por el lado opuesto, pegado a la pared.")
            narrar("Sus cadenas rechinan cuando pasas. No lo miras directamente.")
            tirada = random.random()
            if tirada < 0.3:
                narrar("Llevas ya varios metros cuando oyes el impacto sordo a tu espalda.")
                narrar("Las cadenas se han roto. El hombre está en el suelo.")
                narrar("Echas a correr mientras oyes una avalancha detrás de ti.")
                chequeo = random.randint(1, 25)
                if chequeo > personaje["fuerza"] and chequeo > personaje["destreza"]:                        
                    narrar("La fuerza y velocidad del Rabioso son más de lo que esperabas.")
                    narrar("Y sus alaridos refuerzan tu idea de que no es totalmente humano.")
                    alerta("El maniaco enajenado te alcanza antes de que llegues al recodo. No hubo aviso.")
                    combate(personaje, enemigo_aleatorio("Rabioso"))
                    return {}
                else:
                    narrar("Corres sin dudarlo. El pasillo dobla, y dobla otra vez, y tu no te detienes.")
                    narrar("Los pasos detrás se van espaciando. Luego paran.")
                    narrar("Cuando te detienes a escuchar, solo oyes tu propia respiración desbocada.")
                    return {}
            else:
                narrar("Llevas ya varios metros cuando oyes el impacto sordo a tu espalda.")
                narrar("Las cadenas han cedido solas. No miras atrás.")
                narrar("Aceleras, doblas varios pasillos, y el silencio vuelve.")
                narrar("No sabes qué había en ese hombre. No necesitas saberlo.")
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_18(personaje):
    while True:
        narrar("El pasillo huele a carne podrida y a algo más dulce, casi bilioso, que no identificas.")
        narrar("Las paredes están pegajosas. Al rozarlas sin querer, la mano sale cubierta de una película oscura y tibia.")
        narrar("En el suelo, entre los charcos, hay formas blandas que se retuercen lentamente. Larvas. Cientos.")
        narrar("Y encima de todo eso, el zumbido. Grave, constante, como si las paredes mismas vibraran.")
        narrar("Las manchas oscuras del techo no son manchas. Se mueven.")
        preguntar("¿Avanzas directamente por el pasillo? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Das el primer paso y el suelo cede ligeramente bajo tu peso, blando y húmedo.")
            narrar("Las larvas se apartan con un siseo colectivo. El zumbido sube de tono.")
            narrar("A mitad del pasillo, las manchas del techo explotan hacia abajo de golpe.")
            narrar("Es un enjambre. Una masa oscura, caliente, con alas que cortan el aire en todas direcciones.")
            alerta("Las moscas te envuelven antes de que puedas cubrirte. Pican, muerden, se cuelan bajo el equipo.")
            combate(personaje, enemigo_aleatorio("Mosca de Sangre"))
            narrar("Cuando acallas el último zumbido, el pasillo está cubierto de restos purulentos de moscas.")
            narrar("Tu armadura esta llena de mellas: docenas de puntos perforados donde los aguijones encontraron metal.")
            if random.random() < 0.5:
                narrar("La armadura ha cedido en varios puntos. Notas vacíos donde antes había protección.")
                if random.random() < 0.5:
                    narrar("Entre los restos aplastados de las moscas, algo brilla.")
                    narrar("Un frasco sellado, cubierto de linfa, pero intacto. Lo limpias en el pantalón y lo guardas.")
                    return {"armadura": -1, "pociones": 1}
                else:
                    narrar("Registras el suelo entre arcadas. No hay nada que valga lo que ha costado el cruce.")
                    return {"armadura": -1}
            else:
                narrar("La armadura ha sufrido, pero la remiendas con quitinas y patas.") 
                narrar("Es asqueroso, pero funcional. Sales del pasillo chorreando icor de mosca, pero entero.")
                return {}
        elif resp in ["n", "no"]:
            narrar("Buscas una ruta alternativa por el borde, pegado a la pared menos infestada.")
            narrar("El zumbido se mantiene lejos. Las larvas del suelo se apartan a tu paso, lentas, casi indiferentes.")
            narrar("Llevas la mitad del recorrido cuando el suelo cede bajo tu pie.")
            narrar("Pisas una masa de huevas apiladas. Revientan con un chasquido húmedo. El olor es insoportable.")
            tirada = random.random()
            if tirada < 0.6:
                alerta("Las larvas reaccionan al instante. Se lanzan hacia arriba, directas a las correas y juntas de la armadura.")
                narrar("Son más rápidas de lo que parecen. Las arrancas, las aplastas, pero siguen llegando.")
                combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
                narrar("Cuando termina, tienes restos de larva por todas partes y un sabor metálico en la boca.")
                return {}
            else:
                narrar("Las larvas se agitan, pero no te siguen. Mantienes el paso sin correr.")
                narrar("El zumbido del techo se aleja a medida que avanzas, pero lo notas en los huesos.")
                narrar("Sales del pasillo con las botas empapadas de algo que prefieres no examinar.")
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_19(personaje):
    while True:
        narrar("Llegas a una sala pequeña donde hay un altar de piedra negra, cubierto de símbolos erosionados.")
        narrar("Sobre él descansan dos objetos: un libro de cubiertas doradas y una gema escarlata del tamaño de un puño.")
        narrar("La gema no brilla: palpita. La niebla que emite se enrosca alrededor del tomo como si los dos se conocieran.")
        narrar("Algo en la disposición de los objetos parece deliberado. Calculado.")
        preguntar("¿Qué haces? (g)ema / (l)ibro / (a)mbos / (n)ada")
        resp = leer_input("> ", personaje)

        if resp in ["g", "gema"]:
            narrar("Apartas el libro y centras toda tu atención en la gema.")
            narrar("Cuando la coges, el frío que irradia te sube por el brazo hasta el hombro.")
            narrar("Aprietas. La gema se resquebraja. Aprietas más.")
            susurros_aleatorios()
            narrar("Los fragmentos no caen: se absorben. Entran por la piel como agujas de hielo.")
            narrar("Te arde todo el cuerpo durante unos segundos insoportables.")
            narrar("Luego el dolor se asienta en algo que se parece mucho a la fuerza.")
            narrar("El libro se ha deshecho en polvo cuando vuelves a mirarlo. Decides salir de alli.")
            return {"fuerza": 1, "vida": -1}

        elif resp in ["l", "libro"]:
            narrar("La gema puede esperar. El libro te llama más.")
            narrar("Sus páginas se abren solas en cuanto posas la mano en la cubierta.")
            narrar("Las llamas verdosas que rodean el lomo lamen tus dedos. Duele, pero no paras.")
            narrar("Pasas páginas a una velocidad que no decides tú.")
            narrar("Cuando el libro se consume en un destello verde, tus manos humean y tu mente está más afilada que nunca.")
            narrar("La gema se ha pulverizado en el aire mientras leías. No te queda nada que hacer aqui.")
            return {"destreza": 1, "vida": -1}

        elif resp in ["a", "ambos"]:
            narrar("Los quieres los dos. Cada uno de ellos por separado ya sería demasiado.")
            narrar("Coges la gema con una mano y el libro con la otra. Ambos reaccionan al instante.")
            narrar("La gema palpita más rápido. El libro te arrastra hasta el altar.")
            narrar("El calor y el frío, el dolor y el extasis; se mezclan en tus brazos y suben a la vez hacia tu cabeza.")
            chequeo = random.randint(1, 25)
            if personaje["fuerza"] >= chequeo or personaje["destreza"] >= chequeo:
                narrar("Aguantas. No sabes cómo, pero aguantas, aunqu desearias no haber sido tan avaricioso.")
                narrar("La gema cede primero: se pulveriza en tu palma y los fragmentos entran por la piel.")
                narrar("Con la mano libre, abres el libro. Las páginas giran solas, cada vez más rápido.")
                narrar("La página se hunde como carne al presionarla y la tinta se agrieta en venas negras que reptan bajo tus uñas.")
                narrar("No lees palabras, algo lee dentro de ti.")
                susurros_aleatorios()
                narrar("Ves una torre invertida clavándose en un mar de sangre espesa.")
                narrar("Ves manos, miles, emergiendo de la piedra, no para huir, sino para sostenerla desde abajo.")
                narrar("Un cirujano sin rostro cose metal en un cuerpo que no termina nunca;")
                narrar("cada puntada abre otra boca en la oscuridad que llora sangre.")
                narrar("Hay una sombra que no vive en el aire, sino que rie de la intención de los actos.")
                narrar("Hay otra que no ríe: calcula, miente, envenena.")
                susurros_aleatorios()
                narrar("Una sombra bebe directamente del derramamiento.")
                narrar("Otra no bebe; inclina la copa para que el líquido caiga donde más conviene.")
                susurros_aleatorios()
                narrar("Ambas conocen el nombre del hombre que corta.")
                narrar("Él cree pronunciar sílabas de poder, pero en realidad está siendo pronunciado.")
                narrar("Algo más profundo respira bajo todo ello, vasto y sin forma definida.")
                narrar("No es invocado. Es cultivado. Crece informe, como un oceano de sangre negra.")
                narrar("Durante un instante comprendes que la mazmorra no fue construida para contener la oscuridad.")
                narrar("Luego las páginas vuelven a ser tinta muerta, aunque tus pensamientos ya no lo son.")
                chequeo2 = random.randint(1, 35)
                if personaje["fuerza"] >= chequeo2 or personaje["destreza"] >= chequeo2:
                    susurros_aleatorios()
                    susurros_aleatorios()
                    narrar("No te detienes. Algo en ti exige seguir, ir más hondo.")
                    narrar("Lo que viste no era pasado ni futuro, sino una superposición.")
                    narrar("Fabius no abrió una puerta; abrió una herida prolongada en la realidad,")
                    narrar("y dos infecciones distintas se asentaron en ella.")
                    narrar("Una se nutre de la violencia explícita: cuanto más grotesca la mutilación,")
                    narrar("más densa su presencia, hasta adquirir forma y peso en los niveles inferiores.")
                    narrar("La otra no necesita sangre fresca; prospera en la desviación sutil,")
                    narrar("en el error mínimo de cálculo, en la plegaria torcida que no llega a su destinatario.")
                    narrar("Ambas toleran la existencia de Fabius porque les resulta útil.")
                    narrar("Él cree servir a un señor exterior, pero su obra ya alimenta fuerzas que no responden a ese mandato.")
                    narrar("La mazmorra es ahora un órgano compartido por voluntades que no se reconocen entre sí como iguales.")
                    narrar("Lo más inquietante no es su conflicto, sino su equilibrio.")
                    narrar("Mientras ambos influjos persistan, la mazmorra seguirá produciendo horrores...")
                    narrar("y tú has confirmado, al leer, que estas en un proceso en curso.")
                    narrar("El libro se cierra solo. Las llamas lo consumen por completo.")
                    narrar("Un torrente de fuerza impia te recorre en cuerpo y alma.")
                    narrar("A pesar del dolerte los ojos, estas mejor que nunca desde que despertaste en la mazmorra.")
                    narrar("Pero tu consciencia te da punzadas, sabes que algo no esta bien...")
                    return {"destreza": 1, "fuerza": 1, "vida": -1, "sombra": 1, "sangre": 1}
                else:
                    susurros_aleatorios()
                    narrar("Llegas demasiado hondo. La mente no aguanta tanto a la vez.")
                    narrar("Sientes una grieta que no es física abrirse detrás de tus ojos.")
                    narrar("El libro explota en llamas verdes y sales despedido.")
                    narrar("Cuando vuelves en ti, el altar está vacío y tus manos estan negras.")
                    narrar("No sera facil empuñar armas con esas heridas...")
                    return {"vida": -5}
            else:
                susurros_aleatorios()
                narrar("La confluencia de ambos objetos te supera.")
                narrar("El calor y el frío te quiebran desde dentro antes de que puedas procesar nada.")
                narrar("Caes de rodillas. El libro y la gema se quedan inmóviles en el altar.")
                narrar("Prefieres no tentar a la suerte de nuevo y sales de allí lo más rápido que puedes.")
                return {"vida": -2}
        elif resp in ["n", "no"]:
            narrar("Retrocedes un paso. Algo en esos dos objetos juntos te resulta demasiado limpio para ser inocente.")
            narrar("Nadie deja esto aquí por accidente.")
            tirada = random.random()
            if tirada < 0.3:
                alerta("Un Rabioso enajenado aparece de entre las sombras, atraído por tus movimientos.")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                return {}
            elif tirada < 0.6:
                alerta("Una figura perturbada surge tambaleándose, murmurando palabras incomprensibles.")
                combate(personaje, enemigo_aleatorio("Perturbado"))
                narrar("Tras derrotarlo, encuentras una poción entre sus harapos ensangrentados.")
                return {"pociones": 1}
            else:
                narrar("El silencio se mantiene. Sea lo que sea que vigila este altar, decides no averiguarlo.")
                narrar("Sales de la sala sin mirar atrás.")
                return {}
        else:
            alerta("Respuesta no válida.")
            continue

def _evento_20(personaje):
    while True:
        narrar("La sala huele antes de que la veas: hierro, vísceras y algo quemado que no terminas de identificar.")
        narrar("El suelo está lleno de cuerpos, algunos encima de otros, como si hubieran seguido peleando hasta caer.")
        narrar("Parecen soldados, y no son los unicos que has visto.¿Esta la mazmorra bajo asedio?¿O seran prisioneros?")
        narrar("La sangre no ha terminado de secarse. Y el equipo que llevan —el que queda entero— es de buena factura.")
        preguntar("¿Rebuscas entre los restos? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Tu instinto te dice que te muevas rápido y en silencio. Obedeces a medias.")
            narrar("Empiezas a apartar cuerpos. Hay que buscar antes de que llegue lo que los mató.")
            opciones = ["estoque", "armadura", "pocion"]
            if "estoque" in estado["armas_jugador"]:
                opciones.remove("estoque")
            tirada = random.choice(opciones)
            if tirada == "estoque":
                narrar("Debajo de un cuerpo sin cabeza, medio enterrado en sangre coagulada, hay un estoque.")
                narrar("Hoja estrecha, guardia limpia. Alguien lo cuidaba. Lo limpias en un jirón de tela sin dejar de escuchar.")
                narrar("El silencio de la sala empieza a cambiar de textura.")
                recompensa = {"armas": {"estoque": {}}}
                alerta("Una sombra se desprende del fondo de la sala. Ha estado ahí todo el tiempo.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
            elif tirada == "armadura":
                narrar("Entre los cuerpos hay piezas de armadura que todavía valen algo. Las arrancas con rapidez y te las ajustas encima.")
                narrar("Llevas demasiado tiempo quieto en esta sala.")
                alerta("Algo lo ha notado.")
                recompensa = {"armadura": 2}
                combate(personaje, enemigo_aleatorio("Rabioso"))
            elif tirada == "pocion":
                narrar("Una alforja de cuero aplastada bajo un cuerpo tiene el cierre intacto. Dentro, frascos sellados con cera roja.")
                narrar("Te los guardas sin contarlos.")
                alerta("Cuando te incorporas, el gruñido ya está muy cerca.")
                recompensa = {"pociones": 2}
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
            return recompensa
        elif resp in ["n", "no"]:
            narrar("Demasiado reciente. Quien hizo esto podría seguir cerca, o podría ser lo que hizo esto lo que sigue cerca.")
            tirada = random.random()
            if tirada < 0.2:
                narrar("Al bordear la sala, tu bota tropieza con algo de cristal. Un frasco sellado, intacto, medio escondido bajo un brazo sin dueño.")
                narrar("Lo guardas sin pararte y sigues adelante.")
                return {"pociones": 1}
            elif tirada < 0.5:
                narrar("Llevas medio cruce cuando oyes pasos al fondo del pasillo. Rápidos. Directos.")
                alerta("No te ha visto parar. Ya te tiene.")
                combate(personaje, enemigo_aleatorio())
                narrar("Cuando termina, la sala huele aún peor que antes. Sales sin mirar atrás.")
                return {}
            else:
                narrar("Cruzas pegado a la pared, sin pararte, sin mirar los cuerpos más de lo necesario.")
                narrar("Al salir, el aire sigue oliendo a sangre, pero al menos está en movimiento.")
                narrar("Nadie te sigue. Esta vez.")
                return {}
        else:
            alerta("Respuesta no válida.")
            continue


# ================== TABLA DE DESPACHO ==================
# Número de evento → función correspondiente

_EVENTOS: dict = {
    1: _evento_1,
    2: _evento_2,
    3: _evento_3,
    4: _evento_4,
    5: _evento_5,
    6: _evento_6,
    7: _evento_7,
    8: _evento_8,
    9: _evento_9,
    10: _evento_10,
    11: _evento_11,
    12: _evento_12,
    13: _evento_13,
    14: _evento_14,
    15: _evento_15,
    16: _evento_16,
    17: _evento_17,
    18: _evento_18,
    19: _evento_19,
    20: _evento_20,
}


# ================== ROUTER DE EVENTOS PRINCIPAL ==================

def evento_aleatorio(personaje):
    """
    Router principal de eventos: selecciona y ejecuta un evento aleatorio
    usando el sistema de bolsa no-repetidora.
    
    Gestiona el evento especial 13 (encuentro con jefe) cuando se alcanza
    el contador de eventos_superados.
    
    Args:
        personaje: dict del personaje con stats y nivel actual
    
    Returns:
        dict: resultados del evento (cambios a aplicar al personaje)
    """
    estado["eventos_superados"] += 1
    
    # Evento especial: encuentro con jefe en evento 13 (nivel < 2)
    if estado["eventos_superados"] == eventos_jefe and personaje["nivel"] < 2:
        narrar("Mientras merodeas por los pasillos, oyes un tintineo lejano, seguido por unos pasos mastodonticos, cada vez mas cerca...")
        combate(personaje, crear_carcelero())
        if personaje.get("_huyo_combate", False):
            estado["eventos_superados"] = eventos_jefe - 1  # Forrix reaparecerá en el próximo evento
        return {}    
    
    # Sistema de bolsa para eventos normales
    evento = obtener_evento_de_bolsa()
    handler = _EVENTOS.get(evento)
    return handler(personaje) if handler else {}

# ================== FIN DEL MÓDULO ==================
