# Parte 3 - Projeto Infracom - CIn UFPE

## Grupo: 

- Jeferson Severino de Araujo (jsa2)

- Marcus Vinicius de Faria Santos (mvfs)

- Rodrigo Rocha Moura (rrm2)

- Victor Gabriel de Carvalho (vgc3).

 ---

## Descrição da parte 3:

### Temos os códigos de cliente e servidor que implementam um chat com transferência confiável sobre o UDP.

- ### Descrição do cliente: O código é dividido em duas partes, uma para cada thread: 1 - Recebimento de mensagens enviadas pelo servidor; 2 - Envio de mensagens para o servidor.

- ### Descrição do servidor: O código é dividido em duas partes, uma para cada thread: 1 - Recebimento de mensagens enviadas pelos diversos clientes; 2 - Envio das mensagens (tratamento conforme os diversos tipos de mensagens) para somente um cliente ou para vários.

- ### Diferenças em relação ao código da parte 2: 1 - O servidor precisa de acks e números de sequências para cada cliente já que são vários clientes no chat; 2 - Mandamos números de sequência e acks concatenados aos respectivos pacotes, no código da parte 2 eles eram enviados como pacotes distintos.

---