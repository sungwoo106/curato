using System.Diagnostics;
using System.Text.Json;
using System.IO;
using Curato.Models;

public static class PlannerEngine
{
    public static async Task<TripPlan> GenerateTripPlan(TripRequest request)
    {
        try
        {
            string json = JsonSerializer.Serialize(request);
            var scriptPath = Path.Combine(AppContext.BaseDirectory, "generate_plan.py");
            
            // Debug: Log the resolved script path for troubleshooting
            System.Diagnostics.Debug.WriteLine($"Resolved script path: {scriptPath}");
            System.Diagnostics.Debug.WriteLine($"Script file exists: {File.Exists(scriptPath)}");
            System.Diagnostics.Debug.WriteLine($"Working directory: {AppContext.BaseDirectory}");
            
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"\"{scriptPath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = AppContext.BaseDirectory
            };
            psi.StandardOutputEncoding = System.Text.Encoding.UTF8;

            psi.Environment["INPUT_JSON"] = json;

            using var process = Process.Start(psi)!;
            string result = await process.StandardOutput.ReadToEndAsync();
            string error = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            // Debug: Log stderr output for troubleshooting
            if (!string.IsNullOrEmpty(error))
            {
                System.Diagnostics.Debug.WriteLine($"Python stderr output: {error}");
            }

            try
            {
                using var doc = JsonDocument.Parse(result);
                string? itinerary = doc.RootElement.GetProperty("itinerary").GetString();
                return new TripPlan { EmotionalNarrative = itinerary ?? result };
            }
            catch (Exception parseEx)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to parse Python output: {parseEx.Message}");
                System.Diagnostics.Debug.WriteLine($"Raw output: {result}");
                return new TripPlan { EmotionalNarrative = result };
            }
        }
        catch (Exception ex)
        {
            return new TripPlan();
        }
    }
}
