# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QGroupBox, QGridLayout, QLabel, QLineEdit, QVBoxLayout
from PyQt5 import QtCore
from sys import exit
import pyqtgraph as pg
import numpy as np

class Aplicacion_Gui(QWidget):

    def __init__(self):
        super().__init__()

        #Se establecen las características de la ventana
        self.title = 'Mi aplicación'
        self.left = 80
        self.top = 80
        self.width = 500
        self.height = 550
        #Inicializamos la ventana principal
        self.inicializar_GUI()

    #Funciones auxiliares
    def clickMethod(self):
        valor_ingresado = int(self.txt_numero.text())
        self.valor_actual += valor_ingresado
        self.mensaje_numero.setText('Valor actual: ' + str(self.valor_actual))
        self.txt_numero.clear()

    def clickReset(self):
        self.valor_actual = 0
        self.mensaje_numero.setText('Valor actual: ' + str(self.valor_actual))
    
    def clickStop(self):
        exit()



    def update_plot(self):
        self.time -= 0.1
        self.time = np.append(self.time, [0])
        self.values = np.append(self.values,[self.valor_actual])
        self.line.setData(self.time, self.values)
         

    def inicializar_GUI(self):
        #inicializamos la ventana
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        #Creamos el distribuidor gráfico principal
        self.distr_vertical = QVBoxLayout()

        #Creamos la caja de materias
        self.caja_materias = QGroupBox("Suma con gráfico")
        distr_caja_materias = QGridLayout()
        self.caja_materias.setLayout(distr_caja_materias)

        #Creamos las etiquetas y campos de texto de la materia la caja de materias
        self.etiqueta_numero = QLabel('Número del 1 al 5')
        self.txt_numero = QLineEdit()

        self.mensaje_numero = QLabel('')
        

        

        #Agregamos a la caja de materias las etiquetas
        distr_caja_materias.addWidget(self.etiqueta_numero, 0,0)
        distr_caja_materias.addWidget(self.mensaje_numero,2,0)

        #Agregamos a la caja de materias los campos de texto
        distr_caja_materias.addWidget(self.txt_numero, 0,1)
        
  

        #Creamos la caja de botones
        self.caja_botones = QGroupBox()
        distr_caja_botones = QHBoxLayout()
        self.caja_botones.setLayout(distr_caja_botones)
        self.caja_botones.setFixedHeight(60)
        
        #Creamos los botones para la caja de botones
        self.boton = QPushButton("Ok")
        self.boton.clicked.connect(self.clickMethod)

        self.reset_boton = QPushButton("Reinicio de contador")
        self.reset_boton.clicked.connect(self.clickReset)

        self.stop_boton = QPushButton('Fin de programa')
        self.stop_boton.clicked.connect(self.clickStop)

    

        #Agregamos los botones a la caja de botones
        distr_caja_botones.addWidget(self.boton)
        distr_caja_botones.addWidget(self.reset_boton)
        distr_caja_botones.addWidget(self.stop_boton)
       

        #Mostramos la gráfica
        self.plot_graph = pg.PlotWidget()
        pen = pg.mkPen(color='r', width=4)
        self.plot_graph.setBackground("w")
        self.plot_graph.setTitle("Suma acumulada vs Tiempo", size="20pt")
        self.plot_graph.setXRange(-30, 0)
        self.plot_graph.setYRange(0, 15)
        self.plot_graph.showGrid(x=True, y=True)
        self.plot_graph.setLabel("left", "Suma Acumulada")
        self.plot_graph.setLabel("bottom", "Tiempo (s)")
        self.time = np.array([float(0)])
        self.values = np.array([0])
        self.valor_actual = 0
        #Referenciamos la línea
        self.line = self.plot_graph.plot(
            self.time,
            self.values,
            pen=pen
        )
        # Añadimos temporizador que nos permitirá actualizar los datos cada segundo (1000 ms)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        #Agregamos las cajas a nuestra aplicación
        self.distr_vertical.addWidget(self.caja_materias)
        self.distr_vertical.addWidget(self.caja_botones)
        self.distr_vertical.addWidget(self.plot_graph)
        
        #Definimos el distribuidor principal de la ventana             
        self.setLayout(self.distr_vertical)



        #Hacemos la ventana visible
        self.show()