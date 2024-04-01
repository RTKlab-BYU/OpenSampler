void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.flush();
}

String formatName (String pin_name) {
  if (pin_name.substring(1,2) == "0") {
    pin_name = pin_name.substring(0,1) + pin_name.substring(2,4);
  }
  if (pin_name.substring(0,1) == "D") {
    pin_name = pin_name.substring(1,pin_name.length());
  }
  return pin_name;
}
void loop() {
  // put your main code here, to run repeatedly:
  String input_string = "";
  input_string = Serial.readStringUntil('\n');
  //Serial.println(input_string);
  if (input_string.substring(0,12) == "config_input"){
      String output_string = "D" + input_string.substring(14,16);
      output_string = formatName(output_string);
      uint8_t pinIn =  atoi (output_string.c_str ());
      pinMode(pinIn, INPUT);
     // Serial.println("configured");
  } else if (input_string.substring(0,5) == "input"){
    String pin_string = "D" + input_string.substring(7,9);
    input_string = input_string.substring(6,9);
    String output_string = formatName(pin_string);
    uint8_t inPin =  atoi (output_string.c_str ());
    //pinMode(inPin, INPUT);
    int pin_state = digitalRead(inPin);
    output_string = "pin" + input_string + " logic";
    if (pin_state == HIGH) {
      output_string = "pin" + input_string + " on";
    } else if (pin_state == LOW) {
      output_string = "pin" + input_string + " off";      
    } else {
      output_string = "pin" + input_string + " error";            
    }
    Serial.println(output_string);
   } else if (input_string.substring(0,13) == "config_output") {
     String output_string = "D" + input_string.substring(15,17);
     output_string = formatName(output_string);
     uint8_t outPin =  atoi (output_string.c_str ());
     pinMode(outPin, OUTPUT);
     //Serial.println("configured");
   } else if (input_string.substring(0,7) == "turn_on") {
     String output_string = "D" + input_string.substring(9, 11);
     output_string = formatName(output_string);
     uint8_t pinOut =  atoi (output_string.c_str ());
    // pinMode(pinOut, OUTPUT);
     digitalWrite(pinOut, HIGH);  
    // Serial.println("on");
   } else if (input_string.substring(0,8) == "turn_off") {
     String output_string = "D" + input_string.substring(10, 12);
     output_string = formatName(output_string);
     uint8_t pinOut = atoi (output_string.c_str());
    // pinMode(pinOut, OUTPUT);
     digitalWrite(pinOut, LOW); 
    // Serial.println("off");
   }
   delay(100);                                              
}
