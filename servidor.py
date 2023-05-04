import socket #importando a biblioteca que implementa os sockets
import threading #importando a biblioteca que implementa as threads, utilizadas para receber e enviar pacotes concorrentemente
import queue #importando a biblietoca que implementa uma lista, a qual é utilizadas para armazenar as mensagens
import time #importando a biblioteca utilizada para o relógio do chat

messages = queue.Queue() #mensagens enviadas pelos clientes
clients = [] #lista de clientes conectados
bannedClients = [] #lista de clientes banidos
banCount = {} #dicionário que contém o contador de bans para cada cliente
bufferSize = 1024 #tamanho do buffer de recebimento e envio
haveBanned = [] #Lista para indicar que um cliente já usou um comando de ban contra outro

#VARIÁVEIS PARA A IMPLEMENTAÇÃO DO RDT 3.0
numSeqRecebido = 0 #número de sequência recebido com alguma msg
ackRecebido = 0 #ack recebido quando se envia um pacote
esperandoAck = False #flag para sabermos quando devemos usar o timeout ou não

rdt = {}# elemento no índice 0 é o número de sequência que será enviado no pacote
        # elemento no índice 1 é o número de reconhecimento (ack) é o número de sequência esperado.

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #criando o socket do cliente
serverSocket.bind(("localhost", 5555)) #definindo a porta do servidor como 5555

def receive(): #função que recebe as mensagens enviadas pelos clientes
    global numSeqRecebido
    global ackRecebido
    global esperandoAck

    print("Servidor está rodando")
    while True: #always on server

        try:
            message,  address = serverSocket.recvfrom(bufferSize) #recebendo a mensagem de algum cliente
            message = message.decode('utf-8') #transformando a msg em string
        except socket.timeout: #Se estourou o temporizador, reenvia o conteúdo
            serverSocket.sendto(message.encode(), address)
            esperandoAck = True
        
        while (True):
            if address not in rdt: #Se o cliente não está registrado no dicionário de rdt
                rdt[address] = [0, 0] #Adicionar no dicionário com os valores padrões de 0.

            if(len(message) == 0): #Se a mensagem recebida for vazia, não vou tratar
                continue

            if message[0] == "?": #Se a mensagem recebida for um ack
                ackRecebido = message[1:] #Extraindo o ack da mensagem
                ackRecebido = int(ackRecebido) #Convertendo para inteiro
                if (ackRecebido == rdt[address][0]): #Comparando com o numSeq para o cliente correspodente.
                    serverSocket.settimeout(None) #Desligando o temporizador
                    rdt[address][0] = 1 - rdt[address][0] #Atualizando o valor do número de sequência
                    esperandoAck = False #Não está mais esperando ack
                    break
                
            else: #Recebendo uma mensagem do cliente que não é um ack
                numSeqRecebido = message[0] #recebendo o número de sequência
                #Formatar número recebido de hexadecimal para binário
                if '\x00' in message in message:
                    message = message.replace('\x00', '0')
                    numSeqRecebido = message[-1]
                if '\x01' in message:
                    message = message.replace('\x01', '1')
                    numSeqRecebido = message[-1]
                
                numSeqRecebido = int(numSeqRecebido) #transformando bytes em int

                if(numSeqRecebido == rdt[address][1]): #Recebi um pacote com o número de sequência correto
                    ackmessage = "?"+str(rdt[address][1])
                    serverSocket.sendto(ackmessage.encode(), address) #mandando o ack respectivo
                    rdt[address][1] = 1 - rdt[address][1]
                    break #saindo do loop caso dê tudo certo

                else: #Recebi o número de sequência errado e vou retransmitir o número de sequência recebido
                    pass
                    #ackmessage = "?"+str(numSeqRecebido)
                    #serverSocket.sendto(ackmessage.encode(), address) #mandando o ack respectivo

        if message[0] != "?":
            message = message[1:] #removendo o número de sequência da mensagem
            messages.put((message, address)) #colocando essa msg na fila de mensagens

def broadcast(): #função que envia as mensagens aos clientes

    global numSeqRecebido
    global ackRecebido
    global esperandoAck

    lastTimeBanRequest = 0 #variável para garantir que o comando de ban só seja dado de X em X segundos

    while True:
        while not messages.empty(): #enquanto houver mensagens na fila de mensagens

            individualMessage = "" #mensagem a ser a enviada a somente um cliente
            broadcastMessage = "" #mensagem a ser enviada a todos clientes exceto a quem a enviou
            command = "" #string utilizada para pegar o nome quando é enviado um inbox
            clientDestName = "" #o nome de quem vai receber uma mensagem específica do servidor (ban ou inbox)
            individualAddress = "" #o endereço de um cliente para o qual será enviada uma mensagem específica (em todo o código)
            bannedClient = False #para sabermos se um cliente está banido, quando este tenta entrar na sala novamente
            clientExists = False #para sabermos se um cliente está no chat, quando precisamos contar um ban ou enviar um inbox
            doBroadcast = False #para sabermos se essa msg deve ser enviada a todos os clientes (exceto a quem enviou ela)
            doIndividual = False #para sabermos se essa mensagem deve ser enviada a somente um cliente específico
            message, address = messages.get() #pegando a primeira msg na fila

            tm = time.localtime() #pegando o horário (por causa da formatação das msgs do chat)
            if len(message) == 0:
                continue
            
            current_time = time.strftime("%H:%M:%S", tm) #formatando o horário

            if message[0] == "!": #se a msg for uma de entrada no chat
                name = message[1:] #pegando o nome do cliente que está entrando no server
                for ban in bannedClients: #procurando esse nome na lista de clientes banidos
                    if name == ban: #se ele estiver na lista de banidos
                        bannedClient = True #cliente banido
                
                if bannedClient: #se o cliente estiver banido
                    individualMessage = "BAN"+name #mensagem de aviso para o cliente banido
                    doIndividual = True #mandar essa msg somente a esse cliente
                    individualAddress = address #endereço desse cliente
                
                else: #caso ele não esteja banido
                    broadcastMessage = name + " entrou na sala" #mensagem de boas-vindas
                    clients.append((address, name)) #adicionando-o na lista de clientes conectados
                    banCount[name] = 0 #adicionando-o no dicionário de bans
                    doBroadcast = True #mandar essa msg a todos os clientes, exceto ao que acabara de entrar
            
            elif ":" in message and message.split(": ", 1)[1] == "bye": #se a msg for de saída do server
                individualAddress = address #endereço do cliente que quer se desconectar
                doIndividual = True #mandar essa msg somente ao cliente que quer se desconectar
                name = message.split(": ", 1)[0] #nome do cliente que está se desconectando
                individualMessage = "bye" #msg a ser enviada ao cliente que está se desconectando
                clients.remove((address, name)) #removendo esse cliente da lista de clientes que estão conectando
                del banCount[name] #removendo esse cliente do dicionário de bans
                #Escolhemos limpar o contador de bans de um cliente que deseja sair do servidor.

            elif ":" in message and message.split(":", 1)[1] == " list": #se a msg for a de listar os cliente atualmente conectados no chat
                individualAddress = address #endereço do cliente que deve receber a lista de cliente atualmente conectados no chat
                doIndividual = True #mandar a lista somente a esse cliente
                doBroadcast = True #mandar a solicitação de lista a todos os clientes exceto ao cliente que solicitou
                broadcastMessage = current_time + " " + message #msg que informa que o cliente solicitou a lista de clientes atualmente conectados ao chat
                for connectedClients in clients: #iterando na lista de clientes conectados
                    individualMessage += connectedClients[1] + "\n" #construindo a lista de clientes conectados
                
            elif ":" in message and message.split(": ", 1)[1][0] == "@": #se a msg for de inbox (chama no inbox bb)
                doIndividual = True #mandar essa msg (do inbox) somente ao cliente referido
                command = message.split(": ", 1)[1] #tirando o ": " de todo o comando
                clientDestName = command.split(" ", 1)[0][1:] #pegando somente o nome do cliente a ser enviado o inbox

                for client in clients: #iterando na lista de clientes conectados
                    if client[1] == clientDestName: #se esse cliente está nessa lista
                        clientExists = True
                        individualAddress = client[0] #armazenando o endereço do cliente referido para receber o inbox
                
                if clientExists: #se o cliente referido realmente está conectado
                    individualMessage = "Mensagem Individual -- " + current_time + " " + message.split(": ", 1)[0] + ": " + command.split(" ", 1)[1] #formando a msg do inbox
                else:
                    individualAddress = address #se o usuário não existe, o endereço de quem vai receber esse aviso é o próprio cliente que enviou a msg
                    individualMessage = "O usuário não está na sala de chat" #o usuário não está conectado
                
            elif ":" in message and message.split(": ", 1)[1][0:3] == "ban" and time.time() >= (lastTimeBanRequest + 5): #se a msg for de ban (banido o-o), comando ban somente de 5 em 5 segundos
                lastTimeBanRequest = time.time() #armazenando o momento em que o comando de ban foi enviado
                clientDestName = message.split("ban @", 1)[1] #pegando o nome do cliente que está sendo requisitado a ser banido
                broadcastMessage = current_time + " " + message #montando a msg de ban a ser enviada a todos os cliente, exceto a quem enviou o ban
                doBroadcast = True #enviar essa msg a todos os clientes exceto a quem enviou o ban
                senderName = message.split(":", 1)[0] #Extraindo nome de quem enviou a solicitação de ban

                for client in clients: #iterando na lista de clientes conectados
                    if client[1] == clientDestName: #se esse cliente realmente está conectado ao chat
                        clientExists = True
                        individualAddress = client[0] #pegando o endereço desse cliente
                        break
                
                if clientExists: #se o cliente realmente está conectado ao chat

                    if (senderName, clientDestName) in haveBanned: #Se o cliente está tentando banir alguém que já tentou antes.
                        doBroadcast = False
                        doIndividual = True
                        individualMessage = "Você já requisitou um ban para este cliente"
                        individualAddress = address
                    
                    else:
                        haveBanned.append((senderName, clientDestName)) #Adiciona o pedido de ban de um cliente para o outro a fim de que não seja enviada novamente .
                        banCount[clientDestName] += 1 #incrementando o contador de bans relativo a tal cliente
                        if banCount[clientDestName] >= (2/3)*len(clients): #se a quantidade de bans em relação a esse cliente for maior ou igual a 2/3 da quantidade de clientes conectados
                        
                            individualMessage = "BAN"+clientDestName #montando a msg a ser enviada ao cliente que acabar de ser banido do chat
                            broadcastMessage = clientDestName + " foi banido" #montando a msg a ser enviada a todos os clientes, exceto ao cliente que acabar de ser banido
                            doBroadcast = False #para não enviar a msg de que algum cliente foi banido duas vezes. pois esse broadcast já é feito logo abaixo (linha 108)
                            #esse broadcast em específico não precisa ser feito no loop final (o qual é utilizado para todas as outras msgs)

                            for client in clients: #iterando a lista de clientes conectados
                                if client[1] == clientDestName: 
                                    doIndividual = True #mandar a msg de que foi banido a esse cliente que foi banido
                                
                                else:
                                    broadcastMessage = str(rdt[client[0]][0]) + broadcastMessage #Formatando mensagem de broadcast.
                                    serverSocket.settimeout(3.0) #Setando o temporizador
                                    serverSocket.sendto(broadcastMessage.encode(), client[0]) #mandando a msg avisando que fulano foi banido para os outros clientes, exceto fulano
                                    esperandoAck=True
                            
                            del banCount[clientDestName] #removendo o cliente que foi banido do dicionário de bans
                            clients.remove((individualAddress, clientDestName)) #removendo o cliente que foi banido da lista de clientes conectados
                            bannedClients.append(clientDestName) #adicionando esse cliente à lista de clientes banidos
            
            elif ":" in message and message.split(": ", 1)[1][0:3] == "ban" and time.time() < (lastTimeBanRequest + 5): #se a msg for de ban (banido o-o), comando ban somente de 5 em 5 segundos
                doIndividual = True
                individualAddress = address
                difference = 5 - (time.time() - lastTimeBanRequest) #Calculando quanto tempo falta
                individualMessage = "Comando de ban não aceito, espere " + str(round(difference, 2)) + "s para enviar novamente" #Tentativa muito rápido de ban
            
            else: #se for uma msg comum, que não se encaixa em nenhum dos comandos
                broadcastMessage = current_time + " " + message #montando essa msg
                doBroadcast = True #mandar essa msg a todos, exceto a quem enviou ela
            
            if(doBroadcast): #se é para mandar essa msg a todos, exceto a quem enviou ela
                for client in clients: #iterando a lista de cliente conectados
                    if client[0] != address: #se o endereço é diferente do endereço do cliente que enviou a msg
                        broadcastMessage = str(rdt[client[0]][0]) + broadcastMessage
                        serverSocket.settimeout(3.0)
                        serverSocket.sendto(broadcastMessage.encode(), client[0]) #enviando a msg para todos os clientes, exceto a quem enviou a msg
                        esperandoAck = True
            
            if(doIndividual): #se é para mandar a msg a somente um cliente
                individualMessage = str(rdt[individualAddress][0]) + individualMessage
                serverSocket.sendto(individualMessage.encode(), individualAddress) #enviando essa msg a um cliente específico
                esperandoAck = True
                serverSocket.settimeout(3.0)

t1 = threading.Thread(target=receive) #criando a thread que recebe msgs
t2 = threading.Thread(target=broadcast) #criando a thread que envia msgs

t1.start() #startando a thread que recebe msgs
t2.start() #startando a thread que envia msgs
