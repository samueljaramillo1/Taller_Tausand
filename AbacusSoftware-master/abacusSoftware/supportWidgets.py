import os
import numpy as np
from itertools import combinations

try:
    from PyQt5 import QtWidgets, QtGui, QtCore
    from PyQt5.QtGui import QBrush, QColor, QPixmap, QPen, QIcon
    from PyQt5.QtWidgets import QSizePolicy, QTabWidget, QWidget, QCheckBox, \
                        QVBoxLayout, QFrame, QGroupBox, QLabel, QSizePolicy, \
                        QComboBox, QSpinBox, QFormLayout, QDialog, QDialogButtonBox, \
                        QColorDialog, QHBoxLayout, QGridLayout, QPushButton, QToolButton, \
                        QTableWidgetItem, QScrollArea
except ModuleNotFoundError:
    from PyQt4 import QtWidgets, QtGui, QtCore
    from PyQt4.QtGui import QTableWidgetItem
    from PyQt4.QtWidgets import QSizePolicy

from pyAbacus.constants import CURRENT_OS

import abacusSoftware.common as common
import abacusSoftware.constants as constants
import pyAbacus as abacus
from pyAbacus import findDevices

class SamplingWidget(object):
    def __init__(self, layout = None, label = None, method = None, number_channels = 2):
        self.layout = layout
        self.label = label
        self.method = method
        self.number_channels = 0
        self.widget = None
        self.value = 0
        self.changeNumberChannels(number_channels)

    def setEnabled(self, enabled):
        self.widget.setEnabled(enabled)

    def getValue(self):
        text_value = self.widget.currentText()
        return common.timeInUnitsToMs(text_value)

    def setValue(self, value):
        if value < 1000:
            index = self.widget.findText('%d ms' % value)
        elif value < 10000:
            index = self.widget.findText('%.1f s' % (value / 1000))
        else:
            index = self.widget.findText('%d s' % (value / 1000))

        self.widget.setCurrentIndex(index)

    def changeNumberChannels(self, number_channels):
        self.number_channels = number_channels
        if self.widget != None:
            self.layout.removeWidget(self.widget)
            self.widget.deleteLater()

        self.widget = QComboBox()
        if self.method != None: self.widget.currentIndexChanged.connect(self.method)
        self.widget.setEditable(True)
        self.widget.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.widget.lineEdit().setReadOnly(True)
        if self.number_channels == 2:
            common.setSamplingComboBox(self.widget)
        else:
            bases = np.arange(10, 100, 1)
            values = list(range(1, 10))
            for i in range(5):
                values += list(bases * 10 ** i)
            values.append(int(1e6))
            common.setSamplingComboBox(self.widget, values = values)
        if self.label != None: self.label.setText("Sampling time:")
        if self.layout != None:
            self.layout.setWidget(0, QFormLayout.FieldRole, self.widget)

class currentPlotCheckboxLabelButtons(QWidget):
    def __init__(self, label, parent=None):
        super(currentPlotCheckboxLabelButtons, self).__init__(parent=parent)
        self.parent = parent
        self.layout = QGridLayout(self)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.updateCheckboxes)
        self.label = QLabel(label)
        self.currentWindowButton = QToolButton()
        self.currentWindowButton.setCheckable(True)
        self.currentWindowButton.setAutoRaise(True)
        self.currentWindowButton.setEnabled(False)
        self.currentWindowButton.clicked.connect(self.showHideCurrentWindow)
        self.plotWindowButton = QToolButton()
        self.plotWindowButton.setCheckable(True)
        self.plotWindowButton.setAutoRaise(True)
        self.plotWindowButton.setEnabled(False)
        self.plotWindowButton.clicked.connect(self.showHidePlotWindow)
        self.updateButtonsIcons()
        
        if label == "Multiple": self.checkbox.setVisible(False)
        self.layout.addWidget(self.checkbox, 0, 0)
        self.layout.addWidget(self.label, 0, 1, 1, 2)
        self.layout.addWidget(self.currentWindowButton, 0, 4)
        self.layout.addWidget(self.plotWindowButton, 0, 5)
        self.setLayout(self.layout)

    def showHideCurrentWindow(self):
        label = self.label.text()
        menu_action = None
        main_window = self.parent.getParent()

        for action in self.parent.getParent().menuView.actions():
            if label.lower() in action.text() and "current" in action.text():
                menu_action = action
                break

        if self.currentWindowButton.isChecked():
            if label == "Single":
                main_window.subwindow_current_single.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
            elif label == "Double":
                main_window.subwindow_current_double.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
            elif label == "Multiple":
                main_window.subwindow_current_multiple.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
        elif not self.currentWindowButton.isChecked():
            if label == "Single":
                main_window.subwindow_current_single.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)
            elif label == "Double":
                main_window.subwindow_current_double.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)
            elif label == "Multiple":
                main_window.subwindow_current_multiple.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)

    def showHidePlotWindow(self):
        label = self.label.text()
        menu_action = None
        main_window = self.parent.getParent()

        for action in self.parent.getParent().menuView.actions():
            if label.lower() in action.text() and "plots" in action.text():
                menu_action = action
                break

        if self.plotWindowButton.isChecked():
            if label == "Single":
                main_window.subwindow_plots_single.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
            elif label == "Double":
                main_window.subwindow_plots_double.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
            elif label == "Multiple":
                main_window.subwindow_plots_multiple.show()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(True)
        elif not self.plotWindowButton.isChecked():
            if label == "Single":
                main_window.subwindow_plots_single.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)
            elif label == "Double":
                main_window.subwindow_plots_double.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)
            elif label == "Multiple":
                main_window.subwindow_plots_multiple.hide()
                main_window.mdi.tileSubWindows()
                menu_action.setChecked(False)

    def updateButtonsIcons(self):
        if constants.IS_LIGHT_THEME:
            self.currentWindowButton.setIcon(QIcon(':/current_icon.png'))
            self.plotWindowButton.setIcon(QIcon(':/plot_icon.png'))
        else:
            self.currentWindowButton.setIcon(QIcon(':/current_icon_dark.png'))
            self.plotWindowButton.setIcon(QIcon(':/plot_icon_dark.png'))

    def updateCheckboxes(self, check_state):
        if self.label.text() == "Single":
            letters = self.parent.letters
        elif self.label.text() == "Double":
            letters = self.parent.double
        for letter in letters:
            checkbox = getattr(self.parent, letter)
            if check_state == QtCore.Qt.Checked: 
                checkbox.setChecked(True)
            elif check_state == QtCore.Qt.Unchecked:
                checkbox.setChecked(False)

class Tabs(QFrame):
    MAX_CHECKED_4CH = 1
    MAX_CHECKED_8CH = 8
    def __init__(self, parent = None):
        QFrame.__init__(self)
        self.parent = parent

        self.all = []
        self.letters = []
        self.double = []
        self.multiple = []
        self.multiple_checked = []
        self.last_multiple_checked = None
        self.number_channels = 0

        scrollArea1 = QtWidgets.QScrollArea()
        scrollArea1.setWidgetResizable(True)
        scrollArea2 = QtWidgets.QScrollArea()
        scrollArea2.setWidgetResizable(True)
        scrollArea3 = QtWidgets.QScrollArea()
        scrollArea3.setWidgetResizable(True)

        self.single_tab = QGroupBox()
        self.single_tab.setStyleSheet("QGroupBox{padding-top:15px; margin-top:-15px}")
        self.double_tab = QGroupBox()
        self.double_tab.setStyleSheet("QGroupBox{padding-top:15px; margin-top:-15px}")
        self.multiple_tab = QGroupBox()
        self.multiple_tab.setStyleSheet("QGroupBox{padding-top:15px; margin-top:-15px}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)

        self.single_tab_layout = QGridLayout(self.single_tab)
        self.single_tab_layout.setSpacing(1)
        self.double_tab_layout = QGridLayout(self.double_tab)
        self.double_tab_layout.setSpacing(1)
        self.multiple_tab_layout = QGridLayout(self.multiple_tab)
        self.multiple_tab_layout.setSpacing(1)

        self.single_tab_top = currentPlotCheckboxLabelButtons("Single",self)
        self.double_tab_top = currentPlotCheckboxLabelButtons("Double",self)
        self.multiple_tab_top = currentPlotCheckboxLabelButtons("Multiple",self)

        self.buttons_widget = QWidget()
        self.buttons_widget_layout = QHBoxLayout(self.buttons_widget)
        self.btn_all_currents_subwindow = QPushButton("Current")
        self.btn_all_currents_subwindow.setCheckable(True)
        self.btn_all_currents_subwindow.setFlat(True)
        self.btn_all_currents_subwindow.clicked.connect(self.onToggledCurrent)
        self.btn_all_plots_subwindow = QPushButton("Plots")
        self.btn_all_plots_subwindow.setCheckable(True)
        self.btn_all_plots_subwindow.setFlat(True)
        self.btn_all_plots_subwindow.clicked.connect(self.onToggledPlots)

        self.buttons_widget_layout.addWidget(self.btn_all_currents_subwindow)
        self.buttons_widget_layout.addWidget(self.btn_all_plots_subwindow)

        self.layout.addWidget(self.buttons_widget)
        self.layout.addWidget(self.single_tab_top)
        self.layout.addWidget(scrollArea1)
        self.layout.addWidget(self.double_tab_top)
        self.layout.addWidget(scrollArea2)
        self.layout.addWidget(self.multiple_tab_top)
        self.layout.addWidget(scrollArea3)

        scrollArea1.setWidget(self.single_tab)
        scrollArea2.setWidget(self.double_tab)
        scrollArea3.setWidget(self.multiple_tab)

    def createSingle(self, letter, layout, letters):
        widget = QCheckBox(letter)
        widget.setChecked(False)
        setattr(self, letter, widget)
        if len(letter) == 1:
            n_widgets_created = len(self.single_tab.findChildren(QCheckBox))
        elif len(letter) == 2:
            n_widgets_created = len(self.double_tab.findChildren(QCheckBox))
        elif len(letter) == 3 or len(letter) == 4:
            n_widgets_created = len(self.multiple_tab.findChildren(QCheckBox))
 
        # Puts the checkboxes in two columns
        if n_widgets_created < len(letters)/2:
            row = n_widgets_created
            layout.addWidget(widget, row, 0)
        else:
            row = int(n_widgets_created-len(letters)/2) #v1.6.0: cast to int
            layout.addWidget(widget, row, 1)

        return widget

    def setNumberChannels(self, n_channels):
        self.deleteCheckBoxs()
        self.number_channels = n_channels

        self.letters = [chr(i + ord('A')) for i in range(n_channels)]
        joined = "".join(self.letters)
        self.double = ["".join(pair) for pair in combinations(joined, 2)]
        self.multiple = []
        if n_channels > 2:
            for i in range(3, n_channels + 1):
                self.multiple += ["".join(pair) for pair in combinations(joined, i) if len(pair) == 3 or len(pair) == 4]

        self.all = self.letters + self.double + self.multiple

        for letter in self.letters:
            widget = self.createSingle(letter, self.single_tab_layout, self.letters)
            widget.stateChanged.connect(self.signal)
        for letter in self.double:
            widget = self.createSingle(letter, self.double_tab_layout, self.double)
            widget.stateChanged.connect(self.signal)
        for letter in self.multiple:
            widget = self.createSingle(letter, self.multiple_tab_layout, self.multiple)
            widget.setChecked(False)
            widget.stateChanged.connect(self.signalMultiple)

        if self.number_channels == 8:
            setattr(self, '', QCheckBox())

        if self.number_channels == 2:
            self.multiple_tab_top.currentWindowButton.setEnabled(False)
            self.multiple_tab_top.currentWindowButton.setToolTip("Only available for 4-channel and 8-channel devices")
            self.multiple_tab_top.plotWindowButton.setEnabled(False)
            self.multiple_tab_top.plotWindowButton.setToolTip("Only available for 4-channel and 8-channel devices")
            self.double_tab_top.currentWindowButton.setEnabled(True)
            self.double_tab_top.plotWindowButton.setEnabled(True)
            self.double_tab_top.currentWindowButton.setToolTip("Show or hide current window")
            self.double_tab_top.plotWindowButton.setToolTip("Show or hide plot window")
            self.single_tab_top.currentWindowButton.setEnabled(True)
            self.single_tab_top.plotWindowButton.setEnabled(True)
            self.single_tab_top.currentWindowButton.setToolTip("Show or hide current window")
            self.single_tab_top.plotWindowButton.setToolTip("Show or hide plot window")
            self.parent.subwindow_current_multiple.hide()
            self.parent.subwindow_plots_multiple.hide()
            for action in self.parent.menuView.actions():
                if action.text() == "Show current multiple" or action.text() == "Show plots multiple":
                    action.setEnabled(False) 
        else:
            self.multiple_tab_top.currentWindowButton.setEnabled(True)
            self.multiple_tab_top.plotWindowButton.setEnabled(True)
            self.multiple_tab_top.currentWindowButton.setToolTip("Show or hide current window")
            self.multiple_tab_top.plotWindowButton.setToolTip("Show or hide plot window")
            self.double_tab_top.currentWindowButton.setEnabled(True)
            self.double_tab_top.plotWindowButton.setEnabled(True)
            self.double_tab_top.currentWindowButton.setToolTip("Show or hide current window")
            self.double_tab_top.plotWindowButton.setToolTip("Show or hide plot window")
            self.single_tab_top.currentWindowButton.setEnabled(True)
            self.single_tab_top.plotWindowButton.setEnabled(True)
            self.single_tab_top.currentWindowButton.setToolTip("Show or hide current window")
            self.single_tab_top.plotWindowButton.setToolTip("Show or hide plot window")
            for action in self.parent.menuView.actions():
                if action.text() == "Show current multiple" or action.text() == "Show plots multiple":
                    action.setEnabled(True) 

    def deleteSingle(self, widget, layout):
        layout.removeWidget(widget)
        widget.deleteLater()

    def deleteCheckBoxs(self):
        for letter in self.letters:
            self.deleteSingle(getattr(self, letter), self.single_tab_layout)
        for letter in self.double:
            self.deleteSingle(getattr(self, letter), self.double_tab_layout)
        for letter in self.multiple:
            self.deleteSingle(getattr(self, letter), self.multiple_tab_layout)

        self.all = []
        self.letters = []
        self.double = []
        self.multiple = []

    def getChecked(self):
        return [letter for letter in self.all if getattr(self, letter).isChecked()]

    def getSinglesChecked(self):
        return [letter for letter in self.letters if getattr(self, letter).isChecked()]

    def getDoublesChecked(self):
        return [letter for letter in self.double if getattr(self, letter).isChecked()]

    def signal(self):
        self.parent.activeChannelsChanged(self.getChecked())

    def signalMultiple(self, user_input = True):
        multiple_checked = [letter for letter in self.multiple if getattr(self, letter).isChecked()]
        new = [m for m in multiple_checked if not m in self.multiple_checked]

        if type(self.sender()) == type(QCheckBox()):
            if not self.sender().isChecked() and self.number_channels == 8:
                unchecked_letters = self.sender().text()
                index_ = self.multiple_checked.index(unchecked_letters)
                self.multiple_checked.pop(index_)

        if self.number_channels == 4: max = self.MAX_CHECKED_4CH
        elif self.number_channels == 8: max = self.MAX_CHECKED_8CH

        if len(self.multiple_checked) == max and len(new):
            getattr(self, self.multiple_checked[-1]).setChecked(False)
            del self.multiple_checked[-1]
        self.multiple_checked += new
        if len(new) and new != self.last_multiple_checked:
            self.last_multiple_checked = new
            self.parent.sendMultipleCoincidences(self.multiple_checked)
        if len(new) == 0  and self.number_channels == 8: # if len(new) == 0, then one checkbox in the multiple tab was unchecked
            n_new_elements_in_multiple_checked = 0
            for i in range(self.number_channels - len(self.multiple_checked)):
                self.multiple_checked.append('')
                n_new_elements_in_multiple_checked += 1
            self.parent.sendMultipleCoincidences(self.multiple_checked)
            self.multiple_checked = self.multiple_checked[:(self.number_channels - n_new_elements_in_multiple_checked)]

        self.signal()

    def simplyCheck(self, letters):
        """Checks any checkbox associated with the list of letters. This function is used to restore the previous session settings.
           Args:
                letters: a list of the letters whoses checboxes are to be checked

        """
        for letter in letters:
            getattr(self, letter).setChecked(True)

    def setChecked(self, letters):
        if len(letters) <= 2:
            getattr(self, letters).setChecked(True)
        elif self.last_multiple_checked != letters:
            getattr(self, letters).setChecked(True)
            self.last_multiple_checked = letters

    def changeButtonsIcons(self):
        self.single_tab_top.updateButtonsIcons()
        self.double_tab_top.updateButtonsIcons()
        self.multiple_tab_top.updateButtonsIcons()

        if constants.IS_LIGHT_THEME:
            self.btn_all_currents_subwindow.setIcon(QIcon(':/current_icon.png'))
            self.btn_all_plots_subwindow.setIcon(QIcon(':/plot_icon.png'))
        else:
            self.btn_all_currents_subwindow.setIcon(QIcon(':/current_icon_dark.png'))
            self.btn_all_plots_subwindow.setIcon(QIcon(':/plot_icon_dark.png'))

    def onToggledCurrent(self):
        for action in self.parent.menuView.actions():
            if "Show current" in action.text():
                menu_action = action
                break
        if self.btn_all_currents_subwindow.isChecked():
            self.parent.subwindow_current.show()
            action.setChecked(True)
        else:
            self.parent.subwindow_current.hide()
            action.setChecked(False)
        self.parent.mdi.tileSubWindows()

    def onToggledPlots(self):
        for action in self.parent.menuView.actions():
            if "Show plots" in action.text():
                menu_action = action
                break
        if self.btn_all_plots_subwindow.isChecked():
            self.parent.subwindow_plots.show()
            action.setChecked(True)
        else:
            self.parent.subwindow_plots.hide()
            action.setChecked(False)
        self.parent.mdi.tileSubWindows()

    def updateBtnsStatus(self):
        if self.parent.subwindow_current.isVisible(): self.btn_all_currents_subwindow.setChecked(True)
        if self.parent.subwindow_plots.isVisible(): self.btn_all_plots_subwindow.setChecked(True)

    def clearMultipleChecked(self):
        self.multiple_checked = []

    def getParent(self):
        return self.parent

    def reviewCheckBoxes(self):
        """If all checkboxes of a section (Single or Double) are checked, the main CheckBox of the section should be checked"""
        if len(self.getSinglesChecked()) == self.number_channels:
            self.single_tab_top.checkbox.blockSignals(True)
            self.single_tab_top.checkbox.setChecked(True)
            self.single_tab_top.checkbox.blockSignals(False)
        else:
            self.single_tab_top.checkbox.blockSignals(True)
            self.single_tab_top.checkbox.setChecked(False)
            self.single_tab_top.checkbox.blockSignals(False)

        n = self.number_channels

        if len(self.getDoublesChecked()) == n*(n-1)/2:
            self.double_tab_top.checkbox.blockSignals(True)
            self.double_tab_top.checkbox.setChecked(True)
            self.double_tab_top.checkbox.blockSignals(False)
        else:
            self.double_tab_top.checkbox.blockSignals(True)
            self.double_tab_top.checkbox.setChecked(False)
            self.double_tab_top.checkbox.blockSignals(False)

class Table(QtWidgets.QTableWidget):
    def __init__(self, active_labels, active_indexes):
        QtWidgets.QTableWidget.__init__(self)
        cols = len(active_indexes) + 2
        self.setColumnCount(cols)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setDefaultSectionSize(18)
        self.verticalHeader().setMinimumSectionSize(18)
        self.verticalHeader().setSortIndicatorShown(False)

        self.last_data = 0
        self.n_active = len(active_indexes)
        self.active_indexes = active_indexes

        self.headers = ['Time (s)', 'ID'] + active_labels
        self.setHorizontalHeaderLabels(self.headers)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True);

    def insertData(self, data):
        rows, cols = data.shape
        data = data[self.last_data : ]
        self.last_data = rows
        rows = data.shape[0]

        for i in range(rows):
            self.insertRow(0)
            for j in range(self.n_active + 2):
                fmt = "%d"
                if j < 2:
                    if j == 0:
                        fmt = "%.3f"
                    value = fmt % data[i, j]
                else:
                    value = fmt % data[i, 2 + self.active_indexes[j - 2]]
                self.setItem(0, j, QTableWidgetItem(value))
                self.item(0, j).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

class AutoSizeLabel(QtWidgets.QLabel):
    """ From reclosedev at http://stackoverflow.com/questions/8796380/automatically-resizing-label-text-in-qt-strange-behaviour
    and Jean-Sébastien http://stackoverflow.com/questions/29852498/syncing-label-fontsize-with-layout-in-pyqt
    """
    MAX_DIGITS = 7 #: Maximum number of digits of a number in label.
    MAX_CHARS = 9 + MAX_DIGITS #: Maximum number of letters in a label.
    INITIAL_FONT_SIZE = 10
    global CURRENT_OS
    def __init__(self, text, value):
        QtWidgets.QLabel.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.font_name = "Monospace"
        if CURRENT_OS == "win32":
            self.font_name = "Courier New"
        self.setFont(QtGui.QFont(self.font_name))
        self.font_size = self.INITIAL_FONT_SIZE
        self.MAX_TRY = 150
        self.height = self.contentsRect().height()
        self.width = self.contentsRect().width()
        self.name = text
        self.value = value
        self.setText(self.stylishText(text, value))
        self.setFontSize(self.font_size)

    def setFontSize(self, size):
        """ Changes the size of the font to `size` """
        f = self.font()
        f.setPixelSize(size)
        self.setFont(f)

    def setColor(self, color):
        """ Sets the font color.
        Args:
            color (string): six digit hexadecimal color representation.
        """
        self.setStyleSheet('color: %s'%color)

    def stylishText(self, text, value):
        """ Uses and incomning `text` and `value` to create and text of length
        `MAX_CHARS`, filled with spaces.
        Returns:
            string: text of length `MAX_CHARS`.
        """
        n_text = len(text)
        n_value = len(value)
        N = n_text + n_value
        spaces = [" " for i in range(self.MAX_CHARS - N-1)]
        spaces = "".join(spaces)
        text = "%s: %s%s"%(text, spaces, value)
        return text

    def changeValue(self, value):
        """ Sets the text in label with its name and its value. """
        if type(value) is not str:
            value = "%d"%value
        if self.value != value:
            self.value = value
            self.setText(self.stylishText(self.name, self.value))

    def clearSize(self):
        self.setFontSize(self.INITIAL_FONT_SIZE)

    def resize(self):
        """ Finds the best font size to use if the size of the window changes. """
        f = self.font()
        cr = self.contentsRect()
        height = cr.height()
        width = cr.width()
        if abs(height * width - self.height * self.width) > 1:
            self.font_size = self.INITIAL_FONT_SIZE
            for i in range(self.MAX_TRY):
                f.setPixelSize(self.font_size)
                br =  QtGui.QFontMetrics(f).boundingRect(self.text())
                if br.height() <= cr.height() and br.width() <= cr.width():
                    self.font_size += 1
                else:
                    if (CURRENT_OS == 'win32'):
                        self.font_size += -1
                    else:
                        self.font_size += -2
                    if (not constants.IS_LIGHT_THEME):
                        self.font_size += -2
                    f.setPixelSize(max(self.font_size, 1))
                    break
            self.setFont(f)
            self.height = height
            self.width = width

class CurrentLabels(QtWidgets.QWidget):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.installEventFilter(self)
        self.labels = []

    def createLabels(self, labels, light_colors, dark_colors):
        self.removeLabels()
        if not constants.IS_LIGHT_THEME:
            plots_info = dark_colors
        else:
            plots_info = light_colors
        for name in labels:
            label = AutoSizeLabel(name, "0")
            color = plots_info[name][0]
            self.setColor(label, color)
            self.layout.addWidget(label)
            self.labels.append(label)

    def removeLabels(self):
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels = []

    def setColor(self, label, color):
        label.setColor(color)

    def setColors(self, colors):
        for (label, color) in zip(self.labels, colors):
            self.setColor(label, color)

    def changeValue(self, index, value):
        self.labels[index].changeValue(value)

    def eventFilter(self, object, evt):
        """ Checks if there is the window size has changed.
        Returns:
            boolean: True if it has not changed. False otherwise. """
        ty = evt.type()
        if ty == 97: # DONT KNOW WHY
            self.resizeEvent(evt)
            return False
        elif ty == 12:
            self.resizeEvent(evt)
            return False
        else:
            return True

    def resizeEvent(self, evt):
        sizes = [None] * len(self.labels)
        for (i, label) in enumerate(self.labels):
            label.resize()
            sizes[i] = label.font_size

        if len(self.labels) > 0:
            try:
                size = max(sizes)
                for label in self.labels:
                    label.setFontSize(size)
            except TypeError: pass

    def clearSizes(self):
        for label in self.labels: label.clearSize()

class ConnectDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self)
        self.parent = parent
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame = QtWidgets.QFrame()

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)

        self.label = QtWidgets.QLabel()

        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.frame)

        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_button.setText("Refresh")
        self.refresh_button.clicked.connect(self.refresh)

        self.horizontalLayout.addWidget(self.comboBox)
        self.horizontalLayout.addWidget(self.refresh_button)

        self.label.setText(constants.CONNECT_LABEL)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setWindowTitle("Tausand Abacus device selection")
        self.setMinimumSize(QtCore.QSize(450, 100))

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.verticalLayout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject2)

        self.ports = None

    def refresh(self):
        self.clear()
        self.ports = findDevices(print_on = False)[0]
        ports_names = list(self.ports.keys())
        if len(ports_names) == 0:
            self.label.setText(constants.CONNECT_EMPTY_LABEL)
        else:
            self.label.setText(constants.CONNECT_LABEL)
        self.comboBox.addItems(ports_names)
        self.adjustSize()
        return ports_names

    def clear(self):
        self.comboBox.clear()
        self.parent.tabs_widget.multiple_tab_top.currentWindowButton.setEnabled(False)
        self.parent.tabs_widget.double_tab_top.currentWindowButton.setEnabled(False)
        self.parent.tabs_widget.single_tab_top.currentWindowButton.setEnabled(False)
        self.parent.tabs_widget.multiple_tab_top.plotWindowButton.setEnabled(False)
        self.parent.tabs_widget.double_tab_top.plotWindowButton.setEnabled(False)
        self.parent.tabs_widget.single_tab_top.plotWindowButton.setEnabled(False)

    def reject2(self):
        self.clear()
        self.reject()

class SettingsDialog(QtWidgets.QDialog):
    MAX_CHANNELS = 8
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self)

        self.parent = parent
        self.setWindowTitle("Default settings")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        # self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

        self.tabWidget = QtWidgets.QTabWidget(self)

        self.file_tab = QtWidgets.QWidget()
        self.settings_tab = QtWidgets.QWidget()

        self.tabWidget.addTab(self.file_tab, "File")
        self.tabWidget.addTab(self.settings_tab, "Settings")

        self.verticalLayout.addWidget(self.tabWidget)

        """
        file tab
        """
        self.file_tab_verticalLayout = QtWidgets.QVBoxLayout(self.file_tab)

        # frame1
        self.file_tab_frame1 = QtWidgets.QFrame()
        self.file_tab_frame1_layout = QtWidgets.QHBoxLayout(self.file_tab_frame1)

        self.directory_label = QtWidgets.QLabel("Directory:")
        self.directory_lineEdit = ClickableLineEdit()
        self.directory_pushButton = QtWidgets.QPushButton("Open")

        self.file_tab_frame1_layout.addWidget(self.directory_label)
        self.file_tab_frame1_layout.addWidget(self.directory_lineEdit)
        self.file_tab_frame1_layout.addWidget(self.directory_pushButton)
        self.file_tab_frame1.setMaximumHeight(60)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame1)
        self.directory_lineEdit.clicked.connect(self.chooseFolder)
        self.directory_pushButton.clicked.connect(self.chooseFolder)

        # frame2
        self.file_tab_frame2 = QtWidgets.QFrame()
        self.file_tab_frame2_layout = QtWidgets.QFormLayout(self.file_tab_frame2)

        self.file_prefix_label = QtWidgets.QLabel("File prefix:")
        self.file_prefix_lineEdit = QtWidgets.QLineEdit()
        self.extension_label = QtWidgets.QLabel("Extension:")
        self.extension_comboBox = QtWidgets.QComboBox()
        self.delimiter_label = QtWidgets.QLabel("Delimiter:")
        self.delimiter_comboBox = QtWidgets.QComboBox()
        self.parameters_label = QtWidgets.QLabel("Parameters suffix:")
        self.parameters_lineEdit = QtWidgets.QLineEdit()
        self.autogenerate_label = QtWidgets.QLabel("Autogenerate file name:")
        self.autogenerate_checkBox = QtWidgets.QCheckBox()
        self.check_updates_label = QtWidgets.QLabel("Check for updates:")
        self.check_updates_checkBox = QtWidgets.QCheckBox()
        self.datetime_label = QtWidgets.QLabel("Use datetime:")
        self.datetime_checkBox = QtWidgets.QCheckBox()

        self.theme_label = QtWidgets.QLabel("Light theme:")
        self.theme_checkBox = QtWidgets.QCheckBox()

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        widgets = [(self.theme_label, self.theme_checkBox),
                    (self.check_updates_label, self.check_updates_checkBox),
                    (self.autogenerate_label, self.autogenerate_checkBox),
                    (self.datetime_label, self.datetime_checkBox),
                    (self.file_prefix_label, self.file_prefix_lineEdit),
                    (self.parameters_label, self.parameters_lineEdit),
                    (self.extension_label, self.extension_comboBox),
                    (self.delimiter_label, self.delimiter_comboBox),
                    ]

        self.fillFormLayout(self.file_tab_frame2_layout, widgets)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        self.theme_checkBox.setChecked(True)
        self.autogenerate_checkBox.setCheckState(2)
        self.check_updates_checkBox.setCheckState(2)
        self.autogenerate_checkBox.stateChanged.connect(self.autogenerateMethod)
        self.datetime_checkBox.setCheckState(2)
        self.parameters_lineEdit.setText(constants.PARAMS_SUFFIX)
        self.file_prefix_lineEdit.setText(constants.FILE_PREFIX)
        self.delimiter_comboBox.insertItems(0, constants.DELIMITERS)
        self.extension_comboBox.insertItems(0, sorted(constants.SUPPORTED_EXTENSIONS.keys())[::-1])


        """
        settings tab
        """
        self.settings_tab_verticalLayout = QtWidgets.QVBoxLayout(self.settings_tab)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)

        self.settings_tab_frame = QtWidgets.QFrame()
        self.settings_tab_frame_layout = QtWidgets.QFormLayout(self.settings_tab_frame)

        scrollArea.setWidget(self.settings_tab_frame)

        self.sampling_label = QtWidgets.QLabel("Sampling time:")
        self.sampling_widget = SamplingWidget()#QtWidgets.QComboBox()
        self.coincidence_label = QtWidgets.QLabel("Coincidence window (ns):")
        self.coincidence_spinBox = QtWidgets.QSpinBox()
        self.coincidence_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        widgets = [(self.sampling_label, self.sampling_widget.widget),
                    (self.coincidence_label, self.coincidence_spinBox)]

        letters = [chr(i + ord('A')) for i in range(self.MAX_CHANNELS)]
        self.delays = []
        self.sleeps = []
        d_labels = []
        s_labels = []
        for letter in letters:
            d_label = QtWidgets.QLabel("Delay %s (ns):" % letter)
            d_spinBox = QtWidgets.QSpinBox()
            s_label = QtWidgets.QLabel("Sleep time %s (ns):" % letter)
            s_spinBox = QtWidgets.QSpinBox()
            d_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            s_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            common.setDelaySpinBox(d_spinBox)
            common.setSleepSpinBox(s_spinBox)

            setattr(self, "delay_%s_label"%letter, d_label)
            setattr(self, "sleep_%s_label"%letter, s_label)
            setattr(self, "delay_%s_spinBox"%letter, d_spinBox)
            setattr(self, "sleep_%s_spinBox"%letter, s_spinBox)
            d_labels.append(d_label)
            s_labels.append(s_label)
            self.delays.append(d_spinBox)
            self.sleeps.append(s_spinBox)

        widgets += [(d_labels[i], self.delays[i]) for i in range(self.MAX_CHANNELS)]
        widgets += [(s_labels[i], self.sleeps[i]) for i in range(self.MAX_CHANNELS)]

        self.fillFormLayout(self.settings_tab_frame_layout, widgets)

        self.settings_tab_verticalLayout.addWidget(self.settings_tab_frame)

        common.setSamplingComboBox(self.sampling_widget.widget)
        common.setCoincidenceSpinBox(self.coincidence_spinBox)

        """
        buttons
        """
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply")
        self.buttons.accepted.connect(self.accept_replace)
        self.buttons.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttons)

        self.setConstants()
        self.setMinimumWidth(500)

    def autogenerateMethod(self, val):
        self.datetime_checkBox.setEnabled(val)
        self.file_prefix_lineEdit.setEnabled(val)

    def fillFormLayout(self, layout, values):
        for (i, line) in enumerate(values):
            layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
            layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

    def constantsWriter(self, update_parent = True):
        lines = []
        for (widget, eval_) in zip(constants.WIDGETS_NAMES, constants.WIDGETS_GET_ACTIONS):
            complete = common.findWidgets(self, widget)
            for item in complete:
                val = eval(eval_%item)
                if type(val) is str:
                    if item == "directory_lineEdit":
                        if val == "":
                            val = self.parent.getWorkingDirectory()
                        val = common.unicodePath(val)
                    string = "%s = '%s'"%(item, val)
                else:
                    string = "%s = %s"%(item, val)
                lines.append(string)
        lines.append("sampling_widget = %d" % self.sampling_widget.getValue())
        self.writeDefault(lines)
        lines += ["EXTENSION_DATA = '%s'"%self.extension_comboBox.currentText(),
                    "EXTENSION_PARAMS = '%s.txt'"%self.parameters_lineEdit.text()]
        delimiter = self.delimiter_comboBox.currentText()
        if delimiter == "Tab":
            delimiter = "\t"
        elif delimiter == "Space":
            delimiter = " "
        lines += ["DELIMITER = '%s'"%delimiter]
        self.updateConstants(lines)
        if update_parent: self.parent.updateConstants()

    def accept_replace(self):
        self.constantsWriter()
        self.accept()

    def writeDefault(self, lines):
        try:
            with open(constants.SETTINGS_PATH, "w") as file:
                [file.write(line + constants.BREAKLINE) for line in lines]
        except FileNotFoundError as e:
            print(e)

    def updateConstants(self, lines):
        [exec("constants.%s"%line) for line in lines]

    def setConstants(self):
        try:
            common.updateConstants(self)
            self.sampling_widget.setValue(constants.sampling_widget)
            self.setDirectory()
        except AttributeError:
            pass

    def chooseFolder(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", common.findDocuments(), QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog))
        if folder != "":
            self.directory_lineEdit.setText(folder)

    def setDirectory(self):
        try:
            directory = constants.directory_lineEdit
            if os.path.exists(directory):
                self.directory_lineEdit.setText(directory)
                return
            directory = os.path.normpath(directory)
            documents = os.path.normpath(common.findDocuments())
            e = Exception('The default directory "%s" does not exist.\n\nThe default directory will be set to "%s".' % (directory, documents))
            self.parent.showInformationDialog(e, "Default directory path")
        except AttributeError as e:
            pass
        directory = common.findDocuments()
        self.directory_lineEdit.setText(directory)
        common.directory_lineEdit = directory
        self.constantsWriter()

class SubWindow(QtWidgets.QMdiSubWindow):
    def __init__(self, parent = None):
        super(SubWindow, self).__init__(parent)
        self.parent = parent
        self.setWindowIcon(constants.ICON)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def closeEvent(self, evnt):
        evnt.ignore()
        self.hide()
        name = self.windowTitle().lower()
        actions = self.parent.menuView.actions()
        for action in actions:
            if name in action.text(): action.setChecked(False)
        if "Current single".lower() == name:
            self.parent.tabs_widget.single_tab_top.currentWindowButton.setChecked(False)
        elif "Current double".lower() == name:
            self.parent.tabs_widget.double_tab_top.currentWindowButton.setChecked(False)
        elif "Current multiple".lower() == name:
            self.parent.tabs_widget.multiple_tab_top.currentWindowButton.setChecked(False)
        elif "Current".lower() == name:
            self.parent.tabs_widget.btn_all_currents_subwindow.setChecked(False)

        if "Plots single".lower() == name:
            self.parent.tabs_widget.single_tab_top.plotWindowButton.setChecked(False)
        elif "Plots double".lower() == name:
            self.parent.tabs_widget.double_tab_top.plotWindowButton.setChecked(False)
        elif "Plots multiple".lower() == name:
            self.parent.tabs_widget.multiple_tab_top.plotWindowButton.setChecked(False)
        elif "Plots".lower() == name:
            self.parent.tabs_widget.btn_all_plots_subwindow.setChecked(False)

        self.parent.mdi.tileSubWindows()

    def resizeEvent(self, event):
        self.parent.legend.anchor(itemPos=(1,0), parentPos=(1,0), offset=(22,-15))
        self.parent.legend_single.anchor(itemPos=(1,0), parentPos=(1,0), offset=(17,-15))
        self.parent.legend_double.anchor(itemPos=(1,0), parentPos=(1,0), offset=(20,-15))
        self.parent.legend_multiple.anchor(itemPos=(1,0), parentPos=(1,0), offset=(22,-15))
        QtWidgets.QMdiSubWindow.resizeEvent(self, event)

    def moveEvent(self, event):
        if self.parent.width() == QtWidgets.QDesktopWidget().screenGeometry().width():
            pos = event.pos()
            right = pos.x() + self.width()
            down = pos.y() + self.height()
            left = pos.x()
            area = self.mdiArea()

            if right > area.width():
                self.move(area.width() - self.width(), pos.y())
                return
            elif down > area.height():
                self.move(pos.x(), area.height() - self.height())
                return
            elif left < 0:
                self.move(0, pos.y())
                return

class ClickableLineEdit(QtWidgets.QLineEdit):
    clicked = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        super(ClickableLineEdit, self).__init__(parent)
        self.setReadOnly(True)

    def mousePressEvent(self, event):
        self.clicked.emit()
        QtWidgets.QLineEdit.mousePressEvent(self, event)

class PlotConfigsDialog(QDialog):
    def __init__(self, img, painter, rect, iconSize, active_channels_plotDataItems, 
                light_colors_in_use, dark_colors_in_use, parent) :
        super().__init__(parent=None)

        self.setWindowTitle("Plots configuration")
        self.active_plots = active_channels_plotDataItems
        self.colors = None
        self.colors_names = None
        self.img = img
        self.painter = painter
        self.rect = rect
        self.channels_comboBoxes_colors = {}
        self.unmodified_configuration = {}
        self.markersize_spinbox = None
        self.linewidth_spinbox = None

        # TODO The following parameters shouldn't be assigned to this class attributes 
        # but should rather be accessed through the mainWindow attributes
        self.light_colors_in_use = light_colors_in_use
        self.dark_colors_in_use = dark_colors_in_use

        self.parent = parent

        # Create comboBoxes for each channel that is currently active and 
        # show available colors in each one

        for plot in self.active_plots: 
            if plot.opts['pen'] == type(QPen()):
                self.channels_comboBoxes_colors[plot.opts['name']] = [plot.opts['name'], 
                                                QComboBox(), plot.opts['pen'].color().name(), plot]
                self.unmodified_configuration[plot.opts['name']] = [plot.opts['name'], 
                                                QComboBox(), plot.opts['pen'].color().name(), plot]
            else:
                self.channels_comboBoxes_colors[plot.opts['name']] = [plot.opts['name'], 
                                                QComboBox(), plot.opts['pen'], plot]
                self.unmodified_configuration[plot.opts['name']] = [plot.opts['name'], 
                                                QComboBox(), plot.opts['pen'], plot]

        if not constants.IS_LIGHT_THEME:
            self.colors = constants.DARK_COLORS
            self.colors_names = constants.DARK_COLORS_NAMES
        else: 
            self.colors = constants.COLORS
            self.colors_names = constants.COLORS_NAMES

        for item in self.channels_comboBoxes_colors.values():
            # item[1] is a QComboBox
            item[1].setIconSize(iconSize)
            for i,color in enumerate(self.colors):
                item[1].addItem(self.colors_names[i])
                self.painter.fillRect(self.img.rect(), QColor(color))
                item[1].setItemData(i, QPixmap.fromImage(self.img), QtCore.Qt.DecorationRole)
                if color == item[2]: item[1].setCurrentIndex(i)
                if type(item[2]) == type(QPen()):
                    if color == item[2].color().name():
                        item[1].setCurrentIndex(i)
            if item[2].color().name() not in self.colors:
                color = item[2].color().name()
                item[1].blockSignals(True)
                self.painter.fillRect(self.img.rect(), QColor(color))
                if item[1].count()-1 > len(self.colors):
                    item[1].setItemData(0, QPixmap.fromImage(self.img), QtCore.Qt.DecorationRole)
                else:
                    item[1].insertItem(0, color)
                    item[1].setItemData(0, QPixmap.fromImage(self.img), QtCore.Qt.DecorationRole)
                item[1].setCurrentIndex(0) 
                item[1].blockSignals(False)    
            item[1].addItem("Custom color")
            item[1].currentIndexChanged.connect(self.updateComboBox)

        # Put comboboxes in a GroupBox and add another groupbox for linewidth and markersize
        self.colorsFormGroupBox = self.createColorGroupBox()
        self.lineWidthMarkerFormGroupBox = self.createLineWidthMarkerSizeGroupBox()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.colors_frame = QFrame()
        self.colors_layout = QVBoxLayout(self.colors_frame)
        self.colors_layout.addWidget(self.colorsFormGroupBox)

        self.more_settings_frame = QFrame()
        self.more_settings_layout = QVBoxLayout(self.more_settings_frame)
        self.more_settings_layout.addWidget(self.lineWidthMarkerFormGroupBox)
        self.more_settings_layout.addWidget(self.buttonBox)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.colors_frame)

        painter.end()

        self.outter_layout = QVBoxLayout()
        self.outter_layout.addWidget(scrollArea)
        self.outter_layout.addWidget(self.more_settings_frame)

        self.setLayout(self.outter_layout)
        if self.there_are_single_double_multiple_active(self.active_plots) and constants.IS_LIGHT_THEME:
            self.resize(820, self.sizeHint().height())
        elif self.there_are_single_double_multiple_active(self.active_plots) and not constants.IS_LIGHT_THEME:
            self.resize(850, self.sizeHint().height())

    def there_are_single_double_multiple_active(self, plots_active):
        at_least_one_single = False
        at_least_one_double = False
        at_least_one_multiple = False

        for plot in plots_active:
            channel_name = plot.opts['name']
            if len(channel_name) == 1:
                at_least_one_single = True
            elif len(channel_name) == 2:
                at_least_one_double = True
            else:
                at_least_one_multiple = True

        return at_least_one_single and at_least_one_double and at_least_one_multiple

    def createColorGroupBox(self):
        colorGroupBox = QGroupBox("Lines color")
        single_widget = QWidget()
        double_widget = QWidget()
        multiple_widget = QWidget()

        single_layout = QFormLayout()
        double_layout = QFormLayout()
        multiple_layout = QFormLayout()
        
        for i, plot in enumerate(self.active_plots):
            channel_name = plot.opts['name']
            if len(channel_name) == 1:
                single_layout.addRow(QLabel(self.channels_comboBoxes_colors[channel_name][0]), 
                    self.channels_comboBoxes_colors[channel_name][1])
            elif len(channel_name) == 2:
                double_layout.addRow(QLabel(self.channels_comboBoxes_colors[channel_name][0]), 
                    self.channels_comboBoxes_colors[channel_name][1])
            else:
                multiple_layout.addRow(QLabel(self.channels_comboBoxes_colors[channel_name][0]), 
                    self.channels_comboBoxes_colors[channel_name][1])   

        single_widget.setLayout(single_layout)
        double_widget.setLayout(double_layout)
        multiple_widget.setLayout(multiple_layout)

        layout = QHBoxLayout()
        layout.addWidget(single_widget)
        layout.addWidget(double_widget)
        layout.addWidget(multiple_widget)
        colorGroupBox.setLayout(layout)
        return colorGroupBox
    
    def createLineWidthMarkerSizeGroupBox(self):
        self.markersize_spinbox = QtWidgets.QSpinBox()
        self.linewidth_spinbox = QtWidgets.QSpinBox()
        moreSettingsGroupBox = QGroupBox("More settings")
        layout = QFormLayout()
        layout.addRow(QLabel("Line width"), self.linewidth_spinbox)
        layout.addRow(QLabel("Marker size"), self.markersize_spinbox)
        self.markersize_spinbox.setValue(self.active_plots[0].opts['symbolSize'])
        self.linewidth_spinbox.setValue(self.active_plots[0].opts['pen'].width())
        moreSettingsGroupBox.setLayout(layout)
        return moreSettingsGroupBox

    def updateComboBox(self, val):
        comboBox = self.sender()
        color_selected = None
        
        if comboBox.currentText() == "Custom color":
            customColorPicker = QColorDialog()
            color_selected = customColorPicker.getColor(title="Select custom color",
                                options=QColorDialog.DontUseNativeDialog)
            color_selected = color_selected.name()
            comboBox.blockSignals(True)
            self.painter = QtGui.QPainter(self.img)
            self.painter.fillRect(self.rect, QColor(color_selected))
            if comboBox.count()-1 > len(self.colors):
                comboBox.removeItem(0)   
            comboBox.insertItem(0, color_selected)
            comboBox.setItemData(0, QPixmap.fromImage(self.img), QtCore.Qt.DecorationRole)      
            comboBox.setCurrentIndex(0) 
            comboBox.blockSignals(False)
            self.painter.end()       
        else:
            if comboBox.count()-1 > len(self.colors):
                color_selected = self.colors[val-1]
            else: 
                color_selected = self.colors[val]
        
        for channel in self.channels_comboBoxes_colors.values():
            # channel[1] is a comboBox and channel[2] is its color
            if channel[1] == comboBox:
                channel[2] = color_selected

    def accept(self):
        if constants.IS_LIGHT_THEME: colors = self.light_colors_in_use
        else: colors = self.dark_colors_in_use

        for i,channel in enumerate(self.channels_comboBoxes_colors.values()):
            current_symbol = colors[channel[0]][1]        
            if type(channel[2]) == type(""):
                colors[channel[0]] = [channel[2], current_symbol]
            else:
                colors[channel[0]] = [channel[2].color().name(), current_symbol]
        
        self.parent.symbolSize = self.markersize_spinbox.value()
        self.parent.linewidth = self.linewidth_spinbox.value()                
        self.close()
