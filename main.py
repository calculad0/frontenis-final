from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import platform
from datetime import datetime
import json
import os

# Intentar importar Plyer para vibración
try:
    from plyer import vibrator
    PLYER_AVAILABLE = True
except:
    PLYER_AVAILABLE = False

# ------------------ CONFIGURACIÓN DE ESTILO ------------------

ARCHIVO = "partidos.json"

# Colores (R, G, B, A)
COLOR_AZUL = [0.2, 0.4, 0.9, 1] 
COLOR_ROJO = [0.9, 0.2, 0.2, 1] 
COLOR_AMARILLO = [1, 0.8, 0, 1]
COLOR_VERDE = [0, 0.8, 0.2, 1] 
COLOR_FONDO_CARD = [0.1, 0.1, 0.15, 1]

# Configuración de Fuente Segura
FONT_SPORT = "RussoOne-Regular.ttf"
TIENE_FUENTE = False

if os.path.exists(FONT_SPORT):
    TIENE_FUENTE = True
else:
    FONT_SPORT = "Roboto" 

# TAMAÑOS DE FUENTE
FONT_SIZE_SCORE = 120
FONT_SIZE_TITLE = 40
FONT_SIZE_NAMES = 22

# ------------------ UTILIDADES (VIBRACIÓN Y COMPARTIR) ------------------

def vibrar_corto():
    """Vibración háptica corta (50ms) para feedback"""
    if PLYER_AVAILABLE:
        try:
            vibrator.vibrate(0.05) # 0.05 segundos = 50ms (Tenue y corta)
        except:
            pass

def compartir_en_android(ruta_imagen):
    try:
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')
        StrictMode = autoclass('android.os.StrictMode')

        builder = StrictMode.VmPolicy.Builder()
        StrictMode.setVmPolicy(builder.build())

        share_intent = Intent()
        share_intent.setAction(Intent.ACTION_SEND)
        share_intent.setType("image/png")
        
        image_file = File(ruta_imagen)
        uri = Uri.fromFile(image_file)
        share_intent.putExtra(Intent.EXTRA_STREAM, uri)
        
        current_activity = cast('android.app.Activity', PythonActivity.mActivity)
        current_activity.startActivity(Intent.createChooser(share_intent, "Compartir Marcador"))
    except Exception as e:
        print(f"Error al compartir en Android: {e}")

# ------------------ WIDGET TARJETA ------------------

class TarjetaShare(BoxLayout):
    def __init__(self, datos, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 50
        self.spacing = 15
        self.size_hint = (None, None)
        self.size = (1080, 1200) 
        self.pos = (-5000, -5000) 
        
        with self.canvas.before:
            Color(*COLOR_FONDO_CARD)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"

        self.add_widget(Label(text="RESULTADO FINAL", font_name=font_t, font_size=60, color=COLOR_AMARILLO, size_hint_y=0.1))
        self.add_widget(Label(text=f"{datos.get('fecha')} | {datos.get('modo')}", font_size=30, color=[0.7,0.7,0.7,1], size_hint_y=0.05))

        self.add_widget(Label(text="🏆 GANADOR 🏆", font_size=40, color=COLOR_VERDE, size_hint_y=0.1, bold=True))
        self.add_widget(Label(text=datos.get('ganador', 'Unknown'), font_name=font_t, font_size=80, color=[1,1,1,1], size_hint_y=0.15))

        self.add_widget(Label(text=datos.get('score_final', '0-0'), font_name=font_t, font_size=140, color=COLOR_AMARILLO, size_hint_y=0.25))

        if datos.get('modo') == 'Sets':
            detalles_sets = datos.get('resumen_sets', '')
            self.add_widget(Label(text=detalles_sets, font_size=35, color=[0.9, 0.9, 0.9, 1], size_hint_y=0.1, bold=True))

        sh_rival = 0.1 if datos.get('modo') != 'Sets' else 0.08
        self.add_widget(Label(text=f"Rival: {datos.get('perdedor')}", font_size=40, color=[0.8,0.8,0.8,1], size_hint_y=sh_rival))
        self.add_widget(Label(text="Frontenis Score App", font_size=24, color=[0.4,0.4,0.4,1], size_hint_y=0.05))
        self.update_rect()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# ------------------ MODELO ------------------

class Equipo:
    def __init__(self, nombres):
        self.nombres = nombres
        self.puntos = 0
        self.sets_ganados = 0
        self.stats_largas = 0
        self.stats_cortas = 0
        self.stats_vueltas = 0
        self.largas_consecutivas = 0

# ------------------ UTILIDADES ARCHIVO ------------------

def guardar_partido(datos):
    historial = []
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding='utf-8') as f:
                content = f.read()
                if content:
                    historial = json.loads(content)
        except:
            historial = []
    historial.append(datos)
    try:
        with open(ARCHIVO, "w", encoding='utf-8') as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando: {e}")

def animar_label_puntaje(widget_label):
    anim_crecer = Animation(font_size=FONT_SIZE_SCORE * 1.15, color=COLOR_AMARILLO, duration=0.1, t='out_quad')
    anim_volver = Animation(font_size=FONT_SIZE_SCORE, color=widget_label.color_original, duration=0.25, t='out_back')
    animacion_completa = anim_crecer + anim_volver
    Animation.cancel_all(widget_label)
    animacion_completa.start(widget_label)

# ------------------ PANTALLA INICIO ------------------

class PantallaInicio(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=30, spacing=15)

        font_t = FONT_SPORT if TIENE_FUENTE else None
        layout.add_widget(Label(text="FRONTENIS SCORE", font_name=font_t if font_t else "Roboto", font_size=FONT_SIZE_TITLE, color=COLOR_AMARILLO, size_hint_y=0.25))

        config_box = GridLayout(cols=2, spacing=10, size_hint_y=None, height=180)
        config_box.add_widget(Label(text="Modalidad:", bold=True))
        self.modo = Spinner(text="Puntos corridos", values=["Puntos corridos", "Sets"])
        self.modo.bind(text=self.cambio_modo)
        config_box.add_widget(self.modo)

        config_box.add_widget(Label(text="Puntos a ganar:", bold=True))
        self.input_puntos = TextInput(text="20", multiline=False, input_filter="int")
        config_box.add_widget(self.input_puntos)

        config_box.add_widget(Label(text="Tipo de juego:", bold=True))
        self.tipo = Spinner(text="Singles", values=["Singles", "Dobles"])
        self.tipo.bind(text=self.actualizar_inputs_nombres)
        config_box.add_widget(self.tipo)
        layout.add_widget(config_box)

        self.inputs_box = BoxLayout(orientation="vertical", spacing=8, size_hint_y=0.3)
        layout.add_widget(self.inputs_box)
        
        self.azul1 = TextInput(hint_text="Azul 1", multiline=False, background_color=[0.9,0.9,1,1])
        self.azul2 = TextInput(hint_text="Azul 2", multiline=False, background_color=[0.9,0.9,1,1])
        self.rojo1 = TextInput(hint_text="Rojo 1", multiline=False, background_color=[1,0.9,0.9,1])
        self.rojo2 = TextInput(hint_text="Rojo 2", multiline=False, background_color=[1,0.9,0.9,1])
        self.actualizar_inputs_nombres(None, "Singles")

        botones = BoxLayout(spacing=15, size_hint_y=0.2)
        btn_historial = Button(text="HISTORIAL", background_color=[0.3, 0.3, 0.3, 1])
        if TIENE_FUENTE: btn_historial.font_name = FONT_SPORT
        btn_historial.bind(on_press=self.ir_a_historial)
        
        btn_iniciar = Button(text="INICIAR PARTIDO", background_color=[0, 0.6, 0.2, 1], font_size=20)
        if TIENE_FUENTE: btn_iniciar.font_name = FONT_SPORT
        btn_iniciar.bind(on_press=self.iniciar)

        botones.add_widget(btn_historial)
        botones.add_widget(btn_iniciar)
        layout.add_widget(botones)
        self.add_widget(layout)

    def ir_a_historial(self, _):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "historial"

    def cambio_modo(self, spinner, text):
        if text == "Sets":
            self.input_puntos.text = "Reglas: 15/15/10"
            self.input_puntos.disabled = True
        else:
            self.input_puntos.text = "20"
            self.input_puntos.disabled = False

    def actualizar_inputs_nombres(self, _, tipo):
        self.inputs_box.clear_widgets()
        if tipo == "Singles":
            self.inputs_box.add_widget(self.azul1)
            self.inputs_box.add_widget(self.rojo1)
        else:
            self.inputs_box.add_widget(self.azul1)
            self.inputs_box.add_widget(self.azul2)
            self.inputs_box.add_widget(self.rojo1)
            self.inputs_box.add_widget(self.rojo2)

    def iniciar(self, _):
        app = App.get_running_app()
        if self.tipo.text == "Singles":
            n_azul = [self.azul1.text or "Azul"]
            n_rojo = [self.rojo1.text or "Rojo"]
        else:
            n_azul = [self.azul1.text or "Azul 1", self.azul2.text or "Azul 2"]
            n_rojo = [self.rojo1.text or "Rojo 1", self.rojo2.text or "Rojo 2"]

        limite_puntos = 0
        if self.modo.text == "Puntos corridos":
            try:
                limite_puntos = int(self.input_puntos.text)
            except:
                limite_puntos = 15

        app.config_partido = {
            "modo": self.modo.text,
            "limite_inicial": limite_puntos,
            "azul": n_azul,
            "rojo": n_rojo
        }
        self.manager.transition = SlideTransition(direction="up")
        self.manager.current = "partido"

# ------------------ PANTALLA PARTIDO ------------------

class PantallaPartido(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.inicio_tiempo = datetime.now()
        self.fin = False
        self.evento_reloj = Clock.schedule_interval(self.actualizar_tiempo, 1)

        cfg = App.get_running_app().config_partido
        self.modo_juego = cfg["modo"]
        self.azul = Equipo(cfg["azul"])
        self.rojo = Equipo(cfg["rojo"])
        self.equipo_sacando = None 
        self.set_actual = 1
        
        self.historico_sets = [] 
        
        # PILA PARA DESHACER (UNDO)
        self.pila_deshacer = []

        if self.modo_juego == "Sets":
            self.limite_actual = 15
        else:
            self.limite_actual = cfg["limite_inicial"]

        self.construir_ui()
        self.actualizar_ui_saque()

    def construir_ui(self):
        layout = BoxLayout(orientation="vertical")
        
        # Header (Fila superior)
        header = BoxLayout(size_hint_y=0.12, padding=5, spacing=10)
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        
        # Botón Deshacer (Izquierda)
        btn_undo = Button(text="↩", size_hint_x=0.15, background_color=[0.5, 0.5, 0.5, 1], font_size=30)
        btn_undo.bind(on_press=self.deshacer_accion)
        
        self.lbl_info_partido = Label(text=self.get_info_titulo(), font_name=font_t, font_size=18, color=COLOR_AMARILLO, size_hint_x=0.45)
        self.lbl_tiempo = Label(text="00:00", font_name=font_t, font_size=24, size_hint_x=0.2)
        
        btn_fin = Button(text="Fin", size_hint_x=0.2, background_color=[0.7, 0, 0, 1])
        if TIENE_FUENTE: btn_fin.font_name = FONT_SPORT
        btn_fin.bind(on_press=self.confirmar_final_manual)
        
        header.add_widget(btn_undo)
        header.add_widget(self.lbl_info_partido)
        header.add_widget(self.lbl_tiempo)
        header.add_widget(btn_fin)
        layout.add_widget(header)

        if self.modo_juego == "Sets":
            sets_box = BoxLayout(size_hint_y=0.08, padding=(10,0))
            l_a = Label(text="SETS AZUL: 0", color=COLOR_AZUL)
            l_r = Label(text="SETS ROJO: 0", color=COLOR_ROJO)
            if TIENE_FUENTE:
                l_a.font_name = FONT_SPORT
                l_r.font_name = FONT_SPORT
            self.lbl_sets_azul = l_a
            self.lbl_sets_rojo = l_r
            sets_box.add_widget(self.lbl_sets_azul)
            sets_box.add_widget(self.lbl_sets_rojo)
            layout.add_widget(sets_box)

        zona_juego = BoxLayout(orientation="horizontal")
        col_azul = self.crear_columna_equipo(self.azul, COLOR_AZUL, self.rojo)
        col_rojo = self.crear_columna_equipo(self.rojo, COLOR_ROJO, self.azul)

        self.lbl_puntos_azul = col_azul.ids['score']
        self.lbl_aviso_azul = col_azul.ids['aviso']
        self.lbl_saque_azul = col_azul.ids['saque']
        self.btn_extras_azul = col_azul.ids['btn_extras']
        
        self.lbl_puntos_rojo = col_rojo.ids['score']
        self.lbl_aviso_rojo = col_rojo.ids['aviso']
        self.lbl_saque_rojo = col_rojo.ids['saque']
        self.btn_extras_rojo = col_rojo.ids['btn_extras']

        zona_juego.add_widget(col_azul)
        zona_juego.add_widget(col_rojo)
        layout.add_widget(zona_juego)
        self.add_widget(layout)

    def crear_columna_equipo(self, equipo, color, rival):
        col = BoxLayout(orientation="vertical", padding=10, spacing=5)
        col.ids = {}
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        
        lbl_saque = Label(text="🎾 SAQUE", color=COLOR_VERDE, font_name=font_t, font_size=16, size_hint_y=0.08, opacity=0)
        col.ids['saque'] = lbl_saque
        col.add_widget(lbl_saque)

        col.add_widget(Label(text="\n".join(equipo.nombres), font_name=font_t, font_size=FONT_SIZE_NAMES, color=color, size_hint_y=0.15))
        
        lbl_score = Label(text="0", font_name=font_t, font_size=FONT_SIZE_SCORE, color=color)
        lbl_score.color_original = color 
        col.ids['score'] = lbl_score
        col.add_widget(lbl_score)

        lbl_aviso = Label(text="", font_size=16, color=COLOR_AMARILLO, size_hint_y=0.08, bold=True)
        col.ids['aviso'] = lbl_aviso
        col.add_widget(lbl_aviso)

        btn_punto = Button(text="+ PUNTO", background_color=color, font_size=30, size_hint_y=0.25)
        if TIENE_FUENTE: btn_punto.font_name = FONT_SPORT
        btn_punto.bind(on_press=lambda x: self.sumar_punto(equipo, rival))
        col.add_widget(btn_punto)

        btn_extra = Button(text="Extras (Saque)", size_hint_y=0.12, background_color=[0.4,0.4,0.4,1])
        btn_extra.bind(on_press=lambda x: self.abrir_extras(equipo, rival))
        col.ids['btn_extras'] = btn_extra
        col.add_widget(btn_extra)
        return col

    def actualizar_ui_saque(self):
        if self.equipo_sacando is None:
            self.lbl_saque_azul.opacity = 0
            self.lbl_saque_rojo.opacity = 0
            self.btn_extras_azul.disabled = False
            self.btn_extras_rojo.disabled = False
        elif self.equipo_sacando == self.azul:
            self.lbl_saque_azul.opacity = 1
            self.lbl_saque_rojo.opacity = 0
            self.btn_extras_azul.disabled = False
            self.btn_extras_rojo.disabled = True
        elif self.equipo_sacando == self.rojo:
            self.lbl_saque_azul.opacity = 0
            self.lbl_saque_rojo.opacity = 1
            self.btn_extras_azul.disabled = True
            self.btn_extras_rojo.disabled = False

    def get_info_titulo(self):
        if self.modo_juego == "Sets":
            return f"SET {self.set_actual} (A {self.limite_actual})"
        else:
            return f"OBJETIVO: {self.limite_actual} PUNTOS"

    def on_leave(self):
        Clock.unschedule(self.actualizar_tiempo)

    # ---------- LOGICA UNDO (DESHACER) ----------

    def guardar_estado(self):
        """Guarda una copia de los valores importantes en la pila"""
        sacando_str = 'ninguno'
        if self.equipo_sacando == self.azul: sacando_str = 'azul'
        elif self.equipo_sacando == self.rojo: sacando_str = 'rojo'

        estado = {
            'azul': {
                'puntos': self.azul.puntos, 'sets': self.azul.sets_ganados,
                'largas': self.azul.stats_largas, 'cortas': self.azul.stats_cortas,
                'vueltas': self.azul.stats_vueltas, 'consecutivas': self.azul.largas_consecutivas
            },
            'rojo': {
                'puntos': self.rojo.puntos, 'sets': self.rojo.sets_ganados,
                'largas': self.rojo.stats_largas, 'cortas': self.rojo.stats_cortas,
                'vueltas': self.rojo.stats_vueltas, 'consecutivas': self.rojo.largas_consecutivas
            },
            'set_actual': self.set_actual,
            'limite_actual': self.limite_actual,
            'sacando': sacando_str,
            'historico_sets': list(self.historico_sets) # Copia de la lista
        }
        self.pila_deshacer.append(estado)
        # Limitar historial a 20 pasos para no saturar memoria (opcional)
        if len(self.pila_deshacer) > 20:
            self.pila_deshacer.pop(0)

    def deshacer_accion(self, _):
        if not self.pila_deshacer:
            return
        
        vibrar_corto()
        estado = self.pila_deshacer.pop()
        
        # Restaurar Azul
        self.azul.puntos = estado['azul']['puntos']
        self.azul.sets_ganados = estado['azul']['sets']
        self.azul.stats_largas = estado['azul']['largas']
        self.azul.stats_cortas = estado['azul']['cortas']
        self.azul.stats_vueltas = estado['azul']['vueltas']
        self.azul.largas_consecutivas = estado['azul']['consecutivas']
        
        # Restaurar Rojo
        self.rojo.puntos = estado['rojo']['puntos']
        self.rojo.sets_ganados = estado['rojo']['sets']
        self.rojo.stats_largas = estado['rojo']['largas']
        self.rojo.stats_cortas = estado['rojo']['cortas']
        self.rojo.stats_vueltas = estado['rojo']['vueltas']
        self.rojo.largas_consecutivas = estado['rojo']['consecutivas']

        # Restaurar Juego
        self.set_actual = estado['set_actual']
        self.limite_actual = estado['limite_actual']
        self.historico_sets = estado['historico_sets']
        
        if estado['sacando'] == 'azul': self.equipo_sacando = self.azul
        elif estado['sacando'] == 'rojo': self.equipo_sacando = self.rojo
        else: self.equipo_sacando = None
        
        self.actualizar_ui_textos()
        self.actualizar_ui_saque()

    # ---------- LÓGICA JUEGO ----------

    def actualizar_tiempo(self, dt):
        if self.fin: return
        delta = datetime.now() - self.inicio_tiempo
        self.lbl_tiempo.text = f"{delta.seconds//60:02d}:{delta.seconds%60:02d}"

    def resetear_largas_global(self):
        self.azul.largas_consecutivas = 0
        self.rojo.largas_consecutivas = 0

    def sumar_punto(self, equipo_anotador, rival, es_castigo=False):
        if self.fin: return
        self.guardar_estado() # <--- GUARDAR ANTES DE CAMBIAR
        vibrar_corto()

        self.equipo_sacando = equipo_anotador
        
        if not es_castigo: self.resetear_largas_global()
        
        equipo_anotador.puntos += 1
        label_a_animar = self.lbl_puntos_azul if equipo_anotador == self.azul else self.lbl_puntos_rojo
        animar_label_puntaje(label_a_animar)

        self.actualizar_ui_textos()
        self.actualizar_ui_saque()
        
        if equipo_anotador.puntos >= self.limite_actual:
            if self.modo_juego == "Puntos corridos":
                self.finalizar_partido(equipo_anotador)
            else:
                self.finalizar_set(equipo_anotador)

    def finalizar_set(self, ganador_set):
        ganador_set.sets_ganados += 1
        self.historico_sets.append((self.azul.puntos, self.rojo.puntos))
        
        if ganador_set.sets_ganados == 2:
            self.finalizar_partido(ganador_set)
        else:
            self.set_actual += 1
            self.azul.puntos = 0
            self.rojo.puntos = 0
            self.equipo_sacando = ganador_set 
            self.limite_actual = 10 if self.set_actual == 3 else 15
            self.mostrar_aviso_popup(f"¡{ganador_set.nombres[0]} gana el Set!\nComienza Set {self.set_actual}.")
            self.actualizar_ui_textos()
            self.actualizar_ui_saque()

    def abrir_extras(self, equipo, rival):
        if self.fin: return
        if self.equipo_sacando is None:
            self.guardar_estado()
            self.equipo_sacando = equipo
            self.actualizar_ui_saque()
        
        # OJO: Guardar estado aquí es complejo porque depende de qué botón presione en el popup.
        # Mejor guardamos DENTRO de las funciones lambda.

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        popup = Popup(title=f"Extras - {'/'.join(equipo.nombres)}", content=layout, size_hint=(0.8, 0.5))
        if TIENE_FUENTE: popup.title_font = FONT_SPORT

        def call_larga(x):
            self.guardar_estado() # <--- GUARDAR
            vibrar_corto()
            equipo.stats_largas += 1
            equipo.largas_consecutivas += 1
            if equipo.largas_consecutivas >= 2:
                self.resetear_largas_global()
                # Nota: sumar_punto ya tiene guardar_estado, pero como es castigo interno
                # podemos evitar doble guardado o dejarlo. Por simplicidad, dejamos.
                self.sumar_punto(rival, equipo, es_castigo=True) 
                self.mostrar_aviso_popup(f"¡Doble Larga!\nPunto para {rival.nombres[0]}")
            self.actualizar_ui_textos()
            popup.dismiss()

        def call_corta(x):
            self.guardar_estado() # <--- GUARDAR
            vibrar_corto()
            equipo.stats_cortas += 1
            self.resetear_largas_global()
            self.sumar_punto(rival, equipo, es_castigo=True)
            popup.dismiss()

        def call_vuelta(x):
            # Vuelta no cambia marcador pero sí estadisticas
            self.guardar_estado()
            vibrar_corto()
            equipo.stats_vueltas += 1
            popup.dismiss()

        b1 = Button(text="Larga (Falta)", background_color=[1, 0.8, 0, 1], color=[0,0,0,1], on_press=call_larga)
        b2 = Button(text="Corta / Chapa (Punto Rival)", background_color=[1, 0.4, 0, 1], on_press=call_corta)
        b3 = Button(text="Vuelta", on_press=call_vuelta)
        
        if TIENE_FUENTE:
            b1.font_name = FONT_SPORT
            b2.font_name = FONT_SPORT
            b3.font_name = FONT_SPORT
        layout.add_widget(b1)
        layout.add_widget(b2)
        layout.add_widget(b3)
        popup.open()

    def actualizar_ui_textos(self):
        self.lbl_puntos_azul.text = str(self.azul.puntos)
        self.lbl_puntos_rojo.text = str(self.rojo.puntos)
        self.lbl_info_partido.text = self.get_info_titulo()
        self.lbl_aviso_azul.text = "⚠ 1 Larga" if self.azul.largas_consecutivas == 1 else ""
        self.lbl_aviso_rojo.text = "⚠ 1 Larga" if self.rojo.largas_consecutivas == 1 else ""
        if self.modo_juego == "Sets":
            self.lbl_sets_azul.text = f"SETS AZUL: {self.azul.sets_ganados}"
            self.lbl_sets_rojo.text = f"SETS ROJO: {self.rojo.sets_ganados}"

    def mostrar_aviso_popup(self, texto):
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        p = Popup(title="Aviso", content=Label(text=texto, halign="center", font_name=font_t), size_hint=(0.6, 0.3))
        if TIENE_FUENTE: p.title_font = FONT_SPORT
        p.open()

    def confirmar_final_manual(self, _):
        content = BoxLayout(orientation="vertical", spacing=10)
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        popup = Popup(title="¿Quién ganó?", content=content, size_hint=(0.8, 0.5))
        if TIENE_FUENTE: popup.title_font = FONT_SPORT

        btn_a = Button(text=f"Gana {'/'.join(self.azul.nombres)}", background_color=COLOR_AZUL)
        btn_a.bind(on_press=lambda x: (popup.dismiss(), self.finalizar_partido(self.azul)))
        btn_r = Button(text=f"Gana {'/'.join(self.rojo.nombres)}", background_color=COLOR_ROJO)
        btn_r.bind(on_press=lambda x: (popup.dismiss(), self.finalizar_partido(self.rojo)))
        if TIENE_FUENTE:
            btn_a.font_name = FONT_SPORT
            btn_r.font_name = FONT_SPORT
        content.add_widget(btn_a)
        content.add_widget(btn_r)
        popup.open()

    def finalizar_partido(self, ganador):
        self.fin = True
        Clock.unschedule(self.actualizar_tiempo)
        
        lista_sets_ordenada = []
        for i, (pts_azul, pts_rojo) in enumerate(self.historico_sets, 1):
            if ganador == self.azul:
                lista_sets_ordenada.append(f"Set {i}: {pts_azul}-{pts_rojo}")
            else:
                lista_sets_ordenada.append(f"Set {i}: {pts_rojo}-{pts_azul}")
                
        resumen_sets = " | ".join(lista_sets_ordenada) if lista_sets_ordenada else "Único"
        
        if ganador == self.azul:
            perdedor = self.rojo
            if self.modo_juego == "Sets":
                score_visual = f"Sets: {self.azul.sets_ganados} - {self.rojo.sets_ganados}"
            else:
                score_visual = f"Puntos: {self.azul.puntos} - {self.rojo.puntos}"
        else:
            perdedor = self.azul
            if self.modo_juego == "Sets":
                score_visual = f"Sets: {self.rojo.sets_ganados} - {self.azul.sets_ganados}"
            else:
                score_visual = f"Puntos: {self.rojo.puntos} - {self.azul.puntos}"
        
        datos = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modo": self.modo_juego,
            "ganador": " / ".join(ganador.nombres),
            "perdedor": " / ".join(perdedor.nombres),
            "score_final": score_visual,
            "resumen_sets": resumen_sets,
            "duracion": self.lbl_tiempo.text,
            "stats": {
                "azul": {"nombre": " / ".join(self.azul.nombres), "largas": self.azul.stats_largas, "cortas": self.azul.stats_cortas, "vueltas": self.azul.stats_vueltas},
                "rojo": {"nombre": " / ".join(self.rojo.nombres), "largas": self.rojo.stats_largas, "cortas": self.rojo.stats_cortas, "vueltas": self.rojo.stats_vueltas}
            }
        }
        guardar_partido(datos)
        
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        content = BoxLayout(orientation="vertical", padding=20, spacing=20)
        content.add_widget(Label(text="¡VICTORIA!", font_name=font_t, font_size=30, color=COLOR_AMARILLO, halign="center"))
        content.add_widget(Label(text=f"{' / '.join(ganador.nombres)}", font_name=font_t, font_size=24, halign="center"))
        
        btn_salir = Button(text="Volver al Menú", size_hint_y=0.4, background_color=[0.2,0.2,0.2,1])
        if TIENE_FUENTE: btn_salir.font_name = FONT_SPORT
        popup = Popup(title="Fin del Partido", content=content, size_hint=(0.8, 0.6), auto_dismiss=False)
        if TIENE_FUENTE: popup.title_font = FONT_SPORT
        btn_salir.bind(on_press=lambda x: self.volver_menu(popup))
        content.add_widget(btn_salir)
        popup.open()

    def volver_menu(self, popup_ref):
        popup_ref.dismiss()
        self.manager.transition = SlideTransition(direction="down")
        self.manager.current = "inicio"

# ------------------ HISTORIAL ------------------

class PantallaHistorial(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        font_t = FONT_SPORT if TIENE_FUENTE else "Roboto"
        layout.add_widget(Label(text="HISTORIAL", font_name=font_t, font_size=30, size_hint_y=0.1, color=COLOR_AMARILLO))

        scroll = ScrollView(size_hint_y=0.8)
        lista = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=(0, 10))
        lista.bind(minimum_height=lista.setter("height"))

        tag_font_open = f"[font={FONT_SPORT}]" if TIENE_FUENTE else ""
        tag_font_close = "[/font]" if TIENE_FUENTE else ""

        if not os.path.exists(ARCHIVO):
            lista.add_widget(Label(text="No hay partidos.", size_hint_y=None, height=40))
        else:
            try:
                with open(ARCHIVO, "r", encoding='utf-8') as f:
                    content = f.read()
                    data = json.loads(content) if content else []
                    
                    for p in reversed(data):
                        stats = p.get("stats", {})
                        def_stats = {"nombre": "Desconocido", "largas": 0, "cortas": 0, "vueltas": 0}
                        s_azul = stats.get("azul", def_stats.copy())
                        if s_azul["nombre"] == "Desconocido" and "score_azul" in p: s_azul["nombre"] = "Azul"
                        s_rojo = stats.get("rojo", def_stats.copy())
                        if s_rojo["nombre"] == "Desconocido" and "score_rojo" in p: s_rojo["nombre"] = "Rojo"

                        ganador_nombre = p.get('ganador', '?')
                        perdedor_nombre = p.get('perdedor', 'Rival')
                        score_final = p.get('score_final', '---')
                        fecha = p.get('fecha', '-')
                        duracion = p.get('duracion', '--')
                        sets_info = p.get('resumen_sets', '')
                        detalle_sets = f"\n[size=12]{sets_info}[/size]" if p.get('modo') == 'Sets' else ""

                        if ganador_nombre == s_azul.get('nombre'):
                            st_1, col_1 = s_azul, "6699ff"
                            st_2, col_2 = s_rojo, "ff6666"
                        else:
                            st_1, col_1 = s_rojo, "ff6666"
                            st_2, col_2 = s_azul, "6699ff"
                      
                        card_box = BoxLayout(orientation="vertical", size_hint_y=None, height=220)
                        
                        info_lbl = Label(
                            text=(
                                f"{tag_font_open}[size=18]{fecha}[/size]{tag_font_close} | [size=14]{duracion}[/size]\n"
                                f"[color=ffff00]🏆 {ganador_nombre}[/color] vs [color=aaaaaa]{perdedor_nombre}[/color]\n"
                                f"{tag_font_open}[size=22]{score_final}[/size]{tag_font_close} {detalle_sets}\n"
                                f"[size=14]----------------------------------------[/size]\n"
                                f"[color={col_1}][b]{st_1.get('nombre', 'Eq.1')}[/b][/color]: L:{st_1.get('largas',0)} C:{st_1.get('cortas',0)} V:{st_1.get('vueltas',0)}\n"
                                f"[color={col_2}][b]{st_2.get('nombre', 'Eq.2')}[/b][/color]: L:{st_2.get('largas',0)} C:{st_2.get('cortas',0)} V:{st_2.get('vueltas',0)}"
                            ), 
                            markup=True, 
                            halign="left", 
                            valign="middle"
                        )
                        info_lbl.bind(size=info_lbl.setter('text_size'))
                        card_box.add_widget(info_lbl)

                        btn_share = Button(text="COMPARTIR TARJETA", size_hint_y=0.25, background_color=[0, 0.5, 0.5, 1])
                        btn_share.bind(on_press=lambda x, datos=p: self.generar_y_compartir(datos))
                        card_box.add_widget(btn_share)

                        lista.add_widget(card_box)

            except Exception as e:
                print(f"Error cargando historial: {e}")
                lista.add_widget(Label(text="Error leyendo historial.", size_hint_y=None, height=40))

        scroll.add_widget(lista)
        layout.add_widget(scroll)

        btn_volver = Button(text="VOLVER", size_hint_y=0.1, background_color=[0.3,0.3,0.3,1])
        if TIENE_FUENTE: btn_volver.font_name = FONT_SPORT
        btn_volver.bind(on_press=self.volver_inicio)
        layout.add_widget(btn_volver)
        self.add_widget(layout)
    
    def volver_inicio(self, _):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "inicio"

    def generar_y_compartir(self, datos):
        tarjeta = TarjetaShare(datos)
        self.add_widget(tarjeta)
        Clock.schedule_once(lambda dt: self._exportar_tarjeta(tarjeta), 0.2)

    def _exportar_tarjeta(self, tarjeta):
        tarjeta.update_rect()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_img = f"match_{timestamp}.png"
        ruta_completa = os.path.abspath(nombre_img)
        
        try:
            tarjeta.export_to_png(nombre_img)
            print(f"Imagen guardada en: {ruta_completa}")
        except Exception as e:
            print(f"Error exportando imagen: {e}")
        
        self.remove_widget(tarjeta)
        
        if platform == 'android':
            compartir_en_android(ruta_completa)
        else:
            popup = Popup(title="Tarjeta Guardada", 
                          content=Label(text=f"¡Imagen lista!\nGuardada en:\n{nombre_img}", halign="center"), 
                          size_hint=(0.8, 0.4))
            popup.open()

# ------------------ APP ------------------

class FrontenisApp(App):
    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(PantallaInicio(name="inicio"))
        sm.add_widget(PantallaPartido(name="partido"))
        sm.add_widget(PantallaHistorial(name="historial"))
        return sm

if __name__ == "__main__":
    FrontenisApp().run()
