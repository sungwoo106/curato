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
                FileName = "python3",
                Arguments = scriptPath,
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = AppContext.BaseDirectory
            };

            psi.Environment["INPUT_JSON"] = json;

            using var process = Process.Start(psi)!;
            string result = await process.StandardOutput.ReadToEndAsync();
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
