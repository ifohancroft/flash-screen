"""A Gtk widget implementing a shutter flash & sound."""

import argparse
import gi
gi.require_version('GSound', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GSound, GLib


class Flash (Gtk.Window):
    """Make the screen flash."""

    def __init__(self, duration=50, fade=.95, fps=120, threshold=.95, sound=True):
        """
        Args:
            duration (int): Hold-time for the flash, in ms. After this interval
                the flash begins to fade-out.
            fade (float): A factor by which the opacity is multiplied at each
                fade step.
            threshold (float): The opacity level at which the flash is
                considered finished.
            sound (bool): Toogles whether the shutter-sound is played.
        """

        css = """
            .flash { background-color: rgba(255,255,255,1); }
        """

        super().__init__(type=Gtk.WindowType.POPUP)

        display = Gdk.Display.get_default()
        # num_monitors = display.get_n_monitors()
        # print(num_monitors)
        screen = display.get_default_screen()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        width = geometry.width
        height = geometry.height
        self.resize(width, height)
        self.move(0, 0)

        # Lets color it white
        provider = Gtk.CssProvider()
        provider.load_from_data(bytes(css.encode()))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.get_style_context().add_class('flash')

        # Make the window not look like a regular window.
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.fullscreen()

        # Don’t take focus.
        self.set_accept_focus(False)
        self.set_focus_on_map(False)

        # Don’t cast a shadow.
        visual = screen.get_rgba_visual()
        if visual is None:
            visual = screen.get_system_visual()
        self.set_visual(visual)

        # Ready GSound.
        self.sound = GSound.Context()
        self.sound.init()

        # Set-up the flash.
        self._duration = duration
        self._fade = fade
        self._fps = fps
        self._threshold = threshold
        self._opacity = 1
        self._sound = sound

        # Good to go.
        self.show_all()
        GLib.timeout_add(self._duration, self._begin_fade)
        if self._sound:
            self._fire_shutter_sound()

    def _fire_shutter_sound(self):

        self.sound.play_full({
            GSound.ATTR_EVENT_ID: 'screen-capture'
        })

    def on_draw(self, _wid, ctx):

        ctx.set_source_rgba(1, 1, 1, self._opacity)
        ctx.paint()
        ctx.fill()

    def _begin_fade(self):

        GLib.timeout_add(1000 / self._fps, self._do_fade)

    def _do_fade(self):

        self._opacity *= self._fade
        self.queue_draw()

        if self._opacity <= self._threshold:
            self.hide()
            # Give the shutter sound time to finish.
            GLib.timeout_add(1000, Gtk.main_quit)
            return False
        else:
            return True

parser = argparse.ArgumentParser(
    description="Make the screen flash."
)

parser.add_argument("--muted", dest='muted', default=False, action='store_true', help="Mute the shutter sound.")

def console_entry():

    args = parser.parse_args()
    Flash(sound=not args.muted)
    Gtk.main()

console_entry()