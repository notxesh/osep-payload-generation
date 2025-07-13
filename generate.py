#!/usr/bin/env python3

import os
import re
import sys
import yaml
import string
import random
import argparse
import subprocess
import netifaces as ni
from jinja2 import Template
from typing import Callable
from base64 import b64encode, b64decode

"""
    Encoder
        Exposed to the templating engine to allow payloads to be encoded
"""
class Encoder:
    """
        UTF-8 Encoding
    """
    @staticmethod
    def utf8(data:str):
        return bytes(data,encoding='utf-8')
    """
        UTF-16-LE Encoding
    """
    @staticmethod
    def utf16le(data:str):
        return bytes(data,encoding='utf-16-le')
    """
        Base64 Encoding
            Defaults to utf-16-le encoding for powershell payloads
    """
    @staticmethod
    def base64(data:str, encoder:Callable):
        if type(encoder) == type(Encoder.base64):
            data = encoder(data)
        return b64encode(data).decode()

    @staticmethod
    def xor(data:str, key:str) -> str:
        # Convert the key and data from hex
        data = bytes.fromhex(data)
        key = bytes.fromhex(key)
        # do the xor
        retBytes = []
        for i in range(len(data)):
            retBytes.append(data[i]^key[i%len(key)])
        return bytes(retBytes).hex()

"""
    Helpers
        Any additional helpers to extend the jinja templating
"""
class Helpers:
    @staticmethod
    def len(data,blen=True) -> str:
        # blen == byte length aka data is hex so // 2
        return str(len(data)//2 if blen else len(data))

    @staticmethod
    def read_binary_file(filePath:str) -> str:
        data = b''
        with open(filePath,'rb') as f:
            data = f.read()
        return data.hex()

    @staticmethod
    def file_length(filePath:str) -> str:
        return str(len(bytes.fromhex(Helpers.read_binary_file(filePath))))

    @staticmethod
    def to_csharp_byte_array(data:str) -> str:
        # Takes in a string of hex
        return ', '.join([hex(b) for b in bytes.fromhex(data)])

    @staticmethod
    def binary_to_csharp_byte_array(filePath:str) -> str:
        return Helpers.to_csharp_byte_array(Helpers.read_binary_file(filePath))

    @staticmethod
    def random_key(keyLen=20) -> str:
        return os.urandom(keyLen).hex()
    
    @staticmethod
    def random_str(n=5) -> str:
        return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(n))

    @staticmethod
    def escape_bash(data:str):
        return re.sub(r'([\$`\\])', r'\\\1', data)
    
    @staticmethod
    def get_cwd():
        return os.path.join(os.getcwd(),"output")

"""
    Payload
        Parses the payload yaml into an actual object that we can use programatically
"""
class Payload:
    def __init__(self, name:str, variables:dict, commands:list, printCommands:list, description:str=None):
        self.name = name
        self.description = description
        self.variables = variables
        self.print = printCommands
        self.commands = commands

    def __repr__(self):
        payloadStr = f"{self.name}"
        if self.description:
            payloadStr += f"\t{self.description}"
        return payloadStr
    
    def generate_commands_print(self):
        self.commands = [Template(cmd).render(**self.variables) for cmd in self.commands]
        self.print = [Template(cmd).render(**self.variables) for cmd in self.print]
        print(f"[*][PAYLOAD] {self.name} - {self.description}")

        # Print the print commands
        if len(self.print)> 0:
            print(f"{'-'*28} Print")
            for cmd in self.print:
                print(cmd)
        
        # Execute the commands
        if len(self.commands) > 0:
            print(f"{'-'*28} Commands")
            for cmd in self.commands:
                print(cmd)
                # Ensure it isnt the test payload
                if self.name == 'test':
                    continue
                Payload.execute_command(cmd)
        print()

    @staticmethod
    def execute_command(cmd):
        args = ["/bin/bash",'-c',cmd]
        result = subprocess.run(args)

    @staticmethod
    def get_payload_files(payloadsPath:str="payloads") -> list:
        payloadsPath = os.path.join(os.getcwd(),payloadsPath)
        payloadFiles = [os.path.join(payloadsPath, file) for file in os.listdir(payloadsPath) if file.endswith(('.yaml','.yml'))]
        return payloadFiles

    @staticmethod
    def from_yaml(payloadFile:str, **variables) -> object:
        data = None
        with open(payloadFile, 'r') as f:
            data = yaml.safe_load(f)
        if data == None or len(data.keys()) == 0:
            raise ValueError(f"InvalidYAML, Seems like: {payloadFile} may be empty or does not contain value YAML!")
        
        # Set the name of the payload
        payloadName = os.path.splitext(os.path.basename(payloadFile))[0]
        
        # Get the description
        description = data.get('description',None)
        
        # Load the variables and assign accessible methods
        variables = variables | data.get('variables',{})

        # Execute the setup commands
        setupCommands = [Template(cmd).render(**variables) for cmd in data.get('setupCommands',[])]
        if len(setupCommands) > 0:
            print(f"{'-'*28} Payload {payloadName} Setup Commands")
            for cmd in setupCommands:
                print(cmd)
                Payload.execute_command(cmd)
            print()

        # Load the templates and extend the variables
        templates = data.get('templates',{})
        for name,template in templates.items():
            # Extend the template variables, allow access for variable
            templateVariables = template.get('variables',{})
            for tvName,tvValue in templateVariables.items():
                templateVariables[tvName] = Template(tvValue).render(**variables | templateVariables)
            templateVariables = variables | templateVariables
            # Render the actual template string
            templateStr = Template(template.get('template')).render(**templateVariables)
            variables['Templates'][name] = Helpers.escape_bash(templateStr)

        # Load and parse the print / commands
        commands = data.get('commands',[])
        printCommands = data.get('print',[])
        if len(commands) == 0 and len(printCommands) == 0:
            raise ValueError(f"InvalidPrintOrCommands, Payload {payloadName} ({payloadFile}) is missing print or commands!")
        
        # Create the object
        return Payload(payloadName, variables, commands, printCommands, description)
    
    @staticmethod
    def load_all(payloadsPath:str="payloads", **args) -> dict:
        payloads = {}
        payloadFiles = Payload.get_payload_files(payloadsPath)
        for payloadFile in payloadFiles:
            payload = Payload.from_yaml(payloadFile, **args)
            payloads[payload.name] = payload
        return payloads
    
    @staticmethod
    def get_all_metadata(payloadsPath:str="payloads") -> dict:
        payloads = {}
        payloadFiles = Payload.get_payload_files(payloadsPath)
        for payloadFile in payloadFiles:
            payload = {}
            with open(payloadFile, 'r') as f:
                data = yaml.safe_load(f)
            if data == None or len(data.keys()) == 0:
                raise ValueError(f"InvalidYAML, Seems like: {payloadFile} may be empty or does not contain value YAML!")
            # Set the name of the payload
            payloadName = os.path.splitext(os.path.basename(payloadFile))[0]
            # Get the description
            payload['description'] = data.get('description',None)
            payload['path'] = payloadFile
            payloads[payloadName] = payload
        return payloads


"""
    get_ip_address
        Get the IP address of tun0 or an interface
"""
def get_ip_address(lhost:str='tun0', verbose:bool=False) -> str:
    if not (lhost in ni.interfaces()):
        # We got an IP address
        return lhost
    ip = ni.ifaddresses(lhost)[ni.AF_INET][0]['addr']
    if verbose:
        print(f"[*] Found interface {lhost}")
        print(f"[*] Got IP: {ip}")
    return ip


"""
    list_payloads
        takes a dict of payloads and prints them then exits
"""
def list_payloads(payloads:dict):
    name_w = 50
    desc_w = 100
    print("[*] Available Payloads:")
    print(f"{'Name'.ljust(name_w)} Description")
    print(f"-"*(name_w+desc_w))
    for payloadName,payload in payloads.items():
        pStr = f"{payloadName.ljust(name_w)} {payload.get('description', '')}"
        print(pStr)
    sys.exit(0)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--lhost',default="tun0",help='The interface or IP to have payloads connect back to (Default: tun0)')
    parser.add_argument('-p','--payload',default="loader-compile",help=f"Payload to generate, accepts comma seperated payloads (Default: loader-compile)")
    parser.add_argument('-L','--list',default=False,action='store_true',help="List all the possible payloads")
    parser.add_argument('-v','--verbose',default=False,action='store_true',help="Verbose messages")
    args = parser.parse_args()
    # Build the base jina2 variables exposed to payload templates
    variables = {
        'Encoder': Encoder,
        'Helpers': Helpers,
        'Templates': {},
        'LHOST': get_ip_address(args.lhost, verbose=args.verbose)
    }
    # Load the payload metadata definitions
    payloads = Payload.get_all_metadata()
    # check if we are just listing the payloads
    if args.list:
        list_payloads(payloads)
    # Generate the selected Payload
    ptg = [p.strip() for p in args.payload.split(',')]
    for name in ptg:
        # Load the actual payload
        payload = Payload.from_yaml(payloads.get(name).get('path'), **variables)
        # Ignore unknown payloads
        if not payload:
            continue
        payload.generate_commands_print()
    print("\n[*] Done")
    sys.exit(0)
            


if __name__ == '__main__':
    main()





