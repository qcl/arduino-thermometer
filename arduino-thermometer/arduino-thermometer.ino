/*
 *  QCL's Naive Weather Center
 *
 *  2014.09.26
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
static byte session;
boolean network_is_ok = false;
byte Ethernet::buffer[700];
BufferFiller bfill;
Stash stash;

unsigned long timer = 0;
unsigned long delay_time = 60000;  //update freq: 1 min
unsigned long overflow_count = 0;
boolean is_overflow = false;

const char remote_server[] PROGMEM = "qcl-thermometer.appspot.com";

/*  DHT11 setting  */
#define dht_dpin A0
dht DHT;

/*
 *  homePage()
 *
 *  Simple web server, return a webpage that shows the start time
 *  and current temperature and humidity.
 * */
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
        "<body><h1>qcl's Weather Center</h1><h1>$D C / $D %</h1>"
        "<p>Arduino UNO start time: $D:$D$D:$D$D</p>"
        "<p>Check more information on <a href='http://$F'>remote server</a></p></body>"),
        (int)DHT.temperature,(int)DHT.humidity,h,m/10,m%10,s/10,s%10,remote_server);
    return bfill.position();
}

/*
 *  handelResponse(byte status, word off, word len)
 *
 *  handel the response after call ehter.browseUrl(),
 *  it's a response of http get
 * */
static void handelResponse(byte status, word off, word len){
    Serial.println("browseUrl got response.");
    EtherCard::buffer[off+300] = 0;
    Serial.print((const char*) EtherCard::buffer + off);
    Serial.println("...");
}

/*
 *  postDataToRemoteServer()
 *  
 *  post the temperature and humidity to remote server.
 * */
static void postDataToRemoteServer(){
    Serial.println("prepare to send data to remote server...");
    byte sd = stash.create();

    stash.print("temp=");
    stash.print(DHT.temperature);
    stash.print("&humi=");
    stash.print(DHT.humidity);
    stash.print("&device=");
    stash.println("uno");
    stash.save();

    int stash_size = stash.size();

    Stash::prepare(PSTR("POST http://$F/thermometer HTTP/1.0" "\r\n"
            "Host: $F" "\r\n"
            "Content-Length: $D" "\r\n"
            "\r\n"
            "$H"),
            remote_server,remote_server,stash_size,sd);

    session = ether.tcpSend();

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

    
    if(!ether.dnsLookup(remote_server)){
        Serial.println("[!]DNS fail");
    }else{
        ether.printIp("SRV: ",ether.hisip);
    }
    

    //Humidity&Temperature
    Serial.println("-- init humidity & temperature sensor...");
    delay(1000);    //just give it some time.
 
    //Timer
    timer = 0;
    Serial.print("timer=");
    Serial.print(timer);
    Serial.print(",delay_time=");
    Serial.println(delay_time);

    Serial.println("qcl's Arduino UNO is ready.");
}

/*
 *  loop
 * */
void loop(){

    word len = ether.packetReceive();
    word pos = ether.packetLoop(len);

    //response to request.
    if(pos){
        Serial.println("get http request.");
        ether.httpServerReply(homePage());
    }

    //check post reply
    const char* reply = ether.tcpReply(session);
    if(reply!=0){
        Serial.println("get reply!");
        Serial.println(reply);
    }

    //get temperature and humidity
    if(!is_overflow&&millis()>timer){
        
        DHT.read11(dht_dpin);

        Serial.print("Humidity = ");
        Serial.print(DHT.humidity);
        Serial.print("% ");
        Serial.print(", Temperature = ");
        Serial.print(DHT.temperature);
        Serial.println("C ");

        //http get test
        //ether.browseUrl(PSTR("/"),"",remote_server,handelResponse);

        //post DHT data to server
        postDataToRemoteServer();        

        //update timer
        timer+=delay_time;
        if(timer<delay_time){   //timer overflow
            Serial.println("Timer overflow");
            is_overflow = true;
        }

    }

    //timer overflow, and millis() is also overflow, 
    //so let the overflow flag be false, which means
    //here is no overflow :p
    if(is_overflow&&millis()<delay_time){
        is_overflow = false;
        overflow_count += 1;
    }
  
}
