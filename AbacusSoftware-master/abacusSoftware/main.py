import os
import re
import sys
import traceback
import numpy as np
import abacusSoftware.__GUI_images__
import pyqtgraph as pg
from datetime import datetime
from itertools import combinations
from time import time, localtime, strftime, sleep
from random import randrange
import qtmodern.styles

from serial.serialutil import SerialException, SerialTimeoutException

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtWidgets import QLabel, QSpinBox, QComboBox, QSizePolicy, QAction, \
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, \
        QPushButton, QMdiArea
except ModuleNotFoundError:
    from PyQt4.QtGui import QLabel, QSpinBox, QComboBox, QSizePolicy, QAction

#Original:
import abacusSoftware.constants as constants
import abacusSoftware.common as common
import abacusSoftware.builtin as builtin
import abacusSoftware.url as url
from abacusSoftware.menuBar import AboutWindow
from abacusSoftware.exceptions import ExtentionError
from abacusSoftware.files import ResultsFiles, RingBuffer
from abacusSoftware.supportWidgets import Table, CurrentLabels, ConnectDialog, \
    SettingsDialog, SubWindow, ClickableLineEdit, Tabs, SamplingWidget, \
    PlotConfigsDialog

import pyAbacus as abacus

STDOUT = None

def getCombinations(n_channels):
    letters = [chr(i + ord('A')) for i in range(n_channels)]
    joined = "".join(letters)
    for i in range(2, n_channels + 1):
        letters += ["".join(pair) for pair in combinations(joined, i) if len(pair) <=4 ]
    return letters

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        abacus.setLogfilePath(self.getWorkingDirectory())
        self.port_name = None
        self.start_position = None
        self.number_channels = 0
        self.active_channels = []
        self.active_channels_single = []
        self.active_channels_double = []
        self.active_channels_multiple = []
        self.devices_used = {} # The devices and channels used in the current session and in the past
        constants.IS_LIGHT_THEME = True
        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.setContentsMargins(0, 0, 11, 0)
        layout.setSpacing(0)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)

        horizontalLayout = QHBoxLayout(frame)
        label = QLabel("Save as:")

        self.save_as_lineEdit = ClickableLineEdit()
        self.save_as_lineEdit.clicked.connect(self.chooseFile)

        self.save_as_button = QPushButton("Open")

        horizontalLayout.addWidget(label)
        horizontalLayout.addWidget(self.save_as_lineEdit)
        horizontalLayout.addWidget(self.save_as_button)

        layout.addWidget(frame)

        frame2 = QFrame()
        layout2 = QHBoxLayout(frame2)
        layout2.setContentsMargins(0, 6, 0, 6)
        layout2.setSpacing(0)

        self.connect_button = QPushButton("Connect")
        self.connect_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.connect_button)

        #Añado el botón 'About Me' entre 'Connect' y 'Start acquisition'
        self.about_me_button = QPushButton("About Me")
        self.about_me_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.about_me_button)

        self.acquisition_button = QPushButton("Start acquisition")
        self.acquisition_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.acquisition_button)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        layout2.addWidget(line)
        self.clear_button = QPushButton("Clear plots")
        self.clear_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.clear_button)
        self.plots_config_button = QPushButton('Configure plots')
        self.plots_config_button.clicked.connect(self.configPlot)
        self.plots_config_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.plots_config_button)
        self.reset_time_button = QPushButton('Reset time')
        self.reset_time_button.clicked.connect(self.resetTime)
        self.reset_time_button_pressed = False
        self.reset_time_button.setEnabled(False)
        self.reset_time_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.reset_time_button)
        self.range_label = QLabel("Time range:")
        self.range_label.setMaximumSize(QtCore.QSize(140, 60))
        self.range_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.plots_combo_box = QComboBox(self)
        self.plots_time_options = {'10s':10, '30s':30, '1m':60, 
                                    '5m':300, '15m':900, '1h':3600, 'All':'All'}
        self.plots_combo_box.addItems(list(self.plots_time_options.keys()))
        self.plots_combo_box.setMaximumSize(QtCore.QSize(70, 60))

        layout2.addWidget(self.range_label)
        layout2.addWidget(self.plots_combo_box)

        frame3 = QFrame()
        layout3 = QHBoxLayout(frame3)
        layout.addWidget(frame3)

        toolbar_frame = QFrame()
        toolbar_frame_layout = QVBoxLayout(toolbar_frame)

        self.tabs_widget = Tabs(self)
        toolbar_frame_layout.addWidget(self.tabs_widget)
        toolbar_frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        toolbar_frame.setMinimumWidth(185)
        toolbar_frame.setMaximumWidth(195)

        layout3.addWidget(toolbar_frame)
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.setSpacing(0)

        frame4 = QFrame()
        layout4 = QVBoxLayout(frame4)
        layout4.addWidget(frame2)

        self.mdi = QMdiArea(frame3)
        self.mdi.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #layout3.addWidget(self.mdi)
        layout4.addWidget(self.mdi)
        self.setCentralWidget(widget)

        layout3.addWidget(frame4)

        """
        settings
        """
        self.sampling_widget = None
        self.delay_widgets = []
        self.sleep_widgets = []
        self.subSettings_delays_sleeps = []

        self.subPlotsMultiple()
        self.subwindow_plots_multiple.hide()

        self.subPlotsDouble()
        self.subwindow_plots_double.hide()

        self.subPlotsSingle()
        self.subwindow_plots_single.hide()

        self.subPlots()
        self.subwindow_plots.show()  

        self.subHistorical()
        self.subwindow_historical.show()

        self.subCurrentMultiple()
        self.subwindow_current_multiple.hide()
        
        self.subCurrentDouble()
        self.subwindow_current_double.hide()

        self.subCurrentSingle()
        self.subwindow_current_single.hide()

        self.subCurrent()
        self.subwindow_current.show()

        self.subSettings()
        self.subwindow_settings.show()

        """
        Config
        """
        self.streaming = False
        self.acquisition_button.clicked.connect(self.startAcquisition)

        self.connect_dialog = None
        self.connect_button.clicked.connect(self.connect)

        #Añado la acción al botón 'About Me'
        self.about_me_button.clicked.connect(self.aboutWindowCaller)

        self.clear_button.clicked.connect(self.clearPlot)

        self.coincidence_spinBox.valueChanged.connect(self.coincidenceWindowMethod)
        self.last_valid_value_coincidence_window = abacus.constants.COINCIDENCE_WINDOW_DEFAULT_VALUE

        """
        Plots
        """
        self.plot_lines = []
        self.legend = None
        self.counts_plot = self.plot_win.addPlot()
        self.counts_plot.setLabel('left', "Counts")
        self.counts_plot.setLabel('bottom', "Time", units='s')

        self.plot_lines_single = []
        self.legend_single = None
        self.counts_plot_single = self.plot_win_single.addPlot()
        self.counts_plot_single.setLabel('left', "Counts")
        self.counts_plot_single.setLabel('bottom', "Time", units='s')

        self.plot_lines_double = []
        self.legend_double = None
        self.counts_plot_double = self.plot_win_double.addPlot()
        self.counts_plot_double.setLabel('left', "Counts")
        self.counts_plot_double.setLabel('bottom', "Time", units='s')

        self.plot_lines_multiple = []
        self.legend_multiple = None
        self.counts_plot_multiple = self.plot_win_multiple.addPlot()
        self.counts_plot_multiple.setLabel('left', "Counts")
        self.counts_plot_multiple.setLabel('bottom', "Time", units='s')

        self.dark_colors_in_use = {}
        self.light_colors_in_use = {}

        self.symbolSize = 8
        self.linewidth = 2
        """
        Timers
        """
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(constants.DATA_REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.updateWidgets)

        self.data_timer = QtCore.QTimer()
        self.data_timer.setInterval(constants.DATA_REFRESH_RATE)
        self.data_timer.timeout.connect(self.updateData)

        self.check_timer = QtCore.QTimer()
        self.check_timer.setInterval(constants.CHECK_RATE)
        self.check_timer.timeout.connect(self.checkParams)

        self.lose_focus_timer = QtCore.QTimer()
        self.lose_focus_timer.timeout.connect(self.spinboxLoseFocus)

        self.check_focus_timer = QtCore.QTimer()
        self.check_focus_timer.start(6000) # The timeout interval here should be larger than the one of self.lose_focus_timer 
        self.check_focus_timer.timeout.connect(self.checkSpinboxFocus)

        self.results_files = None
        self.params_buffer = ""
        self.init_time = 0
        self.init_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        self.data_ring = None
        self.combinations = []
        self.combination_indexes = []
        self.save_as_button.clicked.connect(self.chooseFile)
        self.save_as_lineEdit.returnPressed.connect(self.setSaveAs)

        self.unlockSettings(True)

        """
        MenuBar
        """
        self.menubar = self.menuBar()

        self.menuFile = self.menubar.addMenu("File")
        self.menuProperties = self.menubar.addMenu("Properties")
        self.menuBuildIn = self.menubar.addMenu("Built In")
        self.menuView = self.menubar.addMenu("View")
        self.menuHelp = self.menubar.addMenu("Help")

        self.menuBuildInSweep = QtWidgets.QMenu("Sweep")

        delaySweep = QAction('Delay time', self)
        sleepSweep = QAction('Sleep time', self)

        self.menuBuildInSweep.addAction(delaySweep)
        self.menuBuildInSweep.addAction(sleepSweep)
        delaySweep.triggered.connect(self.delaySweep)
        sleepSweep.triggered.connect(self.sleepSweep)

        self.menuBuildIn.addMenu(self.menuBuildInSweep)

        self.statusBar = QtWidgets.QStatusBar(self)
        self.statusBar.setObjectName("statusBar")
        self.setStatusBar(self.statusBar)
        self.statusBarMessage = None

        self.actionAbout = QAction('About', self)
        self.actionSave_as = QAction('Save as', self)
        self.actionDefault_settings = QAction('Default settings', self)
        self.actionExit = QAction('Exit', self)

        self.menuFile.addAction(self.actionSave_as)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)
        self.menuProperties.addAction(self.actionDefault_settings)

        self.menuView.addAction(QAction("Show settings", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show historical", self.menuView, checkable=True))
        self.menuView.addSeparator()
        self.menuView.addAction(QAction("Show current", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show current single", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show current double", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show current multiple", self.menuView, checkable=True))
        self.menuView.addSeparator()
        self.menuView.addAction(QAction("Show plots", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show plots single", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show plots double", self.menuView, checkable=True))
        self.menuView.addAction(QAction("Show plots multiple", self.menuView, checkable=True))
        self.menuView.addSeparator()
        self.menuView.addAction("Tiled")
        self.menuView.addAction("Cascade")
        self.menuView.addAction("Default layout")
        self.menuView.addSeparator()
        self.theme_action = self.menuView.addAction("Dark theme")

        for action in self.menuView.actions():
            action_should_be_initially_hidden = action.text() in ["Show current single", "Show current double", 
                    "Show current multiple", "Show plots single", "Show plots double", "Show plots multiple"]
            if action.isCheckable() and not action_should_be_initially_hidden: 
                action.setChecked(True)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuProperties.menuAction())
        self.menubar.addAction(self.menuBuildIn.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.menuView.triggered.connect(self.handleViews)

        self.actionSave_as.triggered.connect(self.chooseFile)
        self.actionSave_as.setShortcut("Ctrl+S")
        self.actionDefault_settings.triggered.connect(self.settingsDialogCaller)

        self.actionAbout.triggered.connect(self.aboutWindowCaller)
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setShortcut("Ctrl+Q")

        self.acquisition_button.setDisabled(True)
        self.about_window = AboutWindow()
        self.settings_dialog = SettingsDialog(self)
        self.setWindowTitle(constants.WINDOW_NAME)

        self.delaySweepDialog = builtin.DelayDialog(self)
        self.sleepSweepDialog = builtin.SleepDialog(self)

        self.setLightTheme()
        self.setSettings()
        self.updateConstants()

    def getWorkingDirectory(self):
        common.readConstantsFile()
        dirName = common.findDocuments() + "/Tausand"
        if not os.path.exists(dirName):
            os.mkdir(dirName)
        return dirName

    def aboutWindowCaller(self):
        self.about_window.show()

    def activeChannelsChanged(self, actives):
        self.active_channels_single = []
        self.active_channels_double = []
        self.active_channels_multiple = []
        self.active_channels = actives

        for channel in actives:
            if len(channel) == 1:
                self.active_channels_single.append(channel)
            elif len(channel) == 2:
                self.active_channels_double.append(channel)
            elif len(channel) == 3 or len(channel) == 4:
                self.active_channels_multiple.append(channel)

        self.tabs_widget.reviewCheckBoxes()

        self.initPlots()
        self.current_labels.createLabels(self.active_channels, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_single.createLabels(self.active_channels_single, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_double.createLabels(self.active_channels_double, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_multiple.createLabels(self.active_channels_multiple, self.light_colors_in_use, self.dark_colors_in_use)
        self.combination_indexes = [i for (i, com) in enumerate(self.combinations) if com in self.active_channels]

        "Clear table"
        self.historical_layout.removeWidget(self.historical_table)
        self.historical_table.deleteLater()

        "Create new table"
        self.historical_table = Table(self.active_channels, self.combination_indexes)
        self.historical_layout.addWidget(self.historical_table)

        self.updateWidgets()

        if self.port_name != None:
            self.devices_used[self.port_name] = self.active_channels

    def centerOnScreen(self):
        resolution = QtWidgets.QDesktopWidget().availableGeometry()
        sw = resolution.width()
        sh = resolution.height()
        fh = self.frameSize().height()
        fw = self.frameSize().width()
        y_o = (sh - fh) / 2
        x_o = (sw - fw) / 2
        self.move(x_o, y_o)

    def checkFileName(self, name):
        if "." in name:
            name, ext = name.split(".")
            ext = ".%s" % ext
        else:
            try:
                ext = constants.extension_comboBox
                print(ext)
            except AttributeError:
                ext = constants.EXTENSION_DATA
            name = common.unicodePath(name)
            self.save_as_lineEdit.setText(name + ext)
        if ext in constants.SUPPORTED_EXTENSIONS.keys():
            return name, ext
        else:
            raise ExtentionError()

    def checkParams(self):
        if self.port_name != None:
            try:
                if self.statusBar.currentMessage() != abacus.getStatusMessage():
                    if abacus.getStatusMessage() != None and "down" in abacus.getStatusMessage():
                        self.statusBar.setStyleSheet("QStatusBar{padding-left:8px;background:#d71d2a;color:black;}")
                        self.statusBar.showMessage(abacus.getStatusMessage())
                    else:
                        self.statusBar.setStyleSheet("")
                        self.statusBar.showMessage(abacus.getStatusMessage())
                        self.sendMultipleCoincidences(self.tabs_widget.multiple_checked)

                settings = abacus.getAllSettings(self.port_name)
                samp = int(settings.getSetting("sampling"))
                coin = settings.getSetting("coincidence_window")
                if self.number_channels == 4:
                    custom = settings.getSetting("config_custom_c1")
                    self.tabs_widget.setChecked(custom)
                elif self.number_channels == 8:
                    for i in range(8):
                        custom = settings.getSetting("config_custom_c%d" % (i + 1))
                        self.tabs_widget.setChecked(custom)

                if self.coincidence_spinBox.value() != coin:
                    self.coincidence_spinBox.setValue(coin)

                for i in range(self.number_channels):
                    letter = self.getLetter(i)
                    delay = self.delay_widgets[i]
                    sleep = self.sleep_widgets[i]
                    delay_new_val = settings.getSetting("delay_%s" % letter)
                    sleep_new_val = settings.getSetting("sleep_%s" % letter)
                    if (delay.value() != delay_new_val) & delay.keyboardTracking():
                        delay.setValue(delay_new_val)
                    if (sleep.value() != sleep_new_val) & sleep.keyboardTracking():
                        sleep.setValue(sleep_new_val)

                if (self.sampling_widget.getValue() != samp):
                    self.sampling_widget.setValue(samp)

            except abacus.BaseError as e:
                pass
            except SerialException as e:
                self.errorWindow(e)

    def chooseFile(self):
        """
        user interaction with saving file
        """
        path = self.save_as_lineEdit.text()
        if path == "":
            try:
                path = constants.directory_lineEdit
            except:
                path = os.path.expanduser("~")

        nameFilters = [constants.SUPPORTED_EXTENSIONS[extension] for extension in constants.SUPPORTED_EXTENSIONS]
        filters = ";;".join(nameFilters)
        name, ext = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', path, filters, "",
                                                          QtWidgets.QFileDialog.DontUseNativeDialog)
        if name != "":
            ext = ext[-5:-1]
            if ext in name:
                pass
            else:
                name += ext
            self.save_as_lineEdit.setText(common.unicodePath(name))
            self.setSaveAs()

    def clearPlot(self):
        if self.data_ring != None:
            self.data_ring.save()
            self.data_ring.clear()
            for plot in self.plot_lines:
                plot.setData([], [])

    def cleanPort(self):
        if self.streaming:
            self.startAcquisition()

        if self.port_name != None:
            abacus.close(self.port_name)
            self.port_name = None
            self.data_ring = None
            self.setNumberChannels(0)
            self.subSettings(new=False)
            self.check_timer.stop()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                                               quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                if self.data_ring != None:
                    self.data_ring.save()
                self.writeGuiSettings()
            except Exception as e:
                if abacus.constants.DEBUG: print(e)
            if self.results_files != None:
                if self.results_files.data_file.isEmpty():
                    self.results_files.params_file.delete()
            try:
                self.settings_dialog.constantsWriter(update_parent=False)
            except Exception as e:
                if abacus.constants.DEBUG: print(e)
            event.accept()
        else:
            event.ignore()

    def checkSpinboxFocus(self):
        if self.coincidence_spinBox.hasFocus():
            self.lose_focus_timer.start(5000)
        for widget in self.delay_widgets:
            if widget.hasFocus(): self.lose_focus_timer.start(5000)
        for widget in self.sleep_widgets:
            if widget.hasFocus(): self.lose_focus_timer.start(5000)

    def spinboxLoseFocus(self):
        self.coincidence_spinBox.clearFocus()
        for widget in self.delay_widgets:
            widget.clearFocus()
        for widget in self.sleep_widgets:
            widget.clearFocus()
        self.lose_focus_timer.stop()

    def coincidenceWindowMethod(self, value):
        self.coincidence_spinBox.setKeyboardTracking(False)
        value_is_valid = self.checkSpinboxValue(value)
        last_value = self.last_valid_value_coincidence_window
        last_step = self.computeSpinboxStep(last_value)
        limits_of_ranges = (10,100,1000,10000)

        if not value_is_valid: 
            value = self.findValidValueForCoincidenceWindow(value)
            step = self.computeSpinboxStep(value)
            self.coincidence_spinBox.setValue(value)
        elif last_value in limits_of_ranges and value == last_value - last_step:
            step = self.computeSpinboxStep(value)
            value = last_value - step
            self.coincidence_spinBox.setValue(value)
        else:
            step = self.computeSpinboxStep(value)

        self.coincidence_spinBox.setSingleStep(step)        

        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'coincidence_window', value)
                self.writeParams("Coincidence Window (ns), %s" % value)
                self.last_valid_value_coincidence_window = value
            except abacus.InvalidValueError:
                self.coincidence_spinBox.setStyleSheet("color: rgb(255,0,0); selection-background-color: rgb(255,0,0)")
            except serial.serialutil.SerialException:
                self.errorWindow(e)
        elif abacus.constants.DEBUG:
            print("Coincidence Window Value: %d" % value)
        try:
            #self.sleepSweepDialog.setCoincidence(value)
            self.delaySweepDialog.setCoincidence(value)
        except AttributeError:
            pass

    def checkSpinboxValue(self, val):
        """ Checks if val is a valid value based on the range it's is and the resolution
            of the device """
        validValue = False
        if val > 1000 and val <= 10000:
            validValue = val % 100 == 0
        elif val > 100 and val <= 1000:
            validValue = val % 10 == 0
        elif val > 10 and val <= 100:
            if abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE != 1:
                validValue = val % abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE == 0
            else: # For devices with 1 ns resolution
                validValue = val % 2 == 0
        else:
            validValue = val % abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE == 0
        return validValue

    def computeSpinboxStep(self, value):
        step = 10 ** int(np.log10(value) - 1)
        if step < 10 and value >= 10: 
            step = max(2, abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE)
        if step < 10 and value < 10: 
            step = abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE
        return step

    def findValidValueForCoincidenceWindow(self, val):
        temp_val = val
        num_of_digits = int(np.log10(val))+1
        if num_of_digits == 1:
            val = val - val % abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE
        elif num_of_digits == 2:
            val = val//(10**(num_of_digits-1))*(10**(num_of_digits-1))
            step = self.computeSpinboxStep(val)
            adder = (temp_val % val)//step * step
            val = val + adder
        elif num_of_digits >= 3:
            val = val//(10**(num_of_digits-2))*(10**(num_of_digits-2))
        return val

    def connect(self):
        if self.port_name != None:
            self.connect_button.setText("Connect")
            self.acquisition_button.setDisabled(True)
            if self.results_files != None:
                self.results_files.writeParams("Disconnected from device in port,%s" % self.port_name)
            self.cleanPort()
            self.statusBar.setStyleSheet("")
            self.statusBar.showMessage("")
            abacus.setStatusMessage("")
            self.tabs_widget.clearMultipleChecked()
            self.tabs_widget.multiple_tab_top.currentWindowButton.setEnabled(False)
            self.tabs_widget.double_tab_top.currentWindowButton.setEnabled(False)
            self.tabs_widget.single_tab_top.currentWindowButton.setEnabled(False)
            self.tabs_widget.multiple_tab_top.plotWindowButton.setEnabled(False)
            self.tabs_widget.double_tab_top.plotWindowButton.setEnabled(False)
            self.tabs_widget.single_tab_top.plotWindowButton.setEnabled(False)
        else:
            self.connect_dialog = ConnectDialog(self)
            self.connect_dialog.refresh()
            self.connect_dialog.exec_()

            port = self.connect_dialog.comboBox.currentText()

            if port != "":
                try:
                    abacus.open(port)
                except abacus.AbacusError:
                    pass
                n = abacus.getChannelsFromName(port)
                self.combinations = getCombinations(n)

                self.setNumberChannels(n)
                self.acquisition_button.setDisabled(False)
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.connect_button.setText("Disconnect")

                self.subSettings(new=False)

                self.data_ring = RingBuffer(constants.BUFFER_ROWS, len(self.combinations) + 2, self.combinations)
                if self.results_files != None:
                    self.data_ring.setFile(self.results_files.data_file)

                self.port_name = port  # not before
                self.writeParams("Connected to device in port, %s" % self.port_name)
                self.updateConstants()
                self.check_timer.start()

                if self.port_name not in self.devices_used.keys():
                    self.devices_used[self.port_name] = []
                    self.tabs_widget.simplyCheck(["A", "B", "AB"])
                else:
                    channels = self.devices_used[self.port_name]
                    self.tabs_widget.simplyCheck(channels)
            else:
                self.connect_button.setText("Connect")
                self.acquisition_button.setDisabled(True)
                self.statusBar.setStyleSheet("")
                self.statusBar.showMessage("")
                
            abacus.setStatusMessage("")

        self.tabs_widget.updateBtnsStatus()

    def delayMethod(self, widget, letter, val):
        widget.setKeyboardTracking(False)

        # If the spinbox value is not a multiple of the minimum resolution it will try to set a correct value that is close
        if not val % abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE == 0: 
            val = self.findValidValueForCoincidenceWindow(val)

        widget.setValue(val)

        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'delay_%s' % letter, val)
                self.writeParams("Delay %s (ns), %s" % (letter, val))
                widget.setStyleSheet("")
            except abacus.InvalidValueError:
                widget.setStyleSheet("color: rgb(255,0,0); selection-background-color: rgb(255,0,0)")
            except SerialException as e:
                self.errorWindow(e)
        elif abacus.constants.DEBUG:
            print("Delay %s Value: %d" % (letter, val))

    def delaySweep(self):
        self.delaySweepDialog.updateConstants() #new on v1.4.0 (2020-06-30)
        self.delaySweepDialog.show()

    def showInformationDialog(self, exception, title):
        information_text = str(exception)
        dialog = QtWidgets.QMessageBox()
        dialog.setIcon(QtWidgets.QMessageBox.Information)
        dialog.setWindowTitle(title)
        dialog.setText(information_text)
        dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        dialog.exec_()

    def errorWindow(self, exception):
        error_text = str(exception)
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        type_ = type(exception)

        if (type_ is SerialException) or (type_ is SerialTimeoutException):
            self.stopClocks()
            self.cleanPort()
            self.streaming = False
            self.acquisition_button.setDisabled(True)
            self.acquisition_button.setStyleSheet("background-color: red")
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            self.connect_button.setText("Connect")
        try:
            self.results_files.writeParams("Error,%s" % error_text)
        except Exception:
            pass

        msg.setText('An Error has occurred.\n%s' % error_text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def getLetter(self, i):
        return chr(i + ord('A'))

    def handleViews(self, q):
        text = q.text()
        button = None
        if "Show" in text:
            for action in self.menuView.actions():
                if text == action.text():
                    text = text[5:]
                    if "current" in text and ("single" in text or "double" in text or "multiple" in text):
                        text_complement = text[8:]
                        subwindow = getattr(self, "subwindow_current_%s" % text_complement)
                        if "single" in text:
                            button = self.tabs_widget.single_tab_top.currentWindowButton
                        elif "double" in text:
                            button = self.tabs_widget.double_tab_top.currentWindowButton
                        elif "multiple" in text:
                            button = self.tabs_widget.multiple_tab_top.currentWindowButton
                    elif "plots" in text and ("single" in text or "double" in text or "multiple" in text):
                        text_complement = text[6:]
                        subwindow = getattr(self, "subwindow_plots_%s" % text_complement)
                        if "single" in text:
                            button = self.tabs_widget.single_tab_top.plotWindowButton
                        elif "double" in text:
                            button = self.tabs_widget.double_tab_top.plotWindowButton
                        elif "multiple" in text:
                            button = self.tabs_widget.multiple_tab_top.plotWindowButton  
                    else:
                        subwindow = getattr(self, "subwindow_%s" % text)

                    if subwindow == self.subwindow_current: 
                        button = self.tabs_widget.btn_all_currents_subwindow
                    elif subwindow == self.subwindow_plots: 
                        button = self.tabs_widget.btn_all_plots_subwindow
                    
                    check = not action.isChecked() 
                    if check:
                        action.setChecked(False)
                        subwindow.hide()
                        self.mdi.tileSubWindows()
                        if button != None and button.isCheckable(): 
                            button.setChecked(False)
                    else:
                        action.setChecked(True)
                        if subwindow not in self.mdi.subWindowList(): 
                            self.mdi.addSubWindow(subwindow)
                        subwindow.show()
                        self.mdi.tileSubWindows()
                        if button != None and button.isCheckable(): 
                            button.setChecked(True)

        elif text == "Cascade":
            self.mdi.cascadeSubWindows()

        elif text == "Tiled":
            self.mdi.tileSubWindows()

        elif text == "Default layout":
            # Hide unwanted subwindows
            self.subwindow_current_single.hide()
            self.subwindow_current_double.hide()
            self.subwindow_current_multiple.hide()
            self.subwindow_plots_single.hide()
            self.subwindow_plots_double.hide()
            self.subwindow_plots_multiple.hide()

            # Show default subwindows
            self.subwindow_plots.show()
            self.subwindow_current.show()
            self.subwindow_historical.show()
            self.subwindow_settings.show()

            # Update buttons state
            self.tabs_widget.btn_all_plots_subwindow.setChecked(True)
            self.tabs_widget.btn_all_currents_subwindow.setChecked(True)
            self.tabs_widget.single_tab_top.plotWindowButton.setChecked(False)
            self.tabs_widget.double_tab_top.plotWindowButton.setChecked(False)
            self.tabs_widget.multiple_tab_top.plotWindowButton.setChecked(False)
            self.tabs_widget.single_tab_top.currentWindowButton.setChecked(False)
            self.tabs_widget.double_tab_top.currentWindowButton.setChecked(False)
            self.tabs_widget.multiple_tab_top.currentWindowButton.setChecked(False)
            self.mdi.tileSubWindows()

            # Update menuView actions checkboxes
            for action in self.menuView.actions():
                text = action.text()
                if text == "Show settings" or text == "Show historical" or text == "Show current" or text == "Show plots":
                    action.setChecked(True)
                else:
                    action.setChecked(False)

        elif 'theme' in text:
            if 'Dark theme' == text:
                self.setDarkTheme()
            else:
                self.setLightTheme()

    def initial(self):
        self.__sleep_timer__.stop()
        self.connect()

    def initPlots(self):
        self.removePlots()  

        if not constants.IS_LIGHT_THEME:
            nColors = len(constants.DARK_COLORS)
        else:
            nColors = len(constants.COLORS)

        nSymbols = len(constants.SYMBOLS)

        for i,channel in enumerate(self.active_channels):
            if constants.IS_LIGHT_THEME:
                color, symbol = self.chooseChannelColorAndSymbol(channel, constants.COLORS, self.light_colors_in_use, constants.SYMBOLS)
            else:
                color, symbol = self.chooseChannelColorAndSymbol(channel, constants.DARK_COLORS, self.dark_colors_in_use, constants.SYMBOLS)

            letter = self.active_channels[i]
            pen = pg.mkPen(color, width=self.linewidth)
            plot = self.counts_plot.plot(pen=pen, symbol=symbol,
                                         symbolPen=color, symbolBrush=color,
                                         symbolSize=self.symbolSize, name=letter)
            self.plot_lines.append(plot)

        if constants.IS_LIGHT_THEME: 
            legend_color = QtGui.QColor('#000000')
            legend_border = QtGui.QColor('#000000')
        else: 
            legend_color = QtGui.QColor('#ffffff')
            legend_border = QtGui.QColor('#ffffff')

        self.legend = self.counts_plot.addLegend(verSpacing=-8, labelTextColor=legend_color)
        self.legend.setLabelTextColor(legend_color)
        self.legend.setParentItem(self.counts_plot)
        self.legend.anchor(itemPos=(1,0), parentPos=(1,0), offset=(22,-15))

        # Plots single
        for i,channel in enumerate(self.active_channels_single):
            if not constants.IS_LIGHT_THEME:
                #color = constants.DARK_COLORS[i % nColors]
                color = self.dark_colors_in_use[channel][0]
                symbol = self.dark_colors_in_use[channel][1]
            else:
                #color = constants.COLORS[i % nColors]
                color = self.light_colors_in_use[channel][0]
                symbol = self.light_colors_in_use[channel][1]
            #symbol = constants.SYMBOLS[i % nSymbols]
            letter = self.active_channels_single[i]
            pen = pg.mkPen(color, width=self.linewidth)
            plot = self.counts_plot_single.plot(pen=pen, symbol=symbol,
                                         symbolPen=color, symbolBrush=color,
                                         symbolSize=self.symbolSize, name=letter)
            self.plot_lines_single.append(plot)

        self.legend_single = self.counts_plot_single.addLegend(verSpacing=-8, labelTextColor=legend_color)
        self.legend_single.setLabelTextColor(legend_color)
        #self.legend.setPen(legend_border)
        self.legend_single.setParentItem(self.counts_plot_single)
        self.legend_single.anchor(itemPos=(1,0), parentPos=(1,0), offset=(17,-15))

        # Plots double
        for i,channel in enumerate(self.active_channels_double):
            if not constants.IS_LIGHT_THEME:
                #color = constants.DARK_COLORS[i % nColors]
                color = self.dark_colors_in_use[channel][0]
                symbol = self.dark_colors_in_use[channel][1]
            else:
                #color = constants.COLORS[i % nColors]
                color = self.light_colors_in_use[channel][0]
                symbol = self.light_colors_in_use[channel][1]
            #symbol = constants.SYMBOLS[i % nSymbols]
            letter = self.active_channels_double[i]
            pen = pg.mkPen(color, width=self.linewidth)
            plot = self.counts_plot_double.plot(pen=pen, symbol=symbol,
                                         symbolPen=color, symbolBrush=color,
                                         symbolSize=self.symbolSize, name=letter)
            self.plot_lines_double.append(plot)

        self.legend_double = self.counts_plot_double.addLegend(verSpacing=-8, labelTextColor=legend_color)
        self.legend_double.setLabelTextColor(legend_color)
        #self.legend.setPen(legend_border)
        self.legend_double.setParentItem(self.counts_plot_double)
        self.legend_double.anchor(itemPos=(1,0), parentPos=(1,0), offset=(20,-15))

        # Plots multiple
        for i,channel in enumerate(self.active_channels_multiple):
            if not constants.IS_LIGHT_THEME:
                #color = constants.DARK_COLORS[i % nColors]
                color = self.dark_colors_in_use[channel][0]
                symbol = self.dark_colors_in_use[channel][1]
            else:
                #color = constants.COLORS[i % nColors]
                color = self.light_colors_in_use[channel][0]
                symbol = self.light_colors_in_use[channel][1]
            #symbol = constants.SYMBOLS[i % nSymbols]
            letter = self.active_channels_multiple[i]
            pen = pg.mkPen(color, width=self.linewidth)
            plot = self.counts_plot_multiple.plot(pen=pen, symbol=symbol,
                                         symbolPen=color, symbolBrush=color,
                                         symbolSize=self.symbolSize, name=letter)
            self.plot_lines_multiple.append(plot)

        self.legend_multiple = self.counts_plot_multiple.addLegend(verSpacing=-8, labelTextColor=legend_color)
        self.legend_multiple.setLabelTextColor(legend_color)
        #self.legend.setPen(legend_border)
        self.legend_multiple.setParentItem(self.counts_plot_multiple)
        self.legend_multiple.anchor(itemPos=(1,0), parentPos=(1,0), offset=(22,-15))

    def chooseChannelColorAndSymbol(self, channel, palette, colors_in_use, symbols):
        new_color = None
        new_symbol = None

        nColors = len(palette)
        nSymbols = len(symbols)

        if channel in colors_in_use:
            new_color = colors_in_use[channel][0]
            new_symbol = colors_in_use[channel][1]
        elif not any(colors_in_use.keys()):
            new_color = palette[0]
            new_symbol = symbols[0]
        else:
            channels_in_category = [chann for chann in colors_in_use.keys() if len(chann) == len(channel)]
            if len(channels_in_category) == 0:
                if len(channel) == 2:
                    last_color_used = palette[self.number_channels-1]
                    last_symbol_used = symbols[self.number_channels-1]
                elif len(channel) == 3 or len(channel) == 4:
                    last_color_used = palette[-2]
                    last_symbol_used = symbols[-2]
                else:
                    last_color_used, last_symbol_used = list(colors_in_use.values())[-1]
            else:
                last_color_used = colors_in_use[channels_in_category[-1]][0]
                last_symbol_used = colors_in_use[channels_in_category[-1]][1]
            if last_color_used in palette:
                index_color = palette.index(last_color_used)
            else: # if the last color used is a custom color, it will not be in the color pallete list. Therefore a random index should be used
                index_color = np.random.randint(0, nColors)
            index_symbol = symbols.index(last_symbol_used)
            if index_color == (nColors - 1): # in case the last color used is the last in the color pallete list, then the next color will be the first in the pallete list
                index_color = -1
            if index_symbol == (nSymbols - 1): 
                index_symbol = -1
            new_color = palette[index_color + 1]
            new_symbol = symbols[index_symbol + 1]
        colors_in_use[channel] = [new_color, new_symbol]

        return new_color, new_symbol

    def removePlots(self):
        if self.legend != None:
            if self.legend.scene() != None:  #new on v1.4.0 (2020-06-23). This solves the issue of not reconnecting to a device after disconnection.
                self.legend.scene().removeItem(self.legend)
        self.counts_plot.clear()
        self.counts_plot_single.clear()
        self.counts_plot_double.clear()
        self.counts_plot_multiple.clear()
        self.plot_lines = []
        self.plot_lines_single = []
        self.plot_lines_double = []
        self.plot_lines_multiple = []

    def samplingMethod(self, value, force_write=False):
        if self.sampling_widget != None:
            if force_write: self.sampling_widget.setValue(value)
            value = self.sampling_widget.getValue()
            if value > 0 and self.port_name != None:
                try:
                    abacus.setSetting(self.port_name, 'sampling', value)
                    if value > (constants.DATA_REFRESH_RATE*10):
                        self.refresh_timer.setInterval(int(value*0.1)) #v1.6.0: cast to int
                    else:
                        self.refresh_timer.setInterval(constants.DATA_REFRESH_RATE)
                    # 27-sept-2021 The following if-else block was added to prevent the app from crashing.
                    # Previously, only the line after the else was included. Therefore, when sampling times
                    # shorter than 20 ms where chosen, self.data_timer was assigned a small interval which 
                    # caused the function updateData to be called indefinitely and the app would crash.
                    # Something inside the functions writeGuiSettings() and readGuiSettings() is probably causing this
                    if value < 100:
                        self.data_timer.setInterval(100)
                    else:
                        self.data_timer.setInterval(value)
                    self.writeParams("Sampling time (ms), %s" % value)
                # except abacus.InvalidValueError as e:
                #     self.sampling_widget.invalid()
                except SerialException as e:
                    self.errorWindow(e)
            elif abacus.constants.DEBUG:
                print("Sampling Value, %d" % value)
        try:
            self.sleepSweepDialog.setSampling(value)
            self.delaySweepDialog.setSampling(value)
        except AttributeError:
            pass

    def sendMultipleCoincidences(self, coincidences):
        if self.port_name != None:
            try:
                for (i, letters) in enumerate(coincidences):
                    abacus.setSetting(self.port_name, 'config_custom_c%d' % (i + 1), letters)
            except SerialException as e:
                # except Exception as e:
                self.errorWindow(e)

    def getCustomSettingsNumber(self, letters):
        settings = abacus.getAllSettings(self.port_name)
        for i in range(8):
            custom = settings.getSetting("config_custom_c%d" % (i + 1))
            if letters == custom:
                return i+1

    def sendSettings(self):
        self.samplingMethod(self.sampling_widget.getValue())
        self.coincidenceWindowMethod(self.coincidence_spinBox.value())

        for i in range(self.number_channels):
            letter = self.getLetter(i)
            delay_widget = self.delay_widgets[i]
            sleep_widget = self.sleep_widgets[i]
            self.delayMethod(delay_widget, letter, delay_widget.value())
            self.sleepMethod(sleep_widget, letter, sleep_widget.value())

    def setNumberChannels(self, n):
        self.number_channels = n
        self.tabs_widget.setNumberChannels(n)
        self.sampling_widget.changeNumberChannels(n)
        self.delaySweepDialog.setNumberChannels(n)
        self.sleepSweepDialog.setNumberChannels(n)
        self.tabs_widget.signal()

    def setDarkTheme(self):
        constants.IS_LIGHT_THEME = False
        self.initPlots()
        self.initPlots() # (26-09-2021) initPlots() need to be called twice for the legends to have the correct colors, but this shouldn't be the case
        self.plot_win.setBackground((42, 42, 42))
        self.plot_win_single.setBackground((42, 42, 42))
        self.plot_win_double.setBackground((42, 42, 42))
        self.plot_win_multiple.setBackground((42, 42, 42))
        whitePen = pg.mkPen(color=(255, 255, 255))
        self.counts_plot.getAxis('bottom').setPen(whitePen)
        self.counts_plot.getAxis('left').setPen(whitePen)
        self.counts_plot.getAxis('bottom').setTextPen(whitePen)
        self.counts_plot.getAxis('left').setTextPen(whitePen)

        self.counts_plot_single.getAxis('bottom').setPen(whitePen)
        self.counts_plot_single.getAxis('left').setPen(whitePen)
        self.counts_plot_single.getAxis('bottom').setTextPen(whitePen)
        self.counts_plot_single.getAxis('left').setTextPen(whitePen)

        self.counts_plot_double.getAxis('bottom').setPen(whitePen)
        self.counts_plot_double.getAxis('left').setPen(whitePen)
        self.counts_plot_double.getAxis('bottom').setTextPen(whitePen)
        self.counts_plot_double.getAxis('left').setTextPen(whitePen)

        self.counts_plot_multiple.getAxis('bottom').setPen(whitePen)
        self.counts_plot_multiple.getAxis('left').setPen(whitePen)
        self.counts_plot_multiple.getAxis('bottom').setTextPen(whitePen)
        self.counts_plot_multiple.getAxis('left').setTextPen(whitePen)

        self.theme_action.setText('Light theme')
        self.delaySweepDialog.setDarkTheme()
        self.sleepSweepDialog.setDarkTheme()

        self.current_labels.createLabels(self.active_channels, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels.clearSizes()
        self.current_labels.resizeEvent(None)

        self.current_labels_single.createLabels(self.active_channels_single, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_single.clearSizes()
        self.current_labels_single.resizeEvent(None)

        self.current_labels_double.createLabels(self.active_channels_double, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_double.clearSizes()
        self.current_labels_double.resizeEvent(None)

        self.current_labels_multiple.createLabels(self.active_channels_multiple, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_multiple.clearSizes()
        self.current_labels_multiple.resizeEvent(None)

        self.updateWidgets()

        self.tabs_widget.changeButtonsIcons()
        self.mdi.setBackground(QtGui.QBrush(QtGui.QColor("#353535")))

        qtmodern.styles.dark(app)

    def setLightTheme(self):
        constants.IS_LIGHT_THEME = True
        self.initPlots()
        self.initPlots() # (26-09-2021) initPlots() needs to be called twice for the legends to have the correct colors, but this shouldn't be the case
        self.theme_action.setText('Dark theme')
        qtmodern.styles.light(app)

        self.plot_win.setBackground(None)
        self.plot_win_single.setBackground(None)
        self.plot_win_double.setBackground(None)
        self.plot_win_multiple.setBackground(None)
        blackPen = pg.mkPen(color=(0, 0, 0))
        self.counts_plot.getAxis('bottom').setPen(blackPen)
        self.counts_plot.getAxis('left').setPen(blackPen)
        self.counts_plot.getAxis('bottom').setTextPen(blackPen)
        self.counts_plot.getAxis('left').setTextPen(blackPen)

        self.counts_plot_single.getAxis('bottom').setPen(blackPen)
        self.counts_plot_single.getAxis('left').setPen(blackPen)
        self.counts_plot_single.getAxis('bottom').setTextPen(blackPen)
        self.counts_plot_single.getAxis('left').setTextPen(blackPen)

        self.counts_plot_double.getAxis('bottom').setPen(blackPen)
        self.counts_plot_double.getAxis('left').setPen(blackPen)
        self.counts_plot_double.getAxis('bottom').setTextPen(blackPen)
        self.counts_plot_double.getAxis('left').setTextPen(blackPen)

        self.counts_plot_multiple.getAxis('bottom').setPen(blackPen)
        self.counts_plot_multiple.getAxis('left').setPen(blackPen)
        self.counts_plot_multiple.getAxis('bottom').setTextPen(blackPen)
        self.counts_plot_multiple.getAxis('left').setTextPen(blackPen)

        self.delaySweepDialog.setLightTheme()
        self.sleepSweepDialog.setLightTheme()

        self.current_labels.createLabels(self.active_channels, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels.clearSizes()
        self.current_labels.resizeEvent(None)

        self.current_labels_single.createLabels(self.active_channels_single, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_single.clearSizes()
        self.current_labels_single.resizeEvent(None)

        self.current_labels_double.createLabels(self.active_channels_double, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_double.clearSizes()
        self.current_labels_double.resizeEvent(None)

        self.current_labels_multiple.createLabels(self.active_channels_multiple, self.light_colors_in_use, self.dark_colors_in_use)
        self.current_labels_multiple.clearSizes()
        self.current_labels_multiple.resizeEvent(None)

        self.updateWidgets()

        self.tabs_widget.changeButtonsIcons()
        self.mdi.setBackground(QtGui.QBrush(QtGui.QColor("#f0f0f0")))

    def setSaveAs(self):
        new_file_name = self.save_as_lineEdit.text()
        try:
            if new_file_name != "":
                try:
                    name, ext = self.checkFileName(new_file_name)
                    if self.results_files == None:
                        self.results_files = ResultsFiles(name, ext, self.init_date)
                        self.results_files.params_file.header += self.params_buffer
                        self.params_buffer = ""
                    else:
                        self.results_files.changeName(name, ext)
                    names = self.results_files.getNames()
                    if self.data_ring != None:
                        self.data_ring.setFile(self.results_files.data_file)
                    self.statusBar.showMessage('Files: %s, %s.' % (names))
                    self.statusBarMessage = self.statusBar.currentMessage()
                    try:
                        self.results_files.checkFilesExists()
                    except FileExistsError:
                        if abacus.constants.DEBUG:
                            print("FileExistsError on setSaveAs")
                except ExtentionError as e:
                    self.save_as_lineEdit.setText("")
                    self.errorWindow(e)
            elif abacus.constants.DEBUG:
                print("EmptyName on setSaveAs")
        except FileNotFoundError as e:
            self.errorWindow(e)

    def setSettings(self):
        common.setCoincidenceSpinBox(self.coincidence_spinBox)
        for widget in self.delay_widgets:
            common.setDelaySpinBox(widget)
        for widget in self.sleep_widgets:
            common.setSleepSpinBox(widget)

    def settingsDialogCaller(self):
        self.settings_dialog.show()

    def show2(self):
        self.show()

        self.__sleep_timer__ = QtCore.QTimer()
        self.__sleep_timer__.setInterval(10)
        self.__sleep_timer__.timeout.connect(self.initial)
        self.__sleep_timer__.start()

    def sleepMethod(self, widget, letter, val):
        widget.setKeyboardTracking(False)

        # If the spinbox value is not a multiple of the minimum resolution it will try to set a correct value that is close
        if not val % abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE == 0: 
            val = self.findValidValueForCoincidenceWindow(val)

        widget.setValue(val)

        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'sleep_%s' % letter, val)
                self.writeParams("Sleep %s (ns), %s" % (letter, val))
                widget.setStyleSheet("")
            except abacus.InvalidValueError:
                widget.setStyleSheet("color: rgb(255,0,0); selection-background-color: rgb(255,0,0)")
            except SerialException as e:
                self.errorWindow(e)
        elif abacus.constants.DEBUG:
            print("Sleep %s Value: %d" % (letter, val))

    def sleepSweep(self):
        self.sleepSweepDialog.updateConstants() #new on v1.4.0 (2020-06-30)
        self.sleepSweepDialog.show()

    def startAcquisition(self):
        if self.port_name == None:
            QtWidgets.QMessageBox.warning(self, 'Error', "Port has not been choosed", QtWidgets.QMessageBox.Ok)
        elif self.results_files != None:
            self.streaming = not self.streaming
            if not self.streaming:
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.reset_time_button.setEnabled(False)
                self.results_files.writeParams("Acquisition stopped")
                self.unlockSettings()
                self.stopClocks()
            else:
                self.acquisition_button.setStyleSheet("background-color: green")
                self.acquisition_button.setText("Stop acquisition")
                self.reset_time_button.setEnabled(True)
                self.results_files.writeParams("Acquisition started")
                self.sendSettings()
                self.unlockSettings(False)
                self.startClocks()

            if self.init_time == 0:
                self.init_time = time()
        else:
            default_directory = self.getWorkingDirectory()
            path = default_directory +"/abacusdata" + strftime("_%Y%m%d_%H%M") + ".dat"
            nameFilters = [constants.SUPPORTED_EXTENSIONS[extension] for extension in constants.SUPPORTED_EXTENSIONS]
            filters = ";;".join(nameFilters)
            name, ext = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', path, filters, "",
                                                          QtWidgets.QFileDialog.DontUseNativeDialog)
            if name != "":
                ext = ext[-5:-1]
                if ext in name:
                    pass
                else:
                    name += ext
                self.save_as_lineEdit.setText(common.unicodePath(name))
                self.setSaveAs()
                self.settings_dialog.directory_lineEdit.setText(common.unicodePath(default_directory))
                self.startAcquisition()

    def startClocks(self):
        self.refresh_timer.start()
        self.data_timer.start()

    def stopClocks(self):
        self.refresh_timer.stop()
        self.data_timer.stop()
        try:
            self.data_ring.save()
        except FileNotFoundError as e:
            self.errorWindow(e)

    def subCurrent(self):
        widget = QWidget()
        self.current_labels = CurrentLabels(widget)
        self.subwindow_current = SubWindow(self)
        # self.subwindow_current.setMinimumSize(200, 100)
        self.subwindow_current.setWidget(widget)
        self.subwindow_current.setWindowTitle("Current")
        self.mdi.addSubWindow(self.subwindow_current)

    def subCurrentSingle(self):
        widget = QWidget()
        self.current_labels_single = CurrentLabels(widget)
        self.subwindow_current_single = SubWindow(self)
        self.subwindow_current_single.setWidget(widget)
        self.subwindow_current_single.setWindowTitle("Current single")
        self.mdi.addSubWindow(self.subwindow_current_single)

    def subCurrentDouble(self):
        widget = QWidget()
        self.current_labels_double = CurrentLabels(widget)
        self.subwindow_current_double = SubWindow(self)
        self.subwindow_current_double.setWidget(widget)
        self.subwindow_current_double.setWindowTitle("Current double")
        self.mdi.addSubWindow(self.subwindow_current_double)

    def subCurrentMultiple(self):
        widget = QWidget()
        self.current_labels_multiple = CurrentLabels(widget)
        self.subwindow_current_multiple = SubWindow(self)
        self.subwindow_current_multiple.setWidget(widget)
        self.subwindow_current_multiple.setWindowTitle("Current multiple")
        self.mdi.addSubWindow(self.subwindow_current_multiple)

    def subHistorical(self):
        widget = QWidget()
        self.historical_table = Table([], [])
        self.historical_layout = QVBoxLayout(widget)

        self.historical_layout.setSpacing(0)
        self.historical_layout.setContentsMargins(0, 0, 0, 0)

        self.historical_layout.addWidget(self.historical_table)

        self.subwindow_historical = SubWindow(self)
        self.subwindow_historical.setWidget(widget)
        self.subwindow_historical.setWindowTitle("Historical")
        self.mdi.addSubWindow(self.subwindow_historical)

    def subPlots(self):
        pg.setConfigOptions(antialias=True, foreground='k')

        self.subwindow_plots = SubWindow(self)
        self.plot_win = pg.GraphicsWindow()
        self.subwindow_plots.layout().setSpacing(0)
        self.subwindow_plots.layout().setContentsMargins(0,0,0,0)
        self.subwindow_plots.layout().addWidget(self.plot_win)
        self.subwindow_plots.setWindowTitle("Plots")
        self.mdi.addSubWindow(self.subwindow_plots)

    def subPlotsSingle(self):
        pg.setConfigOptions(antialias=True, foreground='k')

        self.subwindow_plots_single = SubWindow(self)
        self.plot_win_single = pg.GraphicsWindow()
        self.subwindow_plots_single.layout().setSpacing(0)
        self.subwindow_plots_single.layout().setContentsMargins(0,0,0,0)
        self.subwindow_plots_single.layout().addWidget(self.plot_win_single)
        self.subwindow_plots_single.setWindowTitle("Plots single")
        self.mdi.addSubWindow(self.subwindow_plots_single)

    def subPlotsDouble(self):
        pg.setConfigOptions(antialias=True, foreground='k')

        self.subwindow_plots_double = SubWindow(self)
        self.plot_win_double = pg.GraphicsWindow()
        self.subwindow_plots_double.layout().setSpacing(0)
        self.subwindow_plots_double.layout().setContentsMargins(0,0,0,0)
        self.subwindow_plots_double.layout().addWidget(self.plot_win_double)
        self.subwindow_plots_double.setWindowTitle("Plots double")
        self.mdi.addSubWindow(self.subwindow_plots_double)

    def subPlotsMultiple(self):
        pg.setConfigOptions(antialias=True, foreground='k')

        self.subwindow_plots_multiple = SubWindow(self)
        self.plot_win_multiple = pg.GraphicsWindow()
        self.subwindow_plots_multiple.layout().setSpacing(0)
        self.subwindow_plots_multiple.layout().setContentsMargins(0,0,0,0)
        self.subwindow_plots_multiple.layout().addWidget(self.plot_win_multiple)
        self.subwindow_plots_multiple.setWindowTitle("Plots multiple")
        self.mdi.addSubWindow(self.subwindow_plots_multiple)

    def configPlot(self):
        if self.data_ring != None:
            iconWidth = 100
            iconHeight = 20
            iconSize = QtCore.QSize(iconWidth, iconHeight)
            img = QtGui.QImage(iconWidth,iconHeight,QtGui.QImage.Format_RGB32)
            painter = QtGui.QPainter(img)
            painter.fillRect(img.rect(), QtCore.Qt.lightGray)
            rect = img.rect().adjusted(1,1,-1,-1)
            self.plot_config_dialog = PlotConfigsDialog(img, painter, rect, iconSize, self.plot_lines, 
                                                        self.light_colors_in_use, self.dark_colors_in_use, self)
            self.plot_config_dialog.exec_()

            self.initPlots()
            self.current_labels.createLabels(self.active_channels, self.light_colors_in_use, self.dark_colors_in_use)
            self.current_labels_single.createLabels(self.active_channels_single, self.light_colors_in_use, self.dark_colors_in_use)
            self.current_labels_double.createLabels(self.active_channels_double, self.light_colors_in_use, self.dark_colors_in_use)
            self.current_labels_multiple.createLabels(self.active_channels_multiple, self.light_colors_in_use, self.dark_colors_in_use)
            self.updateWidgets()

    def resetTime(self):
        self.reset_time_button_pressed = True
        self.updateData()
        self.reset_time_button_pressed = False
        self.clearPlot()

    def subSettings(self, new=True):
        def fillFormLayout(layout, values, new=True):
            for (i, line) in enumerate(values):
                if not new: i += 2
                layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
                layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

        def deleteWidgets(layout, widgets):
            for label, widget in widgets:
                layout.removeWidget(label)
                layout.removeWidget(widget)
                label.deleteLater()
                widget.deleteLater()

        def createWidgets():
            delays = []
            sleeps = []
            self.delay_widgets = []
            self.sleep_widgets = []
            for i in range(self.number_channels):
                letter = self.getLetter(i)
                delay_label = 'delay_%s_label' % letter
                delay_spinBox = 'delay_%s_spinBox' % letter
                sleep_label = 'sleep_%s_label' % letter
                sleep_spinBox = 'sleep_%s_spinBox' % letter

                setattr(self, delay_label, QLabel("Delay %s (ns):" % letter))
                setattr(self, delay_spinBox, QSpinBox())
                setattr(self, sleep_label, QLabel("Sleep %s (ns):" % letter))
                setattr(self, sleep_spinBox, QSpinBox())

                getattr(self, delay_spinBox).setToolTip("Press enter after editing with keyboard")
                getattr(self, sleep_spinBox).setToolTip("Press enter after editing with keyboard")

                getattr(self, delay_spinBox).setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                getattr(self, sleep_spinBox).setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                delays.append((getattr(self, delay_label), getattr(self, delay_spinBox)))
                sleeps.append((getattr(self, sleep_label), getattr(self, sleep_spinBox)))

                self.delay_widgets.append(getattr(self, delay_spinBox))
                self.sleep_widgets.append(getattr(self, sleep_spinBox))

            self.subSettings_delays_sleeps = delays + sleeps

            if self.number_channels == 2:
                self.delay_widgets[0].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.sleep_widgets[0].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
            elif self.number_channels == 4:
                self.delay_widgets[0].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.delay_widgets[2].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[2], 'C', arg))
                self.delay_widgets[3].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[3], 'D', arg))
                self.sleep_widgets[0].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
                self.sleep_widgets[2].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[2], 'C', arg))
                self.sleep_widgets[3].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[3], 'D', arg))
            elif self.number_channels == 8:
                self.delay_widgets[0].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.delay_widgets[2].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[2], 'C', arg))
                self.delay_widgets[3].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[3], 'D', arg))
                self.delay_widgets[4].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[4], 'E', arg))
                self.delay_widgets[5].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[5], 'F', arg))
                self.delay_widgets[6].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[6], 'G', arg))
                self.delay_widgets[7].valueChanged.connect(
                    lambda arg: self.delayMethod(self.delay_widgets[7], 'H', arg))
                self.sleep_widgets[0].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
                self.sleep_widgets[2].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[2], 'C', arg))
                self.sleep_widgets[3].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[3], 'D', arg))
                self.sleep_widgets[4].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[4], 'E', arg))
                self.sleep_widgets[5].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[5], 'F', arg))
                self.sleep_widgets[6].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[6], 'G', arg))
                self.sleep_widgets[7].valueChanged.connect(
                    lambda arg: self.sleepMethod(self.sleep_widgets[7], 'H', arg))

        if new:
            settings_frame = QFrame()
            settings_frame.setFrameShape(QFrame.StyledPanel)
            settings_frame.setFrameShadow(QFrame.Raised)
            settings_verticalLayout = QVBoxLayout(settings_frame)
            settings_verticalLayout.setContentsMargins(0, 0, 0, 0)
            settings_verticalLayout.setSpacing(0)

            scrollArea = QtWidgets.QScrollArea()
            scrollArea.setWidgetResizable(True)

            self.settings_frame2 = QFrame()
            self.settings_frame2.setFrameShape(QFrame.StyledPanel)
            self.settings_frame2.setFrameShadow(QFrame.Raised)

            settings_frame3 = QFrame()

            self.settings_frame2_formLayout = QtWidgets.QFormLayout(self.settings_frame2)
            settings_frame3_formLayout = QtWidgets.QFormLayout(settings_frame3)

            scrollArea.setWidget(self.settings_frame2)

            self.sampling_label = QLabel("Sampling time:")
            self.sampling_widget = SamplingWidget(self.settings_frame2_formLayout, \
                                                  self.sampling_label, self.samplingMethod)
            self.coincidence_label = QLabel("Coincidence window (ns):")
            self.coincidence_spinBox = QSpinBox()
            self.coincidence_spinBox.setToolTip("Press enter after editing with keyboard")
            self.coincidence_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            createWidgets()

            self.settings_frame2_formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.sampling_label)
            self.settings_frame2_formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.coincidence_label)
            self.settings_frame2_formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.coincidence_spinBox)

            self.unlock_settings_button = QPushButton("Unlock settings")
            self.unlock_settings_button.clicked.connect(lambda: self.unlockSettings(True))

            # fillFormLayout(self.settings_frame2_formLayout, widgets)
            settings_frame3_formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.unlock_settings_button)

            settings_verticalLayout.addWidget(scrollArea)
            settings_verticalLayout.addWidget(settings_frame3)

            self.subwindow_settings = SubWindow(self)
            self.subwindow_settings.setWidget(settings_frame)
            self.subwindow_settings.setWindowTitle("Settings")

            self.settings_frame2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.mdi.addSubWindow(self.subwindow_settings)
        else:
            deleteWidgets(self.settings_frame2_formLayout, self.subSettings_delays_sleeps)
            createWidgets()
            fillFormLayout(self.settings_frame2_formLayout, self.subSettings_delays_sleeps, new=False)

        # createSampling()
        self.setSettings()
        self.subwindow_settings.setTabOrder(self.sampling_widget.widget, self.coincidence_spinBox)
        

    def timeInUnitsToMs(self, time):
        value = 0
        if 'ms' in time:
            value = int(time.replace('ms', ''))
        elif 's' in time:
            value = int(time.replace('s', '')) * 1000
        return value

    def unlockSettings(self, unlock=True):
        self.sampling_widget.setEnabled(unlock)
        self.coincidence_spinBox.setEnabled(unlock)
        for widget in self.delay_widgets + self.sleep_widgets:
            widget.setEnabled(unlock)
        if unlock:
            self.unlock_settings_button.setEnabled(False)
        else:
            self.unlock_settings_button.setEnabled(True)

    def updateConstants(self):
        try:
            common.updateConstants(self)
            if constants.autogenerate_checkBox:
                file_name = constants.file_prefix_lineEdit
                if constants.datetime_checkBox: file_name += strftime("_%Y%m%d_%H%M")
                file_name += constants.extension_comboBox
                path = os.path.join(constants.directory_lineEdit, file_name)
                self.save_as_lineEdit.setText(common.unicodePath(path))
                self.setSaveAs()

            self.sampling_widget.setValue(constants.sampling_widget)
            self.sendSettings()

            if constants.theme_checkBox:
                self.setLightTheme()
            else:
                self.setDarkTheme()

            if self.data_ring != None: self.data_ring.updateDelimiter(constants.DELIMITER)

        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)

    def updateCurrents(self, data):
        for (pos, index) in enumerate(self.combination_indexes):
            self.current_labels.changeValue(pos, data[-1, index + 2])
        for pos, index in enumerate(self.combination_indexes[:len(self.active_channels_single)]):
            self.current_labels_single.changeValue(pos, data[-1, index + 2])
        for pos, index in enumerate(self.combination_indexes[len(self.active_channels_single):(len(self.active_channels_single)+len(self.active_channels_double))]):
            self.current_labels_double.changeValue(pos, data[-1, index + 2])
        for pos, index in enumerate(self.combination_indexes[(len(self.active_channels_single)+len(self.active_channels_double)):]):
            self.current_labels_multiple.changeValue(pos, data[-1, index + 2])

    def updateData(self):
        def get(counters, time_, id):
            last = 3
            if self.number_channels == 4:
                last = 10
            elif self.number_channels == 8:
                last = 36
            values = counters.getValues(self.combinations[:last])
            "could be better"
            if self.number_channels > 2:
                i = 1
                for letters in self.combinations[last:]:
                    if letters in self.active_channels:
                        val = counters.getValue("custom_c%d" % i)
                        i += 1
                    else:
                        val = -1
                    values.append(val)

            values = np.array([time_, id] + values)
            values = values.reshape((1, values.shape[0]))
            self.data_ring.extend(values)

        try:
            for i in range(constants.NUMBER_OF_TRIES):
                try:
                    data = self.data_ring[:]
                    if self.reset_time_button_pressed: self.init_time = time()
                    time_ = time() - self.init_time
                    time_range = self.plots_combo_box.currentText()
                    time_range = self.plots_time_options[time_range]
                    if type(time_range) == type(2):
                        self.counts_plot.setXRange(time_-time_range, time_ + 0.15*time_range)
                        self.counts_plot_single.setXRange(time_-time_range, time_+ 0.15*time_range)
                        self.counts_plot_double.setXRange(time_-time_range, time_+ 0.15*time_range)
                        self.counts_plot_multiple.setXRange(time_-time_range, time_+ 0.15*time_range)
                    else:
                        self.counts_plot.setXRange(0, time_ + 0.15*time_)
                        self.counts_plot_single.setXRange(0, time_ + 0.15*time_)
                        self.counts_plot_double.setXRange(0, time_ + 0.15*time_)
                        self.counts_plot_multiple.setXRange(0, time_ + 0.15*time_)
                    if len(data):
                        last_id = data[-1, 1]
                    else:
                        last_id = 0
                    counters, id = abacus.getAllCounters(self.port_name)

                    if (id > 0) and (last_id != id):
                        get(counters, time_, id)
                        break
                    else:
                        time_left = abacus.getTimeLeft(self.port_name) / 1000  # seconds
                        sleep(time_left)
                except abacus.BaseError as e:
                    if i == (constants.NUMBER_OF_TRIES - 1): raise (e)

        except SerialException as e:
            self.errorWindow(e)
        except abacus.BaseError as e:
            self.errorWindow(e)
        except FileNotFoundError as e:
            self.errorWindow(e)

    def updatePlots(self, data):
        time_ = data[:, 0]
        for (i, j) in enumerate(self.combination_indexes):
            self.plot_lines[i].setData(time_, data[:, j + 2])
        for (i, j) in enumerate(self.combination_indexes[:len(self.active_channels_single)]):
            self.plot_lines_single[i].setData(time_, data[:, j + 2])
        for (i, j) in enumerate(self.combination_indexes[len(self.active_channels_single):(len(self.active_channels_single)+len(self.active_channels_double))]):
            self.plot_lines_double[i].setData(time_, data[:, j + 2])
        for (i, j) in enumerate(self.combination_indexes[(len(self.active_channels_single)+len(self.active_channels_double)):]):
            self.plot_lines_multiple[i].setData(time_, data[:, j + 2])

    def updateTable(self, data):
        self.historical_table.insertData(data)

    def updateWidgets(self):
        if self.data_ring != None:
            data = self.data_ring[:]
            if data.shape[0]:
                self.updatePlots(data)
                self.updateTable(data)
                self.updateCurrents(data)

    def writeParams(self, message):
        exceptions = ["Connected", "Acquisition"]
        is_exception = sum([1 if exception in message else 0 for exception in exceptions])
        if is_exception | self.streaming:
            if self.results_files != None:
                try:
                    self.results_files.writeParams(message)
                except FileNotFoundError as e:
                    self.errorWindow(e)
            else:
                self.params_buffer += constants.BREAKLINE + strftime("%H:%M:%S", localtime()) + ", " + message
        elif abacus.constants.DEBUG:
            print("writeParams ignored: %s" % message)

    def writeGuiSettings(self):
        settings = QtCore.QSettings("tausand", "abacus_software")

        settings.beginGroup("dark_colors_in_use")
        if self.dark_colors_in_use != {}:
            dark_channels = []
            for letters in self.dark_colors_in_use.keys():
                settings.setValue(letters, self.dark_colors_in_use[letters])
                dark_channels.append(letters)
            settings.setValue("dark_channels", dark_channels)
        settings.endGroup()

        settings.beginGroup("light_colors_in_use")
        if self.light_colors_in_use != {}:
            light_channels = []
            for letters in self.light_colors_in_use.keys():
                settings.setValue(letters, self.light_colors_in_use[letters])
                light_channels.append(letters)
            settings.setValue("light_channels", light_channels)    
        settings.endGroup()

        settings.beginGroup("devices_previously_used")
        if self.devices_used != {}:
            if len(self.devices_used.keys()) == 1:
                settings.setValue("names_of_devices_used", list(self.devices_used.keys())[0].replace(" ","_"))   
            else: 
                names = list(self.devices_used.keys())
                modified_names = [name.replace(" ","_") for name in names]
                settings.setValue("names_of_devices_used", modified_names)
            for device in self.devices_used.keys():
                device_name = device.replace(" ","_")
                if len(self.devices_used[device]) == 1:
                    settings.setValue(device_name, self.devices_used[device][0])
                else:
                    settings.setValue(device_name, self.devices_used[device])
        settings.endGroup()

        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.setValue("pos", self.pos())
        settings.endGroup()

        settings.beginGroup("tabs_widget")
        settings.setValue("single_tab_top_current_btn", self.tabs_widget.single_tab_top.currentWindowButton.isChecked())
        settings.setValue("double_tab_top_current_btn", self.tabs_widget.double_tab_top.currentWindowButton.isChecked())
        settings.setValue("multiple_tab_top_current_btn", self.tabs_widget.multiple_tab_top.currentWindowButton.isChecked())
        settings.setValue("single_tab_top_plot_btn", self.tabs_widget.single_tab_top.plotWindowButton.isChecked())
        settings.setValue("double_tab_top_plot_btn", self.tabs_widget.double_tab_top.plotWindowButton.isChecked())
        settings.setValue("multiple_tab_top_plot_btn", self.tabs_widget.multiple_tab_top.plotWindowButton.isChecked())
        settings.endGroup()

        settings.beginGroup("mdiArea/subSettings")
        settings.setValue("isVisible", self.subwindow_settings.isVisible())
        settings.setValue("size", self.subwindow_settings.size())
        settings.setValue("pos", self.subwindow_settings.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlots")
        settings.setValue("isVisible", self.subwindow_plots.isVisible())
        settings.setValue("size", self.subwindow_plots.size())
        settings.setValue("pos", self.subwindow_plots.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsSingle")
        settings.setValue("isVisible", self.subwindow_plots_single.isVisible())
        settings.setValue("size", self.subwindow_plots_single.size())
        settings.setValue("pos", self.subwindow_plots_single.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsDouble")
        settings.setValue("isVisible", self.subwindow_plots_double.isVisible())
        settings.setValue("size", self.subwindow_plots_double.size())
        settings.setValue("pos", self.subwindow_plots_double.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsMultiple")
        settings.setValue("isVisible", self.subwindow_plots_multiple.isVisible())
        settings.setValue("size", self.subwindow_plots_multiple.size())
        settings.setValue("pos", self.subwindow_plots_multiple.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrent")
        settings.setValue("isVisible", self.subwindow_current.isVisible())
        settings.setValue("size", self.subwindow_current.size())
        settings.setValue("pos", self.subwindow_current.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentSingle")
        settings.setValue("isVisible", self.subwindow_current_single.isVisible())
        settings.setValue("size", self.subwindow_current_single.size())
        settings.setValue("pos", self.subwindow_current_single.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentDouble")
        settings.setValue("isVisible", self.subwindow_current_double.isVisible())
        settings.setValue("size", self.subwindow_current_double.size())
        settings.setValue("pos", self.subwindow_current_double.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentMultiple")
        settings.setValue("isVisible", self.subwindow_current_multiple.isVisible())
        settings.setValue("size", self.subwindow_current_multiple.size())
        settings.setValue("pos", self.subwindow_current_multiple.pos())
        settings.endGroup()

        settings.beginGroup("mdiArea/subHistorical")
        settings.setValue("isVisible", self.subwindow_historical.isVisible())
        settings.setValue("size", self.subwindow_historical.size())
        settings.setValue("pos", self.subwindow_historical.pos())
        settings.endGroup()

        settings.beginGroup("menuView")
        for action in self.menuView.actions():
            key = action.text().lower().replace(" ","_")
            if key != "":
                settings.setValue(key, action.isChecked())
        settings.endGroup()

        settings.setValue("time_range_for_plots", self.plots_combo_box.currentIndex())
        settings.setValue("symbol_size", self.symbolSize)
        settings.setValue("linewidth", self.linewidth)

    def readGuiSettings(self):
        settings = QtCore.QSettings("tausand", "abacus_software")

        settings.beginGroup("dark_colors_in_use")
        dark_channels = settings.value("dark_channels")
        if dark_channels != None:
            for channel in dark_channels:
                self.dark_colors_in_use[channel] = settings.value(channel)
        settings.endGroup()

        settings.beginGroup("light_colors_in_use")
        light_channels = settings.value("light_channels")
        if light_channels != None:
            for channel in light_channels:
                self.light_colors_in_use[channel] = settings.value(channel)
        settings.endGroup()

        settings.beginGroup("devices_previously_used")
        names_of_devices_used = settings.value("names_of_devices_used")
        if type(names_of_devices_used) == type(" "):
            names_of_devices_used = [names_of_devices_used]

        for name_of_device in names_of_devices_used:
            channels = settings.value(name_of_device)
            if type(channels) == type(" "):
                channels = [channels]
            name_of_device = name_of_device.replace("_"," ")
            self.devices_used[name_of_device] = []
            for channel in channels:
                self.devices_used[name_of_device].append(channel)
        settings.endGroup()

        settings.beginGroup("MainWindow")
        self.resize(settings.value("size"))
        self.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("tabs_widget")
        self.tabs_widget.single_tab_top.currentWindowButton.setChecked(settings.value("single_tab_top_current_btn", type=bool))
        self.tabs_widget.double_tab_top.currentWindowButton.setChecked(settings.value("double_tab_top_current_btn", type=bool))
        self.tabs_widget.multiple_tab_top.currentWindowButton.setChecked(settings.value("multiple_tab_top_current_btn", type=bool))
        self.tabs_widget.single_tab_top.plotWindowButton.setChecked(settings.value("single_tab_top_plot_btn", type=bool))
        self.tabs_widget.double_tab_top.plotWindowButton.setChecked(settings.value("double_tab_top_plot_btn", type=bool))
        self.tabs_widget.multiple_tab_top.plotWindowButton.setChecked(settings.value("multiple_tab_top_plot_btn", type=bool))
        settings.endGroup()

        settings.beginGroup("mdiArea/subSettings")
        self.subwindow_settings.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_settings.resize(settings.value("size"))
        self.subwindow_settings.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlots")
        self.subwindow_plots.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_plots.resize(settings.value("size"))
        self.subwindow_plots.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsSingle")
        self.subwindow_plots_single.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_plots_single.resize(settings.value("size"))
        self.subwindow_plots_single.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsDouble")
        self.subwindow_plots_double.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_plots_double.resize(settings.value("size"))
        self.subwindow_plots_double.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subPlotsMultiple")
        self.subwindow_plots_multiple.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_plots_multiple.resize(settings.value("size"))
        self.subwindow_plots_multiple.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrent")
        self.subwindow_current.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_current.resize(settings.value("size"))
        self.subwindow_current.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentSingle")
        self.subwindow_current_single.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_current_single.resize(settings.value("size"))
        self.subwindow_current_single.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentDouble")
        self.subwindow_current_double.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_current_double.resize(settings.value("size"))
        self.subwindow_current_double.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subCurrentMultiple")
        self.subwindow_current_multiple.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_current_multiple.resize(settings.value("size"))
        self.subwindow_current_multiple.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("mdiArea/subHistorical")
        self.subwindow_historical.setVisible(settings.value("isVisible",True, type=bool))
        self.subwindow_historical.resize(settings.value("size"))
        self.subwindow_historical.move(settings.value("pos"))
        settings.endGroup()

        settings.beginGroup("menuView")
        for action in self.menuView.actions():
            key = action.text().lower().replace(" ","_")
            if key != "":
                action.setChecked(settings.value(key, type=bool))
        settings.endGroup()

        self.plots_combo_box.setCurrentIndex(settings.value("time_range_for_plots", type=int))
        self.symbolSize = settings.value("symbol_size", type=int)
        self.linewidth = settings.value("linewidth", type=int)

def softwareUpdate(splash):
    try:
        check = constants.check_updates_checkBox
    except:
        if constants.SETTING_FILE_EXISTS:
            os.remove(constants.SETTINGS_PATH)
        check = True
    if check:
        version = url.checkUpdate()
        if version != None:
            splash.close()
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("There is a new version avaible (%s).\nDo you want to download it?" % version)
            msg.setWindowTitle("Update avaible")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if msg.exec_() == QtWidgets.QMessageBox.Yes:
                webbrowser.open(url.TARGET_URL)
                exit()

def run():
    from time import sleep
    global app

    app = QtWidgets.QApplication(sys.argv)

    splash_pix = QtGui.QPixmap(':/splash.png').scaledToWidth(600)
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()

    ##in v1.5.0
    #if abacus.CURRENT_OS == 'win32':
    #    constants.ICON = QtGui.QIcon(QtGui.QPixmap(':/abacus_small.ico'))
    #else:
    #    constants.ICON = QtGui.QIcon(QtGui.QPixmap(':/Abacus_small.png'))
    ##since v1.6.0. Use 512x512 png for any OS
    constants.ICON = QtGui.QIcon(QtGui.QPixmap(':/Abacus_small.png'))
    
    app.setWindowIcon(constants.ICON)
    app.processEvents()

    if abacus.CURRENT_OS == 'win32':
        import ctypes
        myappid = 'abacus.abacus.01'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    sleep(1)

    softwareUpdate(splash)
    splash.close()

    main = MainWindow()
    main.setWindowIcon(constants.ICON)
    main.show2()

    try:
        main.readGuiSettings()
    except:
        main.showMaximized()
        main.mdi.tileSubWindows()

    app.exec_()

def exceptHook(exctype, value, tb):
    print('Type:', exctype)
    print('Value:', value)
    print('Traceback:', tb.format_exc())

    return


def open_stdout():
    global STDOUT
    sys.excepthook = exceptHook
    try:
        STDOUT = open(constants.LOGFILE_PATH, 'w')
        sys.stdout = STDOUT
        sys.stderr = STDOUT
    except Exception as e:
        STDOUT = None
        print(e)


def close_stdout():
    global STDOUT
    if STDOUT != None: STDOUT.close()


if __name__ == "__main__":
    abacus.constants.DEBUG = True
    open_stdout()

    # try:
    run()
    # except Exception as e:
    #     print(e)
    # print(traceback.format_exc())

    close_stdout()
    sys.exit()
