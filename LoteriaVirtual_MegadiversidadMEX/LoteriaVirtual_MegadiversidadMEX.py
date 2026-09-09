
import sys
import os
import json
import random
import pygame

# ---------------------------------------------------------
# CONFIGURACIÓN Y CONSTANTES
# ---------------------------------------------------------
ANCHO = 900
ALTO = 700
FPS = 60

# Colores (R, G, B)
COLOR_FONDO = (245, 240, 230)
COLOR_TEXTO = (30, 30, 30)
COLOR_PRIMARIO = (38, 115, 77)     # Verde tradicional
COLOR_SECUNDARIO = (190, 50, 45)   # Rojo mexicano
COLOR_BOTON = (52, 73, 94)
COLOR_BOTON_HOVER = (41, 128, 185)
COLOR_BLANCO = (255, 255, 255)
COLOR_SOMBRA = (0, 0, 0, 160)       # Negro semitransparente para marcar casilla

ARCHIVO_ESTADO = "plantillas_disponibles.json"

# Las 16 plantillas balanceadas de 3x3 (9 cartas cada una)
PLANTILLAS = [
    [1, 2, 3, 9, 12, 13, 17, 19, 21],
    [4, 5, 11, 12, 16, 17, 22, 27, 28],
    [3, 11, 14, 16, 17, 19, 21, 24, 25],
    [1, 4, 9, 10, 14, 18, 21, 25, 29],
    [5, 10, 13, 14, 15, 16, 20, 24, 30],
    [2, 4, 7, 10, 11, 22, 26, 28, 30],
    [8, 9, 12, 18, 22, 23, 26, 28, 30],
    [1, 3, 4, 6, 11, 16, 23, 25, 28],
    [8, 9, 15, 18, 19, 20, 22, 25, 29],
    [2, 8, 12, 13, 15, 23, 24, 29, 30],
    [5, 6, 10, 16, 17, 19, 20, 27, 29],
    [7, 9, 14, 18, 20, 24, 25, 26, 28],
    [2, 5, 8, 10, 15, 19, 21, 22, 30],
    [4, 6, 7, 15, 21, 23, 24, 26, 27],
    [1, 2, 3, 6, 7, 8, 13, 23, 27],
    [3, 5, 7, 11, 13, 14, 18, 20, 29]
]


# ---------------------------------------------------------
# SISTEMA DE BLOQUEO DE PLANTILLAS
# ---------------------------------------------------------
def obtener_plantilla_disponible():
    """Asigna una plantilla aleatoria no usada y la bloquea en el archivo JSON."""
    if not os.path.exists(ARCHIVO_ESTADO):
        disponibles = list(range(len(PLANTILLAS)))
    else:
        try:
            with open(ARCHIVO_ESTADO, "r") as f:
                disponibles = json.load(f)
        except Exception:
            disponibles = list(range(len(PLANTILLAS)))

    if not disponibles:
        return None  # Ya se asignaron las 16

    elegida = random.choice(disponibles)
    disponibles.remove(elegida)

    with open(ARCHIVO_ESTADO, "w") as f:
        json.dump(disponibles, f)

    return elegida


def resetear_plantillas():
    """Libera todas las 16 plantillas para una nueva partida."""
    with open(ARCHIVO_ESTADO, "w") as f:
        json.dump(list(range(len(PLANTILLAS))), f)


# ---------------------------------------------------------
# CARGADOR DE IMÁGENES CON PLACEHOLDER DE RESPALDO
# ---------------------------------------------------------
class GestorImagenes:
    def __init__(self, fuente_placeholder):
        self.imagenes = {}
        self.fuente = fuente_placeholder

    def obtener_imagen(self, numero, ancho, alto):
        clave = (numero, ancho, alto)
        if clave in self.imagenes:
            return self.imagenes[clave]

        # Extensiones a buscar
        extensiones = [".png", ".jpg", ".jpeg", ".webp"]
        rutas_posibles = []
        for ext in extensiones:
            rutas_posibles.append(f"lot{numero}{ext}")
            rutas_posibles.append(os.path.join("imagenes", f"lot{numero}{ext}"))

        superficie = None
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                try:
                    img = pygame.image.load(ruta).convert_alpha()
                    superficie = pygame.transform.smoothscale(img, (ancho, alto))
                    break
                except Exception:
                    pass

        # Si no existe la imagen, se crea un recuadro ilustrativo
        if superficie is None:
            superficie = pygame.Surface((ancho, alto))
            superficie.fill((235, 235, 240))
            pygame.draw.rect(superficie, (180, 180, 190), (0, 0, ancho, alto), 3)

            # Texto informativo
            txt_num = self.fuente.render(f"#{numero}", True, COLOR_PRIMARIO)
            txt_lbl = self.fuente.render(f"lot{numero}", True, COLOR_TEXTO)
            superficie.blit(txt_num, (ancho // 2 - txt_num.get_width() // 2, alto // 2 - 25))
            superficie.blit(txt_lbl, (ancho // 2 - txt_lbl.get_width() // 2, alto // 2 + 10))

        self.imagenes[clave] = superficie
        return superficie


# ---------------------------------------------------------
# ELEMENTO BOTÓN
# ---------------------------------------------------------
class Boton:
    def __init__(self, x, y, ancho, alto, texto, color=COLOR_BOTON, color_hover=COLOR_BOTON_HOVER):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color = color
        self.color_hover = color_hover

    def dibujar(self, pantalla, fuente):
        pos_mouse = pygame.mouse.get_pos()
        col = self.color_hover if self.rect.collidepoint(pos_mouse) else self.color
        pygame.draw.rect(pantalla, col, self.rect, border_radius=10)
        pygame.draw.rect(pantalla, COLOR_BLANCO, self.rect, width=2, border_radius=10)

        superficie_texto = fuente.render(self.texto, True, COLOR_BLANCO)
        pantalla.blit(superficie_texto, (
            self.rect.centerx - superficie_texto.get_width() // 2,
            self.rect.centery - superficie_texto.get_height() // 2
        ))

    def es_clickeado(self, evento):
        return evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos)


# ---------------------------------------------------------
# FLUJO DEL JUEGO
# ---------------------------------------------------------
def ejecutar_juego():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Lotería de la Megadiversidad")
    reloj = pygame.time.Clock()

    fuente_grande = pygame.font.SysFont("Arial", 36, bold=True)
    fuente_media = pygame.font.SysFont("Arial", 24, bold=True)
    fuente_chica = pygame.font.SysFont("Arial", 18)

    gestor_img = GestorImagenes(fuente_media)

    estado = "MENU"
    num_plantilla_idx = None
    cartas_plantilla = []
    casillas_marcadas = [False] * 9  # Estado para las 9 casillas

    # Estado Organizador
    baraja_organizador = []
    indice_organizador = 0

    # Botones menú
    btn_jugador = Boton(ANCHO // 2 - 180, 240, 360, 65, "ENTRAR COMO JUGADOR", COLOR_PRIMARIO)
    btn_organizador = Boton(ANCHO // 2 - 180, 330, 360, 65, "ENTRAR COMO ORGANIZADOR", COLOR_SECUNDARIO)
    btn_reset = Boton(ANCHO // 2 - 180, 420, 360, 50, "Reiniciar Plantillas Asignadas", (100, 100, 100))

    # Botones organizador
    btn_siguiente = Boton(ANCHO // 2 + 20, ALTO - 100, 200, 55, "Siguiente >", COLOR_PRIMARIO)
    btn_anterior = Boton(ANCHO // 2 - 220, ALTO - 100, 200, 55, "< Anterior", COLOR_BOTON)
    btn_volver_org = Boton(30, 30, 140, 40, "< Menú", (120, 120, 120))

    # Botón volver jugador
    btn_volver_jug = Boton(30, 30, 140, 40, "< Menú", (120, 120, 120))

    mensaje_error_menu = ""

    ejecutando = True
    while ejecutando:
        reloj.tick(FPS)
        eventos = pygame.event.get()

        for evento in eventos:
            if evento.type == pygame.QUIT:
                ejecutando = False

            # ---------------------------------------------
            # EVENTOS: MENÚ PRINCIPAL
            # ---------------------------------------------
            if estado == "MENU":
                if btn_jugador.es_clickeado(evento):
                    idx = obtener_plantilla_disponible()
                    if idx is not None:
                        num_plantilla_idx = idx
                        cartas_plantilla = PLANTILLAS[num_plantilla_idx]
                        casillas_marcadas = [False] * 9
                        mensaje_error_menu = ""
                        estado = "JUGADOR"
                    else:
                        mensaje_error_menu = "¡Se agotaron las 16 plantillas! Pulsa 'Reiniciar'."

                elif btn_organizador.es_clickeado(evento):
                    baraja_organizador = list(range(1, 31))
                    random.shuffle(baraja_organizador)
                    indice_organizador = 0
                    estado = "ORGANIZADOR"

                elif btn_reset.es_clickeado(evento):
                    resetear_plantillas()
                    mensaje_error_menu = "¡Plantillas liberadas con éxito (16 disponibles)!"

            # ---------------------------------------------
            # EVENTOS: JUGADOR
            # ---------------------------------------------
            elif estado == "JUGADOR":
                if btn_volver_jug.es_clickeado(evento):
                    estado = "MENU"

                # Clic sobre las casillas de la plantilla 3x3
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Tamaño de cada casilla en la cuadrícula
                    ancho_c, alto_c = 160, 170
                    margen_x = (ANCHO - (3 * ancho_c + 2 * 15)) // 2
                    margen_y = 120

                    mx, my = evento.pos
                    for i in range(9):
                        col = i % 3
                        fil = i // 3
                        rx = margen_x + col * (ancho_c + 15)
                        ry = margen_y + fil * (alto_c + 15)
                        rect_casilla = pygame.Rect(rx, ry, ancho_c, alto_c)

                        if rect_casilla.collidepoint(mx, my):
                            casillas_marcadas[i] = not casillas_marcadas[i]

            # ---------------------------------------------
            # EVENTOS: ORGANIZADOR
            # ---------------------------------------------
            elif estado == "ORGANIZADOR":
                if btn_volver_org.es_clickeado(evento):
                    estado = "MENU"

                # Siguiente carta
                if btn_siguiente.es_clickeado(evento) or (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RIGHT)):
                    if indice_organizador < len(baraja_organizador) - 1:
                        indice_organizador += 1

                # Anterior carta
                if btn_anterior.es_clickeado(evento) or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_LEFT):
                    if indice_organizador > 0:
                        indice_organizador -= 1

        # -------------------------------------------------
        # RENDERIZADO
        # -------------------------------------------------
        pantalla.fill(COLOR_FONDO)

        # ---------------- PANTALLA: MENÚ ----------------
        if estado == "MENU":
            titulo = fuente_grande.render("LOTERÍA MEXICANA", True, COLOR_PRIMARIO)
            subtitulo = fuente_media.render("Megadiversidad de México", True, COLOR_SECUNDARIO)
            pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 90))
            pantalla.blit(subtitulo, (ANCHO // 2 - subtitulo.get_width() // 2, 145))

            btn_jugador.dibujar(pantalla, fuente_media)
            btn_organizador.dibujar(pantalla, fuente_media)
            btn_reset.dibujar(pantalla, fuente_chica)

            if mensaje_error_menu:
                col_txt = COLOR_SECUNDARIO if "agotaron" in mensaje_error_menu else COLOR_PRIMARIO
                txt_err = fuente_chica.render(mensaje_error_menu, True, col_txt)
                pantalla.blit(txt_err, (ANCHO // 2 - txt_err.get_width() // 2, 500))

        # ---------------- PANTALLA: JUGADOR -------------
        elif estado == "JUGADOR":
            btn_volver_jug.dibujar(pantalla, fuente_chica)

            txt_tit = fuente_media.render(f"Plantilla Asignada #{num_plantilla_idx + 1:02d}", True, COLOR_PRIMARIO)
            pantalla.blit(txt_tit, (ANCHO // 2 - txt_tit.get_width() // 2, 35))

            instruccion = fuente_chica.render("Haz clic en una carta para marcarla / desmarcarla", True, (100, 100, 100))
            pantalla.blit(instruccion, (ANCHO // 2 - instruccion.get_width() // 2, 75))

            ancho_c, alto_c = 160, 170
            margen_x = (ANCHO - (3 * ancho_c + 2 * 15)) // 2
            margen_y = 115

            # Dibujar la cuadrícula 3x3
            for i in range(9):
                num_carta = cartas_plantilla[i]
                col = i % 3
                fil = i // 3
                rx = margen_x + col * (ancho_c + 15)
                ry = margen_y + fil * (alto_c + 15)

                # 1. Dibujar la imagen de la carta
                img_carta = gestor_img.obtener_imagen(num_carta, ancho_c, alto_c)
                pantalla.blit(img_carta, (rx, ry))

                # Marco de la carta
                pygame.draw.rect(pantalla, (60, 60, 60), (rx, ry, ancho_c, alto_c), 2, border_radius=6)

                # 2. Si está marcada, dibujar capa oscura transparente
                if casillas_marcadas[i]:
                    capa_oscura = pygame.Surface((ancho_c, alto_c), pygame.SRCALPHA)
                    capa_oscura.fill(COLOR_SOMBRA)
                    pantalla.blit(capa_oscura, (rx, ry))

                    # Indicador de selección (palomita / círculo)
                    pygame.draw.circle(pantalla, COLOR_BLANCO, (rx + ancho_c // 2, ry + alto_c // 2), 22, 3)

            # Verificar si ya ganó (todas las 9 marcadas)
            if all(casillas_marcadas):
                # Banner flotante de victoria
                banner = pygame.Rect(ANCHO // 2 - 250, ALTO // 2 - 60, 500, 120)
                pygame.draw.rect(pantalla, COLOR_SECUNDARIO, banner, border_radius=15)
                pygame.draw.rect(pantalla, COLOR_BLANCO, banner, 4, border_radius=15)

                txt_win1 = fuente_grande.render("¡¡LOTERÍA!!", True, COLOR_BLANCO)
                txt_win2 = fuente_media.render("¡Has completado tu plantilla!", True, COLOR_BLANCO)
                pantalla.blit(txt_win1, (ANCHO // 2 - txt_win1.get_width() // 2, ALTO // 2 - 45))
                pantalla.blit(txt_win2, (ANCHO // 2 - txt_win2.get_width() // 2, ALTO // 2 + 5))

        # ---------------- PANTALLA: ORGANIZADOR ----------
        elif estado == "ORGANIZADOR":
            btn_volver_org.dibujar(pantalla, fuente_chica)

            titulo_org = fuente_media.render("MESA DEL ORGANIZADOR (CANTOR)", True, COLOR_SECUNDARIO)
            pantalla.blit(titulo_org, (ANCHO // 2 - titulo_org.get_width() // 2, 35))

            # Progreso
            txt_progreso = fuente_chica.render(
                f"Carta {indice_organizador + 1} de {len(baraja_organizador)}", True, COLOR_TEXTO
            )
            pantalla.blit(txt_progreso, (ANCHO // 2 - txt_progreso.get_width() // 2, 80))

            # Mostrar la carta actual en grande
            num_actual = baraja_organizador[indice_organizador]
            ancho_grande, alto_grande = 300, 420
            pos_x = ANCHO // 2 - ancho_grande // 2
            pos_y = 120

            img_grande = gestor_img.obtener_imagen(num_actual, ancho_grande, alto_grande)
            pantalla.blit(img_grande, (pos_x, pos_y))
            pygame.draw.rect(pantalla, (40, 40, 40), (pos_x, pos_y, ancho_grande, alto_grande), 3, border_radius=10)

            # Botones de navegación
            btn_anterior.dibujar(pantalla, fuente_media)
            btn_siguiente.dibujar(pantalla, fuente_media)

            teclas_ayuda = fuente_chica.render("Usa [ESPACIO] o [FLECHA DER] para avanzar", True, (120, 120, 120))
            pantalla.blit(teclas_ayuda, (ANCHO // 2 - teclas_ayuda.get_width() // 2, ALTO - 35))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    ejecutar_juego()
