using System;
using System.IO;
using System.Text;
using System.Windows;

namespace Curato.Helpers
{
    public static class Logger
    {
        private static readonly string LogFilePath = Path.Combine(AppContext.BaseDirectory, "curato_debug.log");
        private static readonly object LogLock = new object();

        public static void Log(string message, bool showMessageBox = false)
        {
            try
            {
                var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                var logMessage = $"[{timestamp}] {message}";

                // Write to log file
                lock (LogLock)
                {
                    File.AppendAllText(LogFilePath, logMessage + Environment.NewLine, Encoding.UTF8);
                }

                // Optionally show message box for critical errors
                if (showMessageBox)
                {
                    Application.Current?.Dispatcher?.Invoke(() =>
                    {
                        MessageBox.Show(logMessage, "Curato Debug Info", MessageBoxButton.OK, MessageBoxImage.Information);
                    });
                }
            }
            catch (Exception ex)
            {
                // If logging fails, at least try to show a message box
                try
                {
                    Application.Current?.Dispatcher?.Invoke(() =>
                    {
                        MessageBox.Show($"Logging failed: {ex.Message}\nOriginal message: {message}", "Logging Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    });
                }
                catch
                {
                    // Last resort - can't even show error message
                }
            }
        }

        public static void LogError(string message, Exception? ex = null)
        {
            var fullMessage = ex != null ? $"{message}\nException: {ex.Message}\nStackTrace: {ex.StackTrace}" : message;
            Log(fullMessage, true);
        }

        public static void LogInfo(string message)
        {
            Log(message, false);
        }

        public static string GetLogContents()
        {
            try
            {
                if (File.Exists(LogFilePath))
                {
                    return File.ReadAllText(LogFilePath, Encoding.UTF8);
                }
                return "Log file not found.";
            }
            catch (Exception ex)
            {
                return $"Failed to read log file: {ex.Message}";
            }
        }

        public static void ClearLog()
        {
            try
            {
                if (File.Exists(LogFilePath))
                {
                    File.Delete(LogFilePath);
                }
            }
            catch (Exception ex)
            {
                LogError($"Failed to clear log file: {ex.Message}");
            }
        }
    }
}
