void setup() {
  Serial.begin(115200);  // Set baud rate (must match Python script)
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  // Check if data is available
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Echo back received command
    Serial.print("Received: ");
    Serial.println(command);
    
    // Process commands
    if (command == "LED_ON") {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("LED turned ON");
    }
    else if (command == "LED_OFF") {
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("LED turned OFF");
    }
    else if (command == "GET_TEMP") {
      // Example: Read temperature (if available)
      Serial.println("Temperature: 25.5C");
    }
  }
  
  delay(10);  // Small delay
}