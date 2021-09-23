#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
#Carareto
#17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo
import time

# Interface Física
from interfaceFisica import fisica

# enlace Tx e Rx
from enlaceRx import RX
from enlaceTx import TX

class enlace(object):
    
    def __init__(self, name):
        self.fisica      = fisica(name)
        self.rx          = RX(self.fisica)
        self.tx          = TX(self.fisica)
        self.connected   = False

    def enable(self):
        self.fisica.open()
        self.rx.threadStart()
        self.tx.threadStart()

    def disable(self):
        self.rx.threadKill()
        self.tx.threadKill()
        time.sleep(1)
        self.fisica.close()

    def sendData(self, data):
        self.tx.sendBuffer(data)
        
    def getData(self, size):
        data = self.rx.getNData(size)
        return(data, len(data))

    def getNData(self, size, start):
        start_time = time.time()
        while(self.getBufferLen() < size):
            time.sleep(0.05)
            if time.time() - start < 20:
                runtime = time.time() - start_time
                if runtime > 5:
                    return 'RUNTIME'
            else:
                return 'TIME_OUT'
        return(self.getBuffer(size))
