/*
 *  QCL's Naive Weather Center
 *
 *  2014.09.24
 *  Qing-Cheng Li <qc.linux at gmail.com>
 * 
 *  It's a Arduino test, use sensor and network module, 
 *  detect the humidity and temperature, then upload the 
 *  data to server.
 *
 *  Layout
 *      -   TODO/FIMXE
 *  Module
 *      -   TODO/FIXME
 *  Library
 *      - DHT
 *      - TODO/FIXME
 * */

#include <dht.h>
#include <EtherCard.h>

/*  Network setting  */
static byte mac_address[] = {0x74,0x69,0x69,0x2D,0x30,0x31};
boolean network_is_ok = false;
byte Ethernet::buffer[700];
BufferFiller bfill;
unsigned long timer = 0;

unsigned long delay_time = 1000*2;  //2 sec
boolean is_overflow = false;

double current_temperature;

#define dht_dpin A0

dht DHT;

static word homePage(){
    long t = millis()/1000;
    word h = t/3600;
    byte m = (t/60)%60;
    byte s = t%60;

    bfill = ether.tcpOffset();
    bfill.emit_p(PSTR(
        "HTTP/1.0 200 OK\n"
        "Content-Type: text/html\n"
        "Pragma: no-cache\n"
        "\n"
        "<!DOCTYPE html><html><head><title>qcl's Weather Center</title></head>"
        "<body><h1>qcl's Weather Center</h1><h1>$D C / $D %</h1><p>Arduino UNO start time: $D:$D$D:$D$D</p></body"),
        (int)DHT.temperature,(int)DHT.humidity,h,m/10,m%10,s/10,s%10);
    return bfill.position();
}

/*  Arduino setup & loop */
/*
 *  setup
 * */
void setup(){
    
    //Setup serial
    Serial.begin(57600);
    Serial.println("qcl's naive weather center start init.");
  
    //Network
    Serial.println("-- init network...");
    if(ether.begin(sizeof Ethernet::buffer,mac_address)==0){
        Serial.println("Failed to access Ethernet controller.");
    }

    if(!ether.dhcpSetup()){
        Serial.println("DHCP failed.");
    }else{
        network_is_ok = true;
    }

    if(network_is_ok){
        ether.printIp("IP      = ",ether.myip);
        ether.printIp("Netmask = ",ether.netmask);
        ether.printIp("Gateway = ",ether.gwip);
        ether.printIp("DNS     = ",ether.dnsip);
    }

    //Humidity&Temperature
    Serial.println("-- init humidity & temperature sensor...");
    delay(1000);    //just give it some time.
 
    //Timer
    timer = 0; 

    Serial.println("qcl's Arduino UNO is ready.");
}

/*
 *  loop
 * */
void loop(){

    word len = ether.packetReceive();
    word pos = ether.packetLoop(len);

    if(pos){
        ether.httpServerReply(homePage());
        Serial.println("get http request.");
    }

    if(!is_overflow&&millis()>timer){
        
        DHT.read11(dht_dpin);

        current_temperature = DHT.temperature;

        Serial.print("Humidity = ");
        Serial.print(DHT.humidity);
        Serial.print("% ");
        Serial.print(", Temperature = ");
        Serial.print(current_temperature);
        Serial.println("C ");
  
        Serial.println(millis());

        timer+=delay_time;
        if(timer<delay_time){   //timer overflow
            is_overflow = true;
        }

    }

    //timer overflow, and millis() is also overflow, 
    //so let the overflow flag be false, which means
    //here is no overflow :p
    if(is_overflow&&millis()<delay_time){
        is_overflow = false;
    }

    //response to request.

  
}
