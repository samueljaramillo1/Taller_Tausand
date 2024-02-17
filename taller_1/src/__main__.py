import sys
from gui.visor import Aplicacion_Gui
from PyQt5.QtWidgets import QApplication


class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        self.gui = Aplicacion_Gui()


if __name__ == '__main__':
    app = App(sys.argv)
    sys.exit(app.exec_())