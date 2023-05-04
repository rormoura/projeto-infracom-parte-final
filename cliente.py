import socket #importando a biblioteca que implementa os sockets
import threading #importando a biblioteca que implementa as threads, utilizadas para receber e enviar pacotes concorrentemente

serverAddressPort = ("localhost", 5555) #endereço IP e porta do servidor
bufferSize = 1024 #tamanho do buffer de recebimento e envio
clientName = "" #nome do cliente
messageReceived = "" #mensagem recebida
global clientConnected
clientConnected = False #variável para sabermos se um cliente ainda está conectado ao servidor
global clientIsBanned
clientIsBanned = {} #dicionário para designar, a cada cliente, a sua situação em relação ao servidor (banido ou não)

#VARIÁVEIS PARA A IMPLEMENTAÇÃO DO RDT 3.0
numSeq = 0 #número de sequência a ser enviado junto com uma msg
numSeqRecebido = 0 #número de sequência recebido com alguma msg
ack = 0 #ack a ser enviado quando recebe-se um pacote
ackRecebido = 0 #ack recebido quando se envia um pacote
esperandoAck = False #flag para sabermos quando devemos usar o timeout ou não

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #criando o socket do cliente
#Observação: Esse código só mostra a funcionalidade para múltiplos cliente quando estes estão em terminais distintos. 

message = ""

def receive(): #função para recebimento de pacotes do lado do cliente
    
    global clientConnected
    global clientIsBanned
    global numSeq
    global numSeqRecebido
    global ack
    global ackRecebido
    global esperandoAck
    global message

    while True:

        while True:

            if(esperandoAck): #if para determinar se o temporizador deve ser ligado ou não
                clientSocket.settimeout(3.0) #setando o timeout do cliente
            else:
                clientSocket.settimeout(None) #setando o timeout do cliente
            
            try:
                messageReceived, address = clientSocket.recvfrom(bufferSize) #recebe algum pacote
                messageReceived = messageReceived.decode('utf-8') #decodifica o pacote para string
            except socket.timeout:  #Se estourou o temporizador, reenvia o conteúdo
                clientSocket.sendto(message.encode('utf-8'), serverAddressPort) #reenviando a msg
                esperandoAck = True

            if(messageReceived[0] == "?"): #Se um ack foi recebido pelo cliente
                ackRecebido = int(messageReceived[1]) #extraindo o ack da mensagem
                if(ackRecebido != numSeq): #se o recebi o ack errado
                    #clientSocket.sendto(message.encode('utf-8'), serverAddressPort) #enviando a msg
                    pass
                
                else: #Recebi o ack corretamente
                    esperandoAck = False
                    numSeq = 1 - numSeq #trocando o número de sequência
                    break #saindo do loop caso dê tudo certo

            else: #Se recebi uma mensagem que não é um ack
                numSeqRecebido = int(messageReceived[0])
                messageReceived = messageReceived[1:]

                if numSeqRecebido == ack: #Recebi um pacote cujo número de sequência é o esperado
                    ackMessage = "?" + str(ack) #Formatando a mensagem de ack
                    clientSocket.sendto(ackMessage.encode('utf-8'), address) #Enviando a mensagem de ack
                    ack = 1 - ack #Atualizando o ack
                    break
                
                else: #Recebi um pacote cujo número de sequência não é o esperado
                    numSeqRecebido = numSeqRecebido.to_bytes(4, byteorder="big") 
                    clientSocket.sendto(numSeqRecebido, address) #Reenvio o mesmo número de sequência recebido

        if (messageReceived == "bye"): #confere se eh uma mensagem de desconexão
            clientConnected = False #cliente agora não está mais conectado ao servidor
            print("ADEUS")
        
        elif ("BAN" in messageReceived and ":" not in messageReceived): #confere se o cliente foi banido
            clientIsBanned[messageReceived[3:]] = True #cliente agora está banido
            clientConnected=False #cliente agora não está mais conectado ao servidor
            print("BANIDO") 
        
        elif messageReceived[0] != "?": #Correção de erros de formatação da mensagem recebida pelo cliente.
            if "entrou na sala" in messageReceived and (messageReceived[0] == "0" or messageReceived[0] == "1"):
                messageReceived = messageReceived[1:]
            
            if "foi banido" in messageReceived and (messageReceived[0] == "0" or messageReceived[0] == "1"):
                messageReceived = messageReceived[1:]
            
            if len(messageReceived) > 2 and messageReceived[3] == ":":
                messageReceived = messageReceived[1:]
            
            print(messageReceived) #comportamento normal do chat, ou seja, exibir mensagem recebida no terminal

t = threading.Thread(target=receive) #criando thread que recebe os pacotes
t.start() #startando a thread que recebe os pacotes

print("Pode escrever: ") #mensagem de boas-vindas

while True:
    message = input("") #aguardando texto advindo do terminal

    if message[0:16] == "hi, meu nome eh ": #confere se eh uma msg de inicialização de conexão
        clientName = message[16:] #pegando o nome do cliente

        if clientName not in clientIsBanned or clientIsBanned[clientName] == False: #confere se o cliente não está banido ou se ele nunca se conectou
            clientIsBanned[clientName] = False #se ele eh novo no chat, logo não está banido (ainda o_o)
            print("Bem vindo a sala de chat " + clientName) #msg de boas vindas
            message = "!" + message[16:] #enviando a msg formatada com o sinal indicando que eh de primeira conexão
            clientConnected = True #cliente conectado
            message = str(numSeq)+message #concatenando o número de sequência à msg
            clientSocket.sendto(message.encode('utf-8'), serverAddressPort) #enviando a msg
            esperandoAck = True
            
        else:
            print("Voce está banido desta sala") # se o cliente está banido do chat
        
    else:
        print("Cliente não conectado a sala") #cliente não está conectado ao chat

    while clientConnected: #enquanto o cliente está conectado
        message = input("") #aguardando texto advindo do terminal
        #Observação: Após o cliente ser banido ou desconectar por contra própria, ele ainda precisa mandar uma mensagem para receber o feedback
        #correto quanto a sua situação (ou seja, "Comando inválido. Cliente não conectado a sala").
        while message == "": #se a mensagem for vazia, não é possível enviá-la ao chat
            message = input("É necessário escrever algo, tente novamente: ")

        if clientConnected: # se o cliente está conectado

            if message == "bye": #se o cliente deseja se desconectar do chat
                clientConnected = False #cliente agora não está mais conectado
            
            message = clientName + ": " + message #formatando a msg
            message = str(numSeq)+message #concatenando o número de sequência à msg
            clientSocket.sendto(message.encode('utf-8'), serverAddressPort) #enviando a msg
            esperandoAck = True
