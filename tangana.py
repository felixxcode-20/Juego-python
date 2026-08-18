import pygame
import random
import sys
import os

# ---------- INICIALIZACIÓN ----------
pygame.init()
pygame.mixer.init()

# Constantes de pantalla
ANCHO = 1100
ALTO = 600
FPS = 60
PANTALLA = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("TANGANA")
RELOJ = pygame.time.Clock()

# Colores
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
ROJO = (220, 30, 30)
VERDE = (30, 220, 60)
AMARILLO = (255, 220, 30)
AZUL = (40, 120, 220)
GRIS = (60, 60, 60)
GRIS_CLARO = (180, 180, 180)
DORADO = (255, 200, 60)
NARANJA = (255, 130, 30)
MORADO = (160, 60, 220)
CIAN = (60, 220, 220)
ROSA = (255, 80, 180)

# Estados del juego
MENU_INICIO = 0
SELECCION = 1
COMBATE = 2
GANADOR = 3

# Tipos de ataque
GOLPE = "golpe"
PATADA = "patada"
ESPECIAL = "especial"

# ---------- FUENTES ----------
def fuente(tam):
    # Intentar cargar una fuente del sistema; fallback a la default
    rutas = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
    ]
    for r in rutas:
        if os.path.exists(r):
            try:
                return pygame.font.Font(r, tam)
            except Exception:
                pass
    return pygame.font.Font(None, tam)


# ---------- UTILIDADES DE DIBUJO ----------
def dibujar_texto(texto, x, y, tam=40, color=BLANCO, centro=True, sombra=True):
    f = fuente(tam)
    surf = f.render(texto, True, color)
    rect = surf.get_rect()
    if centro:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    if sombra:
        s = f.render(texto, True, NEGRO)
        sr = s.get_rect()
        if centro:
            sr.center = (x + 3, y + 3)
        else:
            sr.topleft = (x + 3, y + 3)
        PANTALLA.blit(s, sr)
    PANTALLA.blit(surf, rect)
    return rect


# ---------- PERSONAJES (datos) ----------
# Cada personaje tiene: nombre, color principal, color secundario, stats
PERSONAJES = [
    {
        "nombre": "MUSASHI",
        "color": (255, 80, 40),
        "color2": (255, 220, 100),
        "hp": 100,
        "golpe_dmg": 8,
        "patada_dmg": 12,
        "especial_dmg": 22,
        "velocidad": 5,
        "estilo": "Equilibrado",
    },
    {
        "nombre": "RYU",
        "color": (80, 200, 255),
        "color2": (220, 240, 255),
        "hp": 90,
        "golpe_dmg": 7,
        "patada_dmg": 10,
        "especial_dmg": 25,
        "velocidad": 6,
        "estilo": "Rápido",
    },
    {
        "nombre": "ODA",
        "color": (140, 80, 50),
        "color2": (220, 160, 90),
        "hp": 130,
        "golpe_dmg": 10,
        "patada_dmg": 14,
        "especial_dmg": 18,
        "velocidad": 4,
        "estilo": "Tanque",
    },
    {
        "nombre": "STEVE",
        "color": (130, 60, 200),
        "color2": (220, 160, 255),
        "hp": 95,
        "golpe_dmg": 9,
        "patada_dmg": 13,
        "especial_dmg": 24,
        "velocidad": 5.5,
        "estilo": "Agresivo",
    },
]


# ---------- CLASE LUCHADOR ----------
class Luchador:
    def __init__(self, x, y, datos, mirando_derecha=True, es_jugador=True):
        self.datos = datos
        self.x = float(x)
        self.y = float(y)
        self.ancho = 70
        self.alto = 130
        self.velocidad = datos["velocidad"]
        self.vx = 0.0
        self.hp_max = datos["hp"]
        self.hp = datos["hp"]
        self.mirando_derecha = mirando_derecha
        self.es_jugador = es_jugador

        # Estados
        self.atacando = None  # "golpe", "patada", "especial" o None
        self.frame_ataque = 0
        self.duracion_ataque = 0
        self.cooldown_ataque = 0
        self.tiempo_invulnerable = 0
        self.saltando = False
        self.vy = 0.0
        self.suelo = y
        self.ha_golpeado = False  # para que un ataque solo impacte una vez

        # Visual / animación de daño
        self.parpadeo = 0
        self.energia_especial = 0  # 0 a 100
        self.buffer_ataque = None  # para inputs casi simultáneos

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.ancho // 2, int(self.y) - self.alto,
                           self.ancho, self.alto)

    def en_el_suelo(self):
        return not self.saltando

    def saltar(self):
        if not self.saltando:
            self.saltando = True
            self.vy = -16

    def mover(self, dx):
        self.x += dx
        # Limites del escenario
        if self.x < 80:
            self.x = 80
        if self.x > ANCHO - 80:
            self.x = ANCHO - 80

    def iniciar_ataque(self, tipo):
        if self.cooldown_ataque > 0 or self.atacando is not None:
            return False
        self.atacando = tipo
        self.frame_ataque = 0
        self.ha_golpeado = False
        if tipo == GOLPE:
            self.duracion_ataque = 12
            self.cooldown_ataque = 18
        elif tipo == PATADA:
            self.duracion_ataque = 18
            self.cooldown_ataque = 26
        elif tipo == ESPECIAL:
            self.duracion_ataque = 28
            self.cooldown_ataque = 50
        return True

    def rect_ataque(self):
        """Devuelve el rectángulo del arma según el ataque. None si no aplica."""
        if self.atacando is None or self.ha_golpeado:
            return None
        # Solo golpea en ciertos frames
        if self.atacando == GOLPE:
            if not (4 <= self.frame_ataque <= 8):
                return None
            alcance = 60
        elif self.atacando == PATADA:
            if not (8 <= self.frame_ataque <= 13):
                return None
            alcance = 70
        elif self.atacando == ESPECIAL:
            if not (12 <= self.frame_ataque <= 22):
                return None
            alcance = 120
        else:
            return None

        cx = self.x + (alcance // 2 if self.mirando_derecha else -alcance // 2)
        return pygame.Rect(int(cx - alcance // 2), int(self.y - self.alto + 20),
                           alcance, self.alto - 40)

    def actualizar(self):
        # Física salto
        if self.saltando:
            self.y += self.vy
            self.vy += 0.9
            if self.y >= self.suelo:
                self.y = self.suelo
                self.saltando = False
                self.vy = 0

        # Cooldowns
        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= 1
        if self.tiempo_invulnerable > 0:
            self.tiempo_invulnerable -= 1
        if self.parpadeo > 0:
            self.parpadeo -= 1

        # Animación de ataque
        if self.atacando is not None:
            self.frame_ataque += 1
            if self.frame_ataque >= self.duracion_ataque:
                self.atacando = None
                self.frame_ataque = 0

    def recibir_dano(self, dmg):
        if self.tiempo_invulnerable > 0:
            return False
        self.hp -= dmg
        self.hp = max(0, self.hp)
        self.parpadeo = 18
        self.tiempo_invulnerable = 22
        return True

    def cargar_especial(self, cantidad=20):
        self.energia_especial = min(100, self.energia_especial + cantidad)

    def dibujar(self, surf):
        # Parpadeo al recibir daño
        if self.parpadeo > 0 and (self.parpadeo // 2) % 2 == 0:
            return  # dibujar saltado para efecto visual

        x = int(self.x)
        y = int(self.y)
        c1 = self.datos["color"]
        c2 = self.datos["color2"]

        # Sombra en el suelo
        sombra = pygame.Surface((70, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 120), sombra.get_rect())
        surf.blit(sombra, (x - 35, int(self.suelo) + 4))

        # Cuerpo (torso)
        torso_rect = pygame.Rect(x - 22, y - 95, 44, 55)
        pygame.draw.rect(surf, c1, torso_rect, border_radius=8)
        # Borde
        pygame.draw.rect(surf, NEGRO, torso_rect, 2, border_radius=8)

        # Cabeza
        cabeza_centro = (x, y - 115)
        pygame.draw.circle(surf, c2, cabeza_centro, 22)
        pygame.draw.circle(surf, NEGRO, cabeza_centro, 22, 2)

        # Ojos (dirección)
        ojo_dx = 6 if self.mirando_derecha else -6
        pygame.draw.circle(surf, BLANCO, (cabeza_centro[0] + ojo_dx - 4, cabeza_centro[1] - 4), 4)
        pygame.draw.circle(surf, BLANCO, (cabeza_centro[0] + ojo_dx + 6, cabeza_centro[1] - 4), 4)
        pygame.draw.circle(surf, NEGRO, (cabeza_centro[0] + ojo_dx - 3, cabeza_centro[1] - 4), 2)
        pygame.draw.circle(surf, NEGRO, (cabeza_centro[0] + ojo_dx + 7, cabeza_centro[1] - 4), 2)

        # Boca según estado
        if self.atacando == GOLPE:
            pygame.draw.arc(surf, NEGRO,
                            pygame.Rect(cabeza_centro[0] - 6, cabeza_centro[1] + 4, 12, 8),
                            3.14, 6.28, 2)
        else:
            pygame.draw.line(surf, NEGRO,
                             (cabeza_centro[0] - 6, cabeza_centro[1] + 6),
                             (cabeza_centro[0] + 6, cabeza_centro[1] + 6), 2)

        # Piernas
        offset_pierna = 0
        if self.atacando == PATADA:
            offset_pierna = -28 if self.mirando_derecha else 28
        # Pierna izquierda
        pygame.draw.line(surf, c1, (x - 12, y - 40), (x - 12 + offset_pierna, y - 5), 10)
        # Pierna derecha
        pygame.draw.line(surf, c1, (x + 12, y - 40), (x + 12, y - 5), 10)
        # Pies
        pygame.draw.ellipse(surf, NEGRO, (x - 22 + offset_pierna, y - 8, 22, 10))
        pygame.draw.ellipse(surf, NEGRO, (x + 2, y - 8, 22, 10))

        # Brazos
        brazo_golpe_x = 0
        if self.atacando == GOLPE:
            brazo_golpe_x = (40 if self.mirando_derecha else -40)
        # Brazo izquierdo
        pygame.draw.line(surf, c2, (x - 22, y - 80), (x - 22 + brazo_golpe_x, y - 65), 8)
        # Brazo derecho
        pygame.draw.line(surf, c2, (x + 22, y - 80), (x + 22 + brazo_golpe_x, y - 65), 8)
        # Puños
        pygame.draw.circle(surf, c2, (x - 22 + brazo_golpe_x, y - 65), 7)
        pygame.draw.circle(surf, c2, (x + 22 + brazo_golpe_x, y - 65), 7)

        # Efecto visual del ataque especial
        if self.atacando == ESPECIAL and self.frame_ataque > 10:
            for i in range(6):
                ang = self.frame_ataque * 0.4 + i
                ex = x + (60 if self.mirando_derecha else -60) + int(20 * pygame.math.Vector2(1, 0).rotate(ang * 30).x)
                ey = y - 70 + int(20 * pygame.math.Vector2(1, 0).rotate(ang * 30).y)
                r = 12 - (self.frame_ataque - 10) // 3
                if r > 0:
                    col = (random.randint(200, 255), random.randint(100, 200), 50)
                    pygame.draw.circle(surf, col, (ex, ey), r)


# ---------- BARRA DE VIDA ----------
def dibujar_barra_hp(x, y, ancho, alto, hp, hp_max, nombre, color, lado="izq"):
    # Marco
    pygame.draw.rect(PANTALLA, NEGRO, (x - 3, y - 3, ancho + 6, alto + 6), border_radius=6)
    # Fondo
    pygame.draw.rect(PANTALLA, GRIS, (x, y, ancho, alto), border_radius=4)
    # Vida
    pct = max(0, hp / hp_max)
    fill_w = int(ancho * pct)
    if fill_w > 0:
        # Gradiente simulado por dos tonos
        c_fill = color
        if pct < 0.3:
            c_fill = ROJO
        elif pct < 0.6:
            c_fill = AMARILLO
        else:
            c_fill = color
        pygame.draw.rect(PANTALLA, c_fill, (x, y, fill_w, alto), border_radius=4)
        # Brillo interior
        pygame.draw.rect(PANTALLA, BLANCO, (x + 2, y + 2, fill_w - 4, 4), border_radius=2)

    # Nombre
    f = fuente(22)
    surf = f.render(nombre, True, BLANCO)
    rect = surf.get_rect()
    if lado == "izq":
        rect.topleft = (x, y - 28)
    else:
        rect.topright = (x + ancho, y - 28)
    PANTALLA.blit(surf, rect)


# ---------- HUD ENERGÍA ESPECIAL ----------
def dibujar_barra_especial(x, y, ancho, alto, energia, color):
    pct = max(0, energia / 100)
    pygame.draw.rect(PANTALLA, NEGRO, (x - 2, y - 2, ancho + 4, alto + 4), border_radius=4)
    pygame.draw.rect(PANTALLA, GRIS, (x, y, ancho, alto), border_radius=3)
    if pct > 0:
        # Color brillante para especial
        c = DORADO if pct < 1 else NARANJA
        pygame.draw.rect(PANTALLA, c, (x, y, int(ancho * pct), alto), border_radius=3)
    dibujar_texto("ESPECIAL", x + ancho // 2, y + alto // 2, 14, NEGRO, centro=True, sombra=False)


# ---------- ESCENARIO ----------
def dibujar_escenario(t):
    # Cielo de fondo con degradado
    cielo = pygame.Surface((ANCHO, ALTO))
    for i in range(ALTO):
        ratio = i / ALTO
        r = int(20 + 40 * ratio)
        g = int(10 + 30 * ratio)
        b = int(60 + 60 * ratio)
        pygame.draw.line(cielo, (r, g, b), (0, i), (ANCHO, i))
    PANTALLA.blit(ciempo := cielo, (0, 0))

    # Luna / sol con pulso
    luna_x, luna_y = ANCHO - 180, 110
    radio = 50 + int(4 * pygame.math.Vector2(1, 0).rotate(t * 1.5).x)
    halo = pygame.Surface((radio * 3, radio * 3), pygame.SRCALPHA)
    pygame.draw.circle(halo, (255, 220, 180, 60), (radio * 3 // 2, radio * 3 // 2), radio + 30)
    pygame.draw.circle(halo, (255, 220, 180, 110), (radio * 3 // 2, radio * 3 // 2), radio + 10)
    PANTALLA.blit(halo, (luna_x - radio * 3 // 2, luna_y - radio * 3 // 2))
    pygame.draw.circle(PANTALLA, (255, 240, 200), (luna_x, luna_y), radio)

    # Edificios / silueta al fondo
    edificios = [
        (60, 380, 120, 200), (180, 320, 90, 260), (270, 360, 110, 220),
        (380, 300, 80, 280), (460, 340, 130, 240), (590, 320, 90, 260),
        (680, 360, 110, 220), (790, 310, 100, 270), (890, 350, 130, 230),
        (1020, 330, 80, 250),
    ]
    for ex, ey, ew, eh in edificios:
        pygame.draw.rect(PANTALLA, (15, 10, 35), (ex, ey, ew, eh))
        # Ventanas
        for wy in range(ey + 15, ey + eh - 10, 25):
            for wx in range(ex + 8, ex + ew - 8, 18):
                if (wx + wy) % 7 == 0 and random.random() > 0.5:
                    pygame.draw.rect(PANTALLA, (255, 220, 120), (wx, wy, 8, 12))

    # Suelo del estadio
    pygame.draw.rect(PANTALLA, (40, 30, 25), (0, 480, ANCHO, ALTO - 480))
    pygame.draw.rect(PANTALLA, DORADO, (0, 478, ANCHO, 4))

    # Líneas del suelo
    for i in range(0, ANCHO, 80):
        pygame.draw.line(PANTALLA, (80, 60, 40), (i, 482), (i, ALTO), 2)


# ---------- MENÚ DE INICIO ----------
def pantalla_inicio():
    t = 0
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                return SELECCION

        dibujar_escenario(t)
        t += 1

        # Capa oscura semitransparente
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 160))
        PANTALLA.blit(capa, (0, 0))

        # Título grande con efecto
        titulo = "TANGANA"
        dibujar_texto(titulo, ANCHO // 2, 180, 110, ROJO, True, True)

        # Subtítulo parpadeante
        if (t // 30) % 2 == 0:
            dibujar_texto("Presiona cualquier tecla para jugar", ANCHO // 2, 470, 36, BLANCO, True, True)

        dibujar_texto("J1: A D moverse  |  W saltar  |  F golpe  |  G patada  |  H especial",
                      ANCHO // 2, 540, 18, GRIS_CLARO, True, True)

        pygame.display.flip()
        RELOJ.tick(FPS)


# ---------- PANTALLA DE SELECCIÓN ----------
def pantalla_seleccion():
    seleccion_p1 = 0
    t = 0
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_a:
                    seleccion_p1 = (seleccion_p1 - 1) % len(PERSONAJES)
                elif ev.key == pygame.K_d:
                    seleccion_p1 = (seleccion_p1 + 1) % len(PERSONAJES)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    # Confirmar - CPU elige uno distinto al azar
                    opciones_cpu = [i for i in range(len(PERSONAJES)) if i != seleccion_p1]
                    seleccion_cpu = random.choice(opciones_cpu)
                    return seleccion_p1, seleccion_cpu

        dibujar_escenario(t)
        t += 1
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 180))
        PANTALLA.blit(capa, (0, 0))

        dibujar_texto("ELIGE TU LUCHADOR", ANCHO // 2, 70, 50, DORADO, True, True)
        dibujar_texto("A / D para cambiar   |   H (o ENTER) para confirmar",
                      ANCHO // 2, 115, 20, GRIS_CLARO, True, True)

        # Dibujar selección de personajes
        box_w = 180
        box_h = 200
        espacio = 30
        total_w = box_w * len(PERSONAJES) + espacio * (len(PERSONAJES) - 1)
        start_x = (ANCHO - total_w) // 2
        y_box = 200

        for i, p in enumerate(PERSONAJES):
            bx = start_x + i * (box_w + 20)
            by = y_box
            # Marco
            col_marco = DORADO if i == seleccion_p1 else GRIS_CLARO
            pygame.draw.rect(PANTALLA, col_marco, (bx - 4, by - 4, box_w + 8, box_h + 8), border_radius=10)
            pygame.draw.rect(PANTALLA, (30, 30, 50), (bx, by, box_w, box_h), border_radius=8)
            # Personaje (cabeza y cuerpo estilizado)
            cx = bx + box_w // 2
            pygame.draw.circle(PANTALLA, p["color2"], (cx, by + 50), 28)
            pygame.draw.circle(PANTALLA, NEGRO, (cx, by + 50), 28, 2)
            pygame.draw.rect(PANTALLA, p["color"], (cx - 25, by + 80, 50, 70), border_radius=6)
            pygame.draw.rect(PANTALLA, NEGRO, (cx - 25, by + 80, 50, 70), 2, border_radius=6)
            # Nombre
            dibujar_texto(p["nombre"], cx, by + 175, 22, BLANCO, True, True)

            # Stats
            stats_y = by + box_h + 15
            dibujar_texto(f"HP {p['hp']}", cx, stats_y, 16, BLANCO, True, True)
            dibujar_texto(f"Vel {p['velocidad']}", cx, stats_y + 22, 16, GRIS_CLARO, True, True)
            dibujar_texto(p["estilo"], cx, stats_y + 44, 14, DORADO, True, True)

        pygame.display.flip()
        RELOJ.tick(FPS)


# ---------- IA DE LA CPU ----------
def cpu_decidir(cpu, jugador):
    """Decide qué hacer el enemigo CPU."""
    dist = abs(cpu.x - jugador.x)
    dir_hacia = 1 if jugador.x > cpu.x else -1

    # Si está lejos, acercarse
    if dist > 180:
        cpu.vx = dir_hacia * cpu.velocidad * 0.6
        return "acercar"

    # Si está cerca, decidir atacar o moverse lateralmente
    r = random.random()
    if cpu.cooldown_ataque == 0 and cpu.atacando is None:
        if dist < 90:
            if r < 0.35:
                cpu.iniciar_ataque(GOLPE)
                return "golpe"
            elif r < 0.65:
                cpu.iniciar_ataque(PATADA)
                return "patada"
            elif r < 0.85 and cpu.energia_especial >= 100:
                cpu.iniciar_ataque(ESPECIAL)
                cpu.energia_especial = 0
                return "especial"
            else:
                cpu.vx = -dir_hacia * cpu.velocidad * 0.4  # retroceder
                return "retirada"
        else:
            cpu.vx = dir_hacia * cpu.velocidad * 0.5
            return "acercar"
    else:
        # Mover ligeramente
        cpu.vx = dir_hacia * cpu.velocidad * 0.3
        return "idle"


# ---------- PANTALLA DE COMBATE ----------
def combate(idx_p1, idx_cpu):
    p1 = Luchador(280, 480, PERSONAJES[idx_p1], mirando_derecha=True, es_jugador=True)
    cpu = Luchador(820, 480, PERSONAJES[idx_cpu], mirando_derecha=False, es_jugador=False)
    ronda_t = 0
    mensaje = ""
    mensaje_t = 0
    tiempo_para_ganador = 0

    while True:
        ronda_t += 1

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_f:
                    p1.iniciar_ataque(GOLPE)
                elif ev.key == pygame.K_g:
                    p1.iniciar_ataque(PATADA)
                elif ev.key == pygame.K_h and p1.energia_especial >= 100:
                    if p1.iniciar_ataque(ESPECIAL):
                        p1.energia_especial = 0
                elif ev.key == pygame.K_w:
                    p1.saltar()
                elif ev.key == pygame.K_r:
                    # Reiniciar
                    return "reiniciar"
                elif ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Movimiento continuo (mantener tecla)
        keys = pygame.key.get_pressed()
        if p1.atacando is None:
            dx = 0
            if keys[pygame.K_a]:
                dx -= p1.velocidad
            if keys[pygame.K_d]:
                dx += p1.velocidad
            p1.mover(dx)

        # IA CPU
        cpu.mirando_derecha = p1.x < cpu.x
        p1.mirando_derecha = cpu.x > p1.x
        accion = cpu_decidir(cpu, p1)
        cpu.mover(cpu.vx)
        # CPU salta a veces
        if random.random() < 0.005 and not cpu.saltando:
            cpu.saltar()

        # Si están muy juntos, no se traspasen
        if abs(p1.x - cpu.x) < (p1.ancho + cpu.ancho) // 2:
            if p1.x < cpu.x:
                p1.x -= 1
                cpu.x += 1
            else:
                p1.x += 1
                cpu.x -= 1

        # Actualizar entidades
        p1.actualizar()
        cpu.actualizar()

        # Resolver colisiones de ataque
        ra = p1.rect_ataque()
        if ra and ra.colliderect(cpu.get_rect()):
            dmg = 0
            if p1.atacando == GOLPE:
                dmg = p1.datos["golpe_dmg"]
            elif p1.atacando == PATADA:
                dmg = p1.datos["patada_dmg"]
            elif p1.atacando == ESPECIAL:
                dmg = p1.datos["especial_dmg"]
            if cpu.recibir_dano(dmg):
                p1.ha_golpeado = True
                p1.cargar_especial(20 if p1.atacando != ESPECIAL else 100)
                mensaje = f"¡GOLPE! -{dmg}"
                mensaje_t = 30

        rb = cpu.rect_ataque()
        if rb and rb.colliderect(p1.get_rect()):
            dmg = 0
            if cpu.atacando == GOLPE:
                dmg = cpu.datos["golpe_dmg"]
            elif cpu.atacando == PATADA:
                dmg = cpu.datos["patada_dmg"]
            elif cpu.atacando == ESPECIAL:
                dmg = cpu.datos["especial_dmg"]
            if p1.recibir_dano(dmg):
                cpu.ha_golpeado = True
                cpu.cargar_especial(20 if cpu.atacando != ESPECIAL else 100)

        # Verificar ganador
        if p1.hp <= 0 or cpu.hp <= 0:
            tiempo_para_ganador += 1
            if tiempo_para_ganador > 90:
                ganador = "JUGADOR" if cpu.hp <= 0 else "CPU"
                return ("ganador", ganador, idx_p1, idx_cpu)
        else:
            tiempo_para_ganador = 0

        # ---------- DIBUJO ----------
        dibujar_escenario(ronda_t)

        # Barras de vida
        dibujar_barra_hp(40, 30, 480, 28, p1.hp, p1.hp_max, "J1 - " + p1.datos["nombre"], p1.datos["color"], "izq")
        dibujar_barra_hp(ANCHO - 40 - 480, 30, 480, 28, cpu.hp, cpu.hp_max,
                         "CPU - " + cpu.datos["nombre"], cpu.datos["color"], "der")

        # Barras de especial
        dibujar_barra_especial(40, 70, 200, 14, p1.energia_especial, DORADO)
        dibujar_barra_especial(ANCHO - 40 - 200, 70, 200, 14, cpu.energia_especial, DORADO)

        # Línea central del HUD
        pygame.draw.line(PANTALLA, DORADO, (ANCHO // 2, 20), (ANCHO // 2, 90), 2)
        dibujar_texto("VS", ANCHO // 2, 50, 30, DORADO, True, True)

        # Dibujar luchadores (orden: el de atrás primero)
        if p1.x < cpu.x:
            cpu.dibujar(PANTALLA)
            p1.dibujar(PANTALLA)
        else:
            p1.dibujar(PANTALLA)
            cpu.dibujar(PANTALLA)

        # Mensaje flotante
        if mensaje and mensaje_t > 0:
            dibujar_texto(mensaje, ANCHO // 2, 200, 60, DORADO, True, True)
            mensaje_t -= 1

        # Indicador de especiales listos
        if p1.energia_especial >= 100:
            dibujar_texto("¡ESPECIAL LISTO!  (H)", p1.x, p1.y - 160, 16, DORADO, True, True)
        if cpu.energia_especial >= 100:
            dibujar_texto("¡CPU cargó especial!", cpu.x, cpu.y - 160, 14, ROJO, True, True)

        # HUD inferior - ayuda
        dibujar_texto("A/D mover | W saltar | F golpe | G patada | H especial | R reiniciar",
                      ANCHO // 2, ALTO - 18, 16, GRIS_CLARO, True, True)

        pygame.display.flip()
        RELOJ.tick(FPS)


# ---------- PANTALLA DE GANADOR ----------
def pantalla_ganador(ganador, idx_p1, idx_cpu):
    t = 0
    ganador_datos = PERSONAJES[idx_p1] if ganador == "JUGADOR" else PERSONAJES[idx_cpu]
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.key == pygame.K_r or ev.type == pygame.MOUSEBUTTONDOWN:
                    return "reiniciar"
                elif ev.key == pygame.K_ESCAPE:
                    return "salir"

        dibujar_escenario(t)
        t += 1
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 200))
        PANTALLA.blit(capa, (0, 0))

        # Destellos dorados
        for i in range(15):
            x = (t * 3 + i * 80) % ANCHO
            y = 200 + int(50 * pygame.math.Vector2(1, 0).rotate(t + i * 30).x)
            pygame.draw.circle(PANTALLA, DORADO, (x, y), random.randint(2, 5))

        if ganador == "JUGADOR":
            titulo = "¡VICTORIA!"
            col = DORADO
        else:
            titulo = "DERROTA"
            col = ROJO

        dibujar_texto(titulo, ANCHO // 2, 200, 110, col, True, True)
        dibujar_texto(f"{ganador_datos['nombre']} GANA LA PELEA",
                      ANCHO // 2, 300, 36, BLANCO, True, True)

        # Stats del ganador
        stats_y = 380
        hp_restante = ganador_datos["hp"] if ganador == "JUGADOR" else max(0, ganador_datos["hp"] - 30)
        # HP restante real lo sacamos del combate anterior: usamos el del personaje
        dibujar_texto(f"HP del ganador: {hp_restante}", ANCHO // 2, stats_y, 22, BLANCO, True, True)

        if (t // 25) % 2 == 0:
            dibujar_texto("R - Volver al menú   |   ESC - Salir",
                          ANCHO // 2, 520, 26, AMARILLO, True, True)

        pygame.display.flip()
        RELOJ.tick(FPS)


# ---------- BUCLE PRINCIPAL ----------
def main():
    estado = MENU_INICIO
    while True:
        if estado == MENU_INICIO:
            estado = pantalla_inicio()
        elif estado == SELECCION:
            p1_idx, cpu_idx = pantalla_seleccion()
            estado = COMBATE
        elif estado == COMBATE:
            resultado = combate(p1_idx, cpu_idx)
            if resultado == "reiniciar":
                estado = MENU_INICIO
            else:
                tipo, ganador, p1_idx, cpu_idx = resultado
                estado = GANADOR
        elif estado == GANADOR:
            accion = pantalla_ganador(ganador, p1_idx, cpu_idx)
            if accion == "reiniciar":
                estado = MENU_INICIO
            else:
                pygame.quit()
                sys.exit()


if __name__ == "__main__":
    main()