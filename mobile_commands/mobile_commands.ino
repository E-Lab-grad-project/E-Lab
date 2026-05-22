#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// Wi-Fi Credentials
const char* ssid = "Diaa's Galaxy";
const char* password = "12345678";

// ThingsBoard MQTT settings
const char* mqttServer = "eu.thingsboard.cloud"; // Or your ThingsBoard server
const int mqttPort = 1883;
const char* accessToken = "bSRABPjxL4BM8IerNebk"; // Paste your device's token here

// DHT settings
#define DHTPIN 4     // GPIO connected to DHT11 data pin
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Initialize MQTT Client
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Function to connect to Wi-Fi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected.");
}

// Function to connect to ThingsBoard MQTT server
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to ThingsBoard...");
    if (client.connect("ESP32", accessToken, "")) {
      Serial.println("Connected.");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds.");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Read temperature and humidity from DHT11
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Check if readings are valid
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  // Create JSON payload
  String payload = "{";
  payload += "\"temperature\":"; payload += temperature; payload += ",";
  payload += "\"humidity\":"; payload += humidity;
  payload += "}";

  // Publish data to ThingsBoard
  Serial.print("Publishing data: ");
  Serial.println(payload);
  client.publish("v1/devices/me/telemetry", payload.c_str());

  // Wait 10 seconds before sending the next data
  delay(10000);
}