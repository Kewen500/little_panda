using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Program
{
    private static string FindPython(string appDir)
    {
        string scriptsDir = Path.Combine(appDir, ".venv", "Scripts");
        string pythonw = Path.Combine(scriptsDir, "pythonw.exe");
        if (File.Exists(pythonw))
        {
            return pythonw;
        }

        string python = Path.Combine(scriptsDir, "python.exe");
        if (File.Exists(python))
        {
            return python;
        }

        return "pythonw.exe";
    }

    [STAThread]
    private static void Main()
    {
        try
        {
            string appDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
                Path.DirectorySeparatorChar
            );
            string fallbackDir =
                @"C:\Users\User\Desktop\desktop window\api-usage-floating-widget";
            if (!File.Exists(Path.Combine(appDir, "app", "main.py"))
                && File.Exists(Path.Combine(fallbackDir, "app", "main.py")))
            {
                appDir = fallbackDir;
            }

            string python = FindPython(appDir);
            string mainFile = Path.Combine(appDir, "app", "main.py");

            if (!File.Exists(mainFile))
            {
                MessageBox.Show(
                    "Could not find app\\main.py next to the launcher.\n\nExpected folder:\n"
                        + appDir,
                    "API Balance Widget",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return;
            }

            ProcessStartInfo startInfo = new ProcessStartInfo();
            startInfo.FileName = python;
            startInfo.Arguments = "-m app.main";
            startInfo.WorkingDirectory = appDir;
            startInfo.UseShellExecute = false;
            startInfo.CreateNoWindow = true;

            Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                "Could not start API Balance Widget.\n\n" + ex.Message,
                "API Balance Widget",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
        }
    }
}
