#include <Adafruit_LiquidCrystal.h>
#include <Servo.h>

// OBJETOS
Adafruit_LiquidCrystal lcd(0);
Servo servoA;
Servo servoB;
Servo servoC;
Servo servoD;

// CONSTANTES
const int MOTOR_PWM = 3;           // Pino PWM ligado ao TIP120
int VELOCIDADE_MOTOR = 100;        // 0 a 255

const int SERVO_A = 4;
const int SERVO_B = 5;
const int SERVO_C = 6;
const int SERVO_D = 7;

const int ESQUERDA = 30;
const int DIREITA = 120;

//valores a serem ajustados para cada servo
const int A_1REAL = 30;
const int A_OUTRAS = 120;

const int B_25_50 = 30;
const int B_10_5 = 120;

const int C_25 = 30;
const int C_50 = 120;

const int D_5 = 30;
const int D_10 = 120;

// VARIÁVEIS GLOBAIS
int soma_total = 0;              // Soma acumulada de todas as moedas
int valor_moeda_atual = 0;       // Valor da moeda recebida
String buffer_serial = "";       // Buffer para armazenar dados seriais
unsigned long ultima_moeda = 0;  // Timestamp da última moeda recebida


// FUNÇÕES DE MAPEAMENTO
int obter_valor_moeda(String moeda) {
  moeda.toLowerCase();  // Converte para minúsculas
  if      (moeda.indexOf("1 real")  != -1 || moeda.indexOf("1real")  != -1) return 100;
  else if (moeda.indexOf("50 cent") != -1 || moeda.indexOf("50cent") != -1) return 50;
  else if (moeda.indexOf("25 cent") != -1 || moeda.indexOf("25cent") != -1) return 25;
  else if (moeda.indexOf("10 cent") != -1 || moeda.indexOf("10cent") != -1) return 10;
  else if (moeda.indexOf("5 cent")  != -1 || moeda.indexOf("5cent")  != -1) return 5;
  else return 0;  // Desconhecido
}


// FUNÇÕES DE FORMATAÇÃO
String formatar_valor_moeda(int centavos) {
  if (centavos >= 100) {
    int reais = centavos / 100;
    int cents = centavos % 100;
    if (cents == 0) {
      return String(reais) + " Real";
    } else {
      return String(reais) + "." + (cents < 10 ? "0" : "") + String(cents);
    }
  } else {
    return String(centavos) + " Cent";
  }
}


// Converte centavos para reais (float)
float centavos_para_reais(int centavos) {
  return centavos / 100.0;
}


// FUNÇÕES DE COMUNICAÇÃO SERIAL
void processar_dados_serial() { // Verifica se há dados disponíveis
  while (Serial.available() > 0) {
    char caractere = Serial.read();
    if (caractere == '\n') {                      // Se é quebra de linha, processa o valor
      if (buffer_serial.length() > 0) {
        processador_moeda_recebida(buffer_serial);
        buffer_serial = "";                       // Limpa o buffer
      }
    } else if (caractere != '\r') {               // Se não é quebra de linha, acumula no buffer
      buffer_serial += caractere;
    }
  }
}


// FUNÇÃO PRINCIPAL DE PROCESSAMENTO
void processador_moeda_recebida(String nome_moeda) {
  valor_moeda_atual = obter_valor_moeda(nome_moeda);
  soma_total += valor_moeda_atual;
  ultima_moeda = millis();
  posicionar_servos(valor_moeda_atual);
  exibir_no_serial(nome_moeda);
  atualizar_lcd();
}


// FUNÇÕES DE EXIBIÇÃO SERIAL
void exibir_no_serial(String nome_moeda) {
  Serial.println("=====================================");
  Serial.print("✓ Moeda recebida: ");
  Serial.println(nome_moeda);
  Serial.print("  Valor: ");
  Serial.print(valor_moeda_atual);
  Serial.println(" centavos");
  Serial.print("  Valor: R$ ");
  Serial.println(centavos_para_reais(valor_moeda_atual), 2);
  Serial.print("  Soma total: R$ ");
  Serial.println(centavos_para_reais(soma_total), 2);
  Serial.println("=====================================");
}


// FUNÇÕES DE DISPLAY
void atualizar_lcd() {
  lcd.clear();
  // Linha 1: Moeda atual
  lcd.setCursor(0, 0);
  lcd.print("M: R$ ");
  lcd.print(centavos_para_reais(valor_moeda_atual), 2);
  // Linha 2: Soma total
  lcd.setCursor(0, 1);
  lcd.print("Total: R$ ");
  lcd.print(centavos_para_reais(soma_total), 2);
}


// Exibe mensagem de espera se não houver moeda recentemente
void exibir_esperando() {
  // Se não houve moeda recentemente, mostra mensagem
  if (millis() - ultima_moeda > 3000) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Aguardando...");
    lcd.setCursor(0, 1);
    lcd.print("Total: R$ ");
    lcd.print(centavos_para_reais(soma_total), 2);
  }
}


// FUNÇÕES Do MOTOR principal
void ligar_motor_breve(){
  analogWrite(MOTOR_PWM, VELOCIDADE_MOTOR);
  delay(200);
  analogWrite(MOTOR_PWM, 0);
}


// Função do servo motor
void posicionar_servos(int moeda){
  switch (moeda)  {
  case 100: // 1 Real
    servoA.write(A_1REAL);
    break;
  case 50: // 50 centavos
    servoA.write(A_OUTRAS);
    servoB.write(B_25_50);
    servoC.write(C_50);
    break;
  case 25: // 25 centavos
    servoA.write(A_OUTRAS);
    servoB.write(B_25_50);
    servoC.write(C_25);
    break;
  case 10: // 10 centavos
    servoA.write(A_OUTRAS);
    servoB.write(B_10_5);
    servoD.write(D_10);
    break;
  case 5: // 5 centavos
    servoA.write(A_OUTRAS);
    servoB.write(B_10_5);
    servoD.write(D_5);
    break;
  }
  delay(250);
}


// SETUP E LOOP
void setup() {
  
  Serial.begin(9600); // Inicializa Serial com 9600 baud (mesmo do Python)
  analogWrite(MOTOR_PWM, VELOCIDADE_MOTOR);
  
  // Aguarda conexão serial
  delay(2000);
  servoA.attach(SERVO_A);
  servoB.attach(SERVO_B);
  servoC.attach(SERVO_C);
  servoD.attach(SERVO_D);

  // posição inicial
  servoA.write(A_OUTRAS);
  servoB.write(B_25_50);
  servoC.write(C_25);
  servoD.write(D_5);

  // Configura pinos do motor
  pinMode(MOTOR_PWM, OUTPUT);
  analogWrite(MOTOR_PWM, 0);
  pinMode(A1, INPUT);
  pinMode(A0, INPUT);
  
  // Inicializa LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sistema Pronto!");
  lcd.setCursor(0, 1);
  lcd.print("Total: R$ 0.00");
  
  // Mensagem inicial no Serial
  Serial.println("\n========================================");
  Serial.println("Sistema de Deteccao de Moedas");
  Serial.println("Aguardando moedas...");
  Serial.println("========================================\n");
}


// Loop principal
void loop() {
  processar_dados_serial(); // Processa dados recebidos da porta serial
  exibir_esperando();       // Exibe estado de espera se necessário
  delay(50);                // Pequeno delay para evitar sobrecarga
}