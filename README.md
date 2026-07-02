# Sistema de Detecção e Separação Automática de Moedas

Sistema desenvolvido para identificar moedas brasileiras utilizando visão computacional em Python e realizar a separação física das moedas através de um Arduino.

## Objetivo

O projeto utiliza uma câmera para detectar moedas em movimento, identificar seu valor por meio do tamanho e da cor, e enviar o resultado ao Arduino, que controla servomotores responsáveis pelo direcionamento da moeda ao compartimento correto.

Atualmente o sistema reconhece as seguintes moedas:

* R$ 1,00
* R$ 0,50
* R$ 0,25
* R$ 0,10
* R$ 0,05

---

# Funcionamento

O sistema é dividido em duas partes.

## Python

Responsável por:

* Capturar imagens da câmera.
* Detectar moedas utilizando OpenCV.
* Medir o raio da moeda.
* Analisar sua cor no espaço HSV.
* Classificar a moeda.
* Manter um histórico de detecções para aumentar a confiabilidade.
* Enviar o valor detectado ao Arduino pela porta serial.

Bibliotecas utilizadas:

* OpenCV
* NumPy
* PySerial

---

## Arduino

Responsável por:

* Receber o valor enviado pelo Python.
* Controlar os servomotores responsáveis pela separação.
* Controlar o motor DC que movimenta as moedas.
* Atualizar um display LCD 16x2 I2C.
* Somar automaticamente o valor total das moedas recebidas.

---

# Estrutura do projeto

```
Projeto-Moedas/
│
├── python/
│   └── detector_moedas.py
│
├── arduino/
│   └── sistema_moedas.ino
│
├── imagens/
│   └── (opcional)
│
└── README.md
```

---

# Hardware utilizado

* Arduino Uno
* Webcam USB
* Motor DC
* Transistor TIP120
* Diodo de proteção
* Potenciômetro (controle de velocidade)
* 4 Servomotores SG90
* Display LCD 16x2 I2C
* Fonte de alimentação externa
* Estrutura mecânica para condução das moedas

---

# Fluxo de funcionamento

```
Moeda
   │
   ▼
Webcam
   │
   ▼
Python (OpenCV)
   │
   ▼
Classificação da moeda
   │
   ▼
Comunicação Serial
   │
   ▼
Arduino
   │
   ├── Atualiza LCD
   ├── Soma o valor total
   ├── Aciona o motor DC
   └── Posiciona os servomotores
```

---

# Algoritmo de classificação

A classificação utiliza duas características principais:

## Tamanho

A moeda é classificada inicialmente pelo raio detectado em pixels.

* Grande
* Média
* Pequena

Os limites podem ser calibrados conforme a posição da câmera.

## Cor

Após detectar o tamanho, é calculada a média da cor da moeda no espaço HSV.

A saturação é utilizada para diferenciar moedas prateadas das moedas douradas.

---

# Calibração

Os principais parâmetros ajustáveis são:

### Tamanho

```python
TAMANHO_GRANDE_MIN
TAMANHO_MEDIO_MIN
TAMANHO_PEQUENO_MIN
```

### Cor

```python
COR_PRATA_S_MAX
SATURACAO_1_REAL_MIN
SATURACAO_1_REAL_MAX
```

### Detecção de círculos

```python
HOUGH_PARAM2
HOUGH_MIN_DIST
HOUGH_MIN_RADIUS
HOUGH_MAX_RADIUS
```

O projeto possui um modo de calibração que exibe em tempo real:

* Raio da moeda
* Hue
* Saturação
* Value (HSV)
* FPS
* Parâmetros atuais

---

# Comunicação Serial

O Python envia o nome da moeda ao Arduino.

Exemplos:

```
1 Real
50 Cent
25 Cent
10 Cent
5 Cent
```

O Arduino interpreta a mensagem e realiza o acionamento correspondente.

---

# Bibliotecas

## Python

```
opencv-python
numpy
pyserial
```

Instalação:

```bash
pip install opencv-python numpy pyserial
```

## Arduino

Bibliotecas necessárias:

* Servo
* Adafruit LiquidCrystal

---

# Melhorias futuras

* Interface gráfica para calibração.
* Ajuste dos parâmetros em tempo real com Trackbars do OpenCV.
* Armazenamento das contagens em banco de dados.
* Estatísticas de utilização.
* Treinamento utilizando Machine Learning para classificação das moedas.
* Identificação simultânea de múltiplas moedas.
* Exportação automática dos resultados.

---

# Autor

Victor Dias Frota

Projeto desenvolvido para fins acadêmicos e de estudo em Visão Computacional, Sistemas Embarcados e Automação utilizando Python, OpenCV e Arduino.
