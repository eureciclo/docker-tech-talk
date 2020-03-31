Tech talk: Docker
=================

Objetivo
--------

A ideia é sair daqui sabendo o que é e como usar Docker no ambiente de desenvolvimento e dar uma ideia de como usamos em produção com o Kubernetes e noções básicas sobre o Swarm.

1. O que é? Vantagens e desvantagens.
2. Usando imagens pré prontas.
3. Montando uma imagem customizada
4. Compose
5. O que preciso mudar no meu projeto para usar Docker?
6. Como usar em produção?

## O que é? Vantagens e desvantagens.

De uma forma bem simplista: Docker é uma ferramenta que padroniza e isola o ambiente em que sua aplicação vai rodar.

Para devs, usar Docker tem várias vantagens:

* Chegar em um projeto novo e não ter que configurar ambiente.
* Se a aplicação precisar de uma lib ou configuração escondida, ela é replicada para todos os devs.
* Você tem todas linguagens/banco de dados "instalados" na sua máquina ao mesmo tempo que não tem nenhuma.
* É MUITO mais leve que máquina virtual.
* Você pode quebrar sua máquina de desenvolvimento sem medo pois o ambiente é isolado.
* Facilita o deploy.

E algumas desvantagens também:

* Só roda nativo em Linux. Mac e Windows precisam usar uma vm (pequena e leve, mas é uma vm) para o Docker ter as funções do kernel necessárias para rodar.

* Ocupa muito espaço da máquina.
  - Se você lida com alguns projetos, é fácil chegar a mais de 60gb (padrão) no arquivo do Docker.

* As vezes torna as coisas mais lentas e piores:
  - Exemplo de mais lento: O rails usa um programa que chama spring que mantem o rails carregado na memória mesmo quando você termina de rodar para carregar mais rápido da próxima vez. Como o container inteiro é descartado após o uso, isso não funciona e demora um tempo maior para carregar entre usos.

  - Exemplo de piores: Se você usar o terminal dentro de um container e o terminal não estiver configurado para salvar o histórico fora do container, você perde os comandos e tem que digitar tudo de novo.

Mas essas coisas geralmente tem um fix.

## Usando imagens pré prontas.

Dada essa introdução, vamos por a mão na massa.

No ecossistema do Docker, existe o repositório de imagens [https://hub.docker.com/](https://hub.docker.com/), similar ao do `npm`, `bundler` e `pip`. E sempre que formos escrever a nossa, vamos usar uma imagem oficial dessas como base.

Entrando na [página das imagens oficiais do Python](https://hub.docker.com/_/python), temos algumas versões. Vamos utilizar a 3.7.4-alpine3.10.

3.7.4 é a versão do Python.
alpine3.10 é a versão do linux.

Sempre que está disponível, eu uso a versão alpine das imagens por ela ser a menor e com menos coisas instaladas por padrão.

Para abrir um terminal shell, nesse container, vamos usar:

```
docker run -it python:3.7.4-alpine3.10 sh
```

Beleza, nosso ambiente com python3 isolado da máquina está pronto para usar.

Nesse projeto temos um servidor de testes, mas antes precisamos instalar as dependências:

```
apk --update add build-base python3-dev
pip install klein
```

Aí sim podemos rodar o servidor com:

```
python /app/server.py
```

Esse passo não vai funcionar ainda, porque não falamos para o docker montar um volume da nossa máquina dentro do container. Sem problemas, vamos sair e montar o volume com:

```
docker run -it -v `pwd`/demo-app:/app python:3.7.4-alpine3.10 sh
```

A partir de agora, sempre que modificarmos algo dentro do diretório /app dentro do container, será mantido e refletirá na máquina host, por exemplo:

```
echo test > /app/test.txt
```

O arquivo test.txt é criado dentro da pasta demo-app e mesmo que reiniciamos o container, ele estará lá.

Continuando, de dentro do container vamos iniciar nosso servidor:

```
python /app/server.py
```

E.... vai dar erro de depêndencia não encontrada. Esse erro acontece porque os container são efêmeros, ou seja, tudo que alteramos é descartado ao sair do container.

Para não ter que instalar tudo na mão de novo, vamos criar um Dockerfile.

## Montando uma imagem customizada

Criando um Dockerfile, você customiza uma imagem já pronta para suas necessidades.

No nosso caso, vamos partir da imagem do Python3, adicionar as dependencias build-base e python3-dev e instalar o klein e redis via pip:

```
FROM python:3.7.4-alpine3.10

RUN apk --update add build-base python3-dev
RUN pip install klein
RUN pip install redis
```

Agora vamos construir nossa imagem de fato e dar um nome para ela de `demo-server-test` e versão `latest` :

```
docker build -f ./Dockerfile -t demo-server-test:latest .
```

Agora sim temos um container com todas as dependências necessárias, podemos entrar no container e subir o servidor:

```
docker run -it -v `pwd`/demo-app:/app demo-server-test:latest sh
python /app/server.py
```

Se tentarmos acessar pelo browser, vamos ver que as requisições não estão chegando no servidor. Isso acontece porque não falamos para o Docker publicar a porta do servidor para fora do container.

Vamos mudar nosso `docker run` e aproveitar para já chamar o servidor de uma vez, sem precisar entrar no terminal do container:

```
docker run -it -v `pwd`/demo-app:/app -p 5000:5000 demo-server-test:latest python /app/server.py
```

O nosso servidor tem outro método que testa uma conexão com o Redis, o `/redis`.
Ao tentarmos acessar, vamos tomar erro de conexão porque o redis não está disponível.

Com o que vimos até agora, daria para executar uma imagem do redis, pegar o endereço de ip e alterar no código que funcionaria, mas vamos usar um jeito mais fácil tanto de executar serviços adicionais, como o próprio projeto principal.

## Compose

O Compose é uma ferramenta que lê arquivos de configuração e cria containers para você. Assim vocês podem esquecer tudo que vimos até agora :)

Vamos criar um arquivo chamado `docker-compose.yml`, com as configurações do serviço app, que é nosso servidor python.

```
version: '3.6'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    command: python /app/server.py
    volumes:
      - ./demo-app:/app
    ports:
      - "5000:5000"
    stdin_open: true
    tty: true
```

Todas as configurações de build e run estão no `docker-compose.yml` agora: Qual Dockerfile usar, portas, volumes e comando para rodar o servidor.

Vamos buildar a imagem pelo compose e subir o servidor:

```
docker-compose build app
docker-compose up app
```

E vamos criar a configuração para o redis também:

```
  redis:
    image: redis:5.0.4-alpine
    command: ["redis-server", "--appendonly", "yes"]
    hostname: redis
    ports:
      - "6379:6379"
```

A configuração do redis é um pouco diferente pois não precisamos fazer build da imagem, só baixar ela do hub e já executar o redis-server.

Agora vamos subir os dois serviços:

```
docker-compose up
```

E podemos chamar [localhost:5000/redis](http://localhost:5000/redis) que vai funcionar. Vocês podem reparar no código do servidor que ele procura o redis pelo nome "redis". Esse é o mesmo nome configurado no docker-compose, que cria tipo um DNS para acessarmos outros containers.

### Extras do Compose

Com o compose, você também consegue subir o container e acessar o terminal ou executar qualquer outra coisa, para isso, usamos o `docker-compose run`

```
docker-compose run app sh
apk add redis
redis -h redis
ping
```

## O que preciso mudar no meu projeto para usar Docker?

A maior mudança geralmente é a questão de container ser efêmero. Você não pode contar que arquivos enviados ao servidor estarão lá, por isso é necessário subir tudo em um storage.

Fora isso, coisas devem dar pau no começo, mas geralmente são erros bem documentados e com soluções.

## Como usar em produção?

Conseguindo fazer o build do container já é um passo grande para usá-lo em produção.

Geralmente temos builds diferentes para dev e produção, por exemplo: o container de produção deve conter variáveis de ambiente que só podem ser setadas nele (idealmente por um CI, como utilizamos hoje pelo Pipelines).

Após o build ser feito, enviamos a imagem para um repositório de imagens privado (utilizamos o Container Registry da Google Cloud) utilizando o comando `docker push`.

Depois disso temos toda uma camada de Kubernetes que puxa essa imagem e sobe de acordo com o configurado.

### Kubernetes

  O Kubernetes é um orquestrador de containers, ou seja, ele tem configurado dentro dele como deve apresentar os containers para o mundo.

  [Mostrar nossos arquivos de configuração do Kubernetes]

### Swarm

  O Swarm também é um orquestrador de containers, só que, como estamos subindo ele manualmente em máquinas virtuais, o processo é mais custoso. Um exemplo disso é termos que configurar um loadbalancer manualmente, enquanto no Kubernetes da Google Cloud, ele já sobe um padrão e tudo funciona.

  [Mostrar as duas VMs do Swarm, docker service ls]
