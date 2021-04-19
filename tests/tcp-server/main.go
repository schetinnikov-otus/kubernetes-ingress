package main

import (
	"flag"
	"fmt"
	"log"
	"net"
)

func main() {
	port := flag.String("port", "3333", "Port")
	host := flag.String("host", "127.0.0.1", "Host or IP")
	response := flag.String("response", "", "Optional response value")
	flag.Parse()

	if *response == "" {
		*response = fmt.Sprintf("%v:%v", *host, *port)
	}

	l, err := net.Listen("tcp", fmt.Sprintf("%v:%v", *host, *port))
	if err != nil {
		log.Panicln(err)
	}
	defer l.Close()
	log.Printf("listening to tcp connections at: %v:%v\n", *host, *port)
	log.Printf("responding with: %v\n", *response)

	for {
		conn, err := l.Accept()
		if err != nil {
			log.Panicln(err)
		}

		go handleRequest(conn, *response)
	}
}

func handleRequest(conn net.Conn, response string) {
	log.Println("accepted new connection")
	defer conn.Close()
	defer log.Println("closed connection")
	log.Printf("write data to connection: %v\n", response)
	_, err := conn.Write([]byte(response))
	if err != nil {
		log.Printf("error writing to connection: %v", err)
		return
	}
}
