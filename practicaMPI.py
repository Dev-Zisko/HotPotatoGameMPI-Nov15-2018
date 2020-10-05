#!/usr/bin/env python
from mpi4py import MPI
import random
import time

#Inicializamos el mundo de comunicadores
comm = MPI.COMM_WORLD

#Obtenemos el numero total de procesos 
size = comm.Get_size()

#Obtenemos el id del proceso
rank = comm.Get_rank()

#Inicializamos el id del proceso lider
rankMaster = size - 1

#Inicializamos el id del proceso actual con la papa
currentSource = 0

#Inicializamos el rango del proceso anterior
rankBefore = 0

#Inicializamos el rango del proceso siguiente
rankNext = 0

#Inicializamos la variable para guardar el id del proceso seleccionado como master
selectedMaster = None

#Inicializamos la variable para guardar el id del proceso que origino el envio del mensaje
originSource = None

#Obtenemos el id del proceso siuiente en el anillo
if rank + 1 > size - 1:
	rankNext = 0
else:
	rankNext = rank + 1

#Obtenemos el id del proceso anterior en el anillo
if rank - 1 < 0:
	rankBefore = size - 1
else:
	rankBefore = rank - 1

#Inicializamos el flag de quemado
iBurned = False

#Inicializamos la bandera de partida en juego
playing = True

#Inicializamos la bandera de comienzo
isBeginning = False

#Inicializamos la bandera de primer turno
isFirstTurn = True

#Inicializamos el vector de seleccion de master
selectMasterVector = []

#Inicializamos el vector de quemados
burnArray = []

#funcion para buscar el id del proceso anterior que no ha sido quedamo
def findBefore (burnArray):
	recursive = False
	global rankBefore
	global size
	for burned in burnArray:
		if rankBefore == burned:
			if rankBefore - 1 < 0:
				rankBefore = size - 1
			else:
				rankBefore -= 1
	for burned in burnArray:
		if rankBefore == burned:
			recursive = True
	if recursive:
		findBefore(burnArray)

#funcion para buscar el id del proceso siguiente que no ha sido quedamo
def findNext (burnArray):
	recursive = False
	global rankNext
	global size
	for burned in burnArray:
		if rankNext == burned:
			if rankNext + 1 > size - 1:
				rankNext = 0
			else:
				rankNext += 1
	for burned in burnArray:
		if rankNext == burned:
			recursive = True
	if recursive:
		findNext(burnArray)

#funcion para determinar si el proceso actual ha ganado
def findWinner (burnArray):
	global size
	cont = len(burnArray)
	if cont == size - 1:
		return True
	else:
		return False

#Validar que el currentsource no se salga del arreglo de procesos
def valnextsource():
	global currentSource
	global size
	if currentSource + 1 > size - 1:
		currentSource = 0
	else:
		currentSource += 1

#funcion para buscar el id del proceso siguiente que tendra la papa y no haya sido quedamo
def findNextSource (burnArray):
	recursive = False
	global currentSource
	global size
	for burned in burnArray:
		if currentSource == burned:
			if currentSource + 1 > size - 1:
				currentSource = 0
			else:
				currentSource += 1
	for burned in burnArray:
		if currentSource == burned:
			recursive = True
	if recursive:
		findNextSource(burnArray)

#funcion para determinar si el master esta quemado
def isMasterBurned (burnArray):
	global rankMaster
	#print 'Master: ', rankMaster, ' rank: ', rank
	if not findWinner(burnArray):
		for burned in burnArray:
			if burned == rankMaster:
				return True
		return False
	else:
		return False

#function para hacer el broadcast del algoritmo de seleccion
def my_bcast(newMaster):
	send = True
	for x in range(size):
		for burned in burnArray:
			if burned == x:
				send = False
		if send and x != rank:
			comm.send(newMaster, dest=x, tag=9)
		else:
			send = True


#ciclo de partida
while playing:
	#solo ejecuado por el master
	if rank == rankMaster:
		#para comenzar un juego
		if isFirstTurn:
			currentSource = rankNext
			#se envia el arreglo vacio de quemados al primer proceso por jugar
			comm.send(burnArray, dest=rankNext, tag=11)
			isFirstTurn = False
		#si el proceso actual en jugar no es el master
		if currentSource != rankMaster:
			#para restablecer una partida luego de seleccionar el master
			if isBeginning:
				#se envia el arreglo de quemados al proceso que genero el algoritmo de seleccion de master para continuar el juego
				comm.send(burnArray, dest=currentSource, tag=11)
				isBeginning = False
			#se espera que el proceso actual en juego pregunte si fue quemado
			iBurned = comm.recv(source=currentSource, tag=10)
			#se calcula si fue quemado
			if random.randint(0,2) == 1:
				iBurned = True
				burnArray.append(currentSource)
			else:
				iBurned = False
			#se envia la respuesta a la pregunta del proceso actual en juego
			comm.send(iBurned, dest=currentSource, tag=10)
			valnextsource()
			findNextSource(burnArray)
		#si el proceso actual en jugar es el master
		else:
			#espera el arreglo de quemados del proceso anterior
			burnArray = comm.recv(source=rankBefore, tag=11)
			if findWinner(burnArray):
				print ('Rank: ', rank,'. Gane!!')
				playing = False
			else:
				time.sleep(0.2)
				#si no gano, actualizo mis id's de proceso anterior y siguiente
				findBefore(burnArray)
				findNext(burnArray)
				print ('Rank: ', rank,'. Tengo la papa caliente')
				#calculo si fui quemado
				if random.randint(0,2) == 1:
					iBurned = True
				if iBurned:
					burnArray.append(rank)
					print ('Rank: ', rank,'. Me Queme!')
					playing = False
				#envio el arreglo de quemados al proximo proceso
				comm.send(burnArray, dest=rankNext, tag=11)
				#actualizo el proceso actual en juego con el id del proceso
				#siguiente no quemado
				valnextsource()
				findNextSource(burnArray)
	#ejecutado por non masters
	else:
		iBurned = False
		#espera el arreglo de quemados del proceso anterior
		burnArray = comm.recv(source=rankBefore, tag=11)
		#determino si el master esta en el arreglo de quemados
		if isMasterBurned(burnArray):
			#si el id del proceso anterior es el id del master
			#soy quien inicia el algoritmo de seleccion de master
			if rankBefore == rankMaster:
				print('Rank: ', rank, '. Comenzando Algoritmo de seleccion')
				findBefore(burnArray)
				findNext(burnArray)
				#envio el arreglo de los quemados para que los demas procesos
				#entren en el algoritmo de seleccion
				comm.send(burnArray, dest=rankNext, tag=11)
				#construyo el vector para ejecutar el algoritmo de seleccion de anillo
				selectMasterVector.append(rank)
				selectMasterVector.append(rank)
				#envio el vector al siguiente proceso
				comm.send(selectMasterVector, dest=rankNext, tag=11)
				#espero respuesta de mi proceso anterior con el vector de seleccion final
				selectMasterVector = comm.recv(source=rankBefore, tag=11)
				#actualizo mi id del proceso master
				rankMaster = selectMasterVector[1]
				originSource = rank
				#Se genera un broadcast por quien inicio el algoritmo de leccion para comunicar el id del nuevo master
				time.sleep(0.5)
				#rankMaster = comm.bcast(rankMaster, root=originSource)
				my_bcast(rankMaster)
			#no soy quie inicio el proceso de seleccion de master
			else:
				print('Rank: ', rank, '. Participando en el Algoritmo de seleccion')
				findBefore(burnArray)
				findNext(burnArray)
				#espero por el vector de seleccion de master
				selectMasterVector = comm.recv(source=rankBefore, tag=11)
				#envio el arreglo de los quemados para que los demas procesos
				#entren en el algoritmo de seleccion hasta llegar al proceso
				#que origino el algoritmo
				if selectMasterVector[0] != rankNext:
					comm.send(burnArray, dest=rankNext, tag=11)
				#si el id para nuevo master en el vector de seleccion
				#es menor a mi id, lo sustituyo por el mio
				if selectMasterVector[1] < rank:
					selectMasterVector.pop(1)
					selectMasterVector.append(rank)
				originSource = selectMasterVector[0]
				#envio el nuevo vector de seleccion de master
				comm.send(selectMasterVector, dest=rankNext, tag=11)
				#Se espera un broadcast por quien inicio el algoritmo de seleccion para comunicar el id del nuevo master
				#rankMaster = comm.bcast(rankMaster, root=originSource)
				rankMaster = comm.recv(source=originSource, tag=9)
			#si soy el nuevo master, actualizo el proceso actual en juegar
			#por quien inicio el algoritmo y continuo con el juego
			if rank == rankMaster:
				currentSource = selectMasterVector[0]
				isBeginning = True
				isFirstTurn = False
				print('Rank: ', rank, '. Finalizado el Algortimo de seleccion: Soy el nuevo Master')
			selectMasterVector = []
		#si el master no esta en el arreglo de quemados
		else:
			time.sleep(0.5)
			if findWinner(burnArray):
				print ('Rank: ', rank,'. Gane!!')
				playing = False
			else:
				findBefore(burnArray)
				findNext(burnArray)
				print ('Rank: ', rank,'. Tengo la papa caliente')
				#pregunto al master si fui quemado
				comm.send(iBurned, dest=rankMaster, tag=10)
				#espero la respuesta del master
				iBurned = comm.recv(source=rankMaster, tag=10)
				if iBurned:
					burnArray.append(rank)
					print ('Rank: ', rank,'. Me Queme!')
					playing = False
				#paso el arreglo de quemados al siguiente proceso
				comm.send(burnArray, dest=rankNext, tag=11)
MPI.Finalize()