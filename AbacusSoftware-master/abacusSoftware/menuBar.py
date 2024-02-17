import abacusSoftware.__GUI_images__ as __GUI_images__

import pyAbacus as pa
from abacusSoftware.constants import __version__
from PyQt5 import QtCore, QtGui, QtWidgets
from abacusSoftware.__about__ import Ui_Dialog as Ui_Dialog_about

class AboutWindow(QtWidgets.QDialog, Ui_Dialog_about):
    def __init__(self, parent = None):
        super(AboutWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.parent = parent

        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(220, 220, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)

        tausand = '<a href="https://www.tausand.com/"> https://www.tausand.com </a>'
        pages =  '<a href="https://github.com/Tausand-dev/AbacusSoftware"> https://github.com/Tausand-dev/AbacusSoftware </a>'
        message = """Abacus Software is a suite of tools build to ensure your experience with Tausand's coincidence counters becomes simplified. \n\nSoftware Version: %s\nPyAbacus Version: %s\n\nA positive experience with programming: \n
        When I was a junior in high school our physics teacher brought a systems engineer to the class so that he could teach us how to use Arduino. 
        At first, we were all reticent to the new topic and most people (including me) lost their interest after some time. Afterward, we were 
        assigned a project that required using Arduino to create something. We were all scared —no one had really understood what Arduino was or 
        how to use it— so we had to google it and decided we were going to create something simple: a motion sensor. Everything was new to us, 
        all those cables, having to program (what was programming, anyway?), but, after a lot of googling and frustration, our motion sensor 
        detected movement and a LED light bulb lit up every time someone passed by. I was elated. This was the first time I had seen how software 
        and hardware, those until that moment abstract words, interacted to create something tangible. The coding was simple and the hardware was 
        even simpler, but that day I realized that I could understand the principles that underly everyday electronic devices. The automatic 
        streetlights that I saw that night on my ride home weren’t abstract mysteries to me anymore, they were just Arduinos and light sensors 
        connected to a battery. After that day cities seemed a more familiar place to me.\n\n"""%(__version__, pa.__version__)
        self.message_label.setText(message)
        self.visit_label = QtWidgets.QLabel()
        self.github_label = QtWidgets.QLabel()
        self.pages_label = QtWidgets.QLabel()

        self.visit_label.setText("Visit us at: %s "%tausand)
        self.github_label.setText("More information on Abacus Software implementation can be found at: %s"%pages)
        self.verticalLayout.addWidget(self.visit_label)
        self.verticalLayout.addWidget(self.github_label)

        self.visit_label.linkActivated.connect(self.open_link)
        self.github_label.linkActivated.connect(self.open_link)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def open_link(self, link):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
