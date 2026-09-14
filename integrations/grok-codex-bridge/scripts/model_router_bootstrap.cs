using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

internal static class ModelRouterBootstrap
{
    private static void Pump(Stream input, Stream output)
    {
        byte[] buffer = new byte[8192];
        int count;
        while ((count = input.Read(buffer, 0, buffer.Length)) > 0)
        {
            output.Write(buffer, 0, count);
            output.Flush();
        }
    }

    // Microsoft command-line quoting: preserve quotes and trailing backslashes.
    internal static string Quote(string value)
    {
        var output = new StringBuilder("\"");
        int slashes = 0;
        foreach (char ch in value)
        {
            if (ch == '\\') { slashes++; continue; }
            if (ch == '"')
            {
                output.Append('\\', slashes * 2 + 1);
                output.Append(ch);
            }
            else
            {
                output.Append('\\', slashes);
                output.Append(ch);
            }
            slashes = 0;
        }
        output.Append('\\', slashes * 2);
        output.Append('"');
        return output.ToString();
    }

    public static int Main(string[] args)
    {
        try
        {
            string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            var values = new JavaScriptSerializer().Deserialize<Dictionary<string, string>>(
                File.ReadAllText(Path.Combine(folder, "bootstrap.json"), Encoding.UTF8));
            foreach (string key in new[] { "python_executable", "router_entry", "router_settings" })
                if (!Path.IsPathRooted(values[key]) || !File.Exists(values[key]))
                    throw new InvalidOperationException("A required local routing file is unavailable: " + key);
            var parts = new List<string> { "-B", values["router_entry"], "--settings", values["router_settings"], "--" };
            parts.AddRange(args);
            var encoded = new List<string>();
            foreach (string value in parts) encoded.Add(Quote(value));
            var start = new ProcessStartInfo(values["python_executable"], String.Join(" ", encoded.ToArray()));
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.WorkingDirectory = Environment.CurrentDirectory;
            start.RedirectStandardInput = true;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;
            // Explicit raw-byte pumps preserve stdio when the host has no console.
            using (Process process = Process.Start(start))
            {
                Task input = Task.Factory.StartNew(delegate {
                    try { Pump(Console.OpenStandardInput(), process.StandardInput.BaseStream); }
                    catch (IOException) { }
                    finally { try { process.StandardInput.Close(); } catch (IOException) { } }
                });
                Task output = Task.Factory.StartNew(delegate {
                    Pump(process.StandardOutput.BaseStream, Console.OpenStandardOutput());
                });
                Task errorOutput = Task.Factory.StartNew(delegate {
                    Pump(process.StandardError.BaseStream, Console.OpenStandardError());
                });
                process.WaitForExit();
                Task.WaitAll(output, errorOutput);
                return process.ExitCode;
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("Codex model router could not start: " + error.Message);
            return 1;
        }
    }
}
