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
            var psi = new ProcessStartInfo
            {
                // Change this to your Python executable path
                FileName = @"C:\Users\sungw\AppData\Local\Programs\Python\Python310\python.exe",
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

            try
            {
                using var doc = JsonDocument.Parse(result);
                string? itinerary = doc.RootElement.GetProperty("itinerary").GetString();
                return new TripPlan { EmotionalNarrative = itinerary ?? result };
            }
            catch
            {
                return new TripPlan { EmotionalNarrative = result };
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine("Trip generation failed: " + ex.Message);
            return new TripPlan();
        }
    }
}
