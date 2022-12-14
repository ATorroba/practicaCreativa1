#!/usr/bin/python3


#Practica creativa 1

#Luis Trave Reneses
#Andres Emilio Flores Reina
#Alvaro Torroba de Linos

import logging
#OS es una libreria que ofrece funcionalidades de Sistema Operativo sin depender de en cual estés, tales como abrir ficheros o recorrer rutas
import os, sys, subprocess, json
from subprocess import call
#LXML permite utilizar XML y HTML con Python. 
#Etree ofrece una API para crear y analizar XMLs
from lxml import etree

logging.basicConfig(level=logging.DEBUG)
logger= logging.getLogger('gestiona-pc1')

servidores = ["s1", "s2", "s3", "s4" ,"s5"]
bridges = {"c1":["LAN1"],
           "lb":["LAN1"],
		   "s1":["LAN2"],
		   "s2":["LAN2"],
		   "s3":["LAN2"],
		   "s4":["LAN2"],
		   "s5":["LAN2"]}
network = {"c1":["10.20.1.2", "10.20.1.1"],
           "s1":["10.20.2.101", "10.20.2.1"],
		   "s2":["10.20.2.102", "10.20.2.1"], 
		   "s3":["10.20.2.103", "10.20.2.1"],
		   "s4":["10.20.2.104", "10.20.2.1"],
		   "s5":["10.20.2.105", "10.20.2.1"]}


#MAIN FUNCTIONS
def create (numServidores):
	#Se crean las MVs y las redes que forman el escenario a partir de la imagen base
	call(["qemu-img","create", "-f", "qcow2", "-b", "./cdps-vm-base-pc1.qcow2", "c1.qcow2"])
	call(["qemu-img","create", "-f", "qcow2", "-b", "./cdps-vm-base-pc1.qcow2", "lb.qcow2"])
	for i in range(0, numServidores):
		call(["qemu-img","create", "-f", "qcow2", "-b", "./cdps-vm-base-pc1.qcow2", servidores[i] + ".qcow2"])

	#Se modifican los ficheros XML de todas las máquinas del escenario
	call(["cp", "plantilla-vm-pc1.xml", "c1.xml"])
	configuraXML("c1")
	call(["cp", "plantilla-vm-pc1.xml", "lb.xml"])
	configuraXML("lb")
	for i in range(0, numServidores):
		call(["cp", "plantilla-vm-pc1.xml", servidores[i] + ".xml"])
		configuraXML(servidores[i])
	logger.debug("ficheros XML modificados con exito")

    #Se crean los bridges de las dos redes virtuales
	call(["sudo", "brctl", "addbr", "LAN1"])
	call(["sudo", "brctl", "addbr", "LAN2"])
	call(["sudo", "ifconfig", "LAN1", "up"])
	call(["sudo", "ifconfig", "LAN2", "up"])

	#Se definen las MVs
	call(["sudo", "virsh", "define", "c1.xml"])
	call(["sudo", "virsh", "define", "lb.xml"])
	for i in range(0, numServidores):
		call(["sudo", "virsh", "define", servidores[i] + ".xml"])
	logger.debug("Maquinas definidas con exito")

	#Se define la configuración de red de las MVs
	configuraRed("c1")
	configuraRed("lb")
	for i in range(0, numServidores):
		configuraRed(servidores[i])
	
	##Definir configuracion de red en el host 
	call(["sudo", "ifconfig", "LAN1", "10.20.1.3/24"])
	call(["sudo", "ip", "route", "add", "10.20.0.0/16", "via", "10.20.1.1"])
	logger.debug("configuracion de red exitosa")
	

	#Se guarda en JSON
	aux =  { "num_serv" : numServidores }
	file = open("gestiona-pc1.json", "w")
	file.write(json.dumps(aux))
	file.close()
	logger.debug("Archivo json creado correctamente")
	
	logger.debug("Escenario creado correctamente")

def start():
	#Se extrae el numero de servidores
	with open("./gestiona-pc1.json", 'r') as json_file:
		aux = json.load(json_file)
		numServidores = aux["num_serv"]

	#Se arranca c1 y se muestra su consola
	call(["sudo", "virsh", "start", "c1"])
	os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'c1' -e 'sudo virsh console c1' &")

	#Se arranca lb y se muestra su consola
	call(["sudo", "virsh", "start", "lb"])
	os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'lb' -e 'sudo virsh console lb' &")

	#Se arrancan los servidores y se muestra su consola
	for i in range(0, numServidores):
		call(["sudo", "virsh", "start", servidores[i]])
		os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title '" + servidores[i] + "' -e 'sudo virsh console " + servidores[i] + "' &")
	logger.debug("Escenario arrancado correctamente")
def stop() :
	#Extraer numero de servidores
	with open("./gestiona-pc1.json", 'r') as json_file:
		aux = json.load(json_file)
		numServidores = aux["num_serv"]
	call(["sudo", "virsh", "shutdown", "c1"])
	call(["sudo", "virsh", "shutdown", "lb"])
	for i in range(0,numServidores):
		call(["sudo", "virsh", "shutdown", servidores[i]])
	logger.debug("Escenario detenido correctamente")


def destroy() :
	#Extraer numero de servidores
	with open("./gestiona-pc1.json", 'r') as json_file:
		aux = json.load(json_file)
		numServidores = aux["num_serv"]
	call(["sudo", "virsh", "destroy", "c1"])
	call(["sudo", "virsh", "destroy", "lb"])
	for i in range(0,numServidores):
		call(["sudo", "virsh", "destroy", servidores[i]])

	call(["sudo", "virsh", "undefine", "c1"])
	call(["sudo", "virsh", "undefine", "lb"])

	call(["rm", "-f", "c1.qcow2"])	
	call(["rm", "-f", "c1.xml"])	
	call(["rm", "-f", "lb.qcow2"])	
	call(["rm", "-f", "lb.xml"])

	#Borrar servidores y sus archivos	
	for i in range(0,numServidores):
		call(["sudo", "virsh", "undefine", servidores[i]])
		call(["rm", "-f",servidores[i] + ".qcow2"])
		call(["rm", "-f",servidores[i] + ".xml"])


	call(["rm", "-f", "gestiona-pc1.json"])
	call(["rm", "-f", "temporal.xml"])

	#Se eliminan los bridges de las dos redes virtuales
	call(["sudo", "ifconfig", "LAN1", "down"])
	call(["sudo", "ifconfig", "LAN2", "down"])
	call(["sudo", "brctl", "delbr", "LAN1"])
	call(["sudo", "brctl", "delbr", "LAN2"])
	
	logger.debug("Escenario destruido correctamente")

def watch(): 
	os.system("xterm -title monitor -e watch sudo virsh list --all & ")

def help():
	mensaje = """Se pueden ejecutar los siguientes comandos:
	• create, crea el escenario sin llegar a arrancarlo. Introduzca create N,
	donde N es el numero de servidores a crear, N debe estar entre 1 y 5.Si no se introduce 
	N, se crearan 2 servidores por defecto.
	• start, para arrancar las máquinas virtuales y mostrar su consola.
	• stop, para parar las máquinas virtuales (sin liberarlas).
	• destroy, para liberar el escenario, borrando todos los ficheros creados.
	• watch, presenta el estado de todas las maquinas virtuales del escenario.
	• help, para mostrar funcionalidades del programa.
	
	"""
	print(mensaje)


#FUNCIONES AUXILIARES

#Función para modificar los ficheros XML, los XML de definicion de las MVs
def configuraXML(sistema) :

	#Se obtiene el directorio de trabajo
	cwd = os.getcwd()  #método de OS que devuelve el Current Working Directory
	path = cwd + "/" + sistema

	#Se importa el .xml de la máquina pasada como parámetro utilizando métodos de la librería LXML
	tree = etree.parse(path + ".xml")
	root = tree.getroot()

	#Se define el nombre de la MV
	name = root.find("name")
	name.text = sistema

	#Se define el nombre de la imagen, cambiando la ruta del source de la imagen (disk) al qcow2 correspondiente a la maquina pasada como parametro
	sourceFile = root.find("./devices/disk/source")
	sourceFile.set("file", path + ".qcow2")

	#Se definen los bridges, modificando el XML con los bridges correspondientes a la maquina parámetro
	bridge = root.find("./devices/interface/source")
	bridge.set("bridge", bridges[sistema][0])  #se cambia el valor de la etiqueta <source bridge> por la LAN (el bridge) correspondiente a la máquina pasada como parametro
	
	fout = open(path + ".xml", "w")  #se crea fout con el método open y el modo W, que abre un archivo para sobreescribir su contenido y lo crea si no existe
	fout.write(etree.tounicode(tree, pretty_print = True))  #convierte en serie el elemento a la representación unicode de Python de su arbol XML. Pretty_print a true habilita XMLs formateados.
	fout.close()
	if sistema == "lb":
		fin = open(path + ".xml",'r')   #fin es el XML correspondiente a lb, en modo solo lectura
		fout = open("temporal.xml",'w')  #fout es un XML temporal abierto en modo escritura
		for line in fin:
			if "</interface>" in line:
				fout.write("</interface>\n <interface type='bridge'>\n <source bridge='"+"LAN2"+"'/>\n <model type='virtio'/>\n </interface>\n")
				#si el XML de lb contiene un interface (que lo va a contener, ya que previamente se le habrá añadido el bridge LAN1), se le añade al XML temporal otro bridge: LAN2
			else:
				fout.write(line)
		fin.close()
		fout.close()

		call(["cp","./temporal.xml", path + ".xml"])  #sustituimos es XML por el temporal, que es el que contiene las dos LAN
		call(["rm", "-f", "./temporal.xml"])


#Configuración del hostname y los interfaces de red de las maquinas virtuales
def configuraRed(sistema):

	cwd = os.getcwd()
	path = cwd + "/" + sistema

	#Configuración del hostname
	fout = open("hostname",'w')  #Se abre el archivo temporal hostname
	fout.write(sistema + "\n")  #Añade a hostname la maquina pasada como parametro
	fout.close()
	call(["sudo", "virt-copy-in", "-a", sistema + ".qcow2", "hostname", "/etc"])
	call(["rm", "-f", "hostname"])

	#Configuracion del host, que asigna nombres de host a direcciones IP
	fout = open("hosts",'w')
	fout.write("127.0.1.1 " + sistema + "\n")  #Asigna la direccion IP local a la maquina pasada como parametro
	fout.close()
	call(["sudo", "virt-copy-in", "-a", sistema + ".qcow2", "hosts", "/etc"])
	call(["rm", "-f", "hosts"])

	#Configuracion de los interfaces de red de las maquinas virtuales
	fout = open("interfaces",'w')
	if sistema == "lb":   #si la maquina es el balanceador lb, añade a interfaces sus dos interfaces correspondientes a LAN1 y LAN2
		fout.write("auto lo eth0 eth1\niface lo inet loopback\n\niface eth0 inet static\naddress 10.20.1.1\nnetmask 255.255.255.0\niface eth1 inet static\naddress 10.20.2.1\nnetmask 255.255.255.0\n")
	else:  #si no, añade la direccion IP correspondiente a la maquina, y la direccion del LB en gateway
		fout.write("auto lo eth0\niface lo inet loopback\n\niface eth0 inet static\naddress " + network[sistema][0] +"\nnetmask 255.255.255.0 \ngateway " + network[sistema][1] + "\n")
	fout.close()
	call(["sudo", "virt-copy-in", "-a", sistema + ".qcow2", "interfaces", "/etc/network"])
	call(["rm", "-f", "interfaces"])

	#Se habilita forwarding IPv4 para que lb funcione como router al arrancar
	if sistema == "lb":
		fout = open("sysctl.conf",'w')  #Se abre el fichero de configuracion de lb
		fout.write("net.ipv4.ip_forward=1\n") #Se pone net.ipv4.ip_forward a 1 para que lb funcione como roouter IP
		fout.close()
		call(["sudo", "virt-copy-in", "-a", "lb.qcow2", "sysctl.conf", "/etc"])
		call(["rm", "-f", "sysctl.conf"])




#EJECUCION
argumentos = sys.argv

if len(argumentos) >= 2 :

	if argumentos[1] == "create":
			if len(argumentos) > 2 :
				if int(argumentos[2]) > 0 and int(argumentos[2]) < 6 :
					create(int(argumentos[2]))
				else :
					print("El numero de servidores debe estar entre 1 y 5\n")
			if len(argumentos) == 2 :
				print("Si no se especifica el numero de servidores, se crean dos por defecto\n")
				create(2)
	
	if argumentos[1] == "start":
		start()
	if argumentos[1] == "stop":
		stop()
	if argumentos[1] == "destroy":
		destroy()
	if argumentos[1] == "watch":
		watch()
	if argumentos[1] == "help":
		help()


else:
	print("Introduzca uno de los siguientes comandos: create, start, stop, destroy")
