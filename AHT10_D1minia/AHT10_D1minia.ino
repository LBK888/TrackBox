#include <Wire.h>
#include <Adafruit_AHT10.h> // 使用 AHT10 的庫，需要先安裝 (可從 Library Manager 搜尋 "AHT10")

#define SDA_PIN D3         // I²C SDA 腳位
#define SCL_PIN D4         // I²C SCL 腳位
#define BUTTON_PIN D8      // 按鈕開關接 D8 (GPIO15)
#define LED_PIN D2      // 測量指示燈, LED_BUILTIN=D4已經被佔據 


Adafruit_AHT10 aht10;               // 初始化 AHT10 物件
Adafruit_Sensor *aht_humidity, *aht_temp;

bool isMeasuring = false;  // 測量狀態標誌
float filter_r=0.3;     //smoothing filter, 前一次數據，站新數據的filter_r, recommand = 0.2~0.5
float temperature_rec=0.0;
float humidity_rec=0.0;

void setup() {
  // 初始化序列埠
  Serial.begin(115200);
  while (!Serial); // 等待序列埠初始化（適用於部分開發板）

  //Measuring LED
  pinMode(LED_PIN, OUTPUT);  // Initialize the LED_PIN pin as an output

  // 初始化按鈕腳位
  pinMode(BUTTON_PIN, INPUT); // 按鈕接 3.3V，利用內建下拉電阻

  // 初始化 I²C
  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("I2C Initialized");

  // 初始化 AHT10
  if (aht10.begin()) {
    Serial.println("AHT10 sensor initialized successfully");
  } else {
    Serial.println("Failed to initialize AHT10 sensor!"); 
    while (1) { 
      delay(50);   // 如果感測器初始化失敗，停止執行
    }
  }

  aht_temp = aht10.getTemperatureSensor();
  aht_temp->printSensorDetails();

  aht_humidity = aht10.getHumiditySensor();
  aht_humidity->printSensorDetails();

  Serial.println("Waiting for START command...");


    //  /* Get a new normalized sensor event */
    sensors_event_t humidity;
    sensors_event_t temp;
    aht_humidity->getEvent(&humidity);
    aht_temp->getEvent(&temp);

    temperature_rec = temp.temperature; // 讀取溫度
    humidity_rec = humidity.relative_humidity;       // 讀取濕度
}

void loop() {
  // 檢查按鈕狀態
  if (digitalRead(BUTTON_PIN) == HIGH) { // 按鈕被按下（3.3V 高電平）
    delay(50); // 消除按鈕彈跳影響
    if (digitalRead(BUTTON_PIN) == HIGH) { // 確保按鈕保持按下狀態
      isMeasuring = !isMeasuring; // 切換測量狀態
      Serial.println(isMeasuring ? "Measuring started!" : "Measuring stopped!");
      delay(100); // 防止按鈕重複觸發
    }
  }

  // 檢查是否有來自 PC 的序列輸入
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // 讀取指令
    command.trim(); // 去除多餘空白

    if (command == "START") {
      isMeasuring = true;
      Serial.println("Measuring started...");
    } else if (command == "STOP") {
      isMeasuring = false;
      Serial.println("Measuring stopped...");
    }
  }

  digitalWrite(LED_PIN, LOW); //先關燈

  // 如果處於測量狀態，讀取數據並發送
  if (isMeasuring) {
    digitalWrite(LED_PIN, HIGH);

    //  /* Get a new normalized sensor event */
    sensors_event_t humidity;
    sensors_event_t temp;
    aht_humidity->getEvent(&humidity);
    aht_temp->getEvent(&temp);

    //apply ratio filter to smooth the reading
    temperature_rec = temperature_rec*filter_r + temp.temperature*(1-filter_r); // 讀取溫度
    humidity_rec = humidity_rec*filter_r +humidity.relative_humidity*(1-filter_r);       // 讀取濕度

    // 傳送溫濕度數據到序列埠
    if (!isnan(temperature_rec) && !isnan(humidity_rec)) {
      Serial.print("Temperature: ");
      Serial.print(temperature_rec, 1); // 保留一位小數
      Serial.print(" °C, Humidity: ");
      Serial.print(humidity_rec, 1); // 保留一位小數
      Serial.println(" %");
    } else {
      Serial.println("Failed to read data from AHT10 sensor!");
    }

    delay(200); // 每0.2秒傳送一次數據
    digitalWrite(LED_PIN, LOW);
  }
}
