import cv2
import numpy as np
import time
import serial
from serial.tools import list_ports

# ====================== CALIBRAÇÃO ======================

# Modo de calibração
MODO_CALIBRACAO = True

# Tamanho das moedas (raio em pixels)
TAMANHO_GRANDE_MIN = 80
TAMANHO_MEDIO_MIN = 70
TAMANHO_PEQUENO_MIN = 60

# Classificação por cor (HSV)
COR_PRATA_S_MAX = 30
SATURACAO_1_REAL_MIN = 50
SATURACAO_1_REAL_MAX = 90

# Detecção de círculos (Hough)
HOUGH_DP = 1.2
HOUGH_MIN_DIST = 100
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 100
HOUGH_MIN_RADIUS = 20
HOUGH_MAX_RADIUS = 200

# Pré-processamento
BLUR_KERNEL_SIZE = (9, 9)
BLUR_SIGMA = 2


# ====================== CÂMERA ======================

CAMERA_ID = 0
INTERVALO_SEGUNDOS = 0.01


# ====================== ARDUINO ======================

ARDUINO_PORT = "COM3"
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT = 2
TEMPO_ESPERA_ARDUINO = 2


# ====================== DETECÇÃO ======================

TIMEOUT_SEM_MOEDA = 2.0


# ====================== VISUALIZAÇÃO ======================

TITULO_JANELA = "Deteccao de Moedas"

COR_CIRCULO_DETECCAO = (0, 255, 0)
COR_TEXTO_RESULTADO = (255, 0, 0)
COR_TEXTO_STATUS = (0, 255, 0)
COR_TEXTO_AGUARDANDO = (200, 200, 200)

ESPESSURA_CIRCULO = 2
ESPESSURA_FONTE = 2
ESPESSURA_FONTE_STATUS = 2

TAMANHO_FONTE_RESULTADO = 0.5
TAMANHO_FONTE_STATUS = 0.6
TAMANHO_FONTE_AGUARDANDO = 0.7

OFFSET_TEXTO_X = 40
POS_STATUS_X = 10
POS_STATUS_Y = 30
ESPACAMENTO_LINHAS_STATUS = 30

TAMANHO_LINHA_SEPARADORA = 60


# ====================== INTERFACE ======================

TEMPO_ESPERA_TECLA = 1
TECLA_SAIR = 27


def desenhar_dados_calibracao(frame, x, y, raio, h, s, v):
    if not MODO_CALIBRACAO:
        return frame
    linhas = [
        f"Raio : {raio}px",
        f"H : {int(h)}",
        f"S : {int(s)}",
        f"V : {int(v)}"
    ]
    yTexto = y + raio + 20
    for i, texto in enumerate(linhas):
        cv2.putText(
            frame,
            texto,
            (x - 50, yTexto + i*18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0,255,255),
            1
        )
    return frame

def imprimir_dados_calibracao(raio, h, s, v):
    if not MODO_CALIBRACAO:
        return
    print("--------------------------------")
    print(f"Raio.......: {raio}")
    print(f"Hue........: {int(h)}")
    print(f"Saturacao..: {int(s)}")
    print(f"Value......: {int(v)}")

# GERENCIAMENTO DE COMUNICAÇÃO COM ARDUINO===========================================================================
class ComunicadorArduino:

    def __init__(self, porta=ARDUINO_PORT, baudrate=ARDUINO_BAUDRATE):
        self.porta = porta
        self.baudrate = baudrate
        self.conexao = None
        self.conectado = False
    
    def conectar(self):
        try:
            self.conexao = serial.Serial(
                port=self.porta,
                baudrate=self.baudrate,
                timeout=ARDUINO_TIMEOUT
            )
            time.sleep(TEMPO_ESPERA_ARDUINO)  # Aguarda inicialização do Arduino
            self.conectado = True
            print(f"✓ Arduino conectado em {self.porta}")
            return True
        except serial.SerialException as e:
            print(f"✗ Erro ao conectar ao Arduino: {e}")
            self.conectado = False
            return False
    
    def desconectar(self):
        if self.conexao and self.conexao.is_open:
            self.conexao.close()
            self.conectado = False
            print("Arduino desconectado")
    
    def enviar_valor(self, valor_moeda):
        if not self.conectado or not self.conexao:
            print(f"→ Arduino desconectado. Console: {valor_moeda}")
            return False
        try:
            mensagem = f"{valor_moeda}\n"
            self.conexao.write(mensagem.encode())
            print(f"→ Enviado para Arduino: {valor_moeda}")
            return True
        except serial.SerialException as e:
            print(f"✗ Erro ao enviar para Arduino: {e}")
            return False
    
    def ler_resposta(self):
        if not self.conectado or not self.conexao:
            return None
        try:
            if self.conexao.in_waiting:
                resposta = self.conexao.readline().decode().strip()
                return resposta
        except serial.SerialException as e:
            print(f"✗ Erro ao ler do Arduino: {e}")
        return None
    
    def listar_portas_disponiveis(self):
        portas = list_ports.comports()
        portas_disponiveis = [porta.device for porta in portas]
        return portas_disponiveis



# FUNÇÕES DE PROCESSAMENTO DE IMAGEM
def inicializar_camera(camera_id=CAMERA_ID):
    return cv2.VideoCapture(camera_id)

def preparar_frame_para_deteccao(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, BLUR_KERNEL_SIZE, BLUR_SIGMA)
    return gray

def detectar_circulos(gray_frame):
    circles = cv2.HoughCircles(
        gray_frame,
        cv2.HOUGH_GRADIENT,
        dp=HOUGH_DP,
        minDist=HOUGH_MIN_DIST,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=HOUGH_MIN_RADIUS,
        maxRadius=HOUGH_MAX_RADIUS
    )
    if circles is not None:
        return circles[0].astype(int)
    return None


# FUNÇÃO DE EXTRAÇÃO DO MAIOR CÍRCULO
def extrair_maior_circulo(circles):
    x, y, r = max(circles, key=lambda c: c[2])
    return x, y, r


# FUNÇÃO DE EXTRAÇÃO DE CORES
def extrair_cores_hsv(frame, x, y, raio):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.circle(mask, (x, y), raio, 255, -1)
    h, s, v, _ = cv2.mean(hsv, mask=mask)
    return h, s, v


# FUNÇÕES DE DETECÇÃO E CLASSIFICAÇÃO
def detectar_cor(h, s):
    if s < COR_PRATA_S_MAX:
        return "Prata"
    else:
        return "Colorida"


# FUNÇÃO DE DETECÇÃO DE TAMANHO
def detectar_tamanho(raio):
    if raio >= TAMANHO_GRANDE_MIN:
        return "Grande"
    elif raio >= TAMANHO_MEDIO_MIN:
        return "Medio"
    elif raio >= TAMANHO_PEQUENO_MIN:
        return "Pequeno"
    else:
        return "Muito pequeno"


# FUNÇÃO DE CLASSIFICAÇÃO DE MOEDAS
def classificar_moeda(raio, cor, saturacao):
    if raio >= TAMANHO_GRANDE_MIN:
        if SATURACAO_1_REAL_MIN <= saturacao <= SATURACAO_1_REAL_MAX:
            return "1 Real"
        elif cor == "Colorida":
            return "25 Cent"
        else:
            return "Desconhecido"

    elif raio >= TAMANHO_MEDIO_MIN:
        if cor == "Colorida":
            return "5 Cent"
        elif cor == "Prata":
            return "50 Cent"
        else:
            return "Desconhecido"

    elif raio >= TAMANHO_PEQUENO_MIN:
        return "10 Cent" if cor == "Colorida" else "Desconhecido"
    
    else:
        return "Desconhecido"


# FUNÇÕES DE VISUALIZAÇÃO
def desenhar_resultado(frame, x, y, raio, valor, tamanho, cor):
    # Desenha círculo
    cv2.circle(frame, (x, y), raio, COR_CIRCULO_DETECCAO, ESPESSURA_CIRCULO)
    # Desenha texto
    texto = f"{valor}\nTamanho: {tamanho}\nCor: {cor}"
    cv2.putText(
        frame,
        texto,
        (x - OFFSET_TEXTO_X, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        TAMANHO_FONTE_RESULTADO,
        COR_TEXTO_RESULTADO,
        ESPESSURA_FONTE
    )
    return frame


def imprimir_resultado(valor, tamanho, cor):
    print(f"{valor} - Tamanho: {tamanho}, Cor: {cor}")


def imprimir_resultado_final(resultado, comunicador_arduino=None):
    if resultado is None:
        return
    
    print("\n" + "="*TAMANHO_LINHA_SEPARADORA)
    print("✓ MOEDA SAIU DE CENA - RESULTADO FINAL")
    print("="*TAMANHO_LINHA_SEPARADORA)
    print(f"Valor detectado: {resultado['valor']}")
    print(f"Confiança: {resultado['confianca']}%")
    print(f"Duração na câmera: {resultado['duracao']:.2f}s")
    print(f"Total de detecções: {resultado['total_deteccoes']}")
    print("="*TAMANHO_LINHA_SEPARADORA + "\n")
    
    # Envia para Arduino
    if comunicador_arduino:
        comunicador_arduino.enviar_valor(resultado['valor'])



# FUNÇÃO DE DESENHO DE STATUS DE DETECÇÃO
def desenhar_status_deteccao(frame, detector_moeda):
    status = detector_moeda.obter_status()
    
    if status is None:
        # Nenhuma moeda sendo detectada
        cv2.putText(
            frame,
            "Aguardando moeda...",
            (POS_STATUS_X, POS_STATUS_Y),
            cv2.FONT_HERSHEY_SIMPLEX,
            TAMANHO_FONTE_AGUARDANDO,
            COR_TEXTO_AGUARDANDO,
            ESPESSURA_FONTE_STATUS
        )
    else:
        # Moeda em processo de detecção
        y_inicio = POS_STATUS_Y
        info_linhas = [
            f"Detectando: {status['valor_provisorio']}",
            f"Tempo: {status['tempo_decorrido']:.1f}s",
            f"Deteccoes: {status['total_deteccoes']}"
        ]
        
        for i, linha in enumerate(info_linhas):
            cv2.putText(
                frame,
                linha,
                (POS_STATUS_X, y_inicio + i * ESPACAMENTO_LINHAS_STATUS),
                cv2.FONT_HERSHEY_SIMPLEX,
                TAMANHO_FONTE_STATUS,
                COR_TEXTO_STATUS,
                ESPESSURA_FONTE_STATUS
            )
    
    return frame



# GERENCIAMENTO DE DETECÇÃO DE MOEDAS EM MOVIMENTO
class DetectorMoedaEmMovimento:
    def __init__(self, timeout_sem_moeda=TIMEOUT_SEM_MOEDA):
        self.timeout_sem_moeda = timeout_sem_moeda
        self.em_deteccao = False
        self.tempo_inicio = None
        self.historico_deteccoes = []
        self.ultima_deteccao = None
        self.posicao_anterior = None
        
    def adicionar_deteccao(self, valor, tamanho, cor, x, y, raio, tempo_atual):
        if not self.em_deteccao:
            self.iniciar_deteccao(tempo_atual)
        deteccao = {
            "valor": valor,
            "tamanho": tamanho,
            "cor": cor,
            "x": x,
            "y": y,
            "raio": raio,
            "tempo": tempo_atual
        }
        self.historico_deteccoes.append(deteccao)
        self.ultima_deteccao = tempo_atual
        self.posicao_anterior = (x, y)
    
    def iniciar_deteccao(self, tempo_atual):
        self.em_deteccao = True
        self.tempo_inicio = tempo_atual
        self.historico_deteccoes = []
        self.ultima_deteccao = tempo_atual
        
    def finalizar_deteccao(self):
        if not self.em_deteccao or not self.historico_deteccoes:
            return None
        
        duracao = self.ultima_deteccao - self.tempo_inicio
        total_deteccoes = len(self.historico_deteccoes)
        valor_mais_provavel = self._obter_valor_mais_provavel()
        confianca = self._calcular_confianca()
        
        resultado = {
            "valor": valor_mais_provavel,
            "confianca": confianca,
            "duracao": duracao,
            "total_deteccoes": total_deteccoes,
            "historico": self.historico_deteccoes
        }
        
        # Reset
        self.em_deteccao = False
        self.tempo_inicio = None
        self.historico_deteccoes = []
        self.ultima_deteccao = None
        self.posicao_anterior = None
        
        return resultado
    
    def verificar_timeout(self, tempo_atual):
        if not self.em_deteccao:
            return None

        tempo_sem_moeda = tempo_atual - self.ultima_deteccao
        
        if tempo_sem_moeda >= self.timeout_sem_moeda:
            return self.finalizar_deteccao()
        
        return None
    
    def _obter_valor_mais_provavel(self):
        if not self.historico_deteccoes:
            return "Desconhecido"
        
        # Conta ocorrências de cada valor
        contagem_valores = {}
        for deteccao in self.historico_deteccoes:
            valor = deteccao["valor"]
            contagem_valores[valor] = contagem_valores.get(valor, 0) + 1
        
        # Retorna o mais frequente
        valor_mais_provavel = max(contagem_valores, key=contagem_valores.get)
        return valor_mais_provavel
    
    def _calcular_confianca(self):
        if not self.historico_deteccoes:
            return 0.0
        
        contagem_valores = {}
        for deteccao in self.historico_deteccoes:
            valor = deteccao["valor"]
            contagem_valores[valor] = contagem_valores.get(valor, 0) + 1
        
        max_ocorrencias = max(contagem_valores.values())
        total = len(self.historico_deteccoes)
        confianca = (max_ocorrencias / total) * 100
        
        return round(confianca, 2)
    
    def obter_status(self):
        if not self.em_deteccao:
            return None
        
        tempo_decorrido = self.ultima_deteccao - self.tempo_inicio if self.tempo_inicio else 0
        
        return {
            "em_deteccao": self.em_deteccao,
            "tempo_decorrido": round(tempo_decorrido, 2),
            "total_deteccoes": len(self.historico_deteccoes),
            "valor_provisorio": self._obter_valor_mais_provavel() if self.historico_deteccoes else "Aguardando..."
        }



# FUNÇÃO PRINCIPAL
def processar_frame(frame, tempo_atual, ultimo_processamento, detector_moeda):
    tempo_decorrido = tempo_atual - ultimo_processamento
    resultado_final = None
    
    # Processa apenas se passou o intervalo mínimo
    if tempo_decorrido < INTERVALO_SEGUNDOS:
        # Verifica timeout mesmo sem processar novo frame
        resultado_final = detector_moeda.verificar_timeout(tempo_atual)
        return frame, ultimo_processamento, resultado_final
    
    # Prepara o frame
    gray = preparar_frame_para_deteccao(frame)
    
    # Detecta círculos
    circles = detectar_circulos(gray)
    
    if circles is not None:
        # Extrai o maior círculo
        x, y, raio = extrair_maior_circulo(circles)
        # Extrai cores
        h, s, v = extrair_cores_hsv(frame, x, y, raio)
        imprimir_dados_calibracao(raio, h, s, v)
        # Detecta propriedades
        cor = detectar_cor(h, s)
        tamanho = detectar_tamanho(raio)
        valor = classificar_moeda(raio, cor, s)
        # Adiciona ao histórico de detecção
        detector_moeda.adicionar_deteccao(valor, tamanho, cor, x, y, raio, tempo_atual)
        # Desenha no frame
        frame = desenhar_resultado(frame, x, y, raio, valor, tamanho, cor)
        frame = desenhar_dados_calibracao(frame, x, y, raio, h, s, v)
    
    else:
        # Nenhuma moeda detectada - verifica timeout
        resultado_final = detector_moeda.verificar_timeout(tempo_atual)
    
    return frame, tempo_atual, resultado_final



# FUNÇÃO PRINCIPAL
def main():
    cap = inicializar_camera()

    if not cap.isOpened():
        print("Erro: Não foi possível abrir a câmera")
        return
    
    # Inicializa comunicador Arduino
    comunicador_arduino = ComunicadorArduino(porta=ARDUINO_PORT)
    
    # Tenta conectar ao Arduino (não falha se não conseguir)
    if not comunicador_arduino.conectar():
        print("Continuando sem Arduino (valores serão apenas exibidos no console)")
    
    ultimo_processamento = time.time()
    detector_moeda = DetectorMoedaEmMovimento(timeout_sem_moeda=TIMEOUT_SEM_MOEDA)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            tempo_atual = time.time()
            
            # Processa frame e detecta moedas
            frame, ultimo_processamento, resultado_final = processar_frame(
                frame,
                tempo_atual,
                ultimo_processamento,
                detector_moeda
            )
            
            # Se uma moeda saiu de cena, exibe resultado final
            if resultado_final:
                imprimir_resultado_final(resultado_final, comunicador_arduino)
            
            # Desenha status de detecção no frame
            frame = desenhar_status_deteccao(frame, detector_moeda)
            
            cv2.imshow(TITULO_JANELA, frame)
            
            # ESC para sair
            if cv2.waitKey(TEMPO_ESPERA_TECLA) == TECLA_SAIR:
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        comunicador_arduino.desconectar()



if __name__ == "__main__":
    print("Portas seriais disponíveis:")
    comunicador_teste = ComunicadorArduino()
    portas = comunicador_teste.listar_portas_disponiveis()
    if portas:
        for porta in portas:
            print(f"  - {porta}")
    else:
        print("  Nenhuma porta encontrada")
    print(f"\nUsando porta: {ARDUINO_PORT}\n")
    main()