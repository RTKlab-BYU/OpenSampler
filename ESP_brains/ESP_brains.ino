void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.flush();
}

String formatName (String pin_name) {
  if (pin_name.substring(1,2) == "0") {
    pin_name = pin_name.substring(0,1) + pin_name.substring(2,4);
  }
  return pin_name;

}
void loop() {
  if (Serial.available() > 0){
    String input_string = Serial.readStringUntil('\n');
    if (input_string.substring(0,12) == "config_input"){
      String pin_string = input_string.substring(14,16);
      int pin = pin_string.toInt();
      pinMode(pin, INPUT_PULLUP);
    }
    else if (input_string.substring(0,5) == "input"){
      String pin_string = input_string.substring(7,9);
      int pin = pin_string.toInt();
      int pin_state = digitalRead(pin);
      String output_string = "pin " + input_string + " logic";
      if (pin_state == HIGH) {
        output_string = "pin " + pin_string + " on";
      } 
      else if (pin_state == LOW) {
        output_string = "pin " + pin_string + " off";      
      } 
      else {
        output_string = "pin " + pin_string + " error";            
      }
      Serial.println(output_string);
    } 
    else if (input_string.substring(0,13) == "config_output") {
      String pin_string = input_string.substring(15,17);
      int pin = pin_string.toInt();
      pinMode(pin, OUTPUT);
    } 
    else if (input_string.substring(0,7) == "turn_on") {
      String pin_string = input_string.substring(9,11);
      int pin = pin_string.toInt();
      digitalWrite(pin, HIGH);  
    } 
    else if (input_string.substring(0,8) == "turn_off") {
      String pin_string = input_string.substring(10,12);
      int pin = pin_string.toInt();
      digitalWrite(pin, LOW);
    }
    delay(100);  
  }                                            
}
