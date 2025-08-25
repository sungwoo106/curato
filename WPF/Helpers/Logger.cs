using System;
using System.IO;
using System.Text;
using System.Windows;

namespace Curato.Helpers
{
    /// <summary>
    /// Static logger for debugging and error reporting
    /// </summary>
    public static class Logger
    {
        private static readonly string LogFilePath = Path.Combine(AppContext.BaseDirectory, "curato_debug.log");
        private static readonly object LogLock = new object();

        /// <summary>
        /// Logs a message to file and optionally shows a message box
        /// </summary>
        /// <param name="message">Message to log</param>
        /// <param name="showMessageBox">Whether to show message box</param>
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

        /// <summary>
        /// Logs an error message with optional exception details
        /// </summary>
        /// <param name="message">Error message</param>
        /// <param name="ex">Optional exception</param>
        public static void LogError(string message, Exception? ex = null)
        {
            var fullMessage = ex != null ? $"{message}\nException: {ex.Message}\nStackTrace: {ex.StackTrace}" : message;
            Log(fullMessage, true);
        }

        /// <summary>
        /// Logs an informational message
        /// </summary>
        /// <param name="message">Info message</param>
        public static void LogInfo(string message)
        {
            Log(message, false);
        }

        /// <summary>
        /// Gets the contents of the log file
        /// </summary>
        /// <returns>Log file contents or error message</returns>
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

        /// <summary>
        /// Clears the log file
        /// </summary>
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
