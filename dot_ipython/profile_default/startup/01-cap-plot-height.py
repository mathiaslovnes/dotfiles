# Scales down plots that matplotlib-backend-kitty draws in the terminal so they fit in their pane
import fcntl
import os
import struct
import sys
import termios

if os.environ.get("MPLBACKEND") == "module://matplotlib-backend-kitty":
    import matplotlib as mpl
    from matplotlib.figure import Figure

    MAX_PANE_FRACTION = 0.9  # jukit's plot panes are half the screen tall, so this is 45% of the screen
    original_savefig = Figure.savefig

    def savefig(self, *args, **kwargs):
        drawn_by_backend = sys._getframe(1).f_globals.get("__name__") == "matplotlib-backend-kitty"
        # The saves with an explicit dpi are the high-resolution copies for the output history
        if drawn_by_backend and "dpi" not in kwargs and sys.__stdout__.isatty():
            winsize = fcntl.ioctl(sys.__stdout__.fileno(), termios.TIOCGWINSZ, bytes(8))
            max_height = struct.unpack("4H", winsize)[3] * MAX_PANE_FRACTION
            dpi = self.dpi if mpl.rcParams["savefig.dpi"] == "figure" else mpl.rcParams["savefig.dpi"]
            inches = self.get_figheight()
            if mpl.rcParams["savefig.bbox"] == "tight":
                self.draw_without_rendering()  # runs the figure's layout engine, which can change the height
                inches =self.get_tightbbox().height + 2 * mpl.rcParams["savefig.pad_inches"]
            if 0 < max_height < inches * dpi:
                kwargs["dpi"] = max_height / inches
        return original_savefig(self, *args, **kwargs)

    Figure.savefig = savefig
