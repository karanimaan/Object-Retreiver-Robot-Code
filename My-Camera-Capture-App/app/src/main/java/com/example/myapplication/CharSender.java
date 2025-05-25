package com.example.myapplication;

import java.io.IOException;
import java.io.PrintWriter;
import java.net.Socket;

// Sends a single character to the ESP32
class CharSender implements Runnable {
    private final char command;

    CharSender(char command) {
        this.command = command;
    }
    @Override
    public void run() {
        try {
            // Creates a socket and connects it to the specified port number on the specified host
            Socket client = new Socket("192.168.4.1", 80);

            PrintWriter printwriter = new PrintWriter(client.getOutputStream(), true);
            printwriter.write(command); // write the message to output stream

            printwriter.flush();
            printwriter.close();

            // closing the connection
            client.close();

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}


